"""League > Records, its two views (design/src/js/surface/league/rctabs.js, 2026-10-06): All-time and Trade history.

The tabs are `[data-rctab]`: a phone draws them as the Records pill's own segments in the tab row, a desktop as the
view's bar; only one of the two is visible at a width, so one locator reads both. Methods return plain data and
never assert.
"""


class RecordsPage:
    def __init__(self, page):
        self.page = page
        self._tabs = page.locator("[data-rctab]:visible")

    def tabs(self):
        """The visible tabs in order: label, pressed."""
        return self._tabs.evaluate_all("bs => bs.map(b => ({label: b.textContent.trim(), pressed: b.getAttribute('aria-pressed') === 'true'}))")

    def labels(self):
        return [t["label"] for t in self.tabs()]

    def select(self, label):
        """Tap a tab and wait for it to be the pressed one."""
        self._tabs.filter(has_text=label).click()
        self.page.wait_for_function("l => [...document.querySelectorAll('[data-rctab]')].some(b => b.textContent.trim() === l && "
                                    "b.getAttribute('aria-pressed') === 'true')", arg=label)

    def showing(self):
        """Which view is drawn: "alltime" (the head to head and the cases), "trades" (the trade history) or None."""
        return self.page.evaluate("document.querySelector('#view .rc') ? 'alltime' : document.querySelector('#view .tr') ? 'trades' : null")

    def tab_count(self):
        """Tabs drawn at all, visible or not: 0 where the league has no graded trades."""
        return self.page.locator("[data-rctab]").count()

    def empty_count(self):
        """The empty state's blocks (`.rc-empty`, a league with no record book yet)."""
        return self.page.locator(".rc-empty").count()

    def head_to_head_count(self):
        """The All-time head-to-head blocks (`.rc-hh`)."""
        return self.page.locator(".rc-hh").count()

    def history_has_ranking(self):
        return self.page.locator("#view .tr-rank").count() == 1

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")
