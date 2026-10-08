"""The polish fixes from David's 2026-10-08 walk at 360px (ledger #37), each on its own surface, mounted
(tests/component.py) and read through tests/pages/walk.py, pages/dfs.py and pages/phonechrome.py.

1. League > Recap: the lead's score line stays on one line on a phone.
2. Bets > DFS: the best lineup's edge is a neutral, not lime (lime is the reader's own or the pressed control).
3. Players > Schedule: the weeks chips are outlined like League > Teams' sort chips, only the pressed one filled.
4. A desktop's tab row stays under the bar through a scroll, as a phone's does (VISION 2026-10-07: nothing
   slides at the edge of the eye), and a view's own sticky column starts under it.
5. The team picker on a phone: two columns of compact buttons, a league of twelve in six rows."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.dfs import DfsPage
from pages.mates import MatesPage
from pages.phonechrome import PhoneChrome
from pages.tokens import token_rgb
from pages.walk import LeadLine, PickerGrid, StuckColumn, WeeksChips

pytestmark = pytest.mark.render

PHONE = (360, 800)
DESKTOP = (1280, 800)
ONE_LINE = 3            # px: the centres of words on one line differ by less than this
ROOM, DOWN = 3000, 900  # a fixture view lengthened so it scrolls, and how far down
TAP = 44                # px: the smallest tap target (STYLE.md, WCAG 2.5.8's enhanced size)
LONGEST = ("Crystal H.", "Lateef")   # the Madden Curse's two widest names with a score, measured 2026-10-08


@pytest.mark.parametrize("names, stamp", [(None, None), (LONGEST, None), (LONGEST, "Top dog")],
                         ids=["as-drawn", "longest-names", "longest-names-and-a-stamp"])
def test_the_lead_score_line_holds_one_line_on_a_phone(mount, names, stamp):
    page, errors = mount("recap", size=PHONE)
    lead = LeadLine(page)
    if names:
        lead.rename(*names)
    if stamp:
        lead.stamp_winner(stamp)
    got = lead.read()
    mids = got["mids"] + got["stamps"]
    assert max(mids) - min(mids) < ONE_LINE, f"names, scores, beat and stamps on one line: {got}"
    assert got["scores_whole"], "a long name gives way, never a score"
    assert got["past_card"] <= 0, "the line ends inside the card"
    assert errors == []


def test_the_best_lineup_is_edged_in_a_neutral_not_lime(mount):
    # one size: the lineup cards' edges have no breakpoint
    page, errors = mount("dfs", size=PHONE)
    dfs = DfsPage(page)
    dfs.pick_site("dk")
    assert dfs.card_count() >= 2, "the fixture draws a best lineup and another"
    best, other = dfs.best_edge(), dfs.other_edge()
    assert best["border"] == token_rgb(page, "--ink-3"), "the best lineup's edge is the strong neutral"
    assert best["ring"] == "none", "and no lime ring inside it"
    assert other["border"] == token_rgb(page, "--line-2"), "the rest keep the card edge"
    assert errors == []


@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_the_weeks_chips_are_outlined_and_only_the_pressed_one_is_filled(mount, size):
    page, errors = mount("schedule", size=size)
    chips = WeeksChips(page).paint()
    rest = [c for c in chips if c["pressed"] == "false"]
    pressed = [c for c in chips if c["pressed"] == "true"]
    assert len(pressed) == 1 and rest, chips
    assert all(c["fill"] == "rgba(0, 0, 0, 0)" and c["edge"] == token_rgb(page, "--line-2") for c in rest), rest
    assert pressed[0]["fill"] == token_rgb(page, "--lime"), pressed
    assert errors == []


def test_a_desktops_tab_row_stays_under_the_bar_through_a_scroll(mount):
    page, errors = mount("preview", size=DESKTOP)
    chrome = PhoneChrome(page)
    chrome.lengthen(ROOM)
    rest = chrome.edges()
    assert rest["header_top"] == 0 and rest["row_top"] == rest["header_bottom"], rest
    assert chrome.scroll_through([DOWN]) == DOWN
    assert chrome.edges() == rest, "a scroll down moved the bar or the tab row"
    assert errors == []


def test_a_views_sticky_column_starts_under_the_desktop_tab_row(mount):
    # The slate sticks inside Preview's grid, so the fixture's short slate cannot be scrolled to its stuck place;
    # where it sticks is its `top`, read against the tab row's bottom edge.
    page, errors = mount("preview", size=DESKTOP)
    assert StuckColumn(page).stuck_gap_under_tab_row() >= 0, "the slate would stick behind the tab row"
    assert errors == []


def test_the_picker_is_two_columns_of_half_width_buttons_on_a_phone(mount):
    # The fixture's leagues hold one or two teams; a real league's twelve then take six rows (checked at 360px
    # on the real build, 2026-10-08). Two to a row, each half the list wide, a full tap target.
    page, errors = mount("roster", size=PHONE)
    MatesPage(page).forget_pick_and_show_roster()
    grid = PickerGrid(page)
    leagues = grid.leagues()
    assert leagues and all(lg["rows"] == -(-lg["n"] // 2) for lg in leagues), leagues
    assert all(lg["widest"] * 2 <= lg["w"] for lg in leagues), "a button takes at most half the list"
    assert all(lg["min_h"] >= TAP for lg in leagues), "every team is still a full tap target"
    assert grid.overflow() <= 0
    assert errors == []
