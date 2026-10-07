"""Live's three tabs (design/src/js/surface/live/): My league (the strip of matchups, the score head, the
mirrored lineups, the ranking), NFL (a tile per game) and the tab row that holds them.

`LiveTabsPage` is `LivePage` (pages/live.py) with what a test of the tabs reads. Every locator is here,
data-testid first (`live-*`, test hooks only). Two sets are found by class, because the code that draws
them is not Live's: the phone's tab row (chrome/nav.js: `#subnav`, `.tr-seg`) and the team switch
(chrome/teamswitch.js: `#switch`, `#hdrswitch`, `.ts-menu`). A state word on a Live element (`mine`, `on`,
`in`, `lead`, `behind`) is a class, joined to the element's test id with `and_`.

The page is week 2 of the fixture (tests/fixtures/gameday.json): SF's game is on, DET's has not started,
every other game is final. The reader's team is David's ESPN one unless `open_league` is told another.

Reads return plain data; no method asserts. A method that changes state draws again, the way the page's own
poll does (`paintLive`).
"""
import re

from pages.gamesheet import SWIPE
from pages.live import LivePage
from test_render import LIVE_PLANT

PHONE = (360, 780)
DESK = (1400, 900)

COLOUR = """(n) => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue(n);
  document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; }"""
# the week's first game on, its second not started, the rest final (what the fixture has, planted on every club)
WEEK_STATES = """() => {
  const gs = gdWeekGames(), st = GD_STATS.games;
  gs.forEach((g, i) => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = i === 0 ? "in_game" : i === 1 ? "pre_game" : "complete"; });
  paintLive();
}"""
TWO_LIVE = """() => { const st = GD_STATS.games; gdWeekGames().slice(0, 2).forEach(g => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = "in_game"; }); paintLive(); }"""
MIRROR_ROW = "[data-testid='live-mirror'] [data-testid='live-mirror-row']"
LAYOUT = """() => {
  const rows = [...document.querySelectorAll("%s")];
  const box = e => e.getBoundingClientRect();
  const at = s => { const e = document.querySelector(s); return e ? [Math.round(box(e).top + scrollY), Math.round(box(e).height)] : null; };
  const tid = n => `[data-testid="${n}"]`;
  return {last: Math.round(box(rows[8]).bottom + scrollY), tallest: Math.round(Math.max(...rows.map(r => box(r).height))),
          head: Math.round(box(document.querySelector(tid("live-head"))).top + scrollY),
          parts: {tabs: at(tid("live-tabbar")), strip: at(tid("live-strip")), head: at(tid("live-head")),
                  median: at(tid("live-medline")), rows: at(tid("live-mirror"))}};
}""" % MIRROR_ROW
TILE_SCORES = """ts => ts.map(t => {
  const [a, h] = [...t.querySelectorAll('[data-testid="live-tile-club"]')], n = r => +r.querySelector('b').textContent;
  if (isNaN(n(a)) || isNaN(n(h))) return null;
  const cls = r => r.classList.contains('lead') ? 'lead' : r.classList.contains('behind') ? 'behind' : 'plain';
  return [n(a), n(h), cls(a), cls(h)];
}).filter(Boolean)"""
LEADER_COLOURS = "rs => rs.map(r => [getComputedStyle(r.querySelector('span')).color, getComputedStyle(r.querySelector('b')).color, r.style.getPropertyValue('--tc')])"
# every club colour the tab can pick, held to 3:1 against the panel (a near-black one falls back to ink)
LOW_CONTRAST_CLUBS = """() => {
  const lum = h => { const c = [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255).map(v => v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
  const panel = lum('#171b21');
  return Object.keys(TEAM_COLOURS).filter(k => { const t = gdClubTint(k); return t && (lum(t) + 0.05) / (panel + 0.05) < 2.8; });
}"""
CHIP_SHAPE = """cs => cs.map(c => ({state: c.querySelectorAll('[data-testid="live-chip-state"]').length,
  rows: c.querySelectorAll('.gd-cr').length, scores: c.querySelectorAll('.gd-cr b').length}))"""
