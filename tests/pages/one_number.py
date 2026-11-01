"""The number a reader sees for one player's week, in each view that prints it (S11, 2026-11-01).

Ranks prints `shown` of its LIVE_RANKS row; the Roster's row and the profile's strip print `pts` of the player's
LIVE_PROJECTIONS row. `OneNumber(page)` finds a player all three draw, reads the number as each draws it, and plants
a distinctive one in the data so a view that recomputes would print something else. Reads return plain data; none asserts.
"""
from pages.profile import ProfilePage
from pages.ranks import RanksPage

SHARED = """() => {
  const ranked = new Set(LIVE_RANKS.rows.map(r => r.slug));
  const p = TEAMS[VIEW].roster.find(x => x.slug && ranked.has(x.slug) && typeof LIVE_PROJECTIONS.players[x.slug].pts === 'number');
  return {slug: p.slug, n: p.n, pos: LIVE_RANKS.rows.find(r => r.slug === p.slug).pos};
}"""

# The page's data blocks are objects: change the player's number where each view reads it, then draw again.
PLANT = """([slug, pts]) => {
  LIVE_PROJECTIONS.players[slug].pts = pts;
  [...LIVE_RANKS.rows, ...LIVE_RANKS.flex].filter(r => r.slug === slug).forEach(r => { r.pts = pts; r.shown = pts; });
  render();
}"""

ROSTER_NUMBER = """n => {
  const row = [...document.querySelectorAll('[data-testid="roster-row"]')].find(r => r.textContent.includes(n));
  return row.querySelector('.rproj').firstChild.textContent;
}"""


class OneNumber:
    def __init__(self, page):
        self.page = page

    def shared_player(self):
        """{slug, n, pos} of a player on the open roster who also has a Ranks row and a projection."""
        return self.page.evaluate(SHARED)

    def plant(self, slug, pts):
        """Give the player `pts` in his projections row and in his Ranks rows, and draw the view again."""
        self.page.evaluate(PLANT, [slug, pts])

    def ranks_number(self, player):
        """The points Ranks prints on the player's row, at his position."""
        ranks = RanksPage(self.page)
        ranks.pick(player["pos"])
        return next(r["pts"] for r in ranks.rows() if r["slug"] == player["slug"])

    def roster_number(self, player):
        """The projection the Roster's row prints for the player."""
        return self.page.evaluate(ROSTER_NUMBER, player["n"])

    def data_number(self, slug):
        """The player's projections-row `pts` as one decimal: the number every view should print."""
        return self.page.evaluate("s => LIVE_PROJECTIONS.players[s].pts.toFixed(1)", slug)

    def open_from_roster(self, player):
        ProfilePage(self.page).open_from_roster(player["n"])

    def open_from_ranks(self, player):
        RanksPage(self.page).open_player(player["slug"])

    def profile_number(self):
        """The projection cell of the open profile's strip."""
        return next(c["value"] for c in ProfilePage(self.page).strip() if c["proj"])
