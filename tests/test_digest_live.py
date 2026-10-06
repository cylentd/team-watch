"""The Digest during a game and on Monday night is generic (2026-10-04).

David: "The Digest is supposed to be GENERIC for the public. It shouldn't hone on to my roster or their
roster." The first Monday card (2bf04c6) drew the reader's matchup per league and its headline said "You're
up 1.6 going into Monday night"; both are superseded. The card is now one block per game (2026-10-05, about
80px): the day and the clock, the score, and the game's top performer in yards and touchdowns while it is on.

Every state here plants a week with LIVE_GAMEDAY's leagues in the page, because that is what a public reader
also carries, and then asserts the Digest drew none of their league names, team names or opponents' names.
LIVE_RANKS holds five players in the fixtures, so the projections the card reads are planted beside them."""
import re

import pytest

from test_render import LIVE_PLANT, drive, go, open_page  # noqa: F401

pytestmark = pytest.mark.render

SUN, MON = "2026-10-04T12:00:00Z", "2026-10-05T15:00:00Z"
SUNDAY_AT, MONDAY_EARLY, MONDAY_ON = "2026-10-04T14:00:00Z", "2026-10-05T09:00:00Z", "2026-10-05T15:30:00Z"

# Four Monday clubs (two games of two), each with three ranked players; the Monday game's best two are the
# two highest here. pts are the projections the card shows.
RANKS = [
    ("ATL", "Bijan Robinson", "RB", 19.4), ("ATL", "Drake London", "WR", 15.2), ("ATL", "Kyle Pitts", "TE", 9.1),
    ("NO", "Alvin Kamara", "RB", 14.8), ("NO", "Chris Olave", "WR", 13.3), ("NO", "Spencer Rattler", "QB", 12.0),
    ("HOU", "C.J. Stroud", "QB", 20.6), ("HOU", "Nico Collins", "WR", 17.0), ("HOU", "Joe Mixon", "RB", 11.1),
    ("KC", "Patrick Mahomes", "QB", 22.3), ("KC", "Travis Kelce", "TE", 12.9), ("KC", "Xavier Worthy", "WR", 10.2),
]
# Sunday's scorers league-wide, as GD_STATS.lead (api/stats.py lead=1); Monday's are planted per state.
SUNDAY = [("Amon-Ra St. Brown", "WR", "DET", 31.4), ("De'Von Achane", "RB", "MIA", 27.1), ("Brock Purdy", "QB", "SF", 24.0),
          ("Cam Skattebo", "RB", "NYG", 19.2), ("Tee Higgins", "WR", "CIN", 17.8)]
MONDAY_SCORERS = {"ATL": [("Bijan Robinson", "RB", 16.4), ("Kyle Pitts", "TE", 6.2)], "NO": [("Alvin Kamara", "RB", 11.8)]}

PLANT = """(cfg) => {
  PLANT_LEAGUES
  for (const [team, n, pos, pts] of cfg.ranks)
    LIVE_RANKS.rows.push({slug: slugOf(n), n, pos, team, pts, kick: null});
  const mon = cfg.mon;                                     // [[away, home], ...] on Monday, each its own game
  const monClubs = mon.flat();
  const sundayClubs = [...new Set([...GD.leagues.flatMap(lg => Object.values(lg.teams).flatMap(tm => tm.lineup.map(r => r.team))),
    'DET', 'MIA', 'SF', 'NYG', 'CIN', ...cfg.ranks.map(r => r[0])])].filter(c => !monClubs.includes(c));
  const games = sundayClubs.map(c => ({home: c, away: 'O' + c, kickoff: cfg.sun, week: 2, espn: 'E' + c}));
  mon.forEach(([away, home], i) => games.push({home, away, kickoff: cfg.monKick, week: 2, espn: 'EM' + i}));
  GD_GAMES.splice(0, GD_GAMES.length, ...games);
  Date.now = () => Date.parse(cfg.at);
  GD_STATS.games = {};
  for (const g of games) for (const c of [g.home, g.away]) GD_STATS.games[c] = monClubs.includes(c) ? (cfg.monStates[monClubs.indexOf(c) >> 1] || 'pre_game') : cfg.sunState;
  GD_STATS.lead = Object.fromEntries(cfg.lead.map(([n, pos, team, pts], i) => [String(100 + i), {n, pos, team, pts, s: pos === 'QB' ? {pass_yd: 250} : {rec_yd: 60}}]));
  Object.assign(GD_STATS.stats, cfg.stats);
  GD_AT = Date.now(); GD_CLOCK = cfg.clock; GD_HURT = {};
  LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = [];
  DG_CUT = null; render();
}""".replace("PLANT_LEAGUES", LIVE_PLANT())


