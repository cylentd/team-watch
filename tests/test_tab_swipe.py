"""Swipe between tabs (chrome/tabswipe.js, 2026-10-06): on a phone a sideways swipe on the view is a tap on the
next thing in the top tab row. Which stop comes next is data/tabrow.js tabRowStep, proven in Node
(test_js_tabrow.py); these prove the gesture reaches it, and that a touch other surfaces own stays theirs."""
import pytest

from component import mount  # noqa: F401
from pages.live_tabs import LiveTabsPage
from pages.tabswipe import OWNERS, TabSwipe

pytestmark = pytest.mark.render

LEFT, RIGHT = -120, 120   # a swipe left asks for the tab to the right


WEEK = ["live", "matchups", "preview", "weekrecap", "parlay", "build", "dfs"]   # Matchup's row (data/navmap.js); Today is Home since 2026-10-08


@pytest.fixture
def week(mount):
    """Matchup's row on a phone, on Start/Sit: a plain pill with a plain pill on its right."""
    page, errors = mount("preview")
    row = TabSwipe(page)
    assert row.pills() == WEEK
    row.open("matchups")
    yield row
    assert errors == []


@pytest.mark.req("Swipe between tabs", ac="a swipe is a tap on the next thing in the row")
def test_a_swipe_on_the_view_opens_the_tab_beside_the_open_one(week):
    week.swipe(LEFT)
    assert (week.pressed_pill(), week.hash()) == ("preview", "#preview")
    week.swipe(RIGHT)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="the row's ends stop the swipe")
def test_a_swipe_past_the_first_tab_stays_put(week):
    week.open("live")
    week.swipe(RIGHT)
    assert week.pressed_pill() == "live"


def test_a_nudge_is_not_a_swipe(week):
    week.swipe(-30)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="a touch at a screen edge is the browser's")
@pytest.mark.parametrize("x", [10, 350])
def test_a_swipe_from_the_screen_edge_is_left_to_the_browser(week, x):
    week.swipe(LEFT, x=x)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="a surface's own sideways gesture keeps its touch")
@pytest.mark.parametrize("kind", sorted(OWNERS))
def test_a_swipe_on_a_surface_with_its_own_sideways_touch_stays_on_the_tab(week, kind):
    week.swipe_on_owner(kind, LEFT)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="anywhere between the tab row and the bottom bar")
def test_a_swipe_on_the_empty_page_below_a_short_view_opens_the_next_tab(week):
    week.swipe_on_background(LEFT)
    assert week.pressed_pill() == "preview"


@pytest.mark.req("Swipe between tabs", ac="anywhere between the tab row and the bottom bar")
@pytest.mark.parametrize("part", ["header", "tab row", "bottom bar"])
def test_a_swipe_on_the_pages_chrome_is_not_a_tab_swipe(week, part):
    week.swipe_on_chrome(part, LEFT)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="never under an overlay")
def test_a_swipe_while_an_overlay_is_open_stays_on_the_tab(week):
    week.open_search()
    week.swipe_on_background(LEFT)
    week.swipe(LEFT)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="a scroll never turns the tab")
def test_a_touch_that_scrolls_the_page_is_a_scroll(week):
    week.scroll_while_swiping(LEFT, 200)
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="a scroll never turns the tab")
def test_a_touch_that_starts_down_the_page_is_a_scroll_however_it_ends(week):
    week.touch([(200, 400), (201, 386), (150, 385), (80, 385)])
    assert week.pressed_pill() == "matchups"


@pytest.mark.req("Swipe between tabs", ac="a swipe into a view lands on its nearest tab")
def test_a_swipe_into_recap_lands_on_its_first_tab_from_the_left_and_its_last_from_the_right(week):
    week.open("weekrecap")
    segs = week.segs()
    assert len(segs) >= 3, "the fixture's Recap opens into three tabs or more"
    week.tap_seg(segs[-1])                   # Recap remembers its last tab
    week.open("preview")
    week.swipe(LEFT)
    assert (week.pressed_pill(), week.pressed_seg()) == ("weekrecap", segs[0])
    week.open("parlay")
    week.tap_seg(week.segs()[0])             # Slips has tabs of its own: a swipe from its first one leaves it
    week.swipe(RIGHT)
    assert (week.pressed_pill(), week.pressed_seg()) == ("weekrecap", segs[-1])


@pytest.mark.req("Swipe between tabs", ac="a swipe into a view lands on its nearest tab")
def test_a_swipe_onto_a_tab_past_the_rows_edge_brings_it_into_view(week):
    """Recap opened into its four tabs is wider than a 360 px row; landing on its last tab shows that tab."""
    week.open("weekrecap")
    week.tap_seg(week.segs()[0])
    week.open("parlay")
    week.tap_seg(week.segs()[0])             # Slips has tabs of its own: a swipe from its first one leaves it
    week.swipe(RIGHT)
    assert week.pressed_seg() == week.segs()[-1]
    assert week.pressed_seg_overhang() == [0, 0]


@pytest.mark.req("Swipe between tabs", ac="a swipe is a tap on the next thing in the row")
def test_a_swipe_on_the_leaders_card_opens_the_next_tab_not_the_next_stat(mount):
    page, errors = mount("board")
    row = TabSwipe(page)
    pills = row.pills()
    assert row.pressed_pill() == "board"
    row.swipe_on_leaders_card(LEFT)
    assert row.pressed_pill() == pills[pills.index("board") + 1]
    assert errors == []


@pytest.mark.req("Swipe between tabs", ac="the slide moves the page, never what is fixed to the screen")
def test_the_slide_moves_the_page_and_leaves_the_slip_tray_and_its_sheet_where_they_are(mount):
    page, errors = mount("dfs")
    row = TabSwipe(page)
    row.swipe(RIGHT)
    assert row.pressed_pill() == "build"
    kids = row.sliding()
    assert any(pos == "fixed" for _, pos, _ in kids), "All lines keeps its slip tray in the view"
    assert [(name, slid) for name, pos, slid in kids] == [(name, pos != "fixed") for name, pos, _ in kids]
    assert errors == []


@pytest.mark.req("Swipe between tabs", ac="the slide moves the page, never what is fixed to the screen")
def test_the_slide_never_widens_the_page_so_the_bottom_bar_stays_on_screen(week):
    """A block 28 px off to the right widened the page; a phone zoomed out to fit it and the bottom bar,
    fixed to the taller viewport, dropped off the screen for the length of the slide (2026-10-06)."""
    page_w, screen_w = week.width_at_slide_start(LEFT)
    assert page_w == screen_w


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
    row.swipe(RIGHT)                                    # off its first tab: Live leads Matchup's row since Home draft B
    assert row.pills()[0] == "live"
    assert (row.pressed_pill(), row.pressed_seg()) == ("live", "league"), "the row's end stops the swipe"
    assert errors == []
