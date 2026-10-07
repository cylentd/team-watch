"""Live's sideways swipes. In the game sheet a swipe walks the games in the NFL tab's order, and a step
row names the game on each side (2026-10-04). On My league a swipe does nothing since 2026-10-05: the
league is the reader's team's, and the league swipe and chips went with Live's own league setting.
Component tests: Live mounted on the week 2 fixture (tests/fixtures/gameday.json), tests/component.py;
every locator is in tests/pages/live_tabs.py and tests/pages/gamesheet.py."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.gamesheet import GameSheetPage
from pages.live_tabs import PHONE, LiveTabsPage

pytestmark = pytest.mark.render


@pytest.fixture
def live(mount):
    """Live on a phone, DET and SEA in game, the reader the seed picks: (LiveTabsPage, page errors)."""
    return LiveTabsPage.open_league(mount, size=PHONE, team=None, states={"DET": "in_game", "SEA": "in_game"})


def test_a_swipe_on_my_league_leaves_the_league_alone(live):
    league, errors = live
    assert league.league_count() >= 2, "the fixture needs two leagues"
    before = league.league_and_mine()
    for dx in (-120, 120):
        league.swipe_board(dx)
        assert league.league_and_mine() == before
    assert "turn-" not in league.board_class()
    assert errors == []


def test_the_sheet_walks_the_games_in_the_order_the_games_tab_lists_them(live):
    league, errors = live
    league.open_tab("games")
    tiles = league.tile_games()
    assert len(tiles) >= 3, "the fixture needs three games"
    name = lambda g: f"{g[1]} @ {g[2]}"
    league.tap_tile(1)
    league.wait_for_game_sheet()
    sheet = GameSheetPage(league.page)
    assert sheet.step_names() == [name(tiles[0]), name(tiles[2])]
    # a tap on the next one opens it, and the step row moves with it
    sheet.tap_step("next")
    assert sheet.sides() == tiles[2][1:]
    assert sheet.step_name("prev") == name(tiles[1])
    # a swipe right goes back the same way
    sheet.swipe(120)
    assert sheet.sides() == tiles[1][1:]
    # the first game has nothing before it: that side is empty and a swipe right stays put
    sheet.tap_step("prev")
    assert sheet.step_count("prev") == 0 and sheet.step_count("next") == 1
    sheet.swipe(120)
    assert sheet.sides() == tiles[0][1:]
    assert errors == []
