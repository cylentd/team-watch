"""The search sheet (design/src/js/chrome/search.js): opened by `/` on a keyboard or the bar's last slot on a phone.

Search is not a view, so a test mounts any view (`mount("ranks")`) and drives the sheet over it. The results
are `search-*` data-testids (test hooks only: no CSS or JS reads them). The sheet's frame (`#search`, its input,
the bar and the nav slot) is drawn by the shell, which carries no testids, so those are ids and one class.
A result opens the player's profile over the sheet: that modal is pages/profile.py's `ProfilePage`, which
`SearchPage.profile` is. Reads return plain data; no method asserts.
"""
from pages.profile import ProfilePage

BOXES = """() => { const box = e => { const r = e.getBoundingClientRect(); return {y: r.y, height: r.height}; };
    return {bar: box(document.querySelector('#search .search-bar')),
            rows: [...document.querySelectorAll('[data-testid="search-row"]')].map(box)}; }"""
PROFILE_SHUT = "!document.getElementById('modal').classList.contains('on')"     # the shell's dialog, as ProfilePage.is_open reads it


class SearchPage:
    def __init__(self, page):
        self.page = page
        self.profile = ProfilePage(page)
        self._sheet, self._input, self._nav = page.locator("#search"), page.locator("#search-q"), page.locator("#navsearch")
        self._rows = page.get_by_test_id("search-row")
        self._cap, self._none = page.get_by_test_id("search-cap"), page.get_by_test_id("search-none")

    # ---- opening and closing ----

    def press_slash(self):
        """The `/` shortcut, with nothing focused."""
        self.page.keyboard.press("/")

    def tap_nav_slot(self):
        """The bar's last slot (a phone's Search tab)."""
        self._nav.click()

    def press_escape(self):
        self.page.keyboard.press("Escape")

    def is_open(self):
        return self._sheet.is_visible()

    def is_closed(self):
        return self._sheet.is_hidden()

    def wait_closed(self):
        self.page.wait_for_function("document.getElementById('search').hidden")

    def go_back(self):
        self.page.go_back()

    def wait_profile_closed(self):
        """After Back from the profile: the dialog is shut and the sheet is still here."""
        self.page.wait_for_function(PROFILE_SHUT)

    # ---- reading ----

    def focused_id(self):
        return self.page.evaluate("document.activeElement.id")

    def query(self):
        return self._input.input_value()

    def history_state(self):
        return self.page.evaluate("history.state")

    def wait_history_clear(self):
        """The sheet's history entry went with it."""
        self.page.wait_for_function("history.state === null")

    def hash(self):
        return self.page.evaluate("location.hash")

    def caption(self):
        """The list's caption (YOUR ROSTER before a first search, RECENT after one), upper-cased."""
        return self._cap.inner_text().strip().upper()

    def row_text(self, i):
        return self._rows.nth(i).inner_text()

    def row_count(self):
        return self._rows.count()

    def none_text(self):
        """The line shown when nothing matched."""
        return self._none.inner_text()

    def boxes(self):
        """{bar: {y, height}, rows: [{y, height}, ...]} in best-match-first order."""
        return self.page.evaluate(BOXES)

    def fits_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    # ---- driving ----

    def type(self, q):
        self._input.fill(q)

    def tap_row(self, i):
        self._rows.nth(i).click()
