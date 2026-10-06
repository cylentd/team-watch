"""The game sheet (design/src/js/surface/live/gamesheet.js, gamecards.js): one NFL game as a centred modal over
Live, with the scoreboard, the reader's players pinned under it, three tabs (Plays, Box score, Top scorers)
and a follow star that outlives the sheet.

`GameSheetPage` reads the sheet itself, `#gamesheet` (it hangs off <body>, outside every view), by test id
first (`gamesheet-*`, test hooks only). The sheet is opened the way a tap on a game opens it, `gsOpen`, on
Live as the planted week 2 of the fixture (tests/fixtures/gameday.json), with ESPN's summary and Sleeper's
box score (tests/fixtures/data) filled in. A tap on a tile or a clock that opens it is the Live page's
(pages/live.py, pages/live_tabs.py, pages/live_tds.py), not this one's.

Reads return plain data; no method asserts. A method that changes state draws again, the way the sheet's
own poll does (`gsPaint`).
"""
import json
import pathlib

from test_render import LIVE_PLANT

REPO = pathlib.Path(__file__).resolve().parents[2]
SUMMARY = json.loads((REPO / "tests" / "fixtures" / "data" / "espn_summary.json").read_text(encoding="utf-8"))
BOX = json.loads((REPO / "tests" / "fixtures" / "data" / "sleeper_box.json").read_text(encoding="utf-8"))

PHONE = (360, 780)
IN_GAME = {"DET": "in_game", "SEA": "in_game"}     # the week's clubs on the planted game day
FILL = """([s, b]) => { GS_GAME = gsShape(s); GS_BOX = {box: b}; GS_ERR = ""; gsPaint(); }"""
CLOCK_OF = """clubs => { const g = {state: 'in', q: 3, clock: '4:12', half: false, detail: '', clubs};
        GD_CLOCK = Object.fromEntries(clubs.map(c => [c, g])); }"""
FOLLOWED = "JSON.parse(localStorage.getItem('tw-gs-follow.2') || '{}')"
MARGINS = "(() => { const r = document.getElementById('gamesheet').getBoundingClientRect(); return [r.top, r.left, innerWidth - r.right, innerHeight - r.bottom]; })()"
VISIBLE = "els => els.filter(e => e.offsetParent !== null).length"
TWELVE_FOLLOWED = """() => { GS_FOLLOW = Object.fromEntries(Array.from({length: 12}, (_, i) =>
    ['f' + i, {id: 'f' + i, sid: 'f' + i, slug: 'f' + i, n: 'Fake Player' + i, pos: 'WR', team: 'DET'}])); gsPaint(); }"""
SCROLL = """() => {
  const tid = n => d.querySelector(`[data-testid="${n}"]`);
  const d = document.getElementById('gamesheet'), main = tid('gamesheet-main'), yl = tid('gamesheet-yl');
  const scrollers = [...d.querySelectorAll('*')].filter(e => /auto|scroll/.test(getComputedStyle(e).overflowY)).map(e => e.className);
  const before = tid('gamesheet-tabs').getBoundingClientRect().top;
  main.scrollTop = main.scrollHeight;
  return {scrollers, rows: yl.querySelectorAll('[data-testid="gamesheet-yr"]').length, ylScroll: yl.scrollHeight, ylClient: yl.clientHeight,
          mainScrolls: main.scrollHeight > main.clientHeight, scrolled: main.scrollTop > 0,
          tabsTop: Math.round(tid('gamesheet-tabs').getBoundingClientRect().top), mainTop: Math.round(main.getBoundingClientRect().top), before: Math.round(before)};
}"""
FOLLOW_KEYS = "Object.keys(localStorage).filter(k => k.startsWith('tw-gs-follow.') || k === 'tw-follow').sort()"


class GameSheetPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._tabs, self._tabbar, self._panes = tid("gamesheet-tab"), tid("gamesheet-tabs"), tid("gamesheet-panes")
        self._yours, self._rows, self._top, self._mid = tid("gamesheet-yours"), tid("gamesheet-yr"), tid("gamesheet-top"), tid("gamesheet-mid")
        self._stars = tid("gamesheet-star")

    @classmethod
    def on_live(cls, mount, size=PHONE, states=IN_GAME, clock_of=None):
        """Mount Live at `size` as the planted week 2 (`states` is each club's game state), with the reader the seed picks.
        `clock_of`, two clubs, puts their game on at Q3 4:12 before Live draws. Returns (GameSheetPage, the page's errors)."""
        page, errors = mount("live", size=size)
        page.evaluate(LIVE_PLANT(states))
        if clock_of:
            page.evaluate(CLOCK_OF, list(clock_of))
        page.evaluate("render()")
        page.get_by_test_id("live-mirror-row").first.wait_for()
        return cls(page), errors

    # ---- opening and closing ----

    def open(self, **extra):
        """Tap DET at BUF open (`extra` adds to the game, e.g. slug to name the player the reader came from), filled with
        ESPN's summary and Sleeper's box score."""
        self.open_unfilled(**extra)
        self.page.evaluate(FILL, [SUMMARY, BOX])

    def open_unfilled(self, **extra):
        """The same game, before ESPN's summary or Sleeper's box score has come back."""
        self.page.evaluate("g => gsOpen(g, null)", {"event": "1", "away": "DET", "home": "BUF", **extra})
        self.wait_for_open()

    def reopen(self):
        """Open the same game again, with no player named and nothing filled in yet."""
        self.page.evaluate("gsOpen({event: '1', away: 'DET', home: 'BUF'}, null)")
        self.wait_for_open()

    def refill(self):
        """ESPN's summary and Sleeper's box score come back."""
        self.page.evaluate(FILL, [SUMMARY, BOX])

    def close_with_escape(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_selector("#gamesheet:not(.on)", state="attached")

    def wait_for_open(self):
        self.page.wait_for_selector("#gamesheet.on")

    def settle(self):
        """The sheet's spring has come to rest."""
        self.page.evaluate("Promise.all(document.getAnimations().map(a => a.finished))")

    def swap_in_saved_game(self):
        """The sheet a tap opened is repainted as the saved game, DET at BUF, with ESPN's summary and Sleeper's box score."""
        self.page.evaluate("""([s, b]) => { GS = {event: "1", away: "DET", home: "BUF"}; GS_GAME = gsShape(s); GS_BOX = {box: b}; GS_ERR = ""; gsPaint(); }""",
                           [SUMMARY, BOX])

    def repaint(self):
        """The sheet's own poll."""
        self.page.evaluate("gsPaint()")

    def current_game(self):
        """The game the sheet holds (GS), or None once it is closed."""
        return self.page.evaluate("GS")

    def show_no_summary(self):
        """ESPN's summary has not loaded: the scoreboard stands in for it."""
        self.page.evaluate("GS_GAME = null; GS_ERR = ''; gsPaint()")

    def show_a_game_without_my_players(self):
        self.page.evaluate("GS = {event: '', away: 'AAA', home: 'BBB'}; gsPaint()")

    def follow_twelve_players(self):
        """A dozen followed players make the pinned block taller than a third of the screen."""
        self.page.evaluate(TWELVE_FOLLOWED)

    def store_follow_keys(self):
        """Last week's follow key, this week's empty one and the team switch's, before the sheet opens."""
        self.page.evaluate("""() => { localStorage.setItem('tw-gs-follow.1', '{"x":{}}'); localStorage.setItem('tw-gs-follow.2', '{}');
            localStorage.setItem('tw-follow', 'keep'); }""")

    # ---- what a reader does ----

    def select_tab(self, name):
        """plays, box or top."""
        self._tabs.and_(self.page.locator(f"[data-gstab='{name}']")).click()

    def tap_focus_star(self):
        """The star of the player the reader came from."""
        self._rows.and_(self.page.locator(".focus")).get_by_test_id("gamesheet-star").click()

    def follow_first_top_scorer(self):
        """Follow the first top scorer not followed yet, from Top scorers. Returns his id."""
        star = self._top.get_by_test_id("gamesheet-star").and_(self.page.locator("[aria-pressed='false']")).first
        sid = star.get_attribute("data-gsfollow")
        star.click()
        return sid

    def unfollow_top_scorer(self, sid):
        self._top.locator(f"[data-gsfollow='{sid}']").click()

    def toggle_drive(self, i):
        """Tap the i-th drive's line open (or shut) by hand, and wait for the sheet to have recorded it. Returns its key."""
        drive = self.page.get_by_test_id("gamesheet-drive").nth(i)
        drive.locator("summary").click()
        # "toggle" is a task after the click: wait until it has recorded the drive
        key = drive.evaluate("e => e.closest('[data-gsdrive]').dataset.gsdrive")
        self.page.wait_for_function("k => GS_OPEN.get(k) === true", arg=key)
        return key

    def tap_box_club(self, i):
        """The box score's club switch: 0 is the away club, 1 the home club."""
        self.page.get_by_test_id("gamesheet-seg").locator("button").nth(i).click()

    # ---- what a reader sees ----

    def margins(self):
        """The sheet's distance from the top, left, right and bottom edges of the window, in px."""
        return self.page.evaluate(MARGINS)

    def tab_names(self):
        return self._tabs.all_inner_texts()

    def tab_selected(self, name):
        """aria-selected of a tab: "true" or "false"."""
        return self._tabs.and_(self.page.locator(f"[data-gstab='{name}']")).get_attribute("aria-selected")

    def visible_pane_cards(self):
        """The cards under the tabs that are on screen: one."""
        return self._panes.evaluate("p => [...p.children].filter(e => e.offsetParent !== null).length")

    def visible_pane(self, kind):
        """1 when the card for `kind` (box, plays or top) is on screen, else 0."""
        return self.page.get_by_test_id(f"gamesheet-{kind}").evaluate_all(VISIBLE)

    def visible_top_stars(self):
        return self._top.get_by_test_id("gamesheet-star").evaluate_all(VISIBLE)

    def visible_yours(self):
        return self._yours.evaluate_all(VISIBLE)

    def visible_tab_bar(self):
        return self._tabbar.evaluate_all(VISIBLE)

    def scroll_to_bottom(self):
        """The sheet's scrollers, the pinned rows and where the tab bar sits before and after the body is scrolled to its end:
        {scrollers (class names), rows, ylScroll, ylClient, mainScrolls, scrolled, tabsTop, mainTop, before}."""
        return self.page.evaluate(SCROLL)

    def yours_row_count(self):
        return self._rows.count()

    def first_yours_row(self):
        """The first pinned row: {text, cls}."""
        row = self._rows.first
        return {"text": row.inner_text(), "cls": row.get_attribute("class")}

    def focus_row_count(self):
        return self._rows.and_(self.page.locator(".focus")).count()

    def yours_text(self):
        return self._yours.inner_text()

    def yours_icon_count(self):
        """Drawn shapes (the stars) in the pinned block."""
        return self._yours.locator("svg").count()

    def yours_quiet_count(self):
        """The sentence that says no player of the reader's is in this game."""
        return self._yours.get_by_test_id("gamesheet-yours-quiet").count()

    def focus_star_pressed(self):
        return self._rows.and_(self.page.locator(".focus")).get_by_test_id("gamesheet-star").get_attribute("aria-pressed")

    def yours_star_pressed(self, sid):
        return self._yours.locator(f"[data-gsfollow='{sid}']").get_attribute("aria-pressed")

    def yours_follows(self, sid):
        """How many pinned stars follow `sid`."""
        return self._yours.locator(f"[data-gsfollow='{sid}']").count()

    def scoreboard_middle_text(self):
        return self._mid.inner_text()

    def card_count(self):
        """The cards in the sheet: scoreboard, yours, and a card per tab (one shows)."""
        return self.page.locator("#gamesheet .gs-card").count()

    def trailing_score(self):
        """The score of the club that is behind."""
        return self.page.get_by_test_id("gamesheet-club").and_(self.page.locator(".behind")).locator("b").inner_text()

    def drive_count(self):
        return self.page.get_by_test_id("gamesheet-drive").count()

    def open_drive_count(self):
        return self.page.get_by_test_id("gamesheet-drive").and_(self.page.locator("[open]")).count()

    def first_drive_is_open(self):
        return self.page.get_by_test_id("gamesheet-drive").first.get_attribute("open") is not None

    def first_drive_club(self):
        return self.page.get_by_test_id("gamesheet-drive").first.locator(".gs-tm").inner_text()

    def first_drive_scoring_results(self):
        """How many results on the first drive's line are a score."""
        return self.page.get_by_test_id("gamesheet-drive").first.locator("summary b.sc").count()

    def play_texts(self):
        """The text of every play line, in the plays card."""
        return self.page.get_by_test_id("gamesheet-plays").locator(".gs-pl > span:last-child").all_inner_texts()

    def top_scorer_points(self):
        """The points of each top scorer, in the order shown."""
        return [float(x) for x in self.page.get_by_test_id("gamesheet-scorer").locator(":scope > b").all_inner_texts()]

    def box_club(self):
        """The club the box score shows."""
        return self.page.get_by_test_id("gamesheet-seg").locator("[aria-pressed='true']").inner_text()

    def box_table_count(self):
        return self.page.get_by_test_id("gamesheet-table").count()

    # ---- what the page remembers ----

    def followed(self):
        """This week's followed players (tw-gs-follow.2), by id."""
        return self.page.evaluate(FOLLOWED)

    def stored_team_choice(self):
        """tw-follow, the team switch's, which following a player never touches."""
        return self.page.evaluate("localStorage.getItem('tw-follow')")

    def follow_keys(self):
        """The follow keys in the store (tw-gs-follow.<week>, tw-follow), sorted."""
        return self.page.evaluate(FOLLOW_KEYS)
