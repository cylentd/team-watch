"""The rendered page, in Chromium, against a golden snapshot.

What one run captures, for every surface and its main toggles, at a desktop and a phone width:
`#view`, `#drawer` and `#modal` markup (headshot data URIs elided) and the computed style of the first
element carrying each class the CSS defines, over the properties a theme change would move.
A refactor that promises "no visual change" is proved here by an empty diff; an intended change
regenerates the golden with `pytest --update-golden` and the diff is the review.

Deterministic by construction: fixture inputs, Math.random seeded and Date.now pinned before load
(the gallery hides games that have kicked off), external requests
(Google Fonts) blocked so fallback fonts always apply, reduced-motion so no animation is mid-flight.
"""
import json
import os
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from impact import area_of  # noqa: E402  (scripts/impact.py maps a changed golden state the same way)

pytestmark = pytest.mark.render

GOLDEN_FILE = "render.json"
# My teams asks whose team first (teamswitch.js pickHTML, 2026-09-27). Every page here reads as David
# on his own Yahoo team unless a test picked another; the picker's own tests clear it (test_picker.py).
# And as David's own browser (data/owner.js): his Waivers, not the Most added list, unless a test
# clears tw-owner. The hash is read from owner.js, so a new token never needs a test edit.
def _owner_hash():
    import pathlib
    src = (pathlib.Path(__file__).parents[1] / "design" / "src" / "js" / "data" / "owner.js").read_text(encoding="utf-8")
    return re.search(r'OWNER_HASH = "([0-9a-f]{64})"', src).group(1)


OWNER_HASH = _owner_hash()
# The reader has also chosen Sheet (2026-09-28: Cards became the default, and its pack would open a
# stage over every roster state). test_roster_cards.py FRESH is the reader who never chose.
CHOSE_SHEET = ' if (!localStorage.getItem("tw-roster-mode")) localStorage.setItem("tw-roster-mode", "sheet");'
# And as a reader who follows David's three teams (2026-10-04, followLoad() is empty until a reader picks
# or stars: the page no longer defaults to David's rosters). That keeps the team switch's list and every
# Live "mine" (gdMine: the picked team, else a followed one) on David's teams, as these states drew them.
# A first visit with nothing is the state "live-nopick" and tests/test_live_mine.py.
FOLLOWING = ' if (!localStorage.getItem("tw-follow")) localStorage.setItem("tw-follow", JSON.stringify(["yahoo", "espn", "ayo"]));'
PICKED = ('try { if (!localStorage.getItem("tw-team")) localStorage.setItem("tw-team", "yahoo");'
          + CHOSE_SHEET + FOLLOWING +
          f' if (localStorage.getItem("tw-owner") === null) localStorage.setItem("tw-owner", "{OWNER_HASH}"); }} catch (e) {{}}\n')
VIEWPORTS = {"desk": (1400, 900), "phone": (390, 844)}
LOAD_MS = 30000     # the page load only; every other wait keeps open_at's 5 s (see there)
PROPS = ["color", "background-color", "border-top-color", "border-top-style", "border-top-width",
         "padding-top", "padding-left", "margin-top", "gap", "font-family", "font-size",
         "font-weight", "letter-spacing", "line-height", "opacity", "display", "grid-template-columns",
         "transition-duration"]

# (state name, how to reach it from a fresh load). Each is a list of steps: ("click", selector),
# ("eval", js) or ("wait", js condition). The nav is clicked, not set, so the wiring is exercised too.
GAMEDAY_FIX = pathlib.Path(__file__).resolve().parent / "fixtures" / "gameday.json"
# SF's game is on, DET's has not started; every other game is final.
LIVE_STATES = {"SF": "in_game", "DET": "pre_game"}


def LIVE_PLANT(states=None):
    """JS that swaps the page's leagues for week 2 of both (tests/fixtures/gameday.json) and plants a
    /api/stats reply, so nothing fetches. SEED pins Date.now(), so GD_AT is fresh on every run."""
    fix = json.loads(GAMEDAY_FIX.read_text(encoding="utf-8"))
    teams = {r["team"] for lg in (fix["espn"], fix["yahoo"]) for tm in lg["teams"].values() for r in tm["lineup"]}
    games = {tm: (states or LIVE_STATES).get(tm, "complete") for tm in sorted(teams)}
    reply = {"week": 2, "asof": "2026-09-12T12:00:00+00:00", "updated": None, "games": games, "stats": fix["stats"]}
    return (f"GD.leagues.splice(0, GD.leagues.length, {json.dumps(fix['espn'])}, {json.dumps(fix['yahoo'])});"
            f"GD_STATS = {json.dumps(reply)}; GD_AT = Date.now(); GD_ERR = '';")

# The nav is two levels since 2026-09-21: a group, then the view. Reaching a view is therefore
# two clicks, not one, except in a group of one where no sub-row is drawn at all. Spelling both
# out here (rather than trusting the group button's "return me to where I was") keeps a state
# reachable in the same way no matter which state ran before it.
GROUP = {"digest": "week", "roster": "league", "waivers": "league",   # Teams and League merged into League on 2026-10-05
         "recap": "league", "records": "league", "trades": "league", "teams": "league",
         "highlights": "scouting", "ranks": "scouting", "board": "scouting", "movers": "scouting", "matchups": "week", "usage": "scouting",
         "news": "week", "weather": "week", "weekrecap": "week", "preview": "week", "live": "week",
         "schedule": "scouting",
         "parlay": "bets", "build": "bets", "dfs": "bets"}
# Weather left the This week sub-row on 2026-10-05 (nav.js NAV_HIDDEN): it is reached by hash or navGo, not a tap.
# Schedule (Stats, 2026-10-05) is hidden the same way, because Stats' five tabs already fill a phone's sub-row.
HIDDEN = {"weather", "schedule"}


def go(leaf):
    if leaf in HIDDEN:
        return [("click", f".navitem[data-s='{GROUP[leaf]}']"), ("eval", f"navGo('{leaf}')")]
    steps = [("click", f".navitem[data-s='{GROUP[leaf]}']")]
    if len([k for k, g in GROUP.items() if g == GROUP[leaf] and k not in HIDDEN]) > 1:
        steps.append(("click", f"[data-leaf='{leaf}']"))
    return steps


def bdpick(q):
    """Fill a Board slot the way a reader does: the app's own search sheet, opened with a slot to
    fill instead of a profile to open. Driving it through searchOpen/searchPick rather than
    calling bdAdd is the point -- the handoff is the part that would break silently."""
    return [("click", "[data-bdadd]"),
            ("eval", f"document.getElementById('search-q').value = {q!r}; searchPaint()"),
            ("click", "#sr-0")]


MOVERS = go("movers")

# Find trades (2026-10-05). The reader is whoever `key` names; the builder opens from the roster sheet of the team
# `team` (a LIVE_TEAMS key) with the fixture's offers planted, since from file:// the page's own fetch is refused.
TRADE_OFFERS = (GAMEDAY_FIX.parent / "data" / "trade_offers.json").read_text(encoding="utf-8")
LB_OLD_SHAPE = ("() => { TB_DATA = (d => { for (const lg of Object.values(d.leagues)){ delete lg.lineup; delete lg.values; delete lg.other;"
                " for (const ps of Object.values(lg.teams)) for (const ks of Object.values(ps)) for (const os of Object.values(ks))"
                " os.forEach(o => delete o.drop); } return d; })(" + TRADE_OFFERS + "); }")
LB_AS = lambda key: f"localStorage.setItem('tw-team', '{key}')"
# A reader who has picked no team, looking at team `key`'s league (the League group's seat is VIEW then).
UNPICK = lambda key: ("eval", f"localStorage.removeItem('tw-team'); VIEW='{key}'; render()")
LB_BUILDER = lambda team: [("eval", "TB_DATA = " + TRADE_OFFERS), ("click", f"[data-lbopen='{team}']"), ("click", "[data-tbfind]")]