CHIP_GAPS = "cs => cs.map(c => { const [a, b] = [...c.querySelectorAll('.gd-cr b')].map(x => +x.textContent); return Math.abs(a - b); })"
CLOCK_SHAPE = "bs => bs.map(b => ({tag: b.tagName, nfl: b.dataset.gdnfl, focus: b.dataset.gdfocus || ''}))"


class LiveTabsPage(LivePage):
    def __init__(self, page):
        super().__init__(page)
        tid = page.get_by_test_id
        self._tabbar, self._tab_buttons = tid("live-tabbar"), tid("live-tab")
        self._match, self._head, self._side, self._lead = tid("live-match"), tid("live-head"), tid("live-side"), tid("live-lead")
        self._mirror, self._bench, self._mrow = tid("live-mirror"), tid("live-bench"), tid("live-mirror-row")
        self._slots, self._clocks, self._names = tid("live-slot"), tid("live-clock"), tid("live-name")
        self._strip, self._chips, self._ladder = tid("live-strip"), tid("live-chip"), tid("live-ladder")
        self._tiles = tid("live-tile")
        self._mine_side = self._side.and_(page.locator(".a.mine"))
        self._bye = self._head.and_(page.locator(".bye"))
        self._clock_buttons = self._clocks.and_(page.locator("[data-gdnfl]"))

    @classmethod
    def open_league(cls, mount, size=PHONE, team="espn", states=None):
        """Mount Live at `size` as the reader of `team` (espn or yahoo; None keeps the seed's pick) on the week 2 fixture,
        My league drawn. Returns (LiveTabsPage, the page's errors)."""
        page, errors = mount("live", size=size)
        live = cls(page)
        page.evaluate((f"localStorage.setItem('tw-team', '{team}');" if team else "") + LIVE_PLANT(states))
        page.evaluate("render()")
        live._tabbar.wait_for(state="attached")
        return live, errors

    # ---- planting and state a reader changes ----

    def plant_week_states(self):
        """The week's first game on, its second not started, every other final."""
        self.page.evaluate(WEEK_STATES)

    def make_first_two_games_live(self):
        self.page.evaluate(TWO_LIVE)

    def pick_team(self, key):
        """The reader's team changes (another tab or window) and Live's poll draws it."""
        self.page.evaluate(f"localStorage.setItem('tw-team', '{key}'); paintLive()")

    def remove_my_game(self):
        """The reader's team has no game this week (a bye), then Live draws again."""
        self.page.evaluate("(() => { const lg = gdLeague(), me = gdMine(lg); lg.games = lg.games.filter(g => !g.includes(me)); paintLive(); })()")

    def store_tab_and_render(self, value):
        """Another view sent the reader here by storing `value` as the tab, then opening Live."""
        self.page.evaluate(f"localStorage.setItem('tw-live-tab', '{value}'); render()")

    def block_storage(self):
        self.page.evaluate("Object.defineProperty(window, 'localStorage', {get(){ throw new Error('blocked'); }})")

    # ---- what a reader does ----

    def open_benches(self):
        self.page.get_by_test_id("live-bench-toggle").click()

    def tap_first_name(self):
        self._names.first.click()

    def tap_first_clock(self):
        self._clock_buttons.first.click()

    def tap_first_tile(self):
        self._tiles.first.click()

    def tap_tile(self, i):
        self._tiles.nth(i).click()

    def tap_chip(self, i):
        self._chips.nth(i).click()

    def tap_my_chip(self):
        self._my_chips().click()

    def open_team_menu(self):
        """The reader's name on the score head is the team switch (a desktop's; a phone's is the header bar's)."""
        self._mine_side.locator("#switch [data-tsbtn]").click()
        self.page.wait_for_selector("#switch .ts-menu:not([hidden])")

    def choose_team(self, key):
        """Pick a team in the open menu; the board draws that team's league."""
        self.page.locator(f"#switch .ts-item[data-k='{key}']:visible").first.click()
        self._strip.wait_for()

    def wait_for_profile(self):
        self.page.wait_for_selector("#modal.on")

    # ---- the tab row and the board's bar ----

    def tab_names(self):
        """The phone's tab row segments, left to right, without the live count a tab may carry."""
        return [re.sub(r"\d+$", "", s).strip() for s in self.page.locator("#subnav .tr-x .tr-seg").all_inner_texts()]

    def open_pill(self):
        """The pill that opened in place into the tabs."""
        return self.page.locator("#subnav .tr-x .mode-sub[aria-pressed='true']").inner_text()

    def row_pressed_tab(self):
        """The tab pressed in the tab row: league, games or tds."""
        return self.page.locator("#subnav .tr-seg[aria-pressed='true']").get_attribute("data-gdtab")

    def row_tab_pressed(self, name):
        return self.page.locator(f"#subnav [data-gdtab='{name}']").get_attribute("aria-pressed")

    def bar_pressed_tab(self):
        """The tab pressed in the board's own bar (a desktop's; hidden on a phone)."""
        return self._tab_buttons.and_(self.page.locator("[aria-pressed='true']")).get_attribute("data-gdtab")

    def bar_is_hidden(self):
        return self._tabbar.is_hidden()

    def row_live_text(self):
        """The lime count of games on now, on NFL in the tab row."""
        return self.page.locator("#subnav [data-gdtab='games'] .tr-n").inner_text()

    def row_live_label(self):
        return self.page.locator("#subnav [data-gdtab='games'] .tr-n").get_attribute("aria-label")

    def bar_live_label(self):
        """The same count's label in the board's bar."""
        return self._tab_buttons.and_(self.page.locator("[data-gdtab='games']")).locator(".gd-n").get_attribute("aria-label")

    def swipe_board(self, dx):
        """A one-finger swipe on the board, `dx` px sideways: negative is left."""
        self.page.evaluate(SWIPE, ["[data-testid='live-board']", dx])

    def league_and_mine(self):
        """[the league drawn, the reader's team in it]."""
        return self.page.evaluate("[gdLeague().key, gdMine(gdLeague())]")

    def board_class(self):
        return self.page.get_by_test_id("live-board").get_attribute("class")

    def tile_games(self):
        """Each tile's game as the tile carries it, in the order drawn: [espn event, away, home]."""
        return self._tiles.evaluate_all("ts => ts.map(b => b.dataset.gdnfl.split(','))")

    def stored_tab(self):
        return self.page.evaluate("localStorage.getItem('tw-live-tab')")

    def stored_league(self):
        return self.page.evaluate("localStorage.getItem('tw-live-league')")

    def hash(self):
        return self.page.evaluate("location.hash")

    def league_chip_count(self):
        """Live's league chips and the old league row: both are gone."""
        return self.page.locator("[data-gdleague], .gd-leagues:not(.td-mode)").count()

    def tds_card_count(self):
        return self.page.locator(".gd-card").count()

    def empty_state_count(self):
        return self.page.locator(".state-empty").count()

    # ---- My league: the score head ----

    def league_key(self):
        return self.page.evaluate("gdLeague().key")

    def league_count(self):
        return self.page.evaluate("GD.leagues.length")

    def now_card_count(self):
        """Cards of the old games and now views, which the NFL tab does not draw."""
        return self.page.locator(".gd-nfl, .gd-now").count()

    def league_game_count(self):
        return self.page.evaluate("gdLeague().games.length")

    def state(self):
        """[the picked team, the view on screen, the league drawn]."""
        return self.page.evaluate("[localStorage.getItem('tw-team'), SURFACE, gdLeague().key]")

    def my_side_text(self):
        return self._mine_side.inner_text()

    def my_side_count(self):
        """How many score-head sides are the reader's."""
        return self._side.and_(self.page.locator(".mine")).count()

    def my_name_is_visible(self):
        return self._mine_side.get_by_test_id("live-me").is_visible()

    def my_name_is_hidden(self):
        return self._mine_side.get_by_test_id("live-me").is_hidden()

    def switch_on_head_is_hidden(self):
        return self._mine_side.locator(".gd-sw").is_hidden()

    def header_switch_is_visible(self):
        """A phone's team switch is in the header bar."""
        return self.page.locator("#hdrswitch [data-tsbtn]").is_visible()

    def team_menu_count(self):
        return self.page.locator("#switch .ts-menu:not([hidden])").count()

    def lead_text(self):
        return self._lead.inner_text()

    def median_line(self):
        return self.page.get_by_test_id("live-medline").inner_text()

    def bye_text(self):
        return self._bye.inner_text().strip()

    def bye_count(self):
        return self._bye.count()

    def bye_switch_count(self):
        return self._bye.locator("#switch").count()

    def layout(self):
        """Rows and parts in px: {last: the 9th starter row's bottom, tallest: a row, head, parts: {name: [top, height]}}."""
        return self.page.evaluate(LAYOUT)

    def tab_bar_top(self):
        """Where the phone's bottom tab bar starts."""
        return self.page.evaluate("Math.round(document.querySelector('.tabbar').getBoundingClientRect().top)")

    def mirror_width(self):
        return self.page.evaluate("Math.round(document.querySelector('[data-testid=\"live-mirror\"]').getBoundingClientRect().width)")

    def wait_for_rows(self):
        self._mrow.first.wait_for()

    # ---- My league: the mirrored lineups ----

    def starter_count(self):
        """The starters in the reader's lineup, from the data."""
        return self.page.evaluate("gdMineLineup(gdLeague()).filter(gdStarter).length")

    def mirror_count(self):
        return self._mirror.count()

    def starter_rows(self):
        return self._mirror.get_by_test_id("live-mirror-row").count()

    def bench_rows(self):
        return self._bench.get_by_test_id("live-mirror-row").count()

    def bench_count(self):
        return self._bench.count()

    def row_count(self):
        """Rows in any lineup on screen, starters and benches."""
        return self._mrow.count()

    def rows_have_two_halves_and_a_slot(self):
        return self._mirror.get_by_test_id("live-mirror-row").evaluate_all("""rs => rs.every(r => r.querySelectorAll('[data-testid="live-half"]').length === 2
          && r.querySelectorAll('[data-testid="live-slot"]').length === 1)""")

    def clocks(self):
        """Every clock a row carries that opens a game: {tag, nfl (the game's key), focus (the player)}."""
        return self._clock_buttons.evaluate_all(CLOCK_SHAPE)

    def nested_buttons(self):
        return self.page.locator("[data-testid='live-mirror'] button button, [data-testid='live-bench'] button button").count()

    def slot_colour(self, slot):
        return self._slot(slot).evaluate("e => getComputedStyle(e).color")

    def slot_classes(self, slot):
        return self._slot(slot).get_attribute("class").split()

    def slot_background(self, slot):
        return self._slot(slot).evaluate("e => getComputedStyle(e).backgroundImage")

    def slot_class_count(self, cls):
        """Slot pills wearing a position's class (qb, def, ...)."""
        return self._slots.and_(self.page.locator(f".{cls}")).count()

    def _slot(self, slot):
        return self.page.locator(f"[data-testid='live-slot']:text-is('{slot}')").first

    # ---- My league: the strip and the ranking ----

    def strip_order(self):
        """The first class of each child of the match block, top to bottom."""
        return self._match.evaluate("m => [...m.children].map(e => e.className.split(' ')[0])")

    def chip_count(self):
        return self._chips.count()

    def chip_classes(self, i):
        return self._chips.nth(i).get_attribute("class")

    def chip_border_colour(self, i):
        return self._chips.nth(i).evaluate("e => getComputedStyle(e).borderTopColor")

    def chip_shapes(self):
        """Each chip: how many state words, team rows and scores it holds."""
        return self._chips.evaluate_all(CHIP_SHAPE)

    def chip_state_words(self):
        return self.page.get_by_test_id("live-chip-state").all_inner_texts()

    def chip_gaps(self):
        """Each chip's gap between its two scores, in strip order."""
        return self._chips.evaluate_all(CHIP_GAPS)

    def my_chip_count(self):
        return self._my_chips().count()

    def picked_chip_count(self):
        return self._chips.and_(self.page.locator(".on")).count()

    def picked_chip_classes(self):
        return self._chips.and_(self.page.locator(".on")).get_attribute("class")

    def my_picked_chip_count(self):
        return self._chips.and_(self.page.locator(".mine.on")).count()

    def _my_chips(self):
        return self._chips.and_(self.page.locator(".mine"))

    def ladder_is_below_mirror(self):
        return self._ladder.evaluate("(l, m) => l.getBoundingClientRect().top > m.getBoundingClientRect().bottom",
                                     self._mirror.element_handle())

    def ladder_median_lines(self):
        """The median line in the ranking when the league pays the top half (not the quiet grey one)."""
        return self._ladder.get_by_test_id("live-ladder-median").and_(self.page.locator(":not(.quiet)")).count()

    # ---- NFL: the tiles ----

    def week_game_count(self):
        return self.page.evaluate("gdWeekGames().length")

    def tile_grid_count(self):
        return self.page.get_by_test_id("live-tiles").count()

    def tile_count(self):
        return self._tiles.count()

    def tile_kinds(self):
        """in, pre or post for each tile, in the order drawn."""
        return self._tiles.evaluate_all("ts => ts.map(t => t.classList.contains('in') ? 'in' : t.classList.contains('pre') ? 'pre' : 'post')")

    def tile_is_visible(self, i):
        return self._tiles.nth(i).is_visible()

    def focus_is_on_tile(self, i):
        """Focus came home to the tile that opened the game sheet."""
        return self._tiles.nth(i).evaluate("e => document.activeElement === e")

    def tile_lefts(self, n=2):
        return self._tiles.evaluate_all(f"ts => ts.slice(0, {n}).map(t => Math.round(t.getBoundingClientRect().left))")

    def mine_tile_count(self):
        return self._mine_tiles().count()

    def first_mine_tile_says(self):
        """How many of the reader's starters the first of their tiles holds, as the tile says it."""
        return self._mine_tiles().first.get_by_test_id("live-tile-yours").inner_text()

    def first_mine_tile_border(self):
        return self._mine_tiles().first.evaluate("e => getComputedStyle(e).borderTopColor")

    def tile_style(self, kind, prop):
        """A computed style of the first tile in state `kind` (in, pre, post)."""
        return self._tiles.and_(self.page.locator(f".{kind}")).first.evaluate(f"e => getComputedStyle(e).{prop}")

    def resting_mine_tile_count(self):
        """The reader's tiles that are not live: they keep the ring and no live stripe."""
        return self._resting_mine().count()

    def resting_mine_tile_shadow(self):
        return self._resting_mine().first.evaluate("e => getComputedStyle(e).boxShadow")

    def tile_scores(self):
        """Each tile with both scores: [away, home, away's look, home's look], a look being lead, behind or plain."""
        return self._tiles.evaluate_all(TILE_SCORES)

    def leader_colours(self):
        """Each leading club: [its code's colour, its score's colour, the --tc it was given]."""
        return self.page.get_by_test_id("live-tile-club").and_(self.page.locator(".lead")).evaluate_all(LEADER_COLOURS)

    def trailer_colours(self):
        return self.page.get_by_test_id("live-tile-club").and_(self.page.locator(".behind")).locator("b").evaluate_all(
            "bs => bs.map(b => getComputedStyle(b).color)")

    def _mine_tiles(self):
        return self._tiles.and_(self.page.locator(".mine"))

    def _resting_mine(self):
        return self._tiles.and_(self.page.locator(".mine:not(.in)"))

    # ---- colours the page uses ----

    def colours(self, *names):
        """The page's tokens (--lime, --ink) as the browser computes them."""
        return [self.page.evaluate(COLOUR, n) for n in names]

    def low_contrast_clubs(self):
        return self.page.evaluate(LOW_CONTRAST_CLUBS)

    def club_tint(self, code):
        return self.page.evaluate(f"gdClubTint('{code}')")

    def clubs_without_tint(self):
        return self.page.evaluate("Object.keys(TEAM_COLOURS).filter(k => !gdClubTint(k))")
