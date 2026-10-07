"""Stats > Usage (design/src/js/surface/usage/): the grid's rows and the reader's own among them.

A row is `.urow`, its player `data-usage`, and a row that wears the reader's mark has `.u-mine`. The Mine filter
sits in the settings panel, opened by the settings chip; both are found by the hooks the page already has.
"""


class UsagePage:
    def __init__(self, page):
        self.page = page
        self._rows = page.locator(".urow")

    # ---- what a reader does ----

    def filter_to_mine(self):
        """Open the settings panel and turn the Mine filter on."""
        self.page.locator("[data-upanel]").click()
        self.page.locator("[data-umine]").click()

    # ---- what a reader sees ----

    def shown_slugs(self):
        """The players in the grid, in order."""
        return self._rows.evaluate_all("rs => rs.map(r => r.dataset.usage)")

    def mine_slugs(self):
        """The players in the grid wearing the reader's mark."""
        return set(self._rows.and_(self.page.locator(".u-mine")).evaluate_all("rs => rs.map(r => r.dataset.usage)"))

    # ---- the fixture's rosters ----

    def first_mate(self):
        """The first leaguemate's team key, or None."""
        return self.page.evaluate("MATES.length ? MATES[0].key : null")

    def put_on_roster(self, key, slug):
        """Put a player on a team's roster, as the build would."""
        self.page.evaluate("([k, s]) => TEAMS[k].roster.push({n: s, slug: s})", [key, slug])

    def held_by(self, keys):
        """Every player on the rosters of these teams (TEAMS keys), as the page holds them."""
        return set(self.page.evaluate(
            "ks => [...new Set(ks.flatMap(k => (TEAMS[k] ? TEAMS[k].roster : []).map(p => p.slug)))]", keys))

    def follow(self, key):
        """Follow a team as a star in the team switch does, and draw the view again."""
        self.page.evaluate("k => { followToggle(k); render(); }", key)

    def redraw(self):
        self.page.evaluate("render()")
