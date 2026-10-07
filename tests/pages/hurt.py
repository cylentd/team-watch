"""A player who left the game hurt, on the views that show it (design/src/js/data/gameday/hurt.js): the Digest's
headline and Right now rows (surface/digest/now.js, lead.js) and the red "Hurt" chip on Live's lineups
(surface/live/mirror.js), and the poller that asks ESPN for the plays that say so.

`HurtPage` composes the views' own page objects: `.digest` (pages/digest_live.py) and `.live` (pages/live_tabs.py)
read everything those views draw; this one adds only what is about the injury: the planted game day and the
hurt rows, chip and pill, found by test id (`digest-now-hurt`, `live-hurt`) with a state class (`hurt`) joined
by `and_`. The scan and the order of who is hurt are pure and tested in Node (tests/test_left_hurt.py, test_js_hurt.py).

The game day is Sunday 2026-10-04 (`SUN`), week 2 of both leagues, every club given a game of its own (ESPN id
"E<club>"), SF on the clock at Q3 4:12, Brock Purdy's club. A test plants GD_HURT itself: ESPN refuses servers
and headless browsers, so the poller cannot be fed from a test's network.

Reads return plain data; no method asserts. A method that plants draws again, the way the page's own poll does
(`paintDigestLive`, `paintLive`).
"""
import re

from pages.digest_live import DigestLivePage
from pages.live_tabs import COLOUR, LiveTabsPage
from test_render import LIVE_PLANT, LOAD_MS, SEED, drive, go

