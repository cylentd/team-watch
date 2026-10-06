"""The leg sheet (design/src/js/surface/parlay/legsheet.js, legtiles.js, playersheet.js): one bet read in one
screen, from a Build line's info button or a Slips line, and the Slips board's player sheet in the same overlay.

`LegSheetPage` reads the sheet itself, `#legsheet` (static markup in shell.html, outside every view, so it has
no hook of its own), by test id first (`legsheet-*`, test hooks only): the bars and the driver row under them,
the caption, the chance, the three tiles, the matchup line, and the player sheet's usage grid. What opens it
and what it does to the slip is the Slips and Build page objects' (pages/parlay.py, pages/parlay_build.py:
`sheet_open`, `sheet_lines`, `sheet_longest`, `go_back`, `slip_size`); the lines a player sheet holds are read
there too, through `parlay-*` hooks.

Reads return plain data; no method asserts. State a tap cannot reach (which book, a missing catch in a log) is
set through the page's own globals in a method named for what it does.
"""

PHONE = (360, 780)

# the box of the sheet, [top, bottom]; the sheet is settled when two frames running give the same one
SHEET_BOX = "(() => { const r = document.getElementById('legsheet').getBoundingClientRect(); return [r.top, r.bottom]; })()"
# A plain predicate keeping the last box on window, polled every frame (a returned Promise is never re-checked).
SETTLED = """(src) => { const b = eval(src), s = JSON.stringify(b);
      const same = window.__lsb === s; window.__lsb = s; return same && b[0] > 8; }"""


class LegSheetPage:
    def __init__(self, page):
        self.page = page
        self._sheet = page.locator("#legsheet")
        tid = self._sheet.get_by_test_id
        self._bars, self._driver, self._caption = tid("legsheet-bar"), tid("legsheet-cell-drv"), tid("legsheet-caption")
        self._pct, self._tiles = tid("legsheet-pct"), tid("legsheet-tile-label")
        self._match, self._match_head, self._match_names = tid("legsheet-match"), tid("legsheet-match-head"), tid("legsheet-match-names")
        self._weeks, self._labels, self._values = tid("legsheet-use-week"), tid("legsheet-use-label"), tid("legsheet-use-value")

    # ---- opening it ----

    @classmethod
    def on(cls, mount, surface, book, size=PHONE):
        """`surface` ('parlay' or 'build') on `book`, nothing open yet. (LegSheetPage, errors)."""
        page, errors = mount(surface, size=size)
        sheet = cls(page)
        page.evaluate("([s, b]) => { SURFACE = s; PARLAY_BOOK = b; render(); }", [surface, book])
        return sheet, errors

    def open_line(self, name, mkt):
        """The leg sheet of the player's line in that market, opened the way Build's info button opens it."""
        self.page.evaluate("([n, m]) => legSheetOpen(PROPS.findIndex(p => p.n === n && p.mkt === m))", [name, mkt])

    def blank_game(self, slug, mkt, k):
        """His k-th logged game has no value (a null in the log: no catch)."""
        self.page.evaluate("([s, m, k]) => { LIVE_MARKET.logs[s].v[m][k] = null; }", [slug, mkt, k])

    # ---- what a reader sees ----

    def text(self):
        return self._sheet.inner_text()

    def close_button_focused(self):
        """Focus is on the sheet's close control: a keyboard reader starts there."""
        return self.page.evaluate("document.activeElement.hasAttribute('data-legclose')")

    def bar_count(self):
        return self._bars.count()

    def driver_cells(self):
        """The cells of the row under the bars that carries the stat driving the bet (targets, carries)."""
        return self._driver.count()

    def caption(self):
        return self._caption.inner_text()

    def pct_count(self):
        """How many chances the head prints: none for a line the model does not price."""
        return self._pct.count()

    def tile_labels(self):
        return self._tiles.all_inner_texts()

    def match_count(self):
        return self._match.count()

    def match_head(self):
        """The matchup line, its starters-out count included."""
        return self._match_head.inner_text()

    def match_names_visible(self):
        return self._match_names.is_visible()

    def usage_weeks(self):
        """The player sheet's column heads: his last four games."""
        return self._weeks.all_inner_texts()

    def usage_labels(self):
        return self._labels.all_inner_texts()

    def old_usage_cells(self):
        """Value cells faded because the game is from an earlier season than the model's."""
        return self._values.and_(self.page.locator(".old")).count()

    def build_season(self):
        return self.page.evaluate("BUILD_SEASON")

    def height(self):
        return self.page.evaluate("document.getElementById('legsheet').getBoundingClientRect().height")

    def scrolls_inside(self):
        """Whether the sheet's content is taller than the sheet itself (it would scroll)."""
        return self.page.evaluate("document.getElementById('legsheet').scrollHeight > document.getElementById('legsheet').clientHeight")

    def fits_width(self):
        """Nothing wider than the screen."""
        return self.page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    def settled_box(self):
        """[top, bottom] of the sheet once it has stopped moving, which is when it has the same box on two frames."""
        self.page.evaluate("window.__lsb = null")
        self.page.wait_for_function(SETTLED, arg=SHEET_BOX)
        return self.page.evaluate(SHEET_BOX)
