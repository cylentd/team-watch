"""The team switch's menu in the phone's header bar (design/src/js/chrome/teamswitch.js, `#hdrswitch`).

Every locator for the menu is here, data-testid first (`teamswitch-*`, test hooks only: no CSS or JS reads
them). The same markup also draws the switch inside a view (`#switch`, a desktop's); this object reads the
header's, the one a phone has, through its own root hook `teamswitch-hdrswitch`. The page carries one
menu until it opens, so the header's is the only one these methods see.

Two reads go past a testid: the footer (`.foot`, drawn by the shell, which has no hook) and the state a
team row carries (`aria-selected`, `data-k`). The League chip's own switch classes are
pages/league_chip.py's, not read here.

Methods return plain data; none asserts. A phone's views are the surface mounted by the test; `show_leaf`
moves to another leaf the way the nav does, without that leaf's own CSS (the header does not depend on it).
"""


class TeamSwitchPage:
    def __init__(self, page):
        self.page = page
        root = page.get_by_test_id("teamswitch-hdrswitch")
        self._button, self._menu = root.get_by_test_id("teamswitch-button"), root.get_by_test_id("teamswitch-menu")
        self._teams, self._add, self._discord = (self._menu.get_by_test_id(t) for t in ("teamswitch-team", "teamswitch-add",
                                                                                         "teamswitch-discord"))
        self._taps = self._teams.or_(self._add).or_(self._discord)
        self._leagues, self._stars = self._menu.get_by_test_id("teamswitch-league"), self._menu.get_by_test_id("teamswitch-star")
        self._back, self._about = self._menu.get_by_test_id("teamswitch-back"), self._menu.get_by_test_id("teamswitch-about")
        self._credits = self._menu.get_by_test_id("teamswitch-credits")

    # ---- where the reader is ----

    def view_without_picking(self, key):
        """Show a team's view without the reader having picked it (a pick follows the team by default)."""
        self.page.evaluate("k => { VIEW = k; render(); }", key)

    def viewed_team(self):
        return self.page.evaluate("VIEW")

    def footer_count(self):
        return self.page.locator(".foot").count()

    # ---- the menu ----

    def toggle(self):
        """Tap the switch: opens the menu, or closes it when it is open."""
        self._button.click()

    def open_menu(self):
        self.toggle()
        self._menu.wait_for()

    def menu_is_visible(self):
        return self._menu.is_visible()

    def team_keys(self):
        """The teams on the screen the menu shows, top to bottom."""
        return self._teams.evaluate_all("bs => bs.map(b => b.dataset.k)")

    def is_selected(self, key):
        return self._team(key).get_attribute("aria-selected")

    def other_league_team(self):
        """David's team in the league the viewed one is not in (yahoo or espn)."""
        return self.page.evaluate("VIEW === 'yahoo' ? 'espn' : 'yahoo'")

    def choose(self, key):
        """Pick a team in the menu."""
        self._team(key).click()

    def covered_taps(self):
        """Every row in the menu whose centre a finger would not land on: 'key under <what is on top>'."""
        return self._taps.evaluate_all("""bs => bs.map(b => {
          const r = b.getBoundingClientRect(), hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
          return hit && b.contains(hit) ? null : (b.dataset.k || 'add') + ' under ' + (hit ? hit.className : 'nothing');
        }).filter(Boolean)""")

    def edges(self):
        """The menu's [left, right] in px."""
        return self._menu.evaluate("m => { const r = m.getBoundingClientRect(); return [r.left, r.right]; }")

    def overflow(self):
        """How many px the menu's content is taller than the menu."""
        return self._menu.evaluate("m => m.scrollHeight - m.clientHeight")

    # ---- leagues and follows ----

    def first_mate_league(self):
        """The league of the first leaguemate on the page, or None."""
        return self.page.evaluate("MATES[0]?.league || null")

    def first_mate(self):
        """The first leaguemate's team key, or None."""
        return self.page.evaluate("MATES.map(m => m.key)[0] || null")

    def mates_by_name(self, league):
        """A league's other teams in the order its menu list draws them."""
        return self.page.evaluate("lg => mateKeys(lg).sort(tsByName)", league)

    def league_row_count(self):
        return self._leagues.count()

    def open_league(self, league=None):
        """Tap a league's row (the first when none is named): the menu swaps to that league's teams."""
        row = self._leagues.and_(self.page.locator(f"[data-tsleague='{league}']")) if league else self._leagues
        row.first.click()

    def follow(self, key):
        """Tap a team's star: follows it, or unfollows it when it is followed. The menu stays open."""
        self._stars.and_(self.page.locator(f"[data-follow='{key}']")).click()

    def back(self):
        self._back.click()

    def followed_keys(self):
        """The teams this browser follows, as stored."""
        return self.page.evaluate("JSON.parse(localStorage.getItem('tw-follow'))")

    def back_is_visible(self):
        return self._back.is_visible()

    def focused_league(self):
        """The league whose row has focus, or None."""
        return self.page.evaluate("document.activeElement.dataset.tsleague")

    def focused(self):
        """The test id of the element with focus, or None."""
        return self.page.evaluate("document.activeElement.dataset.testid || null")

    # ---- About ----

    def open_about(self):
        self._about.click()

    def about_count(self):
        return self._about.count()

    def credits_are_visible(self):
        return self._credits.is_visible()

    def credits_text(self):
        return self._credits.inner_text()

    def credits_count(self):
        return self._credits.count()

    def _team(self, key):
        return self._teams.and_(self.page.locator(f"[data-k='{key}']"))
