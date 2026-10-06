"""Live as a reader who has not picked a team, then one who has (design/src/js/surface/live/mine.js, mirror.js,
board.js, league.js, nflnow.js) and the board of a reader with a game on.

`LiveMinePage` is `LiveTabsPage` (pages/live_tabs.py) with what a test of whose team is "mine", and of the
board's rows, reads. Every locator is here, data-testid first (`live-*`, test hooks only). The team picker of
"Whose game are you watching?" is the shared one (surface/teams, `[data-pick]`), found inside its card; the
header bar's team switch is chrome (`#hdrswitch`, `.ts-*`), found by id and class. A state word (`mine`, `on`,
`l`, `r`) is a class, joined to the element's test id with `and_`.

`open_bare` is a first visit: the suite's seed picks David's Yahoo team and follows his three, so this page
removes those keys before the page's own script runs. The page is week 2 of the fixture
(tests/fixtures/gameday.json) with TeamMinh (`MATE`) planted as the ESPN team that plays David's.

Reads return plain data; no method asserts. A method that changes state draws again, the way the page's own
poll does (`paintLive`).
"""
import json

from pages.live_tabs import LiveTabsPage
from test_render import LIVE_PLANT

SIZE = (390, 844)
# TeamMinh plays David's ESPN team in the fixture's week 2 (tests/fixtures/gameday.json): key
# "espn-teamminh", Jaxon Smith-Njigba (SEA) in its lineup.
MATE = "espn-teamminh"
PLANT_MATE = f"TEAMS['{MATE}'] = Object.assign({{}}, TEAMS.espn, {{key: '{MATE}', name: 'TeamMinh', mate: true, league: 'espn'}});"
# the seed's pick, follows, roster mode and owner (test_render.PICKED), gone before the page's script runs
BARE = 'try { for (const k of ["tw-team", "tw-follow", "tw-roster-mode", "tw-owner"]) localStorage.removeItem(k); } catch (e) {}'
HALF_STATES = """hs => hs.map(h => [h.querySelector('[data-testid="live-name"]').dataset.gdteam,
  h.classList.contains('on') ? 'LIVE' : h.classList.contains('pre') ? 'PRE' : 'FINAL'])"""
HALF_READINGS = """hs => hs.map(r => ({on: r.classList.contains('on'),
  lime: getComputedStyle(r.querySelector('[data-testid="live-pts"]')).color,
  fire: !!r.querySelector('[data-testid="live-pts"] .gd-flame'),
  ring: false,
  pts: parseFloat(r.querySelector('[data-testid="live-pts"]').textContent), proj: parseFloat(r.querySelector('[data-testid="live-proj"]').textContent)}))"""
STRIPED = """m => {
  const bg = r => getComputedStyle(r).backgroundColor, rs = [...m.querySelectorAll('[data-testid="live-mirror-row"]')];
  return rs.every((r, i) => i < 2 || bg(r) === bg(rs[i - 2])) && bg(rs[0]) !== bg(rs[1]); }"""
OPEN_SHEET = """c => { const g = gdWeekGames().find(x => gdSameClub(x.home, c) || gdSameClub(x.away, c));
        gsOpen({event: '1', away: g.away, home: g.home}, null); }"""


