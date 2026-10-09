"""Players > News, in Chromium: the row reads name first, then what happened (2026-09-30, David: "the first paragraph
of each news repeats the headline. Player names are hard to find on a scan"), now on the injury report (ledger #95,
2026-10-09), whose rows replaced the feed, its kind chips and its search.

Component tests: News mounted (tests/component.py); every locator is in tests/pages/news_report.py."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.news import NewsPage

pytestmark = pytest.mark.render


@pytest.fixture
def wide(mount):
    """News mounted at 1400x900: (NewsPage, page errors)."""
    page, errors = mount("news", size=(1400, 900))
    return NewsPage(page), errors


def test_a_row_says_what_happened_without_repeating_the_name(wide):
    news, errors = wide
    got = [r for r in news.inks() if r["story"]]
    assert got, "the fixture's stories name rostered players"
    assert [r["name"] for r in got if r["name"] in r["story"]] == []
    assert errors == []


def test_the_players_name_is_the_bright_part_of_the_row(wide):
    news, errors = wide
    got = [r for r in news.inks() if r["story"]]
    assert got
    assert [r["name"] for r in got if r["ink"] == r["rest"]] == [], "the name is brighter than the story under it"
    assert errors == []


@pytest.mark.parametrize("size", [(390, 844), (1400, 900)])
def test_the_report_fits_its_width(mount, size):
    page, errors = mount("news", size=size)
    news = NewsPage(page)
    assert news.rows()
    assert news.page_scroll_width() <= size[0]
    assert errors == []
