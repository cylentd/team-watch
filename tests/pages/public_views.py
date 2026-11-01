"""A public view as two readers see it (scenario S4, agent-config must-never-break/team-watch.md).

`STRANGER` is an init script for `mount`: a browser with no team, no follows and no owner mark, the page as
the public gets it. `as_signed_in_reader` reloads the same page as the suite's seeded reader (test_render.SEED:
David's team picked and followed, the owner mark set), the most personal state a browser can hold.

Methods return plain data; none asserts.
"""
from test_render import LOAD_MS

KEEP_SEED = "s4-keep-seed"
STRANGER = f"""try {{
  if (!sessionStorage.getItem("{KEEP_SEED}")) ["tw-team", "tw-follow", "tw-owner"].forEach(k => localStorage.removeItem(k));
}} catch (e) {{}}
"""


class PublicView:
    def __init__(self, page):
        self.page = page

    def text(self):
        """Everything the view shows, the app's header and tab bars left out."""
        return self.page.locator("#view").inner_text()

    def fantasy_team_names(self):
        """The name of every fantasy team the page carries: David's and all his leaguemates'."""
        return self.page.evaluate("[...new Set(Object.values(TEAMS).map(t => t.name).filter(Boolean))]")

    def reader_state(self):
        """(picked team, followed teams, owner mark) as this browser holds them."""
        return self.page.evaluate("[myTeamLoad(), followLoad(), isOwner()]")

    def as_signed_in_reader(self):
        self.page.evaluate("k => sessionStorage.setItem(k, '1')", KEEP_SEED)
        self.page.reload(timeout=LOAD_MS)
        self.page.wait_for_function("document.getElementById('view').children.length > 0", timeout=LOAD_MS)
