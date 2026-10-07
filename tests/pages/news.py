"""This week > News (design/src/js/surface/news/): the freshest "out" story pinned, a kind filter, a search box
that narrows the rows in place, then the stories newest first.

Every News locator lives here, data-testid first (`news-*`, test hooks only). `NewsPage` is the view mounted
(tests/component.py). Reads return plain data; no method asserts.
"""

DESC_AND_IMPACT = """rs => rs.map(r => ({desc: !!r.querySelector('[data-testid="news-desc"]'),
    impact: !!r.querySelector('[data-testid="news-impact"]')}))"""
HEADLINES = """rs => rs.map(r => {
    const t = r.querySelector('[data-testid="news-title"]'), b = t.querySelector('[data-testid="news-name"]');
    return {title: t.textContent, name: b && b.textContent,
            ink: b && getComputedStyle(b).color, rest: getComputedStyle(t).color}; })"""


class NewsPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._rows, self._list, self._box = tid("news-row"), tid("news-list"), tid("news-search")
        self._none, self._all = tid("news-none"), tid("news-chip-all")

    # ---- what a reader sees ----

    def rows_reading(self):
        """Every row, the pinned story included: {desc, impact}, whether it draws the scanner's summary and its read."""
        return self._rows.evaluate_all(DESC_AND_IMPACT)

    def headlines(self):
        """Every row: {title, name, ink, rest}; name is the bold player in the headline (None if it has none),
        ink its computed colour, rest the headline's."""
        return self._rows.evaluate_all(HEADLINES)

    def listed_count(self):
        """Rows in the chronological list under the filter (the pinned story is not one of them)."""
        return self._list.get_by_test_id("news-row").count()

    def shown_count(self):
        """Rows in the list the search has not hidden."""
        return self._list.get_by_test_id("news-row").evaluate_all("rs => rs.filter(r => !r.hidden).length")

    def all_hidden(self):
        return self._list.get_by_test_id("news-row").evaluate_all("rs => rs.every(r => r.hidden)")

    def first_listed_word(self):
        """The first word of the first listed story's own search text (it matches that story)."""
        return self._list.get_by_test_id("news-row").first.get_attribute("data-newsq").split(" ")[0]

    def none_visible(self):
        """The no-match message under the list."""
        return self._none.is_visible()

    def search_value(self):
        return self._box.input_value()

    def search_has_focus(self):
        return self.page.evaluate("document.activeElement.id") == "news-q"

    def page_scroll_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")

    # ---- what a reader does ----

    def search(self, text):
        self._box.fill(text)

    def pick_all(self):
        """The All chip: re-renders the list."""
        self._all.click()
