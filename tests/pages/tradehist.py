"""League > Trade history, its own leaf (`tradehist`, 2026-10-08; it was a tab of Records until then) and the Records
page it left (design/src/js/surface/league/records.js, surface/trades/trades.js).

Methods return plain data and never assert.
"""


class TradeHistoryPage:
    def __init__(self, page):
        self.page = page

    def ranking_count(self):
        """The manager ranking (`.tr-rank`): 1 when the trade history is drawn."""
        return self.page.locator("#view .tr-rank").count()

    def all_time_count(self):
        """Records' head-to-head and cases root (`.rc`): 1 when Records is drawn."""
        return self.page.locator("#view .rc").count()

    def old_tab_count(self):
        """The Records mode row's buttons (`[data-rctab]`), a phone's segments or a desktop's bar: gone since 2026-10-08."""
        return self.page.locator("[data-rctab]").count()

    def old_bar_count(self):
        return self.page.locator("#view .rc-tabs, #subnav .tr-seg").count()

    def subnav_labels(self):
        """The sub-row's pills as drawn, left to right."""
        return self.page.evaluate("[...document.querySelectorAll('#subnav .mode-sub')].map(b => b.textContent.trim())")

    def subnav_overflow(self):
        """How far the sub-row's pills run past its own edge, in px (0 = they fit)."""
        return self.page.evaluate("(() => { const r = document.querySelector('#subnav'); return Math.max(0, r.scrollWidth - r.clientWidth); })()")

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")