LEAD = {
    "7547": {"n": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "pts": 31.4, "s": {"rec": 10, "rec_yd": 180, "rec_td": 2}},
    "9226": {"n": "De'Von Achane", "pos": "RB", "team": "MIA", "pts": 27.1, "s": {"rush_att": 18, "rush_yd": 130, "rush_td": 1}},
    "8183": {"n": "Brock Purdy", "pos": "QB", "team": "SF", "pts": 24.0, "s": {"pass_cmp": 22, "pass_att": 30, "pass_yd": 290, "pass_td": 3}},
    "12481": {"n": "Cam Skattebo", "pos": "RB", "team": "NYG", "pts": 19.2, "s": {"rush_att": 20, "rush_yd": 90, "rush_td": 2}},
    "6801": {"n": "Tee Higgins", "pos": "WR", "team": "CIN", "pts": 17.8, "s": {"rec": 6, "rec_yd": 98}},
    "4217": {"n": "George Kittle", "pos": "TE", "team": "SF", "pts": 15.5, "s": {"rec": 6, "rec_yd": 85, "rec_td": 1}},
    "12526": {"n": "Tetairoa McMillan", "pos": "WR", "team": "CAR", "pts": 12.0, "s": {"rec": 5, "rec_yd": 70}},
}
SUN = "2026-10-04T12:00:00Z"
SF_CLOCK = {"SF": {"state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["SF"]}}

# The fixture's LIVE_RANKS (tests/fixtures) holds seven rows. Planted beside them: Achane (starts for me), Huntley (in
# none of my lineups, the league-wide case) and Stukes (under the 8-point line).
RANKS = [
    {"slug": "devon-achane", "n": "De'Von Achane", "pos": "RB", "team": "MIA", "pts": 21.5},
    {"slug": "tyler-huntley", "n": "Tyler Huntley", "pos": "QB", "team": "BAL", "pts": 19.9},
    {"slug": "tre-stukes", "n": "Tre Stukes", "pos": "WR", "team": "LV", "pts": 5.0},
]

# Week 2 of both leagues, every club given a game of its own (Sunday's, ESPN id "E<club>"), SF on the clock.
PLANT = """(cfg) => {
  PLANT_LEAGUES
  for (const r of cfg.ranks) if (!LIVE_RANKS.rows.some(x => x.slug === r.slug)) LIVE_RANKS.rows.push({kick: null, ...r});
  const clubs = [...new Set([...GD.leagues.flatMap(lg => Object.values(lg.teams).flatMap(tm => tm.lineup.map(r => r.team))), 'BAL'])];
  const games = clubs.map(c => ({home: c, away: 'O' + c, kickoff: cfg.sun, week: 2, espn: 'E' + c}));
  GD_GAMES.splice(0, GD_GAMES.length, ...games);
  Date.now = () => Date.parse(cfg.at);
  GD_STATS.games = {};
  for (const g of games) for (const c of [g.home, g.away]) GD_STATS.games[c] = cfg.state;
  GD_STATS.lead = cfg.lead;
  GD_AT = Date.now(); GD_CLOCK = cfg.clock; GD_HURT = {};
  LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = [];
  DG_CUT = null; render();
}""".replace("PLANT_LEAGUES", LIVE_PLANT())

SERVED = "http://team-watch.test/"


def cfg(**over):
    """The planted game day: 14:00 UTC on the Sunday, every game on, SF on the clock; `over` changes any part."""
    c = {"at": "2026-10-04T14:00:00Z", "sun": SUN, "state": "in_game", "lead": LEAD, "clock": SF_CLOCK, "ranks": RANKS}
    c.update(over)
    return c


def served(browser, page_file):
    """The whole page over http, so PAGE_SERVED() is true (a mounted page is a file); every other request is refused.
    Returns (context, page, errors); the caller closes the context."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    html = page_file.read_text(encoding="utf-8")
    page.route(re.compile(r"^http://team-watch\.test/?$"), lambda r: r.fulfill(status=200, content_type="text/html", body=html))
    page.route(re.compile(r"^https?://(?!team-watch\.test/?$)"), lambda r: r.abort())
    page.add_init_script(SEED)
    page.goto(SERVED, timeout=LOAD_MS)
    page.wait_for_function("document.getElementById('view').children.length > 0")
    return ctx, page, errors


class HurtPage:
    def __init__(self, page):
        self.page = page
        self.digest = DigestLivePage(page)
        self.live = LiveTabsPage(page)
        tid = page.get_by_test_id
        self._now_rows = tid("digest-now-row")
        self._now_hurt = self._now_rows.and_(page.locator(".hurt"))
        self._now_plain = self._now_rows.and_(page.locator(":not(.hurt)"))
        self._chips, self._mirror = tid("live-hurt"), tid("live-mirror")

    @classmethod
    def on_digest(cls, mount, **over):
        """Mount the Digest at a phone and plant the game day (`cfg(**over)`). Returns (HurtPage, the page's errors)."""
        page, errors = mount("digest", size=(390, 844))
        hurt = cls(page)
        hurt.plant(**over)
        page.get_by_test_id("digest-root").wait_for()
        return hurt, errors

    @classmethod
    def on_live(cls, mount, team="espn", **over):
        """Mount Live at a phone, as the reader of `team` (None: the seed's pick), and plant the game day.
        Live follows the reader's team, and Purdy starts for David's ESPN team. Returns (HurtPage, the page's errors)."""
        page, errors = mount("live", size=(360, 780))
        hurt = cls(page)
        if team:
            page.evaluate(f"localStorage.setItem('tw-team', '{team}')")
        hurt.plant(**over)
        hurt._mirror.get_by_test_id("live-mirror-row").first.wait_for()
        return hurt, errors

    # ---- planting ----

    def plant(self, **over):
        """The game day (module docstring), after `cfg(**over)`; the page draws again."""
        self.page.evaluate(PLANT, cfg(**over))

    def open_view(self, leaf):
        """Navigate to a view by its nav tabs, as a reader does (a full page's)."""
        drive(self.page, go(leaf))

    def leave_hurt(self, *players):
        """Each of `players` {slug, name, team, q, clock, back} has left his game hurt; the Digest draws again."""
        self.page.evaluate("(hs) => { GD_HURT = Object.fromEntries(hs.map(h => [h.slug, h])); paintDigestLive(); }", list(players))

    def return_to_game(self, player):
        """He is back in the game; the Digest draws again."""
        self.page.evaluate("(h) => { GD_HURT = {[h.slug]: {...h, back: true}}; paintDigestLive(); }", player)

    def leave_hurt_and_render(self, player):
        """He is flagged and the whole view draws again from a clean cut (before kickoff nothing may change)."""
        self.page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; DG_CUT = null; render(); }", player)

    def leave_hurt_on_live(self, player):
        self.page.evaluate("(h) => { GD_HURT = {[h.slug]: h}; paintLive(); }", player)

    def return_to_game_on_live(self, player):
        self.page.evaluate("(h) => { GD_HURT = {[h.slug]: {...h, back: true}}; paintLive(); }", player)

    def flag_before_his_game_starts(self, club, player):
        """`club`'s games have not kicked off, and a stale hurt flag names `player`; Live draws again."""
        self.page.evaluate("""([club, h]) => { for (const c of gdCodes(club)) GD_STATS.games[c] = 'pre_game'; GD_HURT = {[h.slug]: h}; paintLive(); }""",
                           [club, player])

    # ---- the Digest ----

    def lead_tone(self):
        """The banner's tone class (its second class): `out` for a player who left hurt."""
        return self.page.get_by_test_id("digest-lead").get_attribute("class").split()[1]

    def lead_name(self):
        """The player the banner opens."""
        return self.page.get_by_test_id("digest-lead-go").get_attribute("data-n")

    def first_now_row(self):
        """Right now's first row: {cls, text, pill (the words where the points go)}."""
        row = self._now_rows.first
        return {"cls": row.get_attribute("class"), "text": row.inner_text(),
                "pill": row.get_by_test_id("digest-now-hurt").text_content()}

    def first_now_pill_colour(self):
        return self._now_rows.first.get_by_test_id("digest-now-hurt").evaluate("e => getComputedStyle(e).color")

    def tap_first_now_row(self):
        self._now_rows.first.click()

    def hurt_now_row_count(self):
        return self._now_hurt.count()

    def hurt_now_row_texts(self):
        return self._now_hurt.all_inner_texts()

    def plain_now_row_count(self):
        return self._now_plain.count()

    def plain_now_row_texts(self):
        return self._now_plain.all_inner_texts()

    def down_colour(self):
        """The page's --down as the browser computes it."""
        return self.page.evaluate(COLOUR, "--down")

    def personal_names(self):
        """Every league and team name the page holds (LIVE_GAMEDAY): none may reach the Digest."""
        return self.page.evaluate("[...new Set(GD.leagues.flatMap(lg => [lg.name, ...Object.values(lg.teams).map(tm => tm.name)]))].filter(Boolean)")

    # ---- Live's lineups: the chip on Brock Purdy's row ----

    def purdy_rows(self):
        """How many of the starters' rows carry Brock Purdy on the left, the reader's side."""
        return self._purdy_row().count()

    def chip_count(self):
        """Hurt chips on the whole page."""
        return self._chips.count()

    def purdy_chip_count(self):
        return self._purdy_row().get_by_test_id("live-hurt").count()

    def purdy_chip_text(self):
        return self._purdy_row().get_by_test_id("live-hurt").inner_text()

    def purdy_chip_label(self):
        return self._purdy_row().get_by_test_id("live-hurt").get_attribute("aria-label")

    def purdy_chip_in_name_count(self):
        """Chips inside his one name button, beside his name."""
        return self._purdy_row().get_by_test_id("live-name").get_by_test_id("live-name-text").get_by_test_id("live-hurt").count()

    def purdy_chip_colour(self):
        return self._purdy_row().get_by_test_id("live-hurt").evaluate("e => getComputedStyle(e).color")

    def purdy_row_height(self):
        return self._purdy_row().evaluate("r => r.getBoundingClientRect().height")

    def scroll_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")

    def lineups_html(self):
        """The starters' lineups as drawn."""
        return self._mirror.evaluate("e => e.innerHTML")

    def _purdy_row(self):
        left = self.page.get_by_test_id("live-half").and_(self.page.locator(".l"))
        name = left.get_by_test_id("live-name").and_(self.page.locator("[data-gdn='Brock Purdy']"))
        return self._mirror.get_by_test_id("live-mirror-row").filter(has=name)

    # ---- the poller (a served page) ----

    def stub_espn(self, stub, summary):
        """Replace gsFetchSummary with `stub` (an async function of {summary}: it records every request in window.__calls,
        window.__open and window.__max, and answers window.__summary), planted with `summary`. The stub's latency is the
        test's, so the fixed-wait check (test_honest_tests.py) reads it."""
        self.page.evaluate(stub, {"summary": summary})

    def start_games(self):
        """SF and NYG are on (two games with starters of mine; ESPN is down for NYG's), and a game none of mine is in."""
        self.page.evaluate("""() => {
      GD_STATS.games.SF = GD_STATS.games.NYG = 'in_game';
      GD_GAMES.push({home: 'ZZ', away: 'YY', kickoff: GD_GAMES[0].kickoff, week: 2, espn: 'EZZ'});
      GD_STATS.games.ZZ = GD_STATS.games.YY = 'in_game';
    }""")

    def start_sf_game(self):
        self.page.evaluate("GD_STATS.games.SF = 'in_game'")

    def move_clock(self, ms):
        """The page's clock moves on by `ms`."""
        self.page.evaluate("(ms) => { const t = Date.now() + ms; Date.now = () => t; }", ms)

    def purdy_returns(self):
        """ESPN's summary now carries the line that says he is back."""
        self.page.evaluate("""() => { window.__summary = {...window.__summary, drives: {previous: [{plays: [...window.__summary.drives.current.plays,
        {text: '** Injury Update: SF-B.Purdy has returned to the game.', period: {number: 3}, clock: {displayValue: '2:00'}}]}]}}; }""")

    def finish_every_game(self):
        """No game is on any more, and the clock has moved ten minutes."""
        self.page.evaluate("""() => { for (const k of Object.keys(GD_STATS.games)) GD_STATS.games[k] = 'complete'; GD_CLOCK = {};
      const t = Date.now() + 600000; Date.now = () => t; }""")

    def poll(self):
        """Live's poller, as every poll calls it: asks ESPN for each game that is on and is due."""
        self.page.evaluate("gdHurtPoll()")

    def asked(self):
        """The ESPN event ids asked for, in order."""
        return self.page.evaluate("window.__calls")

    def ask_count(self):
        return self.page.evaluate("window.__calls.length")

    def most_in_flight(self):
        """The most requests open at once."""
        return self.page.evaluate("window.__max")

    def who_is_hurt(self):
        """GD_HURT: {slug: {slug, name, team, q, clock, back}}."""
        return self.page.evaluate("GD_HURT")

    def is_served(self):
        """PAGE_SERVED(): true over http, false from a file."""
        return self.page.evaluate("PAGE_SERVED()")
