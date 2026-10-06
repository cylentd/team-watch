"""Live's TDs tab as a feed of rows (design/src/js/surface/live/tds.js): who has scored, who of Parlay's
top TD chances is still alive, the Feed / By game switch and the Mine, Pass, Rush, Rec chips.

`LiveTdsPage` is `LivePage` (pages/live.py, which holds the TD clips reel and the card, row and chip
locators) with what a test of the rows reads. Every locator is here, data-testid first (`live-td-*`, test
hooks only). The state of a row (`live`, `later`, `missed`, `scored`) is a class, read as one.

Two kinds of read. A tab on screen (`open_games_day`) is read through its rows and cards. The rows' markup
alone (`rows_at`, `colours_at`, `reading_text`, ...) is built by `gdTdsHTML` into a detached element, the
way the page's poll builds it, so the test chooses the clock and the lead without a game day around it.

Reads return plain data; no method asserts. A method that changes state draws again (`paintLive`).
"""
from pages.live import LivePage
from test_render import LIVE_PLANT

PHONE = (360, 780)
PHABLET = (390, 844)

# The page's own TD chances, ranked the way the board ranks them, and the lead rows planted around them.
PLANT = """() => {
  const board = PROPS.filter(p => p.mkt === "TD" && p.slug).sort(SORTS.model).slice(0, TD_ALIVE_N);
  const [a, b, c] = board;
  const lead = {
    "9001": {n: "Test Rusher", pos: "RB", team: "SF", s: {rush_td: 2, rush_yd: 80}, pts: 20},
    "9002": {n: "Test Passer", pos: "QB", team: "SF", s: {pass_td: 3, pass_yd: 300}, pts: 24},
    "9003": {n: "Test Nobody", pos: "WR", team: "SF", s: {rec: 4, rec_yd: 40}, pts: 8},
    "9004": {n: b.n, pos: b.pos, team: b.team, s: {rec_td: 1}, pts: 12}};
  GD_STATS = {week: 2, games: {}, stats: {}, lead};
  GD_CLOCK = {};
  return {a: [a.n, a.team], b: [b.n, b.team], c: [c.n, c.team], n: board.length};
}"""

# One club's game at `state`, then the tab's rows built into a detached element, card by card.
ROWS_AT = """([club, state]) => {
  GD_CLOCK = {[club]: {state, q: 3, clock: "4:12", half: false, detail: "", clubs: [club]}};
  const host = document.createElement("div");
  host.innerHTML = gdTdsHTML(GD.leagues[0]);
  const tid = (el, n) => el.querySelector(`[data-testid="${n}"]`);
  return [...host.querySelectorAll('[data-testid="live-td-card"]')].map(card => [...card.querySelectorAll('[data-testid="live-td-row"]')].map(r =>
    ({cls: r.className.replace("td-row", "").trim(), who: tid(r, "live-td-who").firstChild.textContent.trim(),
      line: (tid(r, "live-td-line") || {}).textContent || "", clock: tid(r, "live-td-clock").textContent,
      slug: r.dataset.tdslug})));
}"""

# Every club in `clubs` final; the tab built, put in Live's view (its CSS is fenced there) and its colours read.
COLOURS_AT = """([clubs]) => {
  GD_CLOCK = Object.fromEntries(clubs.map(c => [c, {state: "post", q: 4, clock: "0:00", half: false, detail: "", clubs: [c]}]));
  const probe = v => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue(v);
    document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; };
  const host = document.createElement('div');
  host.innerHTML = gdTdsHTML(null);
  const view = document.getElementById('view'), was = view.dataset.view;
  view.dataset.view = 'live';                      // the stylesheet is fenced to Live's view (design/scope.json)
  view.append(host);
  const tid = (el, n) => el.querySelector(`[data-testid="${n}"]`);
  const row = host.querySelector('[data-testid="live-td-row"].scored'), miss = host.querySelector('[data-testid="live-td-row"].missed');
  const col = (el, n) => getComputedStyle(tid(el, n)).color;
  const out = {line: col(row, 'live-td-line'), clock: col(row, 'live-td-clock'), name: col(row, 'live-td-who'),
               scoredCls: [...host.querySelector('[data-testid="live-td-card"]').querySelectorAll('[data-testid="live-td-row"]')].map(r => r.className),
               up: probe('--up'), grey: probe('--ink-3'), down: probe('--down'), missLine: miss ? col(miss, 'live-td-line') : null};
  host.remove();
  if (was === undefined) delete view.dataset.view; else view.dataset.view = was;
  return out;
}"""

EMPTY_TEXT = """() => { const h = document.createElement('div'); h.innerHTML = gdTdsHTML(null);
  return h.querySelector('[data-testid="live-td-empty"]').textContent; }"""
ROW_COUNT_AND_TEXT = """() => { const h = document.createElement('div'); h.innerHTML = gdTdsHTML(null);
  return [h.querySelectorAll('[data-testid="live-td-row"]').length, h.textContent.trim()]; }"""
FIRST_ROW_PROFILE = """() => {
  let got = null;
  openProfile = (p) => { got = p; };
  const host = document.createElement("div");
  host.innerHTML = gdTdsHTML(null);
  wireTds(host);
  host.querySelector('[data-testid="live-td-row"]').click();
  return got;
}"""