class LiveMinePage(LiveTabsPage):
    def __init__(self, page):
        super().__init__(page)
        tid = page.get_by_test_id
        self._who, self._who_leagues, self._who_back = tid("live-who"), tid("live-who-league"), tid("live-who-back")
        self._halves = tid("live-half")
        self._left_halves = self._halves.and_(page.locator(".l"))

    @classmethod
    def open_bare(cls, mount, team=None, follow=None):
        """Mount Live at a phone as a first visit: no pick, no follow. `team` and `follow` (a list of keys) are stored
        before Live draws; TeamMinh is planted. Returns (LiveMinePage, the page's errors)."""
        page, errors = mount("live", size=SIZE, init=(BARE,))
        live = cls(page)
        store = (f"localStorage.setItem('tw-team', '{team}');" if team else "") + \
                (f"localStorage.setItem('tw-follow', '{json.dumps(follow)}');" if follow is not None else "")
        page.evaluate(PLANT_MATE + store + LIVE_PLANT())
        page.evaluate("render()")
        live._tabbar.wait_for(state="attached")
        return live, errors

    @classmethod
    def open_board(cls, mount, size=SIZE):
        """Mount Live at `size` as the reader of David's ESPN team on week 2, My league drawn and its rows in."""
        live, errors = cls.open_league(mount, size=size)
        live.wait_for_rows()
        return live, errors

    # ---- who is the reader ----

    def my_team_and_follows(self):
        """[the picked team's key or None, the followed keys]."""
        return self.page.evaluate("[myTeamLoad(), followLoad()]")

    def follows(self):
        return self.page.evaluate("followLoad()")

    def picks_follows_and_league(self):
        """[the picked team, the followed ones, the key of the league Live draws]."""
        return self.page.evaluate("[myTeamLoad(), followLoad(), gdLeague().key]")

    def picked_view_and_hash(self):
        """[the picked team's key, the view on screen, the URL's hash]."""
        return self.page.evaluate("[localStorage.getItem('tw-team'), SURFACE, location.hash]")

    def store_team(self, key):
        """The reader's pick changes in the store only; nothing draws."""
        self.page.evaluate(f"localStorage.setItem('tw-team', '{key}')")

    def follow_and_repaint(self, keys):
        self.page.evaluate(f"localStorage.setItem('tw-follow', JSON.stringify({json.dumps(keys)})); paintLive()")

    def forget_pick_and_repaint(self):
        self.page.evaluate("localStorage.removeItem('tw-team'); paintLive()")

    def toggle_follow(self, key):
        self.page.evaluate(f"followToggle('{key}')")

    def stored_team(self):
        return self.page.evaluate("localStorage.getItem('tw-team')")

    def set_tab(self, name):
        """Live's own tab function, as the board's bar calls it (league, games, tds)."""
        self.page.evaluate(f"gdSetTab('{name}')")

    # ---- "Whose game are you watching?" ----

    def who_title(self):
        return self._who.locator("h3").inner_text()

    def who_card_count(self):
        return self._who.count()

    def who_league_count(self):
        return self._who_leagues.count()

    def who_team_count(self):
        """The teams a league lists in the same card."""
        return self._who.locator("[data-pick]").count()

    def pick_league(self, key):
        self._who_leagues.and_(self.page.locator(f"[data-gdwho='{key}']")).click()

    def tap_who_back(self):
        self._who_back.click()

    def pick_in_card(self, key):
        self._who.locator(f"[data-pick='{key}']").click()

    def my_league_parts_count(self):
        """The score head, lineups (and benches), strip and the reader's own side: none without a team."""
        return self._head.or_(self._mirror).or_(self._bench).or_(self._strip).or_(self._side.and_(self.page.locator(".mine"))).count()

    def tile_mark_count(self):
        """The NFL tab's tiles that count as the reader's, and the "yours" marks inside tiles."""
        return self._tiles.and_(self.page.locator(".mine")).or_(self._tiles.locator("em")).count()

    def mine_tile_yours_count(self):
        return self._mine_tiles().locator("em").count()

    # ---- the score head, the two sides ----

    def left_side_text(self):
        return self._side.and_(self.page.locator(".a")).inner_text()

    def left_side_class(self):
        return self._side.and_(self.page.locator(".a")).get_attribute("class")

    def right_side_text(self):
        return self._side.and_(self.page.locator(".b")).inner_text()

    def head_text(self):
        return self._head.inner_text()

    def left_half_count(self, text):
        """Starter halves on the left (the reader's) that name `text`."""
        return self._starter_halves("l").filter(has_text=text).count()

    def right_half_count(self, text):
        return self._starter_halves("r").filter(has_text=text).count()

    def _starter_halves(self, side):
        """Halves of the starters' lineups, not the benches, on the `l` or `r` side."""
        return self._mirror.get_by_test_id("live-half").and_(self.page.locator(f".{side}"))

    # ---- the game sheet, opened from a lineup ----

    def open_game_of(self, club):
        """Open the sheet on the week's game that `club` plays, as a tap on it would."""
        self.page.evaluate(OPEN_SHEET, club)
        self.wait_for_game_sheet()

    def wait_for_game_sheet_closed(self):
        self.page.wait_for_selector("#gamesheet:not(.on)", state="attached")

    # ---- the NFL tab's live tile ----

    def in_tile_count(self):
        """Tiles of games on now."""
        return self._in_tiles().count()

    def in_tile_game(self):
        """The game key (id, away, home) of the one tile on now."""
        return self._in_tiles().get_attribute("data-gdnfl")

    def in_tile_label(self):
        return self._in_tiles().locator(".gd-ts span").inner_text()

    def tap_in_tile(self):
        self._in_tiles().click()

    def _in_tiles(self):
        return self._tiles.and_(self.page.locator(".in"))

    # ---- the board: halves, points, projections ----

    def left_half_states(self):
        """Each starter half on the left: [its club, LIVE (his game is on), PRE (not kicked off) or FINAL]."""
        return self._starter_halves("l").evaluate_all(HALF_STATES)

    def drawn_shape_count(self):
        """Drawn shapes in the lineups that are not a flame: a lock beside a final game would be one."""
        return self._mirror.or_(self._bench).locator("svg:not(.gd-flame)").count()

    def half_readings(self):
        """Every drawn half: {on (his game is on), lime (the points' colour), fire (a flame beside them), ring, pts, proj}."""
        return self._halves.evaluate_all(HALF_READINGS)

    def smash_margin(self):
        """The Digest's own Smashed margin, the points over projection a flame stands for."""
        return self.page.evaluate("LIVE_DIGEST.rules.smashed.min")

    def left_projections(self):
        return self._left_halves.get_by_test_id("live-proj").all_inner_texts()

    def rows_are_striped(self):
        """Rows shade every other one, and the first two differ."""
        return self._mirror.evaluate(STRIPED)

    def live_half_count(self):
        return self._halves.and_(self.page.locator(".on")).count()

    def first_live_half_background(self):
        return self._halves.and_(self.page.locator(".on")).first.evaluate("e => getComputedStyle(e).backgroundColor")

    # ---- the board: the strip and the ranking ----

    def chip_states_lead_their_chips(self):
        """Every chip's first child is its state word."""
        return self._chips.evaluate_all("gs => gs.every(g => g.firstElementChild.classList.contains('gd-cs'))")

    def tap_other_chip(self):
        """The first chip that is not the reader's."""
        self._chips.and_(self.page.locator(":not(.mine)")).first.click()

    def ladder_quiet_median_count(self):
        """The grey median line of a league that ranks for bragging."""
        return self._ladder.get_by_test_id("live-ladder-median").and_(self.page.locator(".quiet")).count()

    # ---- the header bar's team switch ----

    def open_header_switch(self):
        """The phone's switch opens on the picked team's league."""
        self.page.locator("#hdrswitch [data-tsbtn]").click()
        self._wait_for_header_menu()

    def header_team_count(self, key):
        """How many items in the open menu are the team `key`."""
        return self.page.locator(f"#hdrswitch .ts-menu .ts-item[data-k='{key}']").count()

    def tap_header_back(self):
        self.page.locator("#hdrswitch .ts-back").click()

    def header_empty_count(self):
        """The menu's line that says nothing is followed."""
        return self.page.locator("#hdrswitch .ts-empty").count()

    def header_league_count(self):
        return self.page.locator("#hdrswitch .ts-league").count()

    def open_header_league(self, key):
        """Drill into a league: the menu redraws with that league's own list."""
        self.page.locator(f"#hdrswitch .ts-league[data-tsleague='{key}']").click()
        self._wait_for_header_menu()

    def pick_first_header_team(self, key_prefix):
        """The first team of the open list whose key starts with `key_prefix` and is on screen."""
        self.page.locator(f"#hdrswitch .ts-menu .ts-item[data-k^='{key_prefix}']:visible").first.click()

    def view_and_league(self):
        """[the view on screen, the key of the league Live draws]."""
        return self.page.evaluate("[SURFACE, gdLeague().key]")

    def _wait_for_header_menu(self):
        self.page.wait_for_selector("#hdrswitch .ts-menu:not([hidden]) .ts-back")
