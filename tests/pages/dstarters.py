"""Defenders out (design/src/js/ui/dstarters.js, 2026-10-06): the chip Preview's box score and the profile's Matchup
pane both draw, for a defense missing starters.

Every locator lives here, data-testid first (`preview-ds*` in the dossier, `profile-ds*` in the modal; test hooks
only, no CSS or JS reads them). `where` is "preview" or "profile". A chip is a closed <details>: `chips()` reads
its line, `open()` taps it, `names()` and `why()` read what opens. A test plants what the page would hold with
`plant`, the way Recap's page object does (the block is a const, so its fields change, never the block).
"""
import re

OPEN_GAME = "[data-pvopen='{i}']"


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


class DefendersOut:
    def __init__(self, page, where):
        self.page, self.where = page, where
        self._chip = page.get_by_test_id(f"{where}-ds")

    # ---- what a test sets up ----

    def plant(self, week=None, teams=None):
        """Set the block's week and/or put records under defense codes (the page's spelling)."""
        self.page.evaluate("""([week, teams]) => {
          if (week !== null) LIVE_D_STARTERS.week = week;
          Object.assign(LIVE_D_STARTERS.teams, teams || {}); }""", [week, teams])

    # ---- what a reader does ----

    def open_game(self, i):
        """Preview: tap game `i` (kickoff order) on the slate; the dossier opens over it on a phone."""
        self.page.locator(OPEN_GAME.format(i=i)).click()
        self.page.locator(".pvn").wait_for()

    def open(self, i=0):
        self._chip.nth(i).get_by_test_id(f"{self.where}-ds-line").click()

    # ---- what a reader sees ----

    def count(self):
        return self._chip.count()

    def section_count(self):
        """Preview's "Defenders out" box-score rows (a game has one, with a chip per short defense, or none)."""
        return self.page.locator(".pvn-box .pva.ds").count()

    def lines(self):
        return [squash(t) for t in self._chip.get_by_test_id(f"{self.where}-ds-line").all_inner_texts()]

    def is_open(self, i=0):
        return self._chip.nth(i).evaluate("e => e.open")

    def names(self, i=0):
        """[(name, detail)] of the opened chip."""
        rows = self._chip.nth(i).get_by_test_id(f"{self.where}-ds-names").locator("li")
        return [(squash(r.locator("b").inner_text()), squash(r.locator("span").inner_text())) for r in rows.all()]

    def names_visible(self, i=0):
        return self._chip.nth(i).get_by_test_id(f"{self.where}-ds-names").is_visible()

    def why(self, i=0):
        return squash(self._chip.nth(i).get_by_test_id(f"{self.where}-ds-why").inner_text())

    def teams(self):
        return [c.get_attribute("data-ds-team") for c in self._chip.all()]