def _strip_game():
    """The fixture ESPN summary, shaped by api/game.py exactly as the endpoint serves it."""
    import importlib.util
    from conftest import FIXTURES, REPO
    spec = importlib.util.spec_from_file_location("game_fn", REPO / "api" / "game.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.shape(json.loads((FIXTURES / "data" / "espn_summary.json").read_text(encoding="utf-8")))


# performance.now() is pinned because the strip writes it into --ph, the clock its loops run on.
STRIP_OPEN = """(() => { const D = %s; performance.now = () => 1000;
  openStrip({id: "golden", away: D.away.abbr, home: D.home.abbr, week: D.week || 2}, "", null);
  stripMount(document.querySelector("#stripmodal .stbody"), D, null, null); })()""" % json.dumps(_strip_game())
STRIP_SEEK = """(() => { const s = document.querySelector("#stripmodal .stslider");
  s.value = 6; s.dispatchEvent(new Event("input")); })()"""
# The game sheet (2026-09-28): the fixture game shaped by the page's own gsShape, and a real Sleeper
# box for its two clubs. From file:// the sheet cannot fetch, so both are planted after it opens.
GAME_SUMMARY = (GAMEDAY_FIX.parent / "data" / "espn_summary.json").read_text(encoding="utf-8")
GAME_BOX = (GAMEDAY_FIX.parent / "data" / "sleeper_box.json").read_text(encoding="utf-8")
GAME_SHEET = """(() => { gsOpen({event: "1", away: "DET", home: "BUF"}, null);
  GS_GAME = gsShape(%s); GS_BOX = {box: %s}; GS_ERR = ""; gsPaint(); })()""" % (GAME_SUMMARY, GAME_BOX)
# Game day, 2026-10-04: league-wide leaders as GD_STATS.lead ({sleeperId: {n, pos, team, s, pts}}, what
# api/stats.py serves with lead=1). Seven scorers: two rushing TDs, three receiving, a QB with 3 pass TDs.
GD_LEAD = {
    "7547": {"n": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "pts": 31.4,
             "s": {"rec": 10, "rec_tgt": 12, "rec_yd": 180, "rec_td": 2}},
    "9226": {"n": "De'Von Achane", "pos": "RB", "team": "MIA", "pts": 27.1,
             "s": {"rush_att": 18, "rush_yd": 130, "rush_td": 1, "rec": 4, "rec_tgt": 5, "rec_yd": 40}},
    "8183": {"n": "Brock Purdy", "pos": "QB", "team": "SF", "pts": 24.0,
             "s": {"pass_cmp": 22, "pass_att": 30, "pass_yd": 290, "pass_td": 3}},
    "12481": {"n": "Cam Skattebo", "pos": "RB", "team": "NYG", "pts": 19.2,
              "s": {"rush_att": 20, "rush_yd": 90, "rush_td": 2}},
    "6801": {"n": "Tee Higgins", "pos": "WR", "team": "CIN", "pts": 17.8,
             "s": {"rec": 6, "rec_tgt": 8, "rec_yd": 98}},
    "4217": {"n": "George Kittle", "pos": "TE", "team": "SF", "pts": 15.5,
             "s": {"rec": 6, "rec_tgt": 7, "rec_yd": 85, "rec_td": 1}},
    "12526": {"n": "Tetairoa McMillan", "pos": "WR", "team": "CAR", "pts": 12.0,
              "s": {"rec": 5, "rec_tgt": 7, "rec_yd": 70}},
}
GD_LEAD_JS = f"GD_STATS.lead = {json.dumps(GD_LEAD)};"
# Live's tabs: the choice is a click, so the control's wiring is exercised too.
LIVE_TAB = lambda tab: [("click", f"[data-gdtab='{tab}']")]
# The Digest on a game day. Plants the fixtures' week 2 of both leagues, keeps the ESPN one, and gives every
# club a Sunday game (kickoff 12:00Z) except the Monday pair `mon` ([home, away], kickoff next day 15:00Z).
# Date.now is pinned to cfg.at, so "during a game" is a clock inside a planted game's window, not the wall's.
DG_WEEK = """(cfg) => {
  @@PLANT@@
  GD.leagues.splice(1);
  const lineup = Object.values(GD.leagues[0].teams).flatMap(tm => tm.lineup.map(r => r.team));
  const clubs = [...new Set(lineup)].filter(c => !cfg.mon.includes(c));
  const games = clubs.map(c => ({home: c, away: 'O' + c, kickoff: '2026-10-04T12:00:00Z', week: 2}));
  if (cfg.mon.length) games.push({home: cfg.mon[0], away: cfg.mon[1], kickoff: '2026-10-05T15:00:00Z', week: 2});
  GD_GAMES.splice(0, GD_GAMES.length, ...games);
  Date.now = () => Date.parse(cfg.at);
  GD_STATS.games = {};
  for (const g of games) for (const c of [g.home, g.away]) GD_STATS.games[c] = cfg.mon.includes(c) ? cfg.monState : cfg.sunState;
  GD_STATS.lead = @@LEAD@@;
  Object.assign(GD_STATS.stats, cfg.stats);
  GD_AT = Date.now(); GD_CLOCK = cfg.clock;
  if (cfg.noHurt) { LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = []; }
  DG_CUT = null; render();
}""".replace("@@LEAD@@", json.dumps(GD_LEAD)).replace("@@PLANT@@", LIVE_PLANT())


def DG_WEEK_AT(**cfg):
    base = {"at": "2026-10-04T14:00:00Z", "sunState": "in_game", "monState": "pre_game", "mon": [], "stats": {},
            "clock": {}, "noHurt": False}
    return "(%s)(%s)" % (DG_WEEK, json.dumps({**base, **cfg}))


# A profile's Season tab with this week's row drawn from the poll: SF's game is on and George Kittle
# has a line in the leaders, his week 3 having no log row (tests/test_profile.py LIVE_SEASON_PLANT).
PROFILE_LIVE_PLANT = """(() => {
  const g = LIVE_SCHEDULE.games.find(x => x.week === 3 && (x.home === 'SF' || x.away === 'SF'));
  const kick = Date.parse(g.kickoff);
  Date.now = () => kick + 3600000;
  if (GD.leagues.length) GD.leagues[0].week = 3; else GD.leagues.push({key: 'espn', week: 3, teams: {}, games: [], rules: {off: [], dst: []}});
  GD_CLOCK = {SF: {state: 'in', q: 3, clock: '4:12', half: false, detail: '', clubs: ['SF', 'KC']}};
  GD_STATS = {week: 3, games: {SF: 'in_game', KC: 'in_game'}, stats: {},
    lead: {'4881': {n: 'George Kittle', pos: 'TE', team: 'SF', pts: 16.2, s: {rec: 6, rec_tgt: 8, rec_yd: 82, rec_td: 1}}}};
  GD_AT = Date.now(); GD_ERR = '';
})()"""
# Conditions a step waits for ("wait" steps, page.wait_for_function), never a duration: Cards mode
# drawn, then (after Escape) no pack stage left on the page.
CARDS_DRAWN = "document.querySelector('#view .cardgrid .tc') !== null"
STAGE_GONE = "!document.querySelector('.pk-stage') && !document.body.classList.contains('pk-open')"
ESCAPE = """document.body.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true}))"""
# The fixture slate's picks sit under the deal table's floors (a 35% TD is a backup, no yards leg
# is called lower at 58%+), so Slips' tests open its pool to every Underdog-priced pick at the
# kickoff, TDs and yards kept apart as the real pool keeps them.
OPEN_POOL = """
tablePool = (kind = TABLE.kind) => {
  const w = tableWin(), at = PROPS.map((p, i) => i).filter(i => udPick(PROPS[i]) && inWin(PROPS[i], w));
  const td = at.filter(i => PROPS[i].mkt === 'TD'), safe = at.filter(i => PROPS[i].mkt !== 'TD');
  return kind === 'td' ? td : kind === 'safe' ? safe : [...td, ...safe];
};
TABLE.sig = ''; render();
"""


STATES = [
    # The Digest (This week, 2026-09-26), the page's default: the day picks the open row. Friday
    # opens Hurt (the fixture leads with a doubtful Puka Nacua), Tuesday opens Waiver adds, a tap
    # moves the one open row to Top 5, and a packet with every section empty says "nothing new" on
    # each row with nothing open. LIVE_DIGEST is a const, so the null block (no packet file) is
    # pinned in tests/test_digest.py instead.
    # Friday is 2026-09-18, inside the fixture's week 3 (its last game is KC @ SF, 2026-09-21): the
    # 25th, which it was until 2026-09-29, is after the week, where the preview rows fold into the wait.
    ("digest", [("eval", 'Date.now = () => Date.parse("2026-09-18T12:00:00Z")')] + go("digest")),
    # Tuesday and Monday are after the fixture week: the wait card stands in for Hurt, Matchups,
    # Weather and Top 5 (surface/digest/wait.js, 2026-09-29).
    ("digest-tuesday", [("eval", 'Date.now = () => Date.parse("2026-09-22T12:00:00Z")')] + go("digest")),
    # Monday 06:00 Pacific, the same Friday packet: every game has kicked off, so its preview rows
    # are in the wait card, Puka's lead gives way to the results, and Monday opens Results.
    ("digest-monday", [("eval", 'Date.now = () => Date.parse("2026-09-28T13:00:00Z")')] + go("digest")),
    # Top 5 sits below Results on a phone: opening it scrolls, and whether the header had slid away
    # by the snapshot was timing (the rebuild job's run 2026-09-28 caught it both ways). Back to the
    # top, instantly, the header is always shown.
    ("digest-top5", go("digest") + [("click", "[data-dgrow='t5'] .dg-head"),
                                    ("eval", "window.scrollTo({top: 0, behavior: 'instant'})")]),
    ("digest-empty", [("eval", "Object.assign(LIVE_DIGEST, {lead: null, hurt: [], calls: 0, record: null, best: [],"
                               " wx: [], near: null, adds: [], top5: [], up: [], down: [], gems: [], news: []})")]
                     + go("digest")),
    # The page opens on the Digest since 2026-09-26, so the roster states navigate there.
    ("teams-yahoo", go("roster")),
    # A first visit: no team picked in this browser, so My teams asks whose team first.
    ("teams-pick", [("eval", "localStorage.removeItem('tw-team')")] + go("roster")),
    ("teams-espn", [("eval", "VIEW='espn'; render()")] + go("roster")),
    # The third league (2026-09-29): AYO, a second Yahoo login, the first Yahoo team's shape.
    ("teams-ayo", [("eval", "VIEW='ayo'; render()")] + go("roster")),
    ("teams-modal", go("roster") + [("click", ".row")]),   # Joe Burrow: no matchup profile, the quiet state
    # Clips (2026-10-05): the ring opens a player's clip sheet; with no clips there is no reel and no ring.
    ("teams-clips-sheet", [("eval", "VIEW='espn'; render()")] + go("roster") + [("click", ".head[data-clips]")]),
    ("teams-clips-empty", [("eval", "LIVE_CLIPS.players = {}; LIVE_CLIPS.games = {}")] + go("roster")),
    # One league at a time since v2: the team on screen picks the cards, tiers, hero and rail.
    # SEED is a Saturday, so these are wire-watch mode (the rail leads, every row shown).
    ("waivers-espn", [("eval", "VIEW='espn'; render()")] + go("waivers")),
    ("waivers-yahoo", go("waivers")),
    ("waivers-ayo", [("eval", "VIEW='ayo'; render()")] + go("waivers")),
    # Anyone but David (data/owner.js): the league-wide Most added list in place of his advice.
    ("waivers-visitor", [("eval", "localStorage.setItem('tw-owner', '')")] + go("waivers")),
    ("waivers-claimday", [("eval", 'Date.now = () => Date.parse("2026-09-22T12:00:00Z")')] + go("waivers")),
    # The first card that flips: on a phone the Must claim, on a desktop (where a Must claim lies
    # open with no flip) the first Worth a claim.
    ("waivers-flipped", [("eval", "VIEW='espn'; render()")] + go("waivers") + [("click", ".wvc-flip >> visible=true")]),
    # My teams > League (2026-09-26): ESPN teams only. David's team, a leaguemate's (its own
    # matchup and rivalry), and week 1 picked by its chip.
    ("league-espn", [("eval", LB_AS("espn"))] + go("recap")),
    ("league-mate", [("eval", LB_AS("espn-run-it-back"))] + go("recap")),
    ("league-week1", [("eval", LB_AS("espn"))] + go("recap") + [("click", "[data-lgweek='1']")]),
    # Yahoo (2026-09-27). This week > League, the same for every reader: week 2 roasted with every box
    # shut, week 1 with no roast (scores only), a box opened by its toggle. This week > Records. Then My
    # teams > My recap for David's team, week 2 (his box open) and week 1.
    ("recap-yahoo", go("recap")),
    ("recap-yahoo-week1", go("recap") + [("click", "[data-lgweek='1']")]),
    ("recap-yahoo-sheet", go("recap") + [("click", "[data-lgsheet='10-9']")]),
    ("records-yahoo", go("records")),
    # Records' head to head for another manager (its chip), then that manager's first row as the grudge sheet.
    ("records-yahoo-pair", go("records") + [("eval", "const s = document.querySelector('[data-rcmgr]'); s.value = '3'; s.dispatchEvent(new Event('change', {bubbles: true}))"),
                                            ("click", "[data-rcpair] >> nth=0")]),
    ("records-yahoo-roster", go("records") + [("click", "[data-csroster='2025:champ']")]),
    # The League chip (2026-09-29 as a switch, the team switch since 2026-10-05): AYO's week 2 and its Records,
    # which have no history yet. AYO has no graded trades, so no Trades leaf: a #trades link lands on its Recap.
    ("recap-ayo", [("eval", LB_AS("ayo"))] + go("recap")),
    ("records-ayo", [("eval", LB_AS("ayo"))] + go("records")),
    ("trades-ayo", [("eval", LB_AS("ayo")), ("eval", "location.hash = '#trades'")]),
    # League > Trades (2026-09-28): the page, then Lateef's trades open (a 2026 one still open, a trade
    # whose tree verdict differs, the seasons it decided) and every "decided a season" card shown (a
    # phone swipes through all of them and has no Show all).
    ("trades", go("trades")),
    ("trades-open", go("trades") + [("click", "[data-trmgr='6']"), ("eval", "document.querySelector('[data-trall]')?.click()")]),
    # League > Teams (2026-10-05): the board. The suite's reader is on the Madden Curse, whose fixture is the
    # old scrape with no slots, so the default is the empty state; ESPN's and AYO's boards by the switch, ESPN's
    # sorted by RB. The reader here has no team in ESPN's or AYO's league, so those boards carry the "Tap your team
    # to set it" line. A team opens as a full page (2026-10-05, no sheet): with "This is my team" for that reader,
    # then "Your team" once they tap it, and the board again with their team pinned.
    ("lboard-yahoo", go("teams")),
    ("lboard-espn", [("eval", LB_AS("espn"))] + go("teams")),
    ("lboard-ayo", [("eval", LB_AS("ayo"))] + go("teams")),
    ("lboard-sorted", [("eval", LB_AS("espn"))] + go("teams") + [("click", "[data-lbsort='RB']")]),
    ("lboard-team", [UNPICK("espn")] + go("teams") + [("click", ".lb-row .lb-team")]),
    ("lboard-team-mine", [UNPICK("espn")] + go("teams") + [("click", "[data-lbopen='espn-run-it-back']"), ("click", "[data-lbmine]")]),
    ("lboard-board-picked", [UNPICK("espn")] + go("teams") + [("click", "[data-lbopen='espn-run-it-back']"),
                                                                                ("click", "[data-lbmine]"), ("click", ".lbp-back")]),
    # Find trades (2026-10-05): the team page's lime button for a team in the reader's own league (the reader is
    # on ESPN here, the suite's David being on the Madden Curse), "This is my team" for a reader whose team is in
    # another league, and the builder page from the fixture's offers (planted: from file:// the browser refuses the
    # fetch, and logs it, so -error replaces fetch with a refusal). Bold is the first tab; Fair; a tab with no
    # offer; a pair with no entry.
    ("lboard-offers-button", [("eval", LB_AS("espn"))] + go("teams") + [("click", "[data-lbopen='espn-run-it-back']")]),
    ("lboard-offers-pick", [UNPICK("espn")] + go("teams") + [("click", "[data-lbopen='espn-run-it-back']")]),
    ("lboard-offers-bold", [("eval", LB_AS("espn"))] + go("teams") + LB_BUILDER("espn-run-it-back")),
    ("lboard-offers-fair", [("eval", LB_AS("espn-run-it-back"))] + go("teams") + LB_BUILDER("espn") + [("click", "[data-tbtab='fair']")]),
    ("lboard-offers-empty", [("eval", LB_AS("espn"))] + go("teams") + LB_BUILDER("espn-run-it-back") + [("click", "[data-tbtab='fair']")]),
    ("lboard-offers-none", [("eval", LB_AS("ayo-don-wick"))] + go("teams") + LB_BUILDER("ayo")),
    ("lboard-offers-error", [("eval", LB_AS("espn")), ("eval", "void (window.fetch = () => Promise.reject(new TypeError('offline')))")]
                           + go("teams") + [("click", "[data-lbopen='espn-run-it-back']"), ("click", "[data-tbfind]"), ("eval", "tbLoad()")]),
    # Edit mode (2026-10-05): from the third offer (Purdy for Brown and Watson, which drops Gordon), after taking Watson out
    # of the package, from an empty package (Make your own), and a file with no lineup, values or drops (Edit is shut).
    ("lboard-edit", [("eval", LB_AS("espn"))] + go("teams") + LB_BUILDER("espn-run-it-back") + [("click", "[data-tbedit='2']")]),
    ("lboard-edit-toggled", [("eval", LB_AS("espn"))] + go("teams") + LB_BUILDER("espn-run-it-back")
                            + [("click", "[data-tbedit='2']"), ("click", ".tb-r[data-tbpick='Christian Watson']")]),
    ("lboard-edit-own", [("eval", LB_AS("espn"))] + go("teams") + LB_BUILDER("espn-run-it-back") + [("click", "[data-tbown]")]),
    ("lboard-offers-oldshape", [("eval", LB_AS("espn"))] + go("teams") + [("eval", LB_OLD_SHAPE)]
                               + [("click", "[data-lbopen='espn-run-it-back']"), ("click", "[data-tbfind]")]),
    ("myrecap-yahoo", [("eval", LB_AS("yahoo"))] + go("recap")),
    ("myrecap-ayo", [("eval", LB_AS("ayo"))] + go("recap")),
    ("myrecap-yahoo-week1", [("eval", LB_AS("yahoo"))] + go("recap") + [("click", "[data-lgweek='1']")]),
    # The fixture's week-3 pairings never met, so this seeds three meetings before the view draws.
    ("myrecap-yahoo-margins", [("eval", "() => { const m = [[2024, 3, 12.5, 0], [2025, 6, -30.25, 0], [2025, 14, 4.1, 1]];"
                                        " LGS.yahoo.h2h['9']['3'] = {w: 2, l: 1, t: 0, since: 2024, big: {v: 12.5, y: 2024, wk: 3}, m};"
                                        " LGS.yahoo.h2h['3']['9'] = {w: 1, l: 2, t: 0, since: 2024, big: {v: 30.25, y: 2025, wk: 6},"
                                        " m: m.map(x => [x[0], x[1], -x[2], x[3]])}; }")]
                               + [("eval", LB_AS("yahoo"))] + go("recap") + [("click", "[data-lgmargins]")]),
    ("waivers-folds", go("waivers") + [("click", "summary.wvfold-s >> nth=0"),
                                       ("click", "summary.wvfold-s >> nth=1")]),   # spec + stash open
    # The modal is panes since 2026-09-22, so each one is its own state: the tab bar only renders
    # the pane that is open, and a pane that renders nothing is dropped from the bar entirely (a
    # back has no target depth, a passer no red zone, a player with no pedigree no Bio). Every
    # open lands on Season since 2026-09-28, so the plain open is that pane; the radar is its own
    # state, opened from the sphere in the head.
    ("profile-wr-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')")]),
    ("profile-wr-usage-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-pftab='usage']")]),
    ("profile-wr-matchup-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-pftab='matchup']")]),
    ("profile-wr-props-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-pftab='props']")]),
    ("profile-wr-sheet-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal .pf-orb")]),
    # Compare (2026-09-30): the picker from the head's button, then the sheet with two picks ticked.
    ("profile-wr-compare-picker-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-compare]")]),
    ("profile-wr-compare-modal", go("roster") + [("click", ".row:has-text('Amon-Ra St. Brown')"), ("click", "#modal [data-compare]"),
        ("click", "#modal .cmp-row >> nth=0"), ("click", "#modal .cmp-row >> nth=1"), ("click", "#modal [data-cmp=go]")]),
    ("profile-rb-modal", go("roster") + [("click", ".row:has-text('Chase Brown')"), ("click", "#modal [data-pftab='matchup']")]),
    ("profile-rb-bio-modal", go("roster") + [("click", ".row:has-text('Chase Brown')"), ("click", "#modal [data-pftab='bio']")]),
    # SF's starters-out count is null (no snap-count release yet) -- the shape live data shows
    # until ff-jarvis lands its new fields -- so the line falls back to the plain injury-report
    # count instead of the starters-out cell DET and CIN cover. Kittle is SF only on the ESPN
    # roster fixture, so this is the one state that switches leagues before opening a profile.
    ("profile-te-matchup-modal", [("eval", "VIEW='espn'; render()")] + go("roster") +
                                 [("click", ".row:has-text('George Kittle')"),
                                  ("click", "#modal [data-pftab='matchup']")]),
    ("profile-bye-modal", go("roster") + [("click", ".row:has-text('Jahmyr Gibbs')")]),
    # The Board: the leaderboard it arrives as, the same board as a duel, and a WR board because
    # that position publishes the most elite bars -- the one mark that is drawn only on the lanes
    # whose axis has a published threshold.
    ("board", go("board")),
    # Chase Brown and Skattebo rather than two arbitrary backs: both are in the fixture's archetype
    # block, so this state is the only one that reviews a rendered role and style label. Skattebo
    # carries a null style with its reason ("career carries < 250") and a null role with his, which
    # is the path a blank would silently pass. Picking players the block does not cover renders the
    # lanes and nothing else, which is what this state did before.
    ("board-two", go("board") + bdpick("chase brown") + bdpick("skattebo")),
    # The quarterback label: a style with no role beside it, because role is not a field for the
    # position, and the reason has to render where the word would be. Burrow rather than the
    # fixture's flag-carrying passer: wanted_slugs deliberately excludes the usage grid (build.py),
    # and with no pool block in the fixture the only archetype records that survive the cut are
    # roster and prop players. The `goal_line_runner` flag is therefore not reachable from a
    # fixture-built page at all, and is checked against the live build instead.
    ("board-qb", go("board") + [("click", "[data-bdpos='QB']")] + bdpick("burrow")),
    ("board-wr", go("board") + [("click", "[data-bdpos='WR']")]),
    # The list's second page: the pager turns it in place (a list since 2026-09-26). From 1100px the
    # fixture's WRs fit one page of two lists (2026-09-27), so the desk golden records that page.
    ("board-wr-page2", go("board") + [("click", "[data-bdpos='WR']"),
                                      ("eval", "document.querySelector(\".bd-pager [data-bdpage='2']\")?.click()")]),
    # Players > Ranks (2026-09-26): a position's tiers, and FLEX with its "RB3" per row.
    ("ranks", go("ranks")),
    ("ranks-flex", go("ranks") + [("click", "[data-rkpos='FLEX']")]),
    # This week > Weather (2026-09-26): week 2's four games, the dome first, then the rest by wind
    # (NE windy, IND retractable, SEA with no forecast yet); DET's players listed under DET @ SEA.
    ("weather", go("weather")),
    # Stats > Schedule (2026-10-05, plan U7): the easiest RB schedules for the next 4 weeks, byes marked; the
    # playoff weeks for TE. Hidden from the sub-row, so go() opens it with navGo.
    ("schedule", go("schedule")),
    ("schedule-te-playoffs", go("schedule") + [("click", "[data-sospos='TE']"), ("click", "[data-soswin='playoffs']")]),
    # This week > Recap (2026-10-05, storyboard option C): the banner, a three-tab bar, then the tab's cards,
    # from the fixture's week 4 recap (8 of 16 games final). Players is first; Busts is the phone's list tab
    # (a desktop draws all three open); Show all opens the touchdown list.
    ("weekrecap", go("weekrecap")),
    ("weekrecap-busts", go("weekrecap") + [("eval", "document.querySelector(\"[data-wrlist='busts']\").click()")]),   # the desk has no bar to tap
    ("weekrecap-tds-all", go("weekrecap") + [("click", "[data-wrtds]")]),
    ("weekrecap-scores", go("weekrecap") + [("click", "[data-wrtab='scores']")]),
    ("weekrecap-claude", go("weekrecap") + [("click", "[data-wrtab='claude']")]),
    # This week > Preview (2026-09-29, slate and dossier): the slate (a phone) or the rail beside the
    # Thursday game (a desktop); DET @ CAR's dossier, the fullest; Monday's, with no take yet.
    ("preview", go("preview")),
    ("preview-dossier", go("preview") + [("click", "[data-pvopen='2']")]),
    ("preview-notake", go("preview") + [("click", "[data-pvopen='4']")]),
    # From this game to your slip (2026-10-03): game 3 made the props slate's SEA @ SF, Kittle named
    # in its take, his receiving yards tapped Higher, so the tray and the "on slip" mark show.
    ("preview-slip", go("preview") + [("eval", """(() => { const g = LIVE_PREVIEW.games[3]; g.away = 'SEA'; g.home = 'SF';
      g.take.players = [{n: 'George Kittle', slug: 'george-kittle', pos: 'TE', team: 'SF', proj: 9.1, call: 'up', why: 'Seattle allows the most TE points.'}];
      PV_I = 3; PV_OPEN = true; render(); })()"""), ("click", ".pva.handoff [data-side='higher']")]),
    # Past games (2026-10-05, picks 1A and 2A; the record card before): opened from its row under the slate
    # on week 1, the fixture's earlier graded week; and the slate before any graded week, with no such row.
    ("preview-record", go("preview") + [("click", "[data-pvarcwk]")]),
    ("preview-record-empty", [("eval", "LIVE_PREVIEW.record.weeks.splice(0)")] + go("preview")),
    # Role, leaf `movers` (2026-09-29; Movers' share cards before): the fixture's role board, all
    # positions, one position, every row shown, no board at all, and a row opening the profile.
    ("role", MOVERS),
    ("role-wr", MOVERS + [("click", "[data-rvpos='WR']")]),
    ("role-empty", [("eval", "LIVE_ROLE.rows.splice(0)")] + MOVERS),
    ("role-modal", MOVERS + [("click", "[data-rvopen]")]),
    # Players > Highlights (2026-09-29): the fixture is the real week 4 run's packet; empty says so.
    ("highlights", go("highlights")),
    ("highlights-empty", [("eval", "LIVE_HIGHLIGHTS.views.splice(0)")] + go("highlights")),
    # The usage grid: the default RB level view on the newest week most teams have played, the
    # same grid as week-over-week change (the mode the level view cannot show; the week and the
    # reading sit in the panel the bar's last chip opens since 2026-09-25), a QB grid because its
    # columns are the ones with no counterpart anywhere else in the app, and the profile modal.
    # Start/Sit v3 (2026-10-04): the fixture week (tests/fixtures/data/startsit_v3.json) holds ten SMASH
    # players, four bold STARTs and five bold SITs, and a record with week 5 graded. -open opens the
    # first bold call to its reasons, the opened row's link opens the profile, and a week with nothing
    # yet says each of those in its own place: no week graded (a calm record), no bold calls (one line),
    # no calls at all (Blip). LIVE_SS3 is a const, so the missing block is pinned in tests/test_startsit_v3.py.
    ("matchups", go("matchups")),
    ("matchups-open", go("matchups") + [("click", "[data-mukey^='t:'] .mu-call-h")]),
    ("matchups-modal", go("matchups") + [("click", "[data-mukey^='t:'] .mu-call-h"),
                                         ("click", ".mu-call[data-open] [data-muslug]")]),
    ("matchups-nograde", [("eval", "Object.assign(LIVE_SS3.record, {weeks: [], last_week: [], smash: {hit: 0, miss: 0, void: 0},"
                                   " start: {hit: 0, miss: 0, void: 0}, sit: {hit: 0, miss: 0, void: 0},"
                                   " fun: {fantasypros: {hit: 0, miss: 0}, pitcherlist: {hit: 0, miss: 0}}})")]
                         + go("matchups")),
    ("matchups-notakes", [("eval", "LIVE_SS3.takes.length = 0")] + go("matchups")),
    ("matchups-nocalls", [("eval", "LIVE_SS3.takes.length = 0; LIVE_SS3.smash.length = 0")] + go("matchups")),
    ("usage", go("usage")),
    ("usage-panel", go("usage") + [("click", "[data-upanel]")]),
    ("usage-change", go("usage") + [("click", "[data-upanel]"), ("click", "[data-umode='change']")]),
    ("usage-qb", go("usage") + [("click", "[data-upos='QB']")]),
    ("usage-modal", go("usage") + [("click", "[data-usage]")]),
    # Bets since 2026-09-25: Slips (leaf `parlay`) and Build, the book in the settings panel the
    # bar's last chip opens, and the slip in a sheet the tray opens.
    ("parlay-underdog", go("parlay")),
    ("parlay-dk", go("parlay") + [("click", "[data-betspanel]"), ("click", "[data-parlaybook='dk']")]),
    ("parlay-dk-mine", go("parlay") + [("click", "[data-betspanel]"), ("click", "[data-parlaybook='dk']"),
                                       ("click", "[data-tray]"), ("click", "[data-preset='mine']")]),
    ("build-underdog", go("build")),
    ("build-panel", go("build") + [("click", "[data-betspanel]")]),
    # The research board (2026-10-03; it replaced the deal table): the Sunday tab, Monday night's
    # game on All, St. Brown's player sheet with two legs on, and the tray's sheet with a saved slip.
    ("parlay-day", go("parlay") + [("click", ".bets-tabsrow [data-gwin]")]),
    ("parlay-board-mon", go("parlay") + [("eval", "GAL_WIN = 'evening-mon'; render()"), ("click", "[data-slchip='all']")]),
    ("parlay-player", go("parlay") + [("eval", "GAL_WIN = 'evening-mon'; render()"), ("click", "[data-slchip='all']"),
                                      ("click", ".sl-row[data-slplayer='amonra-st-brown']"),
                                      ("click", "#legsheet [data-slpick][data-side='higher']"),
                                      ("click", "#legsheet .sl-ln:nth-child(2) [data-side='lower']")]),
    ("parlay-saved", go("parlay") + [("eval", "GAL_WIN = 'evening-mon'; render()"),
                                     ("eval", "slipSet(PROPS.findIndex(p => p.slug === 'amonra-st-brown' && p.mkt === 'REC'), 'higher'); render()"),
                                     ("click", "[data-slsave]"), ("click", "[data-tray]")]),
    # The leg sheet (2026-09-27), from Build's ⓘ: Tee Higgins' receptions, whose log carries
    # per-game usage and whose opponent (NYJ) has two starters out.
    ("parlay-legsheet-recs", go("parlay") + [("eval", "legSheetOpen(PROPS.findIndex(p => p.n === 'Tee Higgins' && p.mkt === 'RECS'))")]),
    ("dfs-yahoo", go("dfs")),
    # DFS since 2026-09-25: the strategy as the bar's chips, the site and "how this works" in the
    # panel its last chip opens.
    ("dfs-dk", go("dfs") + [("click", "[data-dfspanel]"), ("click", "[data-dfssite='dk']")]),
    ("dfs-contrarian", go("dfs") + [("click", "[data-topmode='contrarian']")]),
    ("dfs-explain", go("dfs") + [("click", "[data-dfspanel]"), ("click", "[data-explain]")]),   # the drawer
    ("news-injury", go("news") + [("click", "[data-newscat='injury']")]),
    ("news", go("news")),
    # A fresh browser has no saved passphrase, so this is the locked state: the form, not just
    # the composer. Deterministic because the day's counter starts at 0 in empty localStorage.
    ("chat-open", [("click", "#chatfab")]),
    ("chat-ready", [("eval", "chatSetPass('x')"), ("click", "#chatfab")]),
    # The reason it is a floating panel and not a tab: it stays open over another surface, so
    # you can read a player's row while asking about him. #view must still be Movers here.
    ("chat-over-movers", MOVERS + [("click", "#chatfab")]),
    # Player search: idle (the roster, since a fresh browser has no recents), and a query that
    # hits a typo, a hyphenated name and two leagues' tags at once.
    ("search-idle", [("click", "#navsearch")]),
    ("search-typed", [("click", "#navsearch"),
                      ("eval", "document.getElementById('search-q').value = 'brwon'; searchPaint()")]),
    # Live plants week 2 of both leagues (tests/fixtures/gameday.json) and a reply, so nothing
    # fetches: SF's game on, DET's not started, the rest final.
    ("live-board", [("eval", LIVE_PLANT())] + go("live")),
    # A score that just moved wears its "+6.0" for a few seconds.
    ("live-moved", [("eval", LIVE_PLANT() + "GD_PULSE = {'8183': 6.0};")] + go("live")),
    ("live-yahoo", [("eval", LIVE_PLANT())] + go("live") + [("click", "[data-gdleague='yahoo']")]),
    # A first visit (2026-10-04): no team picked or followed, so no side is "mine": neutral BY chips,
    # no "you" under the median, and one line that opens My teams.
    ("live-nopick", [("eval", "localStorage.removeItem('tw-team'); localStorage.removeItem('tw-follow')"),
                     ("eval", LIVE_PLANT())] + go("live")),
    # Sleeper stopped answering: the last good board stays, the stamp says how old it is.
    ("live-stale", [("eval", LIVE_PLANT() + "GD_ERR = 'Could not reach Sleeper. Trying again.'; GD_BUSY = true;")]
                   + go("live")),
    # A first visit before any reply: lineups with projections, a line saying it is reading.
    ("live-loading", [("eval", LIVE_PLANT() + "GD_STATS = null; GD_BUSY = true;")] + go("live")),
    # The only state that lets gdFetch run: from file:// it must say so once, never log an error.
    ("live-unserved", [("eval", LIVE_PLANT() + "GD_STATS = null; GD_ERR = ''; GD_BUSY = false; GD_AT = 0;")]
                      + go("live")),
    # The game sheet over Live: the fixture game's scoreboard, plays by drive, top scorers, box score.
    ("live-game", [("eval", LIVE_PLANT())] + go("live") + [("eval", GAME_SHEET)]),
    # Live's other tabs (2026-10-04): Games (every game of the week by state), TDs (who has scored, from
    # the league-wide leaders: rush and rec TDs only, a QB's passing TDs do not count) and League.
    ("live-games", [("eval", LIVE_PLANT() + GD_LEAD_JS)] + go("live") + LIVE_TAB("games")),
    ("live-tds", [("eval", LIVE_PLANT() + GD_LEAD_JS)] + go("live") + LIVE_TAB("tds")),
    ("live-league", [("eval", LIVE_PLANT())] + go("live") + LIVE_TAB("league")),
    # The Digest on a game day (2026-10-04): Date.now inside the Sunday window with a game in progress, the
    # banner is the top score and Right now lists five; then the day after, every game final but Monday
    # night's (CHI @ DEN, none of the ESPN team's starters), which draws the Monday card.
    ("digest-live", go("digest") + [("eval", DG_WEEK_AT(noHurt=True, clock={"DET": {
        "state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["DET"]}}))]),
    ("digest-mnf", go("digest") + [("eval", DG_WEEK_AT(at="2026-10-05T09:00:00Z", sunState="complete",
                                                       mon=["CHI", "DEN"], stats={"4217": {"rec": 5, "rec_yd": 600}}))]),
    # A profile's Season tab, this week's row drawn live from the poll (week 3, SF on the clock).
    ("profile-live", [("eval", "VIEW='espn'; render()")] + go("roster") + [("eval", PROFILE_LIVE_PLANT),
                     ("click", ".row:has-text('George Kittle')")]),
    # The play strip (2026-09-27): the real dialog, which from file:// says it cannot fetch, then
    # the fixture game mounted into it with the real stripMount. A finished game opens at kickoff
    # and never plays by itself, so the frame is fixed; -seek moves the scrubber to play 6.
    ("strip-kickoff", go("roster") + [("eval", STRIP_OPEN)]),
    ("strip-seek", go("roster") + [("eval", STRIP_OPEN), ("eval", STRIP_SEEK)]),
    # The pack (2026-09-27): Cards opens the week's pack on its own stage, on <body>; Escape puts
    # it back on the page above the dealt cards.
    ("teams-cards-stage", [("eval", "VIEW='espn'; render()")] + go("roster")
                          + [("click", "[data-rmode='cards']"), ("wait", CARDS_DRAWN)]),
    ("teams-cards", [("eval", "VIEW='espn'; render()")] + go("roster")
                    + [("click", "[data-rmode='cards']"), ("wait", CARDS_DRAWN), ("eval", ESCAPE), ("wait", STAGE_GONE)]),
]

SEED = """
(() => { let s = 0x2f6e2b1; Math.random = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; })();
Date.now = () => Date.parse("2026-09-12T12:00:00Z");   // before every fixture kickoff, forever
""" + PICKED

PROBE = """
(props) => {
  const classes = new Set();
  for (const sheet of document.styleSheets) {
    let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    const walk = rs => { for (const r of rs) { if (r.selectorText) for (const m of r.selectorText.matchAll(/\\.([A-Za-z_][\\w-]*)/g)) classes.add(m[1]); if (r.cssRules) walk(r.cssRules); } };
    walk(rules);
  }
  const out = {};
  for (const c of [...classes].sort()) {
    const el = document.querySelector("." + CSS.escape(c));
    if (!el) continue;
    const cs = getComputedStyle(el);
    out[c] = props.map(p => cs.getPropertyValue(p)).join("|");
  }
  const strip = h => h.replace(/data:image\\/webp;base64,[A-Za-z0-9+/=]+/g, "data:webp");
  return {view: strip(document.getElementById("view").innerHTML),
          drawer: strip(document.getElementById("drawer").innerHTML),
          drawerOpen: document.getElementById("drawer").classList.contains("on"),
          modal: strip(document.getElementById("modal").innerHTML),
          modalOpen: document.getElementById("modal").classList.contains("on"),
          // The chat panel lives outside #view so it survives a surface change, which also means
          // the two probes above would never see it.
          chat: strip(document.getElementById("chatdock").innerHTML),
          chatOpen: document.getElementById("chatdock").classList.contains("on"),
          // The search sheet is outside #view for the same reason.
          search: strip(document.getElementById("search-list").innerHTML),
          searchOpen: !document.getElementById("search").hidden,
          // The leg sheet too (2026-09-27).
          legsheet: strip(document.getElementById("legsheet").innerHTML),
          legsheetOpen: document.getElementById("legsheet").classList.contains("on"),
          // The play strip's dialog and the pack's stage (2026-09-27): the stage hangs off <body>,
          // outside every root above, and the strip's CSS was proven by no state until these.
          strip: strip(document.getElementById("stripmodal").innerHTML),
          stage: strip(document.querySelector(".pk-stage")?.outerHTML || ""),
          styles: out};
}
"""


def watch_errors(page, into=None):
    """Collect the page's uncaught exceptions and console errors, into `into` when a list is given
    (pages that share one list). Blocked externals (the font stylesheet) log "Failed to load
    resource"; that one is expected."""
    errors = [] if into is None else into
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and not m.text.startswith("Failed to load resource") else None)
    return errors


def open_at(browser, page_file, size, hash_="", init=()):
    """Open the page at a size, with a hash or pinned-clock init scripts: (ctx, page, errors)."""
    ctx = browser.new_context(viewport={"width": size[0], "height": size[1]}, reduced_motion="reduce")
    try:
        page = ctx.new_page()
        page.set_default_timeout(5000)     # a missing control is a bug, not something to wait 30 s for
        errors = watch_errors(page)
        page.route(re.compile(r"^https?://"), lambda route: route.abort())
        page.add_init_script(SEED)
        for script in init:
            page.add_init_script(script)
        # Loading is not a missing control: the ~6 MB page parses in about 1 s alone, but over 5 s
        # with every worker's Chromium starting at once (two scheduled runs lost 32 tests, 2026-10-05).
        page.goto(page_file.as_uri() + hash_, timeout=LOAD_MS)
        page.wait_for_function("document.getElementById('view').children.length > 0", timeout=LOAD_MS)
    except BaseException:
        ctx.close()      # a page that never drew is the caller's to close, but the caller never got it
        raise
    return ctx, page, errors


def open_page(browser, page_file, viewport):
    return open_at(browser, page_file, viewport)


def drive(page, steps):
    for kind, arg in steps:
        if kind == "click":
            page.locator(arg).first.click()
        elif kind == "wait":
            page.wait_for_function(arg)
        else:
            page.evaluate(arg)
    # Scroll events (the header hiding, hidebar.js) fire in the next rendering step, not after any
    # fixed time: on a loaded machine 50 ms passed without one (2026-09-27, run in parallel).
    page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")


AREAS = sorted({area_of(s) for s, _ in STATES})

# The golden is taken in slices of at most SLICE_MAX states (both viewports each), one xdist group a
# slice (conftest). An area of more states splits into near-equal runs, named `<area>-1`, `<area>-2`:
# as one group Teams' 18 states (lboard) took 38 s on one worker, the floor under the whole suite's
# wall time (2026-10-05). Every state still opens its own fresh page, so the split moves no capture.
SLICE_MAX = 6


def _slices():
    names = {}
    for s, _ in STATES:
        names.setdefault(area_of(s), []).append(s)
    out = {}
    for area in AREAS:
        runs = -(-len(names[area]) // SLICE_MAX)
        size = -(-len(names[area]) // runs)
        for k in range(runs):
            out[area if runs == 1 else f"{area}-{k + 1}"] = (area, names[area][k * size:(k + 1) * size])
    return out


SLICES = _slices()                                                  # slice -> (area, its states)
SLICE_OF = {s: key for key, (_, states) in SLICES.items() for s in states}


def by_slice(values, slice_of):
    """Parametrize over values, each marked with its area so `--areas` can pick it, and with its
    slice, which conftest makes the xdist group."""
    return [pytest.param(v, marks=pytest.mark.area(SLICES[slice_of(v)][0], slice=slice_of(v)), id=v) for v in values]


def fenced_selectors():
    """[css file, source selector, its fence's roots] for every rule design/src/scope.json fences.
    State pseudo-classes and pseudo-elements are dropped: `.a:hover` is checked as `.a`."""
    import assemble
    import scope_css
    state = re.compile(r"::?(hover|focus-visible|focus-within|focus|active|visited|before|after|placeholder"
                       r"|selection|backdrop|marker|-webkit-[\w-]+|-moz-[\w-]+)(\([^)]*\))?")
    out = []
    for rel, names in scope_css.load(assemble.SCOPE)["fenced"].items():
        roots = ", ".join(scope_css.roots(names))
        text = (assemble.SRC / "css" / rel).read_text(encoding="utf-8")
        for sels in {p for _, _, p in scope_css.rules(text)}:
            for sel in scope_css.split_selectors(sels):
                sel = state.sub("", re.sub(r"/\*.*?\*/", "", sel, flags=re.S)).strip()
                if sel:
                    out.append([rel, sel, roots])
    return out


# Every element a fenced rule was written for but that sits outside the fence, so the rule no
# longer reaches it: the leg sheet's OUT tag rendered grey for this reason (2026-09-27).
OUTSIDE_FENCE = """
(fences) => {
  const byFile = new Map();
  for (const [rel, sel, roots] of fences) {
    if (!byFile.has(rel)) byFile.set(rel, {roots, sels: []});
    byFile.get(rel).sels.push(sel);
  }
  const miss = (sel, roots) => { let els; try { els = document.querySelectorAll(sel); } catch (e) { return false; }
                                 for (const el of els) if (!el.closest(roots)) return true; return false; };
  const out = [];
  for (const [rel, {roots, sels}] of byFile) {
    /* one query per file; only a file that misses is asked selector by selector, to name it */
    let whole; try { whole = [...document.querySelectorAll(sels.join(","))].some(el => !el.closest(roots)); }
    catch (e) { whole = true; }
    if (whole) for (const s of sels) if (miss(s, roots)) out.push(`${rel}: ${s}`);
  }
  return out.sort();
}
"""


@pytest.fixture(scope="module")
def snapshot(browser, page_file):
    """snapshot(slice) -> ({viewport: {state: probe}}, errors) for that slice's states (SLICES), taken once.
    snapshot.outside[slice] holds, per state, the fenced rules that miss an element (OUTSIDE_FENCE).
    The fence list goes over as one JSON string: as 3,500 separate strings Playwright's argument
    serialisation cost about 50 ms a page, more than the check itself.
    Each state gets its own fresh context, so nothing one state did reaches the next capture. (Loading
    the next state's page while this one was driven saved nothing on a full run, where every worker is
    busy, and doubled the renderers per worker; removed 2026-10-05.)"""
    taken, failed, fences = {}, {}, json.dumps(fenced_selectors())
    steps_of = dict(STATES)

    def take(key):
        # A state that cannot be drawn fails the slice once; its other tests fail at once with the
        # same error, instead of loading every state of the slice again (conftest, `keep`).
        if key in failed:
            pytest.fail(f"the {key} snapshot failed in an earlier test: {failed[key]}", pytrace=False)
        if key not in taken:
            out, errors, outside = {vp: {} for vp in VIEWPORTS}, {}, {}
            try:
                for vp_name, vp in VIEWPORTS.items():
                    for state in SLICES[key][1]:
                        ctx, page, errs = open_at(browser, page_file, vp)
                        try:
                            drive(page, steps_of[state])
                            out[vp_name][state] = page.evaluate(PROBE, PROPS)
                            missed = page.evaluate(f"(json) => ({OUTSIDE_FENCE})(JSON.parse(json))", fences)
                        finally:
                            ctx.close()
                        if errs:
                            errors[f"{vp_name}/{state}"] = errs
                        if missed:
                            outside[f"{vp_name}/{state}"] = missed
            except BaseException as e:
                failed[key] = (f"{type(e).__name__}: {e}".strip().splitlines() or ["?"])[0][:300]
                raise
            taken[key] = out, errors
            take.outside[key] = outside
        return taken[key]
    take.outside = {}
    return take


@pytest.mark.parametrize("area", by_slice(SLICES, lambda k: k))
def test_no_console_errors(snapshot, area):
    _, errors = snapshot(area)
    assert errors == {}


@pytest.mark.parametrize("area", by_slice(SLICES, lambda k: k))
def test_no_fenced_rule_misses_its_element(snapshot, area):
    """A class a fenced file styles, drawn outside that file's fence, gets none of the style.
    Either the fence lists the new place (design/src/scope.json) or the file is shared."""
    snapshot(area)
    assert snapshot.outside[area] == {}


@pytest.mark.parametrize("leaf,group,label", [
    ("ranks", "scouting", "RANKS"),
    ("board", "scouting", "LEADERS"),  # the leaf is still `board`, so its bookmarks land
    ("movers", "scouting", "WORK VS POINTS"),   # Movers until 2026-09-29, Role until 2026-10-05; the leaf kept its name
    ("highlights", "scouting", "HIGHLIGHTS"),
    ("pool", "scouting", "WORK VS POINTS"),     # the old Movers view's hash, kept for bookmarks
    ("usage", "scouting", "USAGE"),             # Grid until 2026-10-05
    ("matchups", "week", "START/SIT"),  # Matchups -> Takes 2026-09-29 -> Start/Sit 2026-10-03; the leaf stayed
    ("takes", "week", "START/SIT"),
    ("startsit", "week", "START/SIT"),
    ("news", "week", "NEWS"),           # Players until 2026-09-29; the leaf and hash stayed
    ("weather", "week", None),          # out of the sub-row since 2026-10-05 (nav.js NAV_HIDDEN): the hash still lands, no button is pressed
    ("schedule", "scouting", None),     # Stats > Schedule, hidden the same way (2026-10-05)
    ("weekrecap", "week", "RECAP"),
    ("preview", "week", "PREVIEW"),
    ("waivers", "league", "WAIVERS"),   # Teams and League merged into one League group on 2026-10-05
    ("roster", "league", "ROSTER"),
    ("recap", "league", "RECAP"),
    ("myrecap", "league", "RECAP"),     # Yahoo's My recap and ESPN's League are Recap now; their hashes still land
    ("league", "league", "RECAP"),
    ("parlay", "bets", "SLIPS"),        # the leaf is still `parlay`, so its bookmarks land
    ("build", "bets", "ALL LINES"),   # Build until 2026-10-05; the leaf kept its name
    ("records", "league", "RECORDS"),   # League became a group of its own on 2026-09-28
    ("trades", "league", "TRADES"),
    ("teams", "league", "TEAMS"),       # League > Teams, the League board (2026-10-05)
])
def test_a_hash_opens_its_view(browser, page_file, leaf, group, label):
    """The view lives in the hash so a reload lands where you were reading. Renaming a leaf, or
    dropping the hash write, breaks bookmarks and the Back button silently -- the page still works,
    it just always opens on the roster. This is the only thing that would notice."""
    ctx, page, errors = open_at(browser, page_file, (1280, 900), f"#{leaf}")
    try:
        assert page.locator(".navitem[aria-current='true']").get_attribute("data-s") == group
        sub = page.locator("#subnav .mode-sub[aria-pressed='true']")
        if label is None:
            assert sub.count() == 0 and page.evaluate("document.getElementById('view').dataset.view") == leaf
        else:
            assert sub.inner_text().strip().upper().startswith(label)
        # And navigating writes it back, so the next reload holds.
        page.locator(".navitem[data-s='league']").first.click()
        page.wait_for_function("location.hash === '#roster'")
        assert page.evaluate("location.hash") == "#roster"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("hash", ["#movers", "#matchups", "#board"])
def test_a_head_fills_its_circle(browser, page_file, hash):
    """Every drawn headshot is exactly as tall as the circle that clips it. Until 2026-09-25 the
    `.xf-head`/`.bd-head` grid sized its implicit row to the img's default 150px, so a 36px circle
    showed the top of a 36x150 strip -- hair and background, no face -- in Movers, Matchups and
    Leaders alike. The golden probe measures no img, which is how it shipped."""
    ctx, page, errors = open_at(browser, page_file, (390, 844), hash)
    try:
        # Layout settles when every drawn headshot has loaded (or failed) and a frame has passed.
        page.wait_for_function("[...document.querySelectorAll('.xf-head img, .bd-head img')].every(i => i.complete)")
        page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        sizes = page.evaluate("""() => [...document.querySelectorAll('.xf-head img, .bd-head img')].map(i =>
            [Math.round(i.getBoundingClientRect().height), Math.round(i.parentElement.getBoundingClientRect().height)])""")
        assert sizes, f"no headshot drawn on {hash}; the check would pass on nothing"
        assert all(h == box for h, box in sizes), f"img height vs its circle: {sizes[:5]}"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.area("role")
@pytest.mark.parametrize("hash", ["#movers", "#pool"])
def test_movers_hash_opens_role(browser, page_file, hash):
    """Role is the leaf `movers` (2026-09-29; Movers' share cards before, and the `pool` view before
    that): its hash, old or new, must open it with its tab pressed, the Leaders tab must write
    #board, and Back must return to Role."""
    ctx, page, errors = open_at(browser, page_file, (390, 844), hash)
    try:
        assert page.evaluate("SURFACE") == "movers"
        assert page.locator("#subnav [data-leaf='movers'][aria-pressed='true']").count() == 1
        assert page.locator("[data-bdadd]").count() == 0, "+ Compare belongs to Leaders only"
        page.locator("#subnav [data-leaf='board']").click()
        page.wait_for_function("location.hash === '#board' && SURFACE === 'board'")
        assert page.evaluate("[location.hash, SURFACE]") == ["#board", "board"]
        page.go_back()
        page.wait_for_function("SURFACE === 'movers'")
        assert page.locator("[data-rvopen]").count() > 0
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("w", [761, 800, 960, 1024, 1100])
def test_nav_row_fits_a_narrow_desktop(browser, page_file, w):
    """Between the phone and 1100px the groups slid under the search field and "WEEK 3" wrapped to
    two lines (300px of overlap at 761, 9px at 1100; fixed 2026-09-27). The golden viewports are
    390 and 1400, so neither saw it."""
    ctx, page, errors = open_at(browser, page_file, (w, 700), "#board")
    try:
        nav = page.evaluate("""(() => { const n = document.querySelector('.nav'), wk = document.querySelector('.status-btn');
          return {overflow: n.scrollWidth - n.clientWidth, weekOneLine: !wk || wk.getBoundingClientRect().height <= 30}; })()""")
        assert nav == {"overflow": 0, "weekOneLine": True}, nav
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("w,shown", [(1400, True), (1100, True), (390, False)])
def test_the_mark_is_smug_blip(browser, page_file, w, shown):
    """The mark before TEAM//WATCH is Smug Blip (2026-09-29, per David): lib/blip.js pose "smug",
    about the wordmark's cap height plus its // antenna, the wordmark at --t-brand (22px), over the
    18px tabs. A phone hides the brand, as before."""
    ctx, page, errors = open_at(browser, page_file, (w, 800), "#board")
    try:
        got = page.evaluate("""(() => { const m = document.querySelector('.navbar .brand-mark svg.blip.smug'),
            n = document.querySelector('.navbar .brand-name'), bar = document.querySelector('.navbar');
          const r = m && m.getBoundingClientRect();
          return {smug: !!m, eyes: m ? m.querySelectorAll('.blip-eye').length : 0,
            size: r ? Math.round(r.width) : 0, font: getComputedStyle(n).fontSize,
            bar: Math.round(bar.getBoundingClientRect().height)}; })()""")
        assert got["smug"] and got["eyes"] == 2, got
        if shown:
            assert got["size"] == 30 and got["font"] == "22px" and got["bar"] == 57, got
        else:
            assert got["size"] == 0, got
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.area("board")
@pytest.mark.parametrize("w,h", [(360, 740), (1280, 1080)])
def test_leaders_page_fits_the_screen(browser, page_file, w, h):
    """Leaders opens on the #1's card with the list running on under it, and a page is one screen
    (board/fit.js, 2026-09-26): as it lands and after a turn, the card, pager included, ends above
    the bottom edge with no scroll, and a taller screen holds more rows than a phone. A 360x740
    phone showed five players before a tap until then; the hero plus the list must beat that."""
    ctx, page, errors = open_at(browser, page_file, (w, h), "#board")
    fits = "(() => { const m = document.querySelector('.bd-card').getBoundingClientRect(); return scrollY === 0 && m.bottom <= innerHeight; })()"
    try:
        assert page.evaluate(fits)
        assert page.locator(".bd-card > .bd-hero").count() == 1, "the #1 keeps his card"
        rows = page.evaluate("document.querySelectorAll('.bd-card .bd-list:not(.bd-pinned) > .bd-row').length")
        assert rows == page.evaluate("BD_FIRST_SIZE") or page.locator(".bd-pager [data-bdpage='2']").count() == 0
        assert page.evaluate("BD_FIRST_SIZE") >= (15 if h >= 1000 else 6)
        if page.locator(".bd-pager [data-bdpage='2']:not([disabled])").count():
            page.locator(".bd-pager [data-bdpage='2']").click()
            assert page.evaluate(fits)
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.area("recap")
def test_league_back_page_fits_one_desktop_screen(browser, page_file):
    """This week > League on a 1440x900 screen (storyboard 2026-09-27): the masthead, the lead, the
    briefs, the grudges, the standings and all six superlatives end above the bottom edge, every week.
    It ran to 3.3 screens before. On a phone the order is the story, the lead, the briefs, then the rest."""
    ctx, page, errors = open_at(browser, page_file, (1440, 900), "#recap")
    bottom = "Math.max(...[...document.querySelectorAll('.bp2 > *:not(.bp2-you):not(.bp2-mine), .bp2-main > *')].map(e => e.getBoundingClientRect().bottom))"
    try:
        for wk in page.evaluate("LGS.yahoo.weeks.map(w => w.week)"):
            page.locator(f"[data-lgweek='{wk}']").click()
            assert page.evaluate(bottom) <= 900, f"week {wk} runs past the fold"
        page.set_viewport_size({"width": 360, "height": 740})
        order = page.evaluate("['.bp2-mast', '.bp2-lead', '.bp2-briefs', '.bp2-sups', '.bp2-under'].map(q => document.querySelector(q).getBoundingClientRect().top)")
        assert order == sorted(order), order
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.area("trades")
def test_trades_desktop_rows_end_level(browser, page_file):
    """League > Trades at 1440px (STYLE.md "Rows, not columns", 2026-09-28): five cards on top, the ranking
    beside the curses (ending within 250px of them), the decided trades full width, three across. Two
    columns by kind left the ranking ending ~1000px above its neighbour. On a phone it is one strip, its
    card sections swipe rows."""
    ctx, page, errors = open_at(browser, page_file, (1440, 900), "#trades")
    box = "q => { const r = document.querySelector(q).getBoundingClientRect(); return [r.left, r.top, r.width, r.bottom]; }"
    try:
        rank, curses, dec, body = (page.evaluate(box, q) for q in (".tr-rank", ".tr-curses", ".tr-decided", ".tr-body"))
        assert curses[0] > rank[0] and abs(curses[1] - rank[1]) < 1, "curses beside the ranking"
        assert abs(curses[3] - rank[3]) <= 250, f"ranking ends {rank[3]:.0f}, curses {curses[3]:.0f}"
        assert abs(dec[2] - body[2]) < 1, "the decided trades take the full width"
        # The top row (2026-09-28, David: "fit 5 cards on the top"): best, worst and the three heists on one line.
        tops = page.evaluate("() => [...document.querySelectorAll('.tr-top-row > *')].map(c => Math.round(c.getBoundingClientRect().top))")
        assert len(tops) == 5 and len(set(tops)) == 1, f"five cards in the top row: {tops}"
        # Their bodies align (subgrid, 2026-09-29): every card's trade rows start on one line.
        body = page.evaluate("() => [...document.querySelectorAll('.tr-top-row > * > .tr-sc')].map(t => Math.round(t.getBoundingClientRect().top))")
        assert len(set(body)) == 1, f"top-row trade rows start at {body}"
        # The ranking's order is the number it shows (David, 2026-09-29: "sort by shown"), not ff-jarvis's shrunk one.
        shown = page.evaluate("() => [...document.querySelectorAll('.tr-mgrs > li:not(.few) .tr-v')].map(e => parseFloat(e.textContent.replace('−', '-')))")
        assert shown and shown == sorted(shown, reverse=True), f"ranking out of order: {shown}"
        cols = page.evaluate("() => new Set([...document.querySelectorAll('.tr-decided .tr-grid > *')].map(c => Math.round(c.getBoundingClientRect().left))).size")
        assert cols == 3, f"decided cards three across: {cols}"
        # A trade's box score (2026-09-28): the two sides are rows, and their scores share one right-hand
        # column, so the eye compares them straight down; and the players start on one left edge.
        skew = page.evaluate("""() => [...document.querySelectorAll('.tr-sc:not(.tr-chain):not(.tr-io)')].map(t => {
            const n = [...t.querySelectorAll('td.tr-n')].map(c => c.getBoundingClientRect().right);
            const p = [...t.querySelectorAll('.tr-pls')].map(l => l.getBoundingClientRect().left);
            return n.length === 2 && p.length === 2 ? Math.max(Math.abs(n[0] - n[1]), Math.abs(p[0] - p[1])) : 99; })""")
        assert skew and max(skew) < 1, f"a box score's columns are out of line by {max(skew):.0f}px"
        page.set_viewport_size({"width": 360, "height": 740})
        lefts = {round(page.evaluate(box, q)[0]) for q in (".tr-rank", ".tr-top", ".tr-decided", ".tr-curses")}
        assert len(lefts) == 1, f"one strip on a phone: {lefts}"
        # On a phone the card sections swipe sideways, one card wide (2026-09-28: ~4,600px became ~2,800px),
        # inside rows of their own: the page itself never scrolls sideways, and no card clips its content.
        phone = page.evaluate("""() => ({page: document.documentElement.scrollWidth, vw: innerWidth,
            rows: [...document.querySelectorAll('.tr-swipe')].map(r => r.scrollWidth > r.clientWidth),
            clipped: [...document.querySelectorAll('.tr-swipe > .tr-bx')].filter(c => [...c.querySelectorAll('*')]
              .some(e => e.getBoundingClientRect().right > c.getBoundingClientRect().right + 0.5)).length})""")
        assert phone["page"] == phone["vw"], f"the page scrolls sideways: {phone['page']} > {phone['vw']}"
        assert phone["rows"] and all(phone["rows"]), f"every card section swipes: {phone['rows']}"
        assert phone["clipped"] == 0, f"{phone['clipped']} cards clip their content"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.area("board")
@pytest.mark.parametrize("w,h", [(1100, 640), (1920, 1080)])
def test_leaders_wide_is_the_one_beside_two_lists(browser, page_file, w, h):
    """From 1100px (storyboard B, 2026-09-27) the #1 is a 440px column on every page, the page reads
    down two lists beside it, and the whole of it still ends above the bottom edge. Below 1100px it
    is the single card (test_leaders_page_fits_the_screen). Since 2026-09-29 a full page's #1 ends
    where the taller list ends, so no empty page sits under it ('a bottom left gap'), and page 2
    settles: a short last page once flipped between two row counts until the tab crashed."""
    ctx, page, errors = open_at(browser, page_file, (w, h), "#board")
    shape ="""(() => { const c = document.querySelector('.bd-card'), h = c.querySelector(':scope > .bd-hero');
      const lists = [...c.querySelectorAll('.bd-cols > .bd-list')].map(l => l.getBoundingClientRect());
      return {hero: h ? Math.round(h.getBoundingClientRect().width) : 0, lists: lists.length,
              sideBySide: lists.length === 2 && Math.abs(lists[0].top - lists[1].top) < 1 && lists[1].left > lists[0].right,
              fits: scrollY === 0 && c.getBoundingClientRect().bottom <= innerHeight}; })()"""
    gap = """(() => { const c = document.querySelector('.bd-card'), h = c.querySelector(':scope > .bd-hero');
      const low = Math.max(...[...c.querySelectorAll('.bd-cols > .bd-list')].map(l => l.getBoundingClientRect().bottom));
      return Math.round(Math.abs(h.getBoundingClientRect().bottom - low)); })()"""
    try:
        page.locator("[data-bdpos='WR']").click()
        s = page.evaluate(shape)
        assert s == {"hero": 440, "lists": 2, "sideBySide": True, "fits": True}, s
        assert page.evaluate(gap) <= 1, "the #1 ends where the lists end"
        assert page.evaluate("BD_FIRST_SIZE === BD_PAGE_SIZE"), "every page has the same shape"
        if page.locator(".bd-pager [data-bdpage='2']:not([disabled])").count():
            page.locator(".bd-pager [data-bdpage='2']").click()
            assert page.evaluate(shape)["hero"] == 440, "the #1 stays beside page 2"
        assert errors == []
    finally:
        ctx.close()


TUESDAY = 'Date.now = () => Date.parse("2026-09-22T12:00:00Z");'   # a Tuesday in every zone -12..+11


@pytest.mark.parametrize("day,hash,surface,first", [
    ("tue", "", "waivers", "WAIVERS"),     # claims day: Waivers opens and leads its group
    ("tue", "#roster", "roster", "WAIVERS"),   # a hash still wins
    ("sat", "", "digest", "DIGEST"),       # any other day: the Digest, first of This week (Digest, Weather)
])
def test_tuesday_opens_waivers(browser, page_file, day, hash, surface, first):
    """The day is read from Date.now(), so pinning it is the whole injection. SEED pins a
    Saturday; a Tuesday script added after it wins."""
    ctx, page, errors = open_at(browser, page_file, (390, 844), hash, init=[TUESDAY] if day == "tue" else [])
    try:
        assert page.evaluate("SURFACE") == surface
        subs = page.locator("#subnav .mode-sub")
        if first:
            assert subs.first.inner_text().strip().upper().startswith(first)
        else:
            assert subs.count() == 0
        # No sideways scroll on a phone, whichever view opened.
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.parametrize("state", by_slice([s for s, _ in STATES], SLICE_OF.get))
def test_state_renders_something(snapshot, state):
    out, _ = snapshot(SLICE_OF[state])
    for vp in VIEWPORTS:
        assert len(out[vp][state]["view"]) > 200, f"{vp}/{state}: #view is empty"
    if state.endswith("drawer"):
        assert out["desk"][state]["drawerOpen"], "drawer did not open"
        assert len(out["desk"][state]["drawer"]) > 100
    if state.endswith("modal"):
        assert out["desk"][state]["modalOpen"], "modal did not open"
        assert len(out["desk"][state]["modal"]) > 100
    if state.startswith("chat-"):
        for vp in VIEWPORTS:
            assert out[vp][state]["chatOpen"], f"{vp}/{state}: the chat panel did not open"
            assert len(out[vp][state]["chat"]) > 100


@pytest.mark.area("chat", slice=SLICE_OF["chat-over-movers"])
def test_chat_panel_survives_a_surface_change(snapshot):
    """The whole reason it is a floating panel: open it, switch surface, and it is still there
    with the page behind it changed. As a tab, asking about a player meant leaving his row."""
    out, _ = snapshot(SLICE_OF["chat-over-movers"])
    over_pool = out["desk"]["chat-over-movers"]
    assert over_pool["chatOpen"], "the panel closed when the surface changed"
    assert "chatinput" in over_pool["chat"], "the composer is gone"
    # #view is Role (leaf movers), not the chat -- the panel is over the page, not instead of it.
    assert "data-rvopen" in over_pool["view"], \
        "#view is not Role; the panel replaced the surface instead of floating over it"


def diff(golden, now, limit=25):
    lines = []
    for vp in VIEWPORTS:
        for state in now[vp]:
            g, n = golden.get(vp, {}).get(state), now[vp][state]
            if g is None:
                lines.append(f"{vp}/{state}: no golden yet")
                continue
            for key in ("view", "drawer", "modal", "chat", "search", "legsheet", "strip", "stage"):
                if g.get(key) != n[key]:
                    if key not in g:
                        lines.append(f"{vp}/{state}: #{key} has no golden yet")
                        continue
                    i = next((i for i, (a, b) in enumerate(zip(g[key], n[key])) if a != b), min(len(g[key]), len(n[key])))
                    lines.append(f"{vp}/{state}: #{key} differs at char {i}: ...{n[key][max(0, i-40):i+60]!r}")
            for cls in sorted(set(g["styles"]) | set(n["styles"])):
                a, b = g["styles"].get(cls), n["styles"].get(cls)
                if a != b:
                    if a is None or b is None:
                        lines.append(f"{vp}/{state}: .{cls} {'appeared' if a is None else 'vanished'}")
                    else:
                        for p, x, y in zip(PROPS, a.split("|"), b.split("|")):
                            if x != y:
                                lines.append(f"{vp}/{state}: .{cls} {p}: {x} -> {y}")
            if len(lines) > limit:
                return lines[:limit] + ["..."]
    return lines


@pytest.mark.parametrize("area", by_slice(SLICES, lambda k: k))
def test_matches_golden(snapshot, update_golden, area):
    """One slice's states against the golden. An update rewrites that slice's states only, and drops
    states that no longer exist, so `--areas x --update-golden` leaves every other area as it was."""
    from conftest import GOLDEN
    out, _ = snapshot(area)
    path = GOLDEN / GOLDEN_FILE
    golden = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if update_golden or not path.exists():
        if os.environ.get("PYTEST_XDIST_WORKER"):
            pytest.fail("--update-golden runs without -n: areas on two workers would each rewrite the one file")
        names = {s for s, _ in STATES}
        for vp in VIEWPORTS:
            kept = {s: p for s, p in golden.get(vp, {}).items() if s in names and s not in SLICES[area][1]}
            golden[vp] = {**kept, **out[vp]}
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(golden, indent=0, sort_keys=True), encoding="utf-8", newline="\n")
        pytest.skip(f"golden written for {area}: {path.relative_to(GOLDEN.parents[1])}")
    d = diff(golden, out)
    assert d == [], "rendered page differs from tests/golden/render.json (pytest --update-golden if intended):\n" + "\n".join(d)
