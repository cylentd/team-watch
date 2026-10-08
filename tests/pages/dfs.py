"""Bets > DFS (design/src/js/surface/dfs/): the suggested lineups and the pool. Class selectors until
surface/dfs/ has test ids, as in pages/league_chip.py. Reads return plain data; no method asserts."""

EDGE = "e => { const s = getComputedStyle(e); return {border: s.borderTopColor, ring: s.boxShadow}; }"


class DfsPage:
    def __init__(self, page):
        self.page = page
        self._cards = page.locator(".lineupcard")

    def pick_site(self, site):
        """Open the settings panel and pick a site ("dk"): the suggested lineups draw for it."""
        self.page.locator("[data-dfspanel]").click()
        self.page.locator(f"[data-dfssite='{site}']").click()

    def card_count(self):
        return self._cards.count()

    def best_edge(self):
        """The best lineup's (the first card's) border colour and any ring drawn inside it."""
        return self._cards.first.evaluate(EDGE)

    def other_edge(self):
        """A lineup that is not the best one: its border colour and ring."""
        return self._cards.nth(1).evaluate(EDGE)
