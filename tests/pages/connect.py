"""Connecting a visitor's own ESPN league (design/src/js/chrome/connect.js, DESIGN.md "Connected leagues"): the
"Add a league" sheet, and the roster a connected league draws once it is added.

The sheet's locators are `connect-*` test ids (test hooks only: no CSS or JS reads them). api/league.py is read
at runtime, so a test never asks it: `add_league` hands the page a card in the endpoint's shape, the way the GET
would, and shows that league's Roster the way a finished connect does (`connectSubmit`'s last step). The
endpoint itself is tests/test_league.py's.

The reads that are not the sheet's compose their owners, so no selector for them is defined twice: the team
the header names and the sub-row's leaves are `LeagueChip`, the menu is `TeamSwitchPage`, the roster's rows are
`RosterRows`. Three reads go past a test id because their owners have none yet: the Roster's group headings
(role `heading` inside `roster-sheet-col`), the switch's team rows and "Add a league" row (`teamswitch-*`,
scoped to the header's switch), and the Waivers view (`.wv`: surface/teams/waiver.js carries no test id while
another branch changes it; when it does, WaiversPage owns this read).

Methods return plain data; none asserts.
"""
from pages.league_chip import LeagueChip
from pages.roster import RosterRows
from pages.teamswitch import TeamSwitchPage

ADD = "card => { connectAdd(card); VIEW = card.key; SURFACE = 'roster'; paintSubnav(); render(); }"


class ConnectPage:
    def __init__(self, page):
        self.page = page
        self.chip, self.switch, self.rows = LeagueChip(page), TeamSwitchPage(page), RosterRows(page)
        tid = page.get_by_test_id
        self._sheet, self._league, self._private = tid("connect-sheet"), tid("connect-league"), tid("connect-private")
        self._s2, self._list = tid("connect-s2"), tid("connect-list")
        menu = tid("teamswitch-hdrswitch").get_by_test_id("teamswitch-menu")
        self._items, self._add = menu.get_by_test_id("teamswitch-team"), menu.get_by_test_id("teamswitch-add")

    # ---- a league added, the way a finished connect leaves the page ----

    def add_league(self, card):
        """Add `card` (api/league.py's shape) and draw its Roster."""
        self.page.evaluate(ADD, card)

    def view_waivers_stale(self):
        """Draw the Waivers leaf, as a stale #waivers in the address would."""
        self.page.evaluate("SURFACE = 'waivers'; render()")

    # ---- what the connected league draws ----

    def header_team(self):
        return self.chip.header_team().strip()

    def row_count(self):
        return self.rows.count()

    def group_headings(self):
        """The Roster's group headings in order drawn, upper-cased (the page sets them in capitals)."""
        sheet = self.page.get_by_test_id("roster-sheet-col")
        return [h.inner_text().strip().upper() for h in sheet.get_by_role("heading", level=2).all()]

    def leaves(self):
        """The leaves the sub-row draws."""
        return self.chip.subnav_leaves()

    def waivers_view_count(self):
        return self.page.locator(".wv").count()

    # ---- the team switch ----

    def open_switch(self):
        self.switch.open_menu()

    def switch_teams(self):
        """The text of each team the open switch lists."""
        return self._items.all_inner_texts()

    def tap_add_a_league(self):
        self._add.click()

    # ---- the sheet ----

    def sheet_is_visible(self):
        return self._sheet.is_visible()

    def league_field_is_visible(self):
        return self._league.is_visible()

    def listed_leagues(self):
        """The text of the list of leagues already connected, under the sheet's form."""
        return self._list.inner_text()

    def private_open_count(self):
        """How many private-league blocks are open (1 when the bookmark brought cookies in hand)."""
        return self._private.and_(self.page.locator("[open]")).count()

    def espn_s2(self):
        return self._s2.input_value()

    # ---- arriving from the bookmark ----

    def arrive_from_bookmark(self, code):
        """Land on the page as the bookmark does: `#connect=<code>` in the address, then a fresh load."""
        self.page.evaluate("c => { location.hash = '#connect=' + c; }", code)
        self.page.reload()

    def hash(self):
        return self.page.evaluate("location.hash")
