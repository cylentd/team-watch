"""The phone's header bar and tab row stay put while the reader scrolls (2026-10-07, TODO "Tab row jumps on
scroll"). Until then the header slid away on a scroll down and back on a scroll up, the tab row moving
on its own to follow it, and on a phone the two parted mid-slide. Nothing at the top moves now: the
header sits at the top edge and the tab row right under it, whichever way the list scrolls. A mounted
view (tests/component.py), read through tests/pages/phonechrome.py."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.phonechrome import ChromeSurface, PhoneBar, PhoneChrome
from wording import words

PHONE = (360, 740)
DESKTOP = (1280, 800)
CARD_ROW = "ranks-row"       # a Ranks row; the tier card around it is the card the chrome must not look like
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


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the chrome paints its own surface, not the page's or a card's")
@pytest.mark.parametrize("size, part", [(PHONE, "header"), (PHONE, "tab row"), (PHONE, "bottom bar"),
                                        (DESKTOP, "header"), (DESKTOP, "tab row")])
def test_the_chrome_paints_a_ground_unlike_the_page_and_the_cards(mount, size, part):
    page, errors = mount("ranks", size=size)
    paint = ChromeSurface(page).paint(CARD_ROW)
    assert paint[part]["bg"] != paint["card"]["bg"], f"the {part} is painted like a card"
    assert paint[part]["bg"] != paint["page"]["bg"], f"the {part} is painted like the page under the cards"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the chrome's edge against the content is not a card's border")
@pytest.mark.parametrize("size, part", [(PHONE, "tab row"), (PHONE, "bottom bar"),
                                        (DESKTOP, "header"), (DESKTOP, "tab row")])
def test_the_chrome_meets_the_content_with_an_edge_unlike_a_cards_border(mount, size, part):
    page, errors = mount("ranks", size=size)
    paint = ChromeSurface(page).paint(CARD_ROW)
    assert paint[part]["edge"] is not None, f"the {part} draws no edge where it meets the content"
    assert paint[part]["edge"] != paint["card"]["edge"], f"the {part}'s edge is a card's border"
    assert errors == []


GROUPS = ("home", "team", "week", "scouting", "league")    # data/navmap.js NAV, in the bar's order (Home draft B, 2026-10-08)


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the bottom bar is Team, Matchup, Players, League, Bets; Search sits beside Ask")
def test_the_bottom_bar_holds_the_five_sections_and_search_moves_up_beside_ask(mount):
    """Storyboard nav draft B (David 2026-10-08, ledger #32): Bets keeps the fifth slot, so Search moves to the
    header bar, left of Ask, still one tap from every view."""
    page, errors = mount("ranks", size=PHONE)
    bar = PhoneBar(page)
    assert bar.words() == [words(f"nav.group.{g}.short") for g in GROUPS]
    assert bar.search_place() == {"in_header": True, "in_bar": False, "beside_ask": True, "on_screen": True}
    assert errors == []
