"""Players > News (design/src/js/surface/news/), an injury report since 2026-10-09 (ledger #95): a row per player
the reader follows, his Sunday word, Wednesday to Friday, his newest story. Until then it was the feed: a pinned
"out" story, kind chips, a search box and every story newest first (superseded).

`NewsPage` is the view mounted (tests/component.py). Its locators are `NewsReport`'s (pages/news_report.py), the
one place they live; this class adds the reads tests/test_news_tab.py needs. Reads return plain data; no method
asserts.
"""
from pages.news_report import NewsReport

INKS = """rs => rs.map(r => {
    const name = r.querySelector('[data-testid="news-name"]'), story = r.querySelector('[data-testid="news-story"]');
    return {name: name.textContent, ink: getComputedStyle(name).color,
            story: story && story.textContent, rest: story && getComputedStyle(story).color}; })"""


class NewsPage(NewsReport):
    def inks(self):
        """Each row: {name, ink, story, rest}; ink is the name's computed colour, rest the newest story's (None for
        a row with no story)."""
        return self._rows.evaluate_all(INKS)
