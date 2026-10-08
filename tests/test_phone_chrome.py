"""The phone's header bar and tab row stay put while the reader scrolls (2026-10-07, TODO "Tab row jumps on
scroll"). Until then the header slid away on a scroll down and back on a scroll up, the tab row moving
on its own to follow it, and on a phone the two parted mid-slide. Nothing at the top moves now: the
header sits at the top edge and the tab row right under it, whichever way the list scrolls. A mounted
view (tests/component.py), read through tests/pages/phonechrome.py."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.phonechrome import PhoneChrome

PHONE = (360, 740)
DOWN, BACK_UP = 900, 700     # past hidebar's old 120px floor, then a scroll up of 200px
ROOM = 3000                  # the fixture's Ranks is shorter than a screen; this much more lets it scroll


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the header bar and tab row stay put on a scroll down and up")
def test_the_header_and_tab_row_stay_put_through_a_scroll_down_and_back_up(mount):
    page, errors = mount("ranks", size=PHONE, touch=True)
    chrome = PhoneChrome(page)
    chrome.lengthen(ROOM)
    rest = chrome.edges()
    assert rest["header_top"] == 0, "the header bar sits on the top edge"
    assert rest["row_top"] == rest["header_bottom"], "the tab row sits right under the header bar"

    assert chrome.scroll_through([DOWN]) == DOWN
    assert chrome.edges() == rest, "a scroll down moved the header or the tab row"

    assert chrome.scroll_through([BACK_UP]) == BACK_UP
    assert chrome.edges() == rest, "a scroll back up moved the header or the tab row"
    assert errors == []
