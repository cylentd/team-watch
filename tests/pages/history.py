"""The browser's history as the page keeps it (design/src/js/chrome/layers.js, nav.js): which view and hash each
entry holds, whether an overlay's entry is still on the stack, and where Back lands.

A test reads an entry as plain data and presses Back through `back_to`, which waits for a condition (the view and
hash the entry should show), never a duration. The nav controls are the shell's `#nav` and `#subnav`, drawn with
no test ids, so they are ids and data attributes here. Reads return plain data; no method asserts.
"""

ENTRY = """() => ({hash: location.hash, surface: SURFACE, layers: LAYERS.map(l => l.id),
  entry_layer: history.state && history.state.layer || null})"""


class HistoryPage:
    def __init__(self, page):
        self.page = page

    # ---- driving ----

    def tap_group(self, group):
        self.page.locator(f"#nav .navitem[data-s='{group}']").click()
        self.page.wait_for_function("g => navGroupOf(SURFACE) === g", arg=group)

    def tap_pill(self, leaf):
        self.page.locator(f"#subnav [data-leaf='{leaf}']").click()
        self.page.wait_for_function("l => SURFACE === l", arg=leaf)

    def open_dossier(self):
        """Preview's first game, over the slate: a layer on a phone."""
        self.page.locator("[data-pvopen]").first.click()
        self.page.wait_for_function("PV_OPEN")

    def open_compare(self):
        """Start/Sit's Compare page, a layer: the lineup card's Compare the two, or its Compare two with no team."""
        self.page.locator("[data-mucmp], [data-sscmp]").first.click()
        self.page.wait_for_function("SS_CMP")

    def open_search_result(self, query):
        """The bar's Search slot, a query, the first result: the profile over the open sheet."""
        self.page.locator("#navsearch").click()
        self.page.fill("#search-q", query)
        self.page.get_by_test_id("search-row").first.click()
        self.page.wait_for_function("LAYERS.map(l => l.id).join() === 'search,modal'")

    def follow_grid_link(self):
        self.page.get_by_test_id("profile-grid-link").click()

    def follow_first_owner(self):
        self.page.get_by_test_id("profile-owner").and_(self.page.locator("[data-ownteam]")).first.click()

    def pick_team(self, key):
        """The team switch's pick, which may land the view on the nearest leaf the new league has."""
        self.page.evaluate("k => pickTeam(k)", key)

    def back(self):
        self.page.go_back()

    def back_to(self, leaf):
        """Press Back and wait until the page shows `leaf` at `#leaf` with no layer still open."""
        self.page.go_back()
        self.page.wait_for_function("l => SURFACE === l && location.hash === '#' + l && LAYER_SKIP.length === 0", arg=leaf)

    # ---- reading ----

    def entry(self):
        """{hash, surface, layers (open overlays, top last), entry_layer (the overlay the current entry stands for)}."""
        return self.page.evaluate(ENTRY)
