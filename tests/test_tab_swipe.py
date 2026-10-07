"""Swipe between tabs (chrome/tabswipe.js, 2026-10-06): on a phone a sideways swipe on the view is a tap on the
next thing in the top tab row. Which stop comes next is data/tabrow.js tabRowStep, proven in Node
(test_js_tabrow.py); these prove the gesture reaches it, and that a touch other surfaces own stays theirs."""
import pytest

from component import mount  # noqa: F401
from pages.live_tabs import LiveTabsPage
from pages.tabswipe import OWNERS, TabSwipe

pytestmark = pytest.mark.render

LEFT, RIGHT = -120, 120   # a swipe left asks for the tab to the right


WEEK = ["digest", "weekrecap", "news", "matchups", "preview", "live"]   # This week's row (data/navmap.js)


@pytest.fixture
def week(mount):
    """This week's row on a phone, on News: a plain pill with a plain pill on its right."""
    page, errors = mount("digest")
    row = TabSwipe(page)
    assert row.pills() == WEEK
    row.open("news")
    yield row
    assert errors == []


@pytest.mark.req("Swipe between tabs", ac="a swipe is a tap on the next thing in the row")
def test_a_swipe_on_the_view_opens_the_tab_beside_the_open_one(week):
    week.swipe(LEFT)
    assert (week.pressed_pill(), week.hash()) == ("matchups", "#matchups")
    week.swipe(RIGHT)
    assert week.pressed_pill() == "news"


@pytest.mark.req("Swipe between tabs", ac="the row's ends stop the swipe")
def test_a_swipe_past_the_first_tab_stays_put(week):
    week.open("digest")
    week.swipe(RIGHT)
    assert week.pressed_pill() == "digest"


def test_a_nudge_is_not_a_swipe(week):
    week.swipe(-30)
    assert week.pressed_pill() == "news"


@pytest.mark.req("Swipe between tabs", ac="a touch at a screen edge is the browser's")
@pytest.mark.parametrize("x", [10, 350])
def test_a_swipe_from_the_screen_edge_is_left_to_the_browser(week, x):
    week.swipe(LEFT, x=x)
    assert week.pressed_pill() == "news"


@pytest.mark.req("Swipe between tabs", ac="a surface's own sideways gesture keeps its touch")
@pytest.mark.parametrize("kind", sorted(OWNERS))
def test_a_swipe_on_a_surface_with_its_own_sideways_touch_stays_on_the_tab(week, kind):
    week.swipe_on_owner(kind, LEFT)
    assert week.pressed_pill() == "news"


@pytest.mark.req("Swipe between tabs", ac="a swipe is a tap on the next thing in the row")
def test_a_swipe_walks_an_opened_pills_own_tabs_before_the_next_view(mount):
    live, errors = LiveTabsPage.open_league(mount)
    row = TabSwipe(live.page)
    segs = row.segs()
    assert segs == ["league", "games", "tds"], "Live opens in place into My league, NFL, TDs"
    live.open_tab("league")
    row.swipe(LEFT)
    assert row.pressed_seg() == "games"
    row.swipe(RIGHT)
    row.swipe(RIGHT)                                    # off its first tab: the pill before Live
    pills = row.pills()
    assert row.pressed_pill() == pills[pills.index("live") - 1]
    assert errors == []
