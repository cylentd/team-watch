"""This week > Recap > Accuracy (design/src/js/surface/recap/accuracy*.js): the tab and the cards it draws.

The tab bar, the open tab's name and the sideways scroll are Recap's, read through `RecapPage`; this class
only adds what the Accuracy body holds. The one locator that is not a test id is the tab's own
`data-wrtab` attribute (the tab row on a phone has no test id), which says whether the tab is listed at all.
"""
from pages.recap import RecapPage


class AccuracyPage:

    def __init__(self, page):
        self.page = page
        self.recap = RecapPage(page)
        self._weeks = page.get_by_test_id("accuracy-week")

    # ---- what a reader does ----

    def open(self):
        """Tap the Accuracy tab where the reader sees it."""
        self.recap.pick_tab("accuracy")

    # ---- what a reader sees ----

    def tab_names(self):
        """The tab bar, left to right."""
        return self.recap.tabs()

    def open_tab(self):
        """The tab the body is showing."""
        return self.recap.body_tab()

    def tab_listed(self):
        """How many Accuracy tabs the view offers, in the bar or the tab row."""
        return self.page.locator("[data-wrtab='accuracy']").count()

    def week_cards(self):
        """One card per graded week."""
        return self._weeks.count()

    def empty_states(self):
        """How many empty-state blocks the view draws: none while a tab has something to show."""
        return self.recap.empty_count()

    def sideways(self):
        """How far the page scrolls sideways: 0 or less is none."""
        return self.recap.sideways()
