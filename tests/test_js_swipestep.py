"""When a touch on the view is a swipe between tabs, in Node (data/swipestep.js, 2026-10-06).

David on his phone: "it switches tabs while I am scrolling". The old rule looked only at where the finger
let go: 48 px sideways and 1.5 times more sideways than down. A thumb scrolling a list drifts sideways on
its arc and passed that. The decision is now made from every point of the touch (start, each move, end)
and how far the page scrolled meanwhile: the first ~10 px pick the axis, and a touch that began up or
down, or moved the page, is a scroll however it ends."""
import pytest

CLEAN_LEFT = [[200, 400], [185, 401], [140, 403], [100, 404]]


@pytest.fixture(scope="module")
def sw(node_js):
    return node_js("data/swipestep.js")


@pytest.mark.req("Swipe between tabs", ac="a clean sideways swipe turns the tab")
def test_a_clean_swipe_left_is_the_next_tab_and_right_the_one_before(sw):
    assert sw("swipeStep", CLEAN_LEFT, 0) == 1
    assert sw("swipeStep", [[100, 400], [115, 401], [160, 403], [200, 404]], 0) == -1


def test_a_swipe_with_only_a_start_and_an_end_still_counts(sw):
    """Some browsers send no move for a fast flick: the end point picks the axis."""
    assert sw("swipeStep", [[200, 400], [100, 402]], 0) == 1


@pytest.mark.req("Swipe between tabs", ac="a scroll never turns the tab")
def test_a_diagonal_flick_scroll_is_a_scroll(sw):
    """Starts a little more sideways than up, ends 90 px across and 70 px up: a thumb's arc, not a swipe."""
    assert sw("swipeStep", [[200, 400], [191, 393], [150, 360], [110, 330]], 0) is None


@pytest.mark.req("Swipe between tabs", ac="a scroll never turns the tab")
def test_a_touch_that_starts_up_or_down_is_a_scroll_however_it_ends(sw):
    assert sw("swipeStep", [[200, 400], [201, 388], [150, 386], [90, 386]], 0) is None


@pytest.mark.req("Swipe between tabs", ac="a scroll never turns the tab")
def test_a_touch_that_moved_the_page_is_a_scroll(sw):
    assert sw("swipeStep", CLEAN_LEFT, 30) is None


def test_a_few_px_of_page_movement_is_not_a_scroll(sw):
    """The page settling by a pixel or two (iOS rubber band) does not cancel a real swipe."""
    assert sw("swipeStep", CLEAN_LEFT, 2) == 1


@pytest.mark.req("Swipe between tabs", ac="a scroll never turns the tab")
def test_sideways_drift_on_a_scroll_is_not_a_swipe(sw):
    """100 px across and 55 down passed the old rule (48 px, 1.5 times): it is a scroll's drift."""
    assert sw("swipeStep", [[200, 400], [190, 404], [140, 430], [100, 455]], 0) is None


@pytest.mark.parametrize("dx,want", [(-72, 1), (-71, None), (72, -1)])
def test_a_swipe_counts_from_72_px_across(sw, dx, want):
    assert sw("swipeStep", [[200, 400], [200 + dx // 2, 400], [200 + dx, 400]], 0) == want


@pytest.mark.parametrize("scrolled,want", [(4, 1), (-4, 1), (5, None), (-5, None)])
def test_more_than_4_px_of_scroll_either_way_makes_it_a_scroll(sw, scrolled, want):
    assert sw("swipeStep", CLEAN_LEFT, scrolled) == want


@pytest.mark.parametrize("dx", [-30, -60])
def test_a_short_nudge_is_not_a_swipe(sw, dx):
    assert sw("swipeStep", [[200, 400], [200 + dx // 2, 400], [200 + dx, 401]], 0) is None


def test_a_tap_is_not_a_swipe(sw):
    assert sw("swipeStep", [[200, 400], [201, 400]], 0) is None
    assert sw("swipeStep", [[200, 400]], 0) is None
