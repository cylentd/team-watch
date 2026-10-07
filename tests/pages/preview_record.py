"""Preview's Past games (design/src/js/surface/preview/record.js): Claude's season by bet, a week stepper and that
week's finished games. `PreviewPage.record` is this class; the slate row that opens it, and the dossier a game
opens, are `PreviewPage`'s.

Locators are `preview-*` data-testids (test hooks only). A row of an earlier week's archive carries `data-pvarcg`, a
parameter a test id cannot carry, so it is found by that attribute. Reads return plain data; no method asserts.
"""
import re

ARCHIVED = """() => { const g = structuredClone(LIVE_PREVIEW.games[2]);
  Object.assign(g, {key: "2026_01_DET_CAR", week: 1, kickoff: "2026-09-14T17:00:00Z", matchup: null, inj: null,
    wx: null, rest: null, travel: null, site: null});
  g.take.players.forEach(p => p.proj = null);
  PV_ARC = {season: 2026, weeks: {"1": [g]}}; }"""


class PreviewRecord:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._sheet, self._games, self._steps = tid("preview-record"), tid("preview-game-row"), tid("preview-week-step")

    # ---- what a reader does ----

    def show(self, wk):
        """Past games on week `wk`, by state."""
        self.page.evaluate(f"() => {{ PV_OPEN = false; PV_REC = true; PV_ARC_WK = {wk}; render(); }}")

    def tap_back(self):
        self.page.get_by_test_id("preview-record-back").click()

    def step_week(self, d):
        (self._steps.first if d < 0 else self._steps.last).click()

    def tap_game(self, n):
        """The n-th finished game."""
        self._games.nth(n).click()

    def tap_archived_game(self):
        self._games.and_(self.page.locator("[data-pvarcg]")).click()

    # ---- what a test plants ----

    def plant_archived_week_one(self):
        """One week-1 game in the fetched archive: DET @ CAR as it was written, no projections archived."""
        self.page.evaluate(ARCHIVED)

    def drop_graded_weeks(self):
        self.page.evaluate("() => { LIVE_PREVIEW.record.weeks.splice(0); render(); }")

    def drop_record(self):
        self.page.evaluate("() => { LIVE_PREVIEW.record = null; render(); }")

    # ---- what a reader sees ----

    def visible(self):
        return self._sheet.is_visible()

    def count(self):
        return self._sheet.count()

    def text(self):
        return self._sheet.inner_text()

    def legacy_cards(self):
        """The record card that used to head the slate."""
        return self.page.locator(".pv-rec, .pv-rec0").count()

    def back_text(self):
        return self.page.get_by_test_id("preview-record-back").inner_text()

    def season_title(self):
        return self.page.get_by_test_id("preview-season-title").inner_text()

    def season_rows(self):
        return self.page.get_by_test_id("preview-season-table").evaluate(
            "t => [...t.querySelectorAll('tr')].map(r => [...r.cells].map(c => c.innerText.trim()))")

    def season_conf(self):
        return self.page.get_by_test_id("preview-season-conf").inner_text()

    def season_count(self):
        return self.page.get_by_test_id("preview-season").count()

    def week_label(self):
        return self.page.get_by_test_id("preview-week").inner_text()

    def week_line(self):
        return self.page.get_by_test_id("preview-week-line").inner_text()

    def week_step_disabled(self, d):
        return (self._steps.first if d < 0 else self._steps.last).is_disabled()

    def game_count(self):
        return self._games.count()

    def game_matches(self):
        return [re.sub(r"\s+", " ", t).strip() for t in self.page.get_by_test_id("preview-game-match").all_inner_texts()]

    def archived_game_open(self):
        return self.page.evaluate("PV_ARC_G") is not None
