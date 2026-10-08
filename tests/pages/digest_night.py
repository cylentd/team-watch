"""The Digest's night-game card (2026-10-07): Thursday night's game on Wednesday, Sunday night's on Sunday.

`DigestNightPage` is `DigestCardsPage` plus what the night card plants (a preview slate with a night game in it,
at a clock) and reads (its title, the game line, Claude's headline, the bets, the tap that opens Preview). Locators
by data-testid (`digest-night-*`, `digest-vs-bet`, `digest-card*`); the card holds its own rows, so a second card
on the page never leaks into a read. Reads return plain data and never assert.
"""
from pages.digest_cards_b import BETS, DigestCardsPage

# The fixture's preview games, replanted in kickoff order at a clock. A spec is {from, kickoff, slot, head?}: the
# fixture game at index `from` with that kickoff and window, and Claude's headline when `head` is given.
PLANT = """([at, specs]) => { Date.now = () => Date.parse(at);
  const base = LIVE_PREVIEW.games.slice();
  LIVE_PREVIEW.games = specs.map(s => ({...base[s.from], kickoff: s.kickoff, slot: s.slot,
    ...(s.head ? {take: {...base[s.from].take, head: s.head}} : {})}));
  DG_CUT = null; render(); }"""
# Every card but the night card replaced by a stub that draws, so a day shows all its cards at once.
STUBS = """() => { for (const n of ['Adds', 'Gains', 'Usage', 'Defenses', 'Calls', 'Weather'])
  window['dgCard' + n] = () => dgCardHTML({id: n.toLowerCase(), title: n, body: '<p>' + n + '</p>'});
  render(); }"""


class DigestNightPage(DigestCardsPage):

    def plant_night(self, at, *specs):
        self.page.evaluate(PLANT, [at, list(specs)])

    def plant_stub_cards(self):
        """Wednesday's other cards all drawing, so only the cap decides which show."""
        self.page.evaluate(STUBS)

    def plant_bare_games(self):
        """No game holds a line or a take: nothing to preview."""
        self.page.evaluate("() => { LIVE_PREVIEW.games.forEach(g => { g.line = null; g.take = null; g.market_win = null; }); render(); }")

    def order(self):
        """The day's sections top to bottom: each card by its plan id, Need to know as 'need'."""
        return self.page.get_by_test_id("digest-ticker").evaluate(
            "m => [...m.children].map(c => c.dataset.dgcard || (c.matches('[data-testid=\"digest-need\"]') ? 'need' : null)).filter(Boolean)")

    def night_game(self):
        return self._card("night").get_by_test_id("digest-night-game").inner_text().strip()

    def night_head(self):
        return self._card("night").get_by_test_id("digest-night-head").inner_text().strip()

    def night_bets(self):
        """One entry per bet: label, Vegas, Claude."""
        return self._card("night").get_by_test_id("digest-vs-bet").evaluate_all(BETS)

    def night_opens(self):
        """The ways into Preview the card draws: its tap target and its header link."""
        card = self._card("night")
        return {"body": card.get_by_test_id("digest-night-open").count(), "more": card.get_by_test_id("digest-card-more").count()}

    def tap_night(self):
        self._card("night").get_by_test_id("digest-night-open").click()

    def tap_night_more(self):
        self._card("night").get_by_test_id("digest-card-more").click()
