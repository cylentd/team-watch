"""The leg sheet (2026-09-27). A Build line's info button opens one bet from the bottom edge: the
last ten games against the line, three tiles, the matchup as one line, and Add; since 2026-10-03 a
Slips board row opens the player sheet in the same overlay. Back closes either before it changes
the view. The fixture gives Tee Higgins and Chase Brown per-game usage (`u`) and Amon-Ra St. Brown
none, and a defense block in which NYJ has two starters out.

Component tests mount Slips or Build (tests/pages/legsheet.py reads the sheet; parlay.py and parlay_build.py
open it and hold the slip). The one that needs Back is a journey on the full page."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.legsheet import PHONE, LegSheetPage
from pages.parlay import ParlayPage
from pages.parlay_build import BuildPage
from test_render import open_page

pytestmark = pytest.mark.render


@pytest.fixture
def full(browser, page_file):
    """The whole page, for a journey: open(size) -> (ParlayPage, LegSheetPage, errors). Closed when the test ends."""
    opened = []

    def open_full(size):
        ctx, page, errors = open_page(browser, page_file, size)
        opened.append(ctx)
        return ParlayPage(page), LegSheetPage(page), errors
    yield open_full
    for ctx in opened:
        ctx.close()


@pytest.mark.journey
def test_a_board_row_opens_the_player_sheet_and_back_closes_it(full):
    """The Slips board's player sheet (2026-10-03) lives in the leg sheet's overlay: Chase Brown's
    work game by game (his log carries usage; his last four games are 2025's, faded only when the
    model's season is a later one -- the fixture's model runs through 2025), then his touchdown and
    rushing lines. Back closes it before the view."""
    board, sheet, errors = full(PHONE)
    board.show_slips("morning", "underdog")
    board.tap_chip("all")
    before = board.href()
    board.tap_row("chase-brown")
    assert board.sheet_open() and sheet.close_button_focused()
    old = sheet.build_season() > 2025
    want = [f"2025 W{w}" if old else f"W{w}" for w in (15, 16, 17, 18)]
    assert sheet.usage_weeks() == want
    assert sheet.usage_labels() == ["Snaps", "Targets", "Carries", "RZ looks"]
    assert sheet.old_usage_cells() == (16 if old else 0)
    lines = board.sheet_lines()
    assert lines[0]["market"].startswith("Anytime TD") and len(lines) == 2
    assert board.sheet_longest().get("cells") == ["9", "14", "7", "18"], "his longest catches, history only"
    assert "—" not in sheet.text(), "absent data is not drawn, never a dash"
    assert sheet.fits_width()
    board.go_back()
    assert not board.sheet_open()
    assert board.href() == before and board.surface() == "parlay", "Back closed the sheet, not the view"
    assert errors == []


def test_a_longest_reception_leg_sheet_draws_a_missing_catch_as_nothing(mount):
    """Build's ⓘ on a Longest reception line: a game with no catch logged (null) is an empty bar,
    never a crash, and no chance is printed for a line the model does not price."""
    sheet, errors = LegSheetPage.on(mount, "build", "underdog")
    sheet.blank_game("amonra-st-brown", "LONG", 0)
    sheet.open_line("Amon-Ra St. Brown", "LONG")
    assert sheet.bar_count() >= 1 and sheet.pct_count() == 0
    assert "null" not in sheet.text() and "NaN" not in sheet.text()
    assert errors == []


def test_a_receptions_sheet_with_usage_fits_one_phone_screen(mount):
    sheet, errors = LegSheetPage.on(mount, "parlay", "dk")
    sheet.open_line("Tee Higgins", "RECS")
    assert sheet.bar_count() == 10, "the last 10 of his 11 games"
    assert sheet.driver_cells() == 10, "targets under every bar"
    assert sheet.caption().startswith("Over 4.5 in ")
    assert sheet.tile_labels() == ["Targets/gm", "Target share", "Catch rate"]
    match = sheet.match_head()
    assert match.startswith("vs NYJ · allows 5% fewer WR receptions than average") and match.endswith("2 starters out")
    assert not sheet.match_names_visible(), "the names wait for a tap"
    assert "—" not in sheet.text(), "absent data is not drawn, never a dash"
    assert sheet.height() <= PHONE[1]
    assert not sheet.scrolls_inside()
    assert sheet.fits_width()
    assert errors == []


def test_on_a_desktop_the_sheet_is_a_centred_dialog(mount):
    """A desktop has no thumb at the bottom edge (David, 2026-10-03): the sheet sits mid-screen."""
    sheet, errors = LegSheetPage.on(mount, "parlay", "dk", size=(1280, 900))
    sheet.open_line("Tee Higgins", "RECS")
    box = sheet.settled_box()
    assert box[0] > 8 and abs((box[0] + box[1]) / 2 - 450) <= 2, box
    assert errors == []


def test_a_sheet_without_usage_draws_what_it_has(mount):
    """No `u` for St. Brown: no row under the bars, the tiles from this season's grid."""
    sheet, errors = LegSheetPage.on(mount, "parlay", "dk")
    sheet.open_line("Amon-Ra St. Brown", "REC")
    assert sheet.bar_count() == 4 and sheet.driver_cells() == 0
    # Yards/target needs his yards in the grid's weeks, and his fixture log ends in 2025: no tile.
    assert sheet.tile_labels() == ["Targets/gm", "aDOT"]
    assert sheet.match_count() == 0, "GB allows 2% more: noise, and no starter out, so no line"
    assert "—" not in sheet.text()
    assert errors == []


def test_builds_info_button_opens_the_sheet_and_the_row_still_adds(mount):
    build, errors = BuildPage.open(mount, size=PHONE)
    build.tap_first_line_evidence()
    assert build.sheet_open() and build.slip_size() == 0
    build.close_sheet()
    build.tap_first_call()
    assert build.slip_size() == 1
    assert errors == []