# Three games of week 2: KC at SF is on, MIN at DET went final early, BUF at MIA went final late. One of the
# reader's own players (the first of their lineups) scored for KC. Returns his initial-and-name, as a row says it.
GAMES = """() => {
  const week = GD.leagues[0].week;
  GD_GAMES.splice(0, GD_GAMES.length,
    {home: "SF", away: "KC", kickoff: "2026-09-13T20:25:00Z", week},
    {home: "DET", away: "MIN", kickoff: "2026-09-13T17:00:00Z", week},
    {home: "MIA", away: "BUF", kickoff: "2026-09-13T17:30:00Z", week});
  GD_CLOCK = {SF: {state: "in", q: 3, clock: "4:12", half: false, detail: "", clubs: ["SF", "KC"]},
              DET: {state: "post", q: 4, clock: "0:00", half: false, detail: "", clubs: ["DET", "MIN"]},
              MIA: {state: "post", q: 4, clock: "0:00", half: false, detail: "", clubs: ["MIA", "BUF"]}};
  Object.assign(GD_STATS.stats, {SF: {pts_allow: 17}, KC: {pts_allow: 24}, DET: {pts_allow: 20}, MIN: {pts_allow: 13},
                                  MIA: {pts_allow: 10}, BUF: {pts_allow: 27}});
  const m = GD.leagues.flatMap(l => gdMineLineup(l)).find(r => r.sid && r.n);
  GD_STATS.lead = {
    "9001": {n: "Test Rusher", pos: "RB", team: "SF", s: {rush_td: 2}, pts: 20},
    "9002": {n: "Test Passer", pos: "QB", team: "SF", s: {pass_td: 3}, pts: 24},
    "9003": {n: "Test Catcher", pos: "WR", team: "KC", s: {rec_td: 1}, pts: 12},
    "9004": {n: "Detroit Catcher", pos: "WR", team: "DET", s: {rec_td: 1}, pts: 11},
    "9005": {n: "Miami Runner", pos: "RB", team: "MIA", s: {rush_td: 1}, pts: 10},
    [m.sid]: {n: m.n, pos: m.pos, team: "KC", s: {rush_td: 1}, pts: 9}};
  return nameInitial(m.n);
}"""

WHO = "rs => rs.map(r => r.querySelector('[data-testid=\"live-td-who\"]').firstChild.textContent.trim())"
GAME_CARDS = """cs => cs.map(c => ({head: c.querySelector('[data-testid="live-td-gh"]').innerText.replace(/\\s+/g, ' ').trim(),
  rows: [...c.querySelectorAll('[data-testid="live-td-row"]')].map(r => r.querySelector('[data-testid="live-td-who"]').firstChild.textContent.trim())}))"""
CONTROLS_LAYOUT = """() => {
  const tid = n => `[data-testid="${n}"]`;
  const chips = [...document.querySelectorAll(`${tid("live-td-chip")}, ${tid("live-td-bygame")}`)];
  const row = document.querySelector(tid("live-td-filters"));
  return {w: document.documentElement.scrollWidth, vw: innerWidth, chips: row.getBoundingClientRect(),
          n: chips.length, last: chips[chips.length - 1].dataset.tdgame !== undefined,
          tops: [...new Set(chips.map(c => Math.round(c.getBoundingClientRect().top)))].length,
          tallest: Math.max(...chips.map(c => c.getBoundingClientRect().height)),
          shortest: Math.min(...chips.map(c => c.getBoundingClientRect().height)),
          gdRows: document.querySelectorAll('.gd-leagues, .td-mode').length,
          rowW: row.clientWidth, sep: document.querySelectorAll(tid("live-td-sep")).length};
}"""
BLOCK_STORAGE = "Storage.prototype.setItem = () => { throw new Error('blocked'); }; Storage.prototype.getItem = () => { throw new Error('blocked'); }; 0"


