"""Stats > Schedule (design/src/js/surface/sos/): the 32 teams easiest first, a control row, the opponents by week.

Every Schedule locator lives here, data-testid first (`schedule-*`, test hooks only). `SchedulePage` is
the view mounted (tests/component.py). `ScheduleNav` is the chrome around it (the Stats sub-row, the
group, the hash), for the journeys that need the full page: Schedule is the Stats sub-row's sixth
pill since 2026-10-06 (hidden by `NAV_HIDDEN` before), and the hash and `navGo` open it too.

Reads return plain data; no method asserts.
"""

TO_FLOAT = "bs => bs.map(b => parseFloat(b.textContent))"
CHIP_TOPS = "cs => cs.map(b => Math.round(b.getBoundingClientRect().y))"
CELLS_FIT = "cs => cs.every(c => c.scrollWidth <= c.clientWidth)"
ROW_SHAPE = """e => { const r = e.getBoundingClientRect();
  return [r.height, e.querySelector('[data-testid="schedule-cells"]').getBoundingClientRect().y - r.y]; }"""


class SchedulePage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        # The position: the view's chip on a desktop, Stats' strip above the bottom bar on a phone (pages/statspos.py, 2026-10-06).
        self._control, self._pos, self._win = tid("schedule-control"), tid("schedule-pos-chip").or_(tid("stats-pos-seg")), tid("schedule-win-chip")
        self._head, self._title, self._label = tid("schedule-head"), tid("schedule-title"), tid("schedule-label")
        self._rows, self._cells, self._cell_lists = tid("schedule-row"), tid("schedule-cell"), tid("schedule-cells")
        self._pts, self._empty = tid("schedule-pts-value"), tid("schedule-empty")
        self._byes = self._cells.and_(page.locator(".bye"))

    # ---- what a reader does ----

    def pick_position(self, pos):
        """Tap a position chip: "QB", "RB", "WR", "TE"."""
        self._pos.and_(self.page.locator(f"[data-sospos='{pos}']")).click()

    def pick_window(self, win):
        """Tap a weeks chip: "next4", "ros", "playoffs"."""
        self._win.and_(self.page.locator(f"[data-soswin='{win}']")).click()

    # ---- what a reader sees ----

    def title(self):
        return self._title.inner_text()

    def label(self):
        """The file's own one-line label under the heading."""
        return self._label.inner_text()

    def label_is_visible(self):
        return self._label.is_visible()

    def row_count(self):
        return self._rows.count()

    def control_count(self):
        return self._control.count()

    def chip_tops(self):
        """The y of every chip in the control row (position and weeks), rounded, in order drawn."""
        return self._control.locator("[data-testid$='-chip']").evaluate_all(CHIP_TOPS)

    def position_pressed(self, pos):
        return self._pos.and_(self.page.locator(f"[data-sospos='{pos}']")).get_attribute("aria-pressed")

    def window_pressed(self, win):
        return self._win.and_(self.page.locator(f"[data-soswin='{win}']")).get_attribute("aria-pressed")

    def first_row_top(self):
        return self._rows.first.evaluate("r => r.getBoundingClientRect().y")

    def first_row_cell_count(self):
        """Weeks drawn on the first team's row."""
        return self._rows.first.get_by_test_id("schedule-cell").count()

    def first_row_shape(self):
        """[the row's height, how far under the row's top its opponents start]: a desktop joins them to the team's line."""
        return self._rows.first.evaluate(ROW_SHAPE)

    def points(self):
        """The points shown per row (allowed per game), top to bottom."""
        return self._pts.evaluate_all(TO_FLOAT)

    def cells_fit(self):
        """No row's opponents are cut off or scroll."""
        return self._cell_lists.evaluate_all(CELLS_FIT)

    def bye_count(self):
        return self._byes.count()

    def first_bye(self):
        """The first bye cell: its text on one line and its aria-label."""
        return {"text": self._byes.first.inner_text().replace("\n", " "),
                "aria": self._byes.first.get_attribute("aria-label")}

    def empty_text(self):
        return self._empty.inner_text()

    def overflow(self):
        """Pixels the page is wider than the screen (0 or less: it never scrolls sideways)."""
        return self.page.evaluate("document.scrollingElement.scrollWidth - innerWidth")


class ScheduleNav:
    """The nav chrome around Schedule, for a journey on the full page: the Stats group, its sub-row, the view."""

    def __init__(self, page):
        self.page = page

    def group(self):
        return self.page.locator(".navitem[aria-current='true']").get_attribute("data-s")

    def pressed_subs(self):
        return self.page.locator("#subnav .mode-sub[aria-pressed='true']").count()

    def pressed_sub_text(self):
        return self.page.locator("#subnav .mode-sub[aria-pressed='true']").inner_text()

    def view(self):
        return self.page.evaluate("document.getElementById('view').dataset.view")

    def sub_row(self):
        return self.page.locator("#subnav .mode-sub").all_inner_texts()

    def sub_row_overflow_x(self):
        return self.page.evaluate("getComputedStyle(document.querySelector('#subnav .modes-sub')).overflowX")

    def page_scroll_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")
