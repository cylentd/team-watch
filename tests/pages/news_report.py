"""Players > News as an injury report (design/src/js/surface/news/news.js, ledger #95, 2026-10-09).

Every locator of the report lives here, data-testid first (`news-*`, test hooks only). `NewsReport` is the view
mounted (tests/component.py). Reads return plain data; no method asserts.
"""

ROWS = """rs => rs.map(r => ({
    slug: r.dataset.slug,
    name: r.querySelector('[data-testid="news-name"]').textContent,
    sunday: r.querySelector('[data-testid="news-sunday"]').textContent.trim(),
    days: [...r.querySelectorAll('[data-testid="news-day"]')].map(d => d.textContent.trim()),
    story: (r.querySelector('[data-testid="news-story"]') || {}).textContent || null,
    noreport: (r.querySelector('[data-testid="news-noreport"]') || {}).textContent || null,
    next: [...r.querySelectorAll('[data-testid="news-next"]')].map(n => n.textContent)}))"""
GROUPS = """gs => gs.map(g => ({key: g.dataset.group, title: g.querySelector('h2').firstChild.textContent,
    rows: g.querySelectorAll('[data-testid="news-player"]').length}))"""


class NewsReport:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._report, self._groups, self._rows = tid("news-report"), tid("news-group"), tid("news-player")

    # ---- what a reader sees ----

    def groups(self):
        """Each group top to bottom: {key, title, rows}."""
        return self._groups.evaluate_all(GROUPS)

    def rows(self):
        """Each player row top to bottom: {slug, name, sunday, days (each cell's text), story, next}."""
        return self._rows.evaluate_all(ROWS)

    def text(self):
        return self._report.inner_text()

    def earlier_shown(self, slug):
        """Whether the row's earlier stories are open."""
        return self._row(slug).locator(".nr-earlier").is_visible()

    def page_scroll_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")

    # ---- what a reader does ----

    def plant_report_without_marks(self, note):
        """ff-jarvis's report as it ships while Sleeper carries no practice word: every day null, a `note` set.
        Redraws the view."""
        self.page.evaluate("""note => { LIVE_NEWS.practice = {note};
            Object.values(LIVE_NEWS.players).forEach(p => { if (p.days) p.days = {Wed: null, Thu: null, Fri: null}; });
            render(); }""", note)

    def plant_days(self, slug, days):
        """ff-jarvis's report marks for one player ({Wed, Thu, Fri: dnp|limited|full|None}), no note. Redraws."""
        self.page.evaluate("""([s, d]) => { LIVE_NEWS.practice = {note: null};
            LIVE_NEWS.players[s] = {...LIVE_NEWS.players[s], days: d, report: true}; render(); }""", [slug, days])

    def open_earlier(self, slug):
        self._row(slug).get_by_test_id("news-more").click()

    def _row(self, slug):
        return self._rows.and_(self.page.locator(f'[data-slug="{slug}"]'))
