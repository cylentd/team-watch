"""The number a reader sees for one player's week in three more views (S11, 2026-11-01): Start/Sit's lineup card, the
Compare sheet's cards, and League > Teams' starter rows. `pages/one_number.py` has Ranks, the Roster and the profile.

`MoreViews(page, surface)` finds a player the view draws, reads the number as the view draws it, and plants a distinctive
one where the view reads it. Start/Sit and Compare read the projections row (`LIVE_PROJECTIONS`); Teams reads its own
build-time copy in `LIVE_TEAMS`, so that is where it is planted. Reads return plain data; none asserts.
"""
from pages.matchups import MatchupsPage
from pages.one_number import OneNumber
from pages.profile import ProfilePage
from pages.teams import TeamsPage, pick_script

SIZE = (1400, 900)
TEAM = "espn"          # the reader's team on Teams: a TEAMS key, and the key of its card
MOUNTS = {"startsit": "ranks", "compare": "roster", "teams": "teams"}

# A starter of the reader's team whose printed points are his projections row's, and the name Teams draws for him.
TEAMS_PLAYER = """team => {
  const t = LIVE_TEAMS.leagues.find(l => l.key === VIEW).teams.find(x => x.key === team);
  const r = t.lineup.find(x => LIVE_PROJECTIONS.players[slugOf(x.n)] && x.pts === LIVE_PROJECTIONS.players[slugOf(x.n)].pts);
  return {slug: slugOf(r.n), n: nameInitial(r.n), team};
}"""

# Teams' rows carry the points the build copied from the projections row; plant the copy and draw again.
PLANT_TEAMS = """([slug, pts]) => {
  LIVE_TEAMS.leagues.forEach(l => l.teams.forEach(t => [...t.lineup, ...t.bench]
    .filter(r => slugOf(r.n) === slug).forEach(r => { r.pts = pts; })));
  render();
}"""


def open_view(mount, surface):
    """The surface mounted for a reader on `TEAM`: (MoreViews, errors)."""
    page, errors = mount(MOUNTS[surface], size=SIZE, init=(pick_script(TEAM),))
    return MoreViews(page, surface), errors


class MoreViews:
    def __init__(self, page, surface):
        self.page, self.surface, self.one = page, surface, OneNumber(page)

    def player(self):
        """{slug, n, ...} of a player the view draws with his projections-row number."""
        return {"startsit": self._lineup_player, "compare": self.one.shared_player, "teams": self._teams_player}[self.surface]()

    def plant(self, player, pts):
        """Give the player `pts` where this view reads his number, and draw it again."""
        if self.surface == "teams":
            self.page.evaluate(PLANT_TEAMS, [player["slug"], pts])
        else:
            self.one.plant(player["slug"], pts)

    def number(self, player):
        """The points the view prints for the player."""
        return {"startsit": self._lineup_number, "compare": self._compare_number, "teams": self._teams_number}[self.surface](player)

    def data_number(self, player):
        """The player's projections-row `pts` as one decimal: the number every view should print."""
        return self.one.data_number(player["slug"])

    def _lineup_player(self):
        rows = MatchupsPage(self.page).open().lineup()["starters"]
        return next(r for r in rows if r["pts"].replace(".", "").isdigit())

    def _lineup_number(self, player):
        lineup = MatchupsPage(self.page).lineup()
        return next(r["pts"] for g in lineup.values() for r in g if r["slug"] == player["slug"])

    def _compare_number(self, player):
        profile = ProfilePage(self.page)
        profile.open_from_roster(player["n"])
        profile.compare_pick_two("wr")
        return self.page.locator('[data-testid="profile-cmp-card"] .cmp-proj').first.inner_text()

    def _teams_player(self):
        return self.page.evaluate(TEAMS_PLAYER, TEAM)

    def _teams_number(self, player):
        cards = TeamsPage(self.page).cards()
        return next(s["pts"] for c in cards if c["key"] == player["team"] for s in c["starters"] if s["name"] == player["n"])