class LiveTdsPage(LivePage):
    def __init__(self, page):
        super().__init__(page)
        tid = page.get_by_test_id
        self._heads, self._filters, self._lines = tid("live-td-head"), tid("live-td-filters"), tid("live-td-line")
        self._empty, self._headers = tid("live-td-empty"), tid("live-td-gh")

    @classmethod
    def open_games_day(cls, mount, size=PHONE):
        """Mount Live at `size` as David's ESPN reader on the week 2 fixture, plant three games of week 2 with scorers
        and open the TDs tab. Returns (LiveTdsPage, the reader's own scorer as a row names him, the page's errors)."""
        live, errors = cls.mounted(mount, size, plant_week=True)
        mine = live.page.evaluate(GAMES)
        live.open_tab("tds")
        return live, mine, errors

    @classmethod
    def mounted(cls, mount, size=PHABLET, plant_week=False):
        """Live mounted at `size`, as it draws; with `plant_week` the week 2 fixture as the ESPN reader, drawn again.
        Returns (LiveTdsPage, the page's errors)."""
        page, errors = mount("live", size=size)
        live = cls(page)
        if plant_week:
            page.evaluate("localStorage.setItem('tw-team', 'espn');" + LIVE_PLANT())
            page.evaluate("render()")
            page.get_by_test_id("live-tabbar").wait_for(state="attached")
        return live, errors

    # ---- planting ----

    def plant_scorers(self):
        """The page's own top TD chances and four scorers around them. Returns {a, b, c: [name, club], n: chances planted}."""
        return self.page.evaluate(PLANT)

    def drop_lead(self):
        """The day's scorers are gone: nobody has scored."""
        self.page.evaluate("GD_STATS.lead = {}")

    def drop_lead_from_reply(self):
        """An older edge copy: the reply has no `lead` at all."""
        self.page.evaluate("GD_STATS = {week: 2, games: {}, stats: {}}")

    def drop_stats(self):
        self.page.evaluate("GD_STATS = null")

    def forget_team_and_filter_mine(self):
        """The reader picked no team and has Mine on; Live draws again."""
        self.page.evaluate("localStorage.removeItem('tw-team'); localStorage.removeItem('tw-follow'); TD_ON = {mine: true}; paintLive()")

    def clear_filters(self):
        """The chips clear, as they do on a visit; the view stays."""
        self.page.evaluate("TD_ON = {}; paintLive()")

    def block_storage(self):
        """A store that will not answer."""
        self.page.evaluate(BLOCK_STORAGE)

    # ---- what a reader does ----

    def tap_first_game_header(self):
        self._headers.first.click()

    # ---- what a reader sees on the tab ----

    def by_game_pressed(self):
        """aria-pressed of the By game toggle: "true" (By game) or "false" (Feed)."""
        return self._by_game.get_attribute("aria-pressed")

    def chip_pressed(self, kind):
        return self.page.locator(f"[data-tdchip='{kind}']").get_attribute("aria-pressed")

    def pressed_control_count(self):
        """Chips and the toggle that are on."""
        return self._filters.locator("[aria-pressed='true']").count()

    def card_count(self):
        """Feed cards (Scored, Still alive, or the one empty line)."""
        return self._cards.count()

    def alive_card_count(self):
        """Feed cards headed Still alive."""
        return self._cards.filter(has=self._heads.filter(has_text="Still alive")).count()

    def rows(self):
        """Who each row names, top to bottom, as the row says it (initial and last name)."""
        return self._rows.evaluate_all(WHO)

    def line_texts(self):
        """The second line of every row that has one (2 rush TD, No TD yet, ...)."""
        return self._lines.all_inner_texts()

    def only_line_text(self):
        """The second line, when exactly one row has one (raises if not)."""
        return self._lines.inner_text()

    def game_cards(self):
        """Each By game card: its header (clubs, score, clock) and the rows under it."""
        return self._gcards.evaluate_all(GAME_CARDS)

    def clock_or_club_in_game_cards(self):
        """Clocks, club tags and chance tags in a game's rows: a game card's header holds the first two, the rows none."""
        return self._gcards.locator("[data-testid='live-td-clock'], [data-testid='live-td-club'], [data-testid='live-td-chance']").count()

    def cards_in_game_cards(self):
        """Cards inside a game card: one card per subject, never a card in a card."""
        return self._gcards.locator("[data-testid='live-td-card'], [data-testid='live-td-gcard'], .gd-card").count()

    def buttons_in_buttons_in_game_cards(self):
        return self._gcards.locator("button button").count()

    def empty_count(self):
        return self._empty.count()

    def empty_text(self):
        """The one line a tab with nothing to show says (raises if there is not exactly one)."""
        return self._empty.inner_text()

    def stored_mode(self):
        """The view the reader left, in the store: feed (nothing yet) or game."""
        return self.page.evaluate("localStorage.getItem('tw-live-tds')")

    def controls_layout(self):
        """The chip row on screen: {w, vw, chips (the row's box), n, last (By game is last), tops (distinct lines), tallest, shortest, gdRows, rowW, sep}."""
        return self.page.evaluate(CONTROLS_LAYOUT)

    def wait_for_game_sheet_closed(self):
        self.page.wait_for_selector("#gamesheet:not(.on)", state="attached")

    # ---- the tab's markup, built alone (a detached element) ----

    def rows_at(self, club, state):
        """[Scored rows, Still alive rows] with `club`'s game at `state` (in, post, pre): {cls (the state class), who, line, clock, slug}."""
        return self.page.evaluate(ROWS_AT, [club, state])

    def colours_at(self, clubs):
        """With every club in `clubs` final: the colours of a scorer's line, clock and name, a missed row's line, and the page's
        --up, --ink-3 and --down; plus the classes of the first card's rows."""
        return self.page.evaluate(COLOURS_AT, [clubs])

    def empty_text_built(self):
        return self.page.evaluate(EMPTY_TEXT)

    def rows_and_text_built(self):
        """[how many rows, the text] of the tab as built now."""
        return self.page.evaluate(ROW_COUNT_AND_TEXT)

    def profile_from_first_row_built(self):
        """What a tap on the first row of the tab as built now hands openProfile (stubbed to hand its argument back)."""
        return self.page.evaluate(FIRST_ROW_PROFILE)
