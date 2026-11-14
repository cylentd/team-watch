"""Defense form as the two views draw it (2026-11-14): Schedule's note on a team row (`schedule-form`) and Preview's
"Defenses lately" lines in the box score (`preview-form-line`). Every locator for it lives here; reads return plain
data and never assert. The rest of each view stays in pages/schedule.py and pages/preview.py.
"""
import re

ROW_NOTES = """rows => rows.map(r => { const n = r.querySelector('[data-testid="schedule-form"]');
  return [r.querySelector('.sos-team').textContent, n ? n.textContent.replace(/\\s+/g, ' ').trim() : null]; })"""
MARKED = """rows => rows.map(r => { const c = r.querySelector('[data-testid="schedule-cell"].df');
  return [r.querySelector('.sos-team').textContent, c ? c.innerText.replace(/\\s+/g, ' ').trim() : null]; })"""
LINES ="""ls => ls.map(l => [...l.children].map(c => c.textContent.replace(/\\s+/g, ' ').trim()))"""


class ScheduleForm:
    def __init__(self, page):
        self.page = page
        self._rows, self._notes = page.get_by_test_id("schedule-row"), page.get_by_test_id("schedule-form")

    def notes(self):
        """{team: the note's words} for every row that draws one."""
        return {t: n for t, n in self._rows.evaluate_all(ROW_NOTES) if n}

    def note(self, team):
        """{text, trend, tip} of the note on `team`'s row."""
        n = self._rows.filter(has=self.page.locator(".sos-team", has_text=re.compile(f"^{team}$"))).get_by_test_id("schedule-form")
        return {"text": re.sub(r"\s+", " ", n.inner_text()).strip(), "trend": n.get_attribute("data-trend"),
                "tip": n.get_attribute("title")}

    def note_count(self):
        return self._notes.count()

    def marked_cells(self):
        """{team: the marked opponent cell's words on one line} for every row with one."""
        return {t: c for t, c in self._rows.evaluate_all(MARKED) if c}

    def row_height(self, team):
        row = self._rows.filter(has=self.page.locator(".sos-team", has_text=re.compile(f"^{team}$")))
        return row.evaluate("r => Math.round(r.getBoundingClientRect().height)")

    def note_cut(self, team):
        """Pixels of `team`'s note hidden by its one-line ellipsis (0: every word shows)."""
        n = self._rows.filter(has=self.page.locator(".sos-team", has_text=re.compile(f"^{team}$"))).get_by_test_id("schedule-form")
        return n.evaluate("e => e.scrollWidth - e.clientWidth")


class PreviewForm:
    def __init__(self, page):
        self.page = page
        self._lines, self._section = page.get_by_test_id("preview-form-line"), page.locator(".pva.form")

    def lines(self):
        """[[the defense and its trend, its numbers]] in the order drawn."""
        return self._lines.evaluate_all(LINES)

    def trends(self):
        return [self._lines.nth(i).get_attribute("data-trend") for i in range(self._lines.count())]

    def section_count(self):
        return self._section.count()

    def mark(self):
        """The section head's "context only" mark: (its words, its tip)."""
        em = self._section.locator(".pva-h em")
        return em.inner_text(), em.get_attribute("title")
