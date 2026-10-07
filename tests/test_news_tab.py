"""This week > News, in Chromium (2026-09-30, David: "the first paragraph of each news repeats the headline.
Player names are hard to find on a scan. Should we have a search for players here?").

Component tests: News mounted (tests/component.py); every locator is in tests/pages/news.py."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.news import NewsPage

pytestmark = pytest.mark.render


@pytest.fixture
def wide(mount):
    """News mounted at 1400x900: (NewsPage, page errors)."""
    page, errors = mount("news", size=(1400, 900))
    return NewsPage(page), errors


def test_a_story_with_a_read_drops_the_summary_that_repeats_its_headline(wide):
    news, errors = wide
    got = news.rows_reading()
    assert got and not any(r["desc"] and r["impact"] for r in got)
    assert errors == []


def test_the_players_name_is_the_bright_part_of_the_headline(wide):
    news, errors = wide
    got = news.headlines()
    named = [r for r in got if r["name"]]
    assert named, "at least one fixture headline names its player"
    not_in_title = [r["name"] for r in named if r["name"] not in r["title"]]
    assert not_in_title == []
    not_brighter = [r["name"] for r in named if r["ink"] == r["rest"]]
    assert not_brighter == [], "the name is brighter than the rest of the headline"
    assert errors == []


@pytest.mark.parametrize("size", [(390, 844), (1400, 900)])
def test_the_search_narrows_the_list_in_place(mount, size):
    page, errors = mount("news", size=size)
    news = NewsPage(page)
    total = news.listed_count()
    # A word from the first listed story's own text matches it, and the box keeps the caret.
    word = news.first_listed_word()
    news.search(word)
    assert 1 <= news.shown_count() <= total
    assert news.search_has_focus()
    news.search("zzqxnotaplayer")
    assert news.all_hidden()
    assert news.none_visible()
    # A chip re-renders the list and keeps what was typed.
    news.search(word)
    news.pick_all()
    assert news.search_value() == word
    assert news.page_scroll_width() <= size[0]
    assert errors == []
