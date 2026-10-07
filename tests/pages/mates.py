"""A leaguemate's page (design/src/js/chrome/teamswitch.js `pickHTML`, data/mates.js): the picker a reader with no
team sees, the pick that sticks, and the Waivers rail a leaguemate's team gets.

No view of its own draws a leaguemate: the Roster asks whose team it is until a pick is made, then draws that team.
`MatesPage` composes the pages that own each part (`LeagueChip` for the League's team line, `RosterRows` for roster
rows, `WaiversPage` for David's claim cards and rows) and holds what is only the picker's: its team buttons and
league lists, `data-testid` `teamswitch-pick` and `teamswitch-pick-league`.

Two reads are Waivers' own classes (`.wv-mate`, `.wvr-row.k-status`): surface/teams/waiver*.js carries no test ids
yet, while another branch changes it. They are here, beside the one place that needs them, until it does.

Reads return plain data; no method asserts.
"""
from pages.league_chip import LeagueChip
from pages.roster import RosterRows
from pages.waivers import WaiversPage


class MatesPage:
    def __init__(self, page):
        self.page = page
        self.chip, self.rows, self.waivers = LeagueChip(page), RosterRows(page), WaiversPage(page)
        self._picker = page.locator("#view[data-view='pick']")      # the view's own state attribute, set by render()
        self._teams, self._lists = page.get_by_test_id("teamswitch-pick"), page.get_by_test_id("teamswitch-pick-league")

    # ---- driving: who the reader is, and the leaf on screen ----

    def forget_pick_and_show_roster(self):
        """A browser with no team picked, the Roster drawn again."""
        self.page.evaluate("localStorage.removeItem('tw-team'); SURFACE='roster'; render()")

    def forget_owner_and_show_waivers(self):
        """No owner token either, Waivers drawn."""
        self.page.evaluate("localStorage.removeItem('tw-owner'); SURFACE='waivers'; render()")

    def show(self, leaf):
        self.page.evaluate(f"SURFACE='{leaf}'; render()")

    def show_waivers_of(self, key):
        """Team `key`'s Waivers, with the sub-row drawn for it."""
        self.page.evaluate(f"VIEW = '{key}'; SURFACE = 'waivers'; render(); paintSubnav()")

    def pick(self, key):
        """Tap a team in the picker."""
        self._teams.and_(self.page.locator(f"[data-pick='{key}']")).click()

    def reload(self):
        """Load the page again, as a refresh does; the pick is remembered in the browser."""
        self.chip.reload()

    # ---- the picker ----

    def picker_count(self):
        """1 while the view is the picker, 0 once a team is picked or on a leaf that does not ask."""
        return self._picker.count()

    def picker_team_count(self):
        return self._picker.get_by_test_id("teamswitch-pick").count()

    def league_list_count(self):
        return self._lists.count()

    # ---- what the pick leaves ----

    def viewed_team(self):
        return self.page.evaluate("VIEW")

    def stored_pick(self):
        return self.page.evaluate("localStorage.getItem('tw-team')")

    def subnav_text(self):
        return self.page.locator("#subnav").inner_text()

    def view_text(self):
        return self.page.locator("#view").inner_text()

    # ---- a leaguemate's Waivers ----

    def mate_rail_count(self):
        """The rail's note that it is the league's, not the reader's (`.wv-mate`)."""
        return self.page.locator(".wv-mate").count()

    def status_row_count(self):
        """Rows about the reader's own players (`.wvr-row.k-status`): none for a leaguemate."""
        return self.page.locator(".wvr-row.k-status").count()