def cfg(**over):
    c = {"at": SUNDAY_AT, "sun": SUN, "monKick": MON, "sunState": "in_game", "monStates": [],
         "mon": [["NO", "ATL"]], "ranks": RANKS, "lead": [list(x) for x in SUNDAY], "stats": {}, "clock": {}}
    c.update(over)
    return c


def digest(browser, page_file, viewport=(390, 844), **over):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("digest"))
    page.wait_for_selector(".dg")
    page.evaluate(PLANT, cfg(**over))
    return ctx, page, errors


def personal(page):
    """Every league name and team name (mine and my opponents') the page holds in LIVE_GAMEDAY."""
    names = page.evaluate("[...new Set(GD.leagues.flatMap(lg => [lg.name, ...Object.values(lg.teams).map(tm => tm.name)]))].filter(Boolean)")
    assert len(names) >= 10, names
    return names


def assert_generic(page):
    """Nothing the Digest drew names a league or a team of the reader's, or says "you"."""
    html = page.evaluate("document.querySelector('.dg').outerHTML")
    text = page.evaluate("document.querySelector('.dg').innerText")
    assert [n for n in personal(page) if n in html] == []
    assert not re.search(r"going into|you're|your |yours|theirs to play|median", text, re.I), text


def card_text(page):
    return re.sub(r"\s+", " ", page.locator(".dg-mnf").inner_text()).strip()


