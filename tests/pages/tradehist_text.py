"""League > Trade history as words: who the page names and how it names the players (design/src/js/surface/trades/).

Added 2026-11-01 for the ESPN league's history; `pages/tradehist.py` (the leaf's tab and layout checks) is
unchanged. Methods return plain data and never assert. Class selectors until trades.js has `data-testid`s,
except the ESPN caption, which has one.
"""


class TradeHistoryText:
    def __init__(self, page):
        self.page = page

    def plant_and_open(self, block):
        """Give ESPN's graded trades to a page built without any (the const object takes a new key; a planted
        window variable would be shadowed by the build's own `const LIVE_TRADES_ESPN = null`), then open the leaf."""
        self.page.evaluate("b => { LG_TRADES.espn = b; navGo('tradehist'); }", block)
        self.page.wait_for_function("SURFACE === 'tradehist' && document.querySelector('#view .tr, #view .tr-none')")

    def managers(self):
        """The trader ranking's manager names, in order."""
        return self.page.eval_on_selector_all("#view .tr-mgrs .tr-i + b", "els => els.map(e => e.textContent.trim())")

    def players(self):
        """Every player name the cards and open trades print, as drawn."""
        return self.page.eval_on_selector_all("#view .tr-pls b", "els => els.map(e => e.textContent.trim())")

    def trade_names(self):
        """The manager names on the cards' trade rows (the row headers of each trade's box score)."""
        return self.page.eval_on_selector_all("#view .tr-sc th", "els => els.map(e => e.textContent.trim())")

    def caption(self):
        """The ESPN-only caption's text, or None when the page draws none."""
        note = self.page.locator("[data-testid='trades-espn-note']")
        return note.text_content().strip() if note.count() else None

    def league_title(self):
        """The page's h1: the league it is about."""
        return self.page.locator("#view .tr-head h1").text_content().strip()
