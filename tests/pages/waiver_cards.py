"""Watch cards drawn alone from a planted player row, for the blank-stats and no-back rules.

Methods return plain data; none asserts. They call the page's own wvFrontHTML / wvCardHTML on a
detached host, so no league data has to name the planted player.
"""


class WaiverCards:
    def __init__(self, page):
        self.page = page

    def unknown_card_stats(self, pos, slug):
        """Draw a Watch card whose availability is unknown for a player with no usage this week; return
        its proof stats' values and whether a stats row exists."""
        return self.page.evaluate("""([pos, slug]) => {
          const r = {n: "Test Player", slug, pos, team: "KC", leagues: {x: {status: "unknown", lane: null}}, summary: null};
          const host = document.createElement("div");
          host.innerHTML = wvFrontHTML(r, "x", "watch");
          return {values: [...host.querySelectorAll(".wvp b")].map(b => b.textContent.trim()),
                  row: host.querySelectorAll(".wvc-proof").length};
        }""", [pos, slug])

    def unknown_card_faces(self, leagues):
        """Draw a whole Watch card for a player with no usage and no news, in `leagues` ({key: view});
        return how many backs, flip buttons and direct-open buttons it has."""
        return self.page.evaluate("""(leagues) => {
          const r = {n: "Test Player", slug: "zz-none", pos: "WR", team: "KC", leagues, summary: null};
          const host = document.createElement("div");
          host.innerHTML = wvCardHTML(r, 0, 0, Object.keys(leagues)[0]);
          return {backs: host.querySelectorAll(".wvc-back").length, flips: host.querySelectorAll(".wvc-flip:not(.wvc-open)").length,
                  opens: host.querySelectorAll(".wvc-open[data-wire]").length,
                  front_others: host.querySelectorAll(".wvc-front .wvc-other").length};
        }""", leagues)
