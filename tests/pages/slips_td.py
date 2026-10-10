"""Slips' Anytime TDs card (design/src/js/surface/parlay/tdcard.js, 2026-10-09). Every locator lives here, data-testid
first (`td-*`, test hooks only). Opens through SlipsPage, so the tab, the book and the slip start as Slips' tests do."""
import re

from pages.slips import SlipsPage


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


class TdCard:
    def __init__(self, slips):
        self.slips, self.page = slips, slips.page
        self.card = self.page.get_by_test_id("td-card")
        self.rows = self.card.get_by_test_id("td-row")

    @classmethod
    def open(cls, mount, win, size=(360, 800)):
        s, errors = SlipsPage.open(mount, win, size=size)
        return cls(s), errors

    # ---- what a test sets up ----

    def drop_pending(self):
        self.page.evaluate("() => { LIVE_TD_RESEARCH.pending = []; render(); }")

    # ---- what a reader does ----

    def add(self, i=0):
        self.rows.nth(i).get_by_test_id("td-add").click()

    def open_row(self, i=0):
        self.rows.nth(i).get_by_test_id("td-open").click()
        self.page.wait_for_function("typeof LEG_SHEET === 'string' && LEG_SHEET.startsWith('td:')")

    def close_sheet(self):
        self.page.locator("#legsheet").get_by_test_id("td-sheet-close").click()
        self.page.wait_for_function("LEG_SHEET === null")

    def unfold(self, tier):
        self.group(tier).get_by_test_id("td-fold").click()

    # ---- what a reader sees ----

    def visible(self):
        return self.card.count() == 1 and self.card.is_visible()

    def names(self):
        return [squash(n) for n in self.rows.get_by_test_id("td-name").all_inner_texts()]

    def first_row_top(self):
        return self.rows.first.bounding_box()["y"]

    def group(self, tier):
        return self.card.locator(f"[data-testid='td-group'][data-tier='{tier}']")

    def group_rows(self, tier):
        return self.group(tier).get_by_test_id("td-row").count()

    def expanded(self, tier):
        return self.group(tier).get_by_test_id("td-fold").get_attribute("aria-expanded")

    def record(self):
        return squash(self.card.get_by_test_id("td-record").inner_text())

    def wait_line(self):
        w = self.card.get_by_test_id("td-wait")
        return squash(w.inner_text()) if w.count() else None

    def sheet_text(self):
        return squash(self.page.locator("#legsheet").inner_text())

    def has_ours(self):
        return self.page.locator("#legsheet").get_by_test_id("td-sheet-ours").count() == 1
