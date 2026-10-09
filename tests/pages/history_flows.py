"""More of the browser's history (tests/pages/history.py is the base; its file is frozen, so what a later walk
needed lives here): the "How this works" drawer and a league added through the Connect sheet.

Reads return plain data; no method asserts. A wait is on a condition the page sets, never a duration."""
from pages.history import HistoryPage


class HistoryFlows(HistoryPage):
    # ---- the drawer ----

    def open_explain(self):
        """DFS's settings chip, then its "How this works" button: the slide-over drawer."""
        self.page.locator("[data-dfspanel]").click()
        self.page.locator("[data-explain]").click()
        self.page.wait_for_function("document.getElementById('drawer').classList.contains('on')")

    def close_drawer_with_x(self):
        self.page.locator("#drawer .dr-close").click()
        self.page.wait_for_function("!document.getElementById('drawer').classList.contains('on')")

    def wait_drawer_closed(self):
        self.page.wait_for_function("!document.getElementById('drawer').classList.contains('on')")

    def drawer_is_open(self):
        return self.page.evaluate("document.getElementById('drawer').classList.contains('on')")

    # ---- Connect ----

    def connect_league(self, card):
        """Add a league through the sheet: open it, and let the endpoint answer with `card` (api/league.py's shape)."""
        self.page.evaluate("card => { connectPost = async () => { connectAdd(card); return {league: card}; }; connectOpen(); }", card)
        self.page.wait_for_function("LAYERS.map(l => l.id).join() === 'connect'")
        self.page.evaluate("connectSubmit()")
        self.page.wait_for_function("SURFACE === 'roster' && LAYERS.length === 0 && LAYER_SKIP.length === 0")
