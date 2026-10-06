"""This week > Digest, the banner and the last game's card with a planted week (surface/digest/lead.js, mnf.js).

`DigestStoryPage` is `DigestLivePage` plus what the story and generic-banner tests plant (a Sunday with
LIVE_GAMEDAY's leagues in the page, Monday's clubs, Claude's story, the day's scorers) and read (the
banner, the last game's blocks). The Recap banner belongs to Recap and is read there, not here. See
pages/digest.py.
"""
import re

from pages.digest_live import DigestLivePage
from test_render import LIVE_PLANT

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

SET_STORY = "(story) => { LIVE_DIGEST.story = story; DG_CUT = null; render(); }"
SET_TOP = """(rows) => { GD_STATS.lead = Object.fromEntries(rows.map(([n, pos, team, pts, s], i) => [String(100 + i), {n, pos, team, pts, s: s || {}}]));
  DG_CUT = null; render(); }"""


def cfg(**over):
    c = {"at": SUNDAY_AT, "sun": SUN, "monKick": MON, "sunState": "in_game", "monStates": [],
         "mon": [["NO", "ATL"]], "ranks": RANKS, "lead": [list(x) for x in SUNDAY], "stats": {}, "clock": {}}
    c.update(over)
    return c


def _flat(text):
    return re.sub(r"\s+", " ", text).strip()


class DigestStoryPage(DigestLivePage):
    """DigestLivePage, with the generic week planted and the banner and the last game's blocks read."""

    # ---- planting ----

    def plant(self, **over):
        """The Digest as a public reader has it: `cfg(**over)` (a clock, Sunday's and Monday's games and
        states, the day's scorers, the poll's stats and clocks), drawn."""
        self.page.evaluate(PLANT, cfg(**over))

    def plant_story(self, story):
        """Claude's story for the packet's week, drawn."""
        self.page.evaluate(SET_STORY, story)

    def plant_top(self, rows):
        """The day's scorers, `[name, pos, club, pts, stat line]` best first, drawn."""
        self.page.evaluate(SET_TOP, rows)

    def plant_hurt(self, slug):
        """A ranked player leaves the game hurt, and the poll repaints."""
        self.page.evaluate("""(slug) => { const r = LIVE_RANKS.rows.find(x => x.slug === slug);
          GD_HURT = {[r.slug]: {slug: r.slug, name: r.n, team: r.team, q: 2, clock: '3:00', back: false}}; paintDigestLive(); }""", slug)

    def plant_scorer_stat(self, key, stat, value):
        """One stat of a poll scorer changes (`GD_STATS.lead[key].s[stat]`), and the poll repaints."""
        self.page.evaluate("([k, s, v]) => { GD_STATS.lead[k].s[s] = v; paintDigestLive(); }", [key, stat, value])

    def plant_pts_allowed(self, club, pts):
        """The poll's points a club's defense allowed (the other side's score), and the poll repaints."""
        self.page.evaluate("([c, p]) => { GD_STATS.stats[c].pts_allow = p; paintDigestLive(); }", [club, pts])

    # ---- what the page holds ----

    def league_names(self):
        """Every league name and team name (mine and my opponents') the page holds in LIVE_GAMEDAY."""
        return self.page.evaluate("[...new Set(GD.leagues.flatMap(lg => [lg.name, ...Object.values(lg.teams).map(tm => tm.name)]))].filter(Boolean)")

    def text(self):
        """What the Digest prints, as the reader reads it."""
        return self.page.get_by_test_id("digest-root").inner_text()

    def resize(self, width, height):
        """The window's size; a kept context keeps it for the next test, so restore what you changed."""
        self.page.set_viewport_size({"width": width, "height": height})

    def now_hurt_rows(self):
        """Right now's rows for a player who left the game hurt."""
        return self.page.get_by_test_id("digest-now-row").and_(self.page.locator(".hurt")).count()

    def pwned(self):
        """Whether a script a story smuggled in ran (`window.__pwned`)."""
        return self.page.evaluate("window.__pwned")

    # ---- the banner ----

    def banner(self):
        """The headline, its whitespace collapsed."""
        return _flat(self._head.inner_text())

    def lead_card(self):
        """The banner's article: its classes and its inline style."""
        card = self.page.get_by_test_id("digest-lead")
        return {"class": card.get_attribute("class"), "style": card.get_attribute("style")}

    def lead_text(self):
        return self.page.get_by_test_id("digest-lead").inner_text()

    def lead_fact_text(self):
        return self.page.get_by_test_id("digest-lead-fact").inner_text().strip()

    def lead_escaped(self):
        """Markup a story's words smuggled in: an `<img src=x>` in the banner and a `<b>` in its fact line."""
        return {"img": self.page.get_by_test_id("digest-lead").locator("img[src='x']").count(),
                "bold": self.page.get_by_test_id("digest-lead-fact").locator("b").count()}

    # ---- the last game's card ----

    def late_cards(self):
        """How many last-game cards the page draws (none until the week reaches its last day)."""
        return self._tn.and_(self.page.locator("[data-dgmnf]")).count()

    def mnf_block_count(self):
        return self._mnf_blocks().count()

    def mnf_when(self, i=0):
        return self._mnf_blocks().nth(i).get_by_test_id("digest-mnf-when").inner_text().strip()

    def mnf_when_flat(self, i=0):
        return _flat(self._mnf_blocks().nth(i).get_by_test_id("digest-mnf-when").inner_text())

    def mnf_parts(self, i=0):
        """How many score lines and top performers the block draws (neither before kickoff)."""
        block = self._mnf_blocks().nth(i)
        return {"score": block.get_by_test_id("digest-mnf-score").count(), "top": block.get_by_test_id("digest-mnf-top").count()}

    def mnf_score(self, i=0):
        return _flat(self._mnf_blocks().nth(i).get_by_test_id("digest-mnf-score").inner_text())

    def mnf_score_numbers(self, i=0):
        return self._mnf_blocks().nth(i).get_by_test_id("digest-mnf-score").locator("b").all_inner_texts()

    def mnf_top(self, i=0):
        return _flat(self._mnf_blocks().nth(i).get_by_test_id("digest-mnf-top").inner_text())

    def mnf_state(self, i=0):
        return self._mnf_blocks().nth(i).get_attribute("data-st")

    def mnf_box(self, i=0):
        """The block's box in px (x, y, width, height)."""
        return self._mnf_blocks().nth(i).bounding_box()

    def mnf_card_box(self):
        return self._mnf_cards().bounding_box()

    def mnf_retired_parts(self):
        """Parts the card no longer draws (the projections, the headline, the foot)."""
        return self._mnf_cards().locator(".dg-mnf-c, .dg-mnf-p, .dg-mnf-h, .dg-foot").count()

    def tap_mnf_block(self, i=0):
        self._mnf_blocks().nth(i).click()

    def _mnf_cards(self):
        return self._tn.and_(self.page.locator(".dg-mnf"))

    def _mnf_blocks(self):
        return self._mnf_cards().get_by_test_id("digest-mnf-block")
