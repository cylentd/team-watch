"""Live's game as a centred modal, the names in its plays, and the ball on a live card (U9, 2026-10-05).

David: "In This Week > Live > Games why cant you do a centered modal? Also, the game log should bold the
players name. The live scoreboard should show the direction of the ball or team and the redzone."

The logic (which names, which side has the ball, the red zone) is test_js_gamesituation.py, in Node. This
file is layout and taps only: the margins on four sides, every way to close it, a bold name per play line,
and the ball and red-zone mark on the Games tab's live tile.
Component tests (Live mounted, tests/component.py; every locator in tests/pages/gamesheet.py and live_tabs.py, live_ball.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.gamesheet import GameSheetPage
from pages.live_ball import LiveBallPage
from pages.live_tabs import LiveTabsPage


def open_game(mount, size):
    """Live at `size` on the planted week 2, the game DET at BUF open and settled, with ESPN's summary and Sleeper's box."""
    sheet, errors = GameSheetPage.on_live(mount, size=size)
    sheet.open()
    sheet.settle()
    return sheet, errors


@pytest.mark.render
@pytest.mark.parametrize("size", [(390, 844), (1280, 800)], ids=["phone", "desktop"])
def test_the_game_opens_centred_with_a_margin_on_all_four_sides(mount, size):
    sheet, errors = open_game(mount, size)
    e = sheet.edges()
    assert min(e["top"], e["left"], e["right"], e["bottom"]) >= 15, e
    assert abs(e["left"] - e["right"]) <= 1 and abs(e["top"] - e["bottom"]) <= 1, e      # centred both ways
    assert e["width"] <= 1040, e                                                         # a desktop max-width
    assert sheet.width() == e["width"]
    assert errors == []


@pytest.mark.render
def test_the_game_closes_by_the_x_a_tap_on_the_scrim_and_back(mount):
    sheet, errors = GameSheetPage.on_live(mount, size=(390, 844))
    left_open = {}
    for how in ("x", "scrim", "back"):
        sheet.open()
        sheet.settle()
        {"x": sheet.close_with_x, "scrim": sheet.close_with_scrim, "back": sheet.close_with_back}[how]()
        left_open[how] = (sheet.current_game(), sheet.layer_count())
    assert left_open == {"x": (None, 0), "scrim": (None, 0), "back": (None, 0)}
    assert errors == []


@pytest.mark.render
def test_the_phone_closes_the_game_from_a_48px_bar_at_the_bottom(mount):
    sheet, errors = GameSheetPage.on_live(mount, size=(360, 780))
    live = LiveTabsPage(sheet.page)
    live.open_tab("games")
    live.tap_tile(1)
    sheet.wait_for_open()
    sheet.settle()
    got = sheet.close_bar()
    assert got["closeBottomGap"] <= 80 and got["inSheet"], got
    assert got["h"] == [48, 48, 48] and got["left"] and got["right"], got
    # the bar stays put while the body scrolls
    sheet.scroll_body_to(400)
    assert sheet.close_bar_bottom_gap() == got["closeBottomGap"]
    sheet.tap_close_bar()
    assert sheet.current_game() is None and sheet.layer_count() == 0
    assert live.tile_is_visible(1)                                    # still on the Games tab, the tile in place
    assert live.focus_is_on_tile(1)                                   # focus came home
    assert errors == []


@pytest.mark.render
def test_every_name_in_a_play_line_is_bold(mount):
    sheet, errors = open_game(mount, (390, 844))
    sheet.select_tab("plays")
    sheet.open_all_drives()
    got = sheet.play_names()
    assert got["lines"] > 30 and got["names"] > 30, got
    assert got["missed"] == [] and got["bold"] == got["names"], got
    assert int(got["weight"]) >= 700, got
    assert errors == []


@pytest.mark.render
def test_a_live_card_shows_who_has_the_ball_and_the_red_zone(mount):
    live, errors = LiveBallPage.open_league(mount, size=(390, 844), team="yahoo", states={"DET": "in_game", "SEA": "in_game"})
    live.open_tab("games")
    assert live.in_tile_ball_count() == 0 and live.in_tile_sit_count() == 0     # ESPN sent nothing: nothing guessed
    live.plant_ball_in_the_red_zone()
    assert live.in_tile_ball_count() == 1
    # the ball sits beside the club that has it: SEA, the second row
    assert live.in_tile_ball_by_club() == [0, 1]
    assert live.in_tile_ball_label() == "SEA has the ball"
    assert live.in_tile_down_text() == "3rd & 4"
    sit_box, rz_box = live.in_tile_down_and_zone_boxes()
    assert live.in_tile_down_fits()                                  # the down is never cut off
    assert sit_box["x"] + sit_box["width"] <= rz_box["x"] + 1
    assert live.in_tile_zone_text().lower() == "red zone"
    box = live.in_tile_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 390
    # outside the 20 the tag goes and the ball stays
    live.plant_ball_outside_the_red_zone()
    assert live.in_tile_zone_count() == 0 and live.in_tile_ball_count() == 1
    assert errors == []