def test_during_a_game_the_digest_draws_no_league_team_or_opponent(browser, page_file):
    ctx, page, errors = digest(browser, page_file, mon=[], clock={"DET": {"state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["DET"]}})
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown ERUPTS: 60 yards"
    assert page.locator("[data-dgnow] .dg-now-r").count() == 3      # three rows and More (2026-10-05)
    assert_generic(page)
    # a player is hurt: the banner and a row name him, by his club, no team of mine
    page.evaluate("""() => { const r = LIVE_RANKS.rows.find(x => x.slug === 'bijan-robinson');
      GD_HURT = {[r.slug]: {slug: r.slug, name: r.n, team: r.team, q: 2, clock: '3:00', back: false}}; paintDigestLive(); }""")
    assert page.locator(".dg-lead-h").inner_text() == "B. Robinson left the game hurt"
    assert page.locator(".dg-lead-fact").inner_text() == "ATL · Live"
    assert page.locator(".dg-now-r.hurt").count() == 1
    assert_generic(page)
    ctx.close()
    assert errors == []


def test_monday_before_kickoff_is_the_game_its_projections_and_a_generic_headline(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete")
    card = page.locator(".dg-mnf")
    assert card.count() == 1 and "has-tn" in page.locator(".dg-ticker").get_attribute("class")
    # one block: the day and the kickoff over the matchup, on line 1; no score and no top performer yet
    block = card.locator(".dg-mnf-g")
    assert block.count() == 1
    assert re.fullmatch(r"[A-Z]{3} \d{1,2}:\d\d [AP]M · NO @ ATL", block.locator(".dg-mnf-w").inner_text().strip())
    assert block.locator(".dg-mnf-s").count() == 0 and block.locator(".dg-mnf-t").count() == 0
    assert block.bounding_box()["height"] <= 96
    # the projections left the card
    assert card.locator(".dg-mnf-c, .dg-mnf-p, .dg-mnf-h, .dg-foot").count() == 0
    # the banner is the week's top scorer between windows, not a matchup
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown went off for 60 yards"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert_generic(page)
    # a tap on the block opens that game's sheet
    block.click()
    page.wait_for_selector("#gamesheet.on")
    ctx.close()
    assert errors == []


def test_monday_during_the_game_is_the_score_the_clock_and_the_games_top_scorers(browser, page_file):
    scorers = [[n, pos, team, pts] for team, rows in MONDAY_SCORERS.items() for n, pos, pts in rows]
    stats = {"ATL": {"pts_allow": 10}, "NO": {"pts_allow": 17}}      # a club's score is what the other's defense allowed
    ctx, page, errors = digest(browser, page_file, at=MONDAY_ON, sunState="complete", monStates=["in_game"], stats=stats,
                               lead=[list(x) for x in SUNDAY] + scorers,
                               clock={"ATL": {"state": "in", "q": 2, "clock": "3:15", "half": False, "detail": "", "clubs": ["ATL", "NO"]}})
    card = page.locator(".dg-mnf")
    assert card.count() == 1
    block = card.locator(".dg-mnf-g")
    assert block.count() == 1 and block.bounding_box()["height"] <= 96
    flat = lambda loc: re.sub(r"\s+", " ", loc.inner_text()).strip()
    # line 1: the day and the clock, no matchup once it is on
    assert re.fullmatch(r"[A-Z]{3} · Q2 3:15", flat(block.locator(".dg-mnf-w")))
    # line 2: the score reads away then home: NO 10 (what ATL's defense allowed), ATL 17 (what NO's did)
    assert flat(block.locator(".dg-mnf-s")) == "NO 10 · ATL 17"
    # line 3: this game's best performer in yards and touchdowns, never Sunday's, never points
    assert flat(block.locator(".dg-mnf-t")) == "B. Robinson 60 yds"
    assert page.locator(".dg-lead-h").inner_text() == "St. Brown went off for 60 yards"    # the week's top score, on any field; his game is final, so the past
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert_generic(page)
    # a poll repaints the block in place: the score moves, the page is not rebuilt
    page.evaluate("() => { document.querySelector('.dg').dataset.keep = '1'; GD_STATS.stats.ATL.pts_allow = 13; paintDigestLive(); }")
    assert flat(card.locator(".dg-mnf-s")) == "NO 13 · ATL 17"
    assert page.evaluate("document.querySelector('.dg').dataset.keep") == "1"
    # a desktop: the block is at most 560px (STYLE.md, a label within 560px of its value) and the card as wide as its game
    page.set_viewport_size({"width": 1400, "height": 900})
    w_block = block.bounding_box()["width"]
    assert 360 <= w_block <= 560 and page.locator(".dg-mnf").bounding_box()["width"] <= w_block + 2
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ctx.close()
    assert errors == []


def test_two_late_games_each_have_their_own_line_and_a_finished_one_says_final(browser, page_file):
    stats = {"ATL": {"pts_allow": 7}, "NO": {"pts_allow": 24}}
    # before either kickoff by the clock, but Sleeper already calls the first one complete
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete", mon=[["NO", "ATL"], ["KC", "HOU"]],
                               monStates=["complete", "pre_game"], stats=stats)
    card = page.locator(".dg-mnf")
    games = card.locator(".dg-mnf-g")
    assert games.count() == 2
    when = lambda i: games.nth(i).locator(".dg-mnf-w").inner_text().strip()
    assert re.fullmatch(r"[A-Z]{3} · Final", when(0)) and re.fullmatch(r"[A-Z]{3} \d{1,2}:\d\d [AP]M · KC @ HOU", when(1))
    assert games.nth(0).locator(".dg-mnf-s b").all_inner_texts() == ["7", "24"]
    assert games.nth(0).get_attribute("data-st") == "final" and games.nth(1).get_attribute("data-st") == "pre"
    assert games.nth(1).locator(".dg-mnf-s, .dg-mnf-t").count() == 0       # the one to come has no score and no performer
    assert games.nth(0).bounding_box()["height"] <= 96 and games.nth(1).bounding_box()["height"] <= 96
    assert games.nth(0).bounding_box()["y"] < games.nth(1).bounding_box()["y"]   # two games stack on a phone
    assert_generic(page)
    ctx.close()
    assert errors == []


def test_before_the_week_reaches_its_last_day_there_is_no_card(browser, page_file):
    """Sunday's games still on: no Monday card, whatever Monday's slot holds."""
    ctx, page, errors = digest(browser, page_file)
    assert page.locator("[data-dgmnf]").count() == 0
    assert_generic(page)
    ctx.close()
    assert errors == []


def test_the_digest_surface_reads_no_league_roster_or_matchup():
    """The rule, as a grep: nothing under surface/digest or data/digest.js touches a league, a roster, a
    matchup or Live's scorer. A view that does is personal, and the Digest is for the public."""
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"
    files = sorted((src / "surface" / "digest").glob("*.js")) + [src / "data" / "digest.js"]
    bad = re.compile(r"\bGD\.leagues|\blg\.(me|teams|games|median)\b|\bgdSide\b|\bgdLeague\b|\bgdGame\b|\bgdMineIn\b|\bgdStarter\b|\bgdLadder\b")
    hits = []
    for f in files:
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", f.read_text(encoding="utf-8"), flags=re.S)
        hits += [f"{f.name}: {m.group(0)}" for m in bad.finditer(code)]
    assert hits == []
    hurt = (src / "data" / "gameday" / "hurt.js").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", hurt, flags=re.S)
    assert not bad.search(code), "hurt.js watches players league-wide: it reads LIVE_RANKS, not my lineups"
