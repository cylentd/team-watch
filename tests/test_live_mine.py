"""Whose team is "mine" on Live (2026-10-04, David: "Make sure that the site registers the roster(s)
that the user picks as the 'yours' or 'mine'. I don't want it to default to my personal rosters.").

The page is public and David's three teams are three of ~36. A reader's team is the one they picked
(tw-team), else one they follow (tw-follow) that plays in the league on screen (live.js gdMine), and
since 2026-10-05 that team's league is Live's league; with neither, My league asks whose game it is
and the reader picks right there (mine.js gdWhoHTML). The seed
of every other test picks David's Yahoo team and follows his three, so this file mounts Live as a first
visit (pages/live_mine.py `open_bare`, 2026-10-06: component tests, every locator in that page object).
"""
import pathlib
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.gamesheet import GameSheetPage
from pages.live_mine import MATE, LiveMinePage

pytestmark = pytest.mark.render

SRC = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"


def test_a_first_visit_has_no_team_of_its_own_on_live(mount):
    live, errors = LiveMinePage.open_bare(mount)
    assert live.my_team_and_follows() == [None, []]
    # My league asks whose game it is, one card listing every league: no score, no lineups, no "you"
    assert live.who_title() == "Whose game are you watching?"
    assert live.who_league_count() == live.league_count()
    assert live.my_league_parts_count() == 0
    # the NFL tab counts none as yours; the sheet marks none
    live.open_tab("games")
    assert live.tile_mark_count() == 0
    live.set_tab("league")
    live.open_game_of("DET")
    sheet = GameSheetPage(live.page)
    assert sheet.yours_row_count() == 0 and sheet.yours_quiet_count() == 1
    live.press_escape()
    assert errors == []


def test_the_reader_picks_their_team_inside_live_and_stays_there(mount):
    live, errors = LiveMinePage.open_bare(mount)
    # a league lists its teams in the same spot; the back link returns to the leagues
    live.pick_league("espn")
    assert live.who_team_count() >= 2 and live.who_league_count() == 0
    live.tap_who_back()
    assert live.who_league_count() == live.league_count()
    live.pick_league("espn")
    live.pick_in_card(MATE)
    # saved as the team switch saves it, and the reader's matchup is drawn where they are
    assert live.picked_view_and_hash() == [MATE, "live", "#live"]
    assert live.who_card_count() == 0 and live.my_chip_count() == 1
    assert "TeamMinh" in live.my_side_text()
    assert errors == []


def test_the_readers_pick_becomes_the_left_side_with_up_or_down(mount):
    live, errors = LiveMinePage.open_bare(mount, team=MATE)
    assert live.my_team_and_follows() == [MATE, [MATE]]    # the pick is followed until they star more
    assert live.who_card_count() == 0
    assert "TeamMinh" in live.left_side_text() and "mine" in live.left_side_class()      # not David's team, who is its opponent
    assert live.right_side_text().startswith("Purdy Big in Japan")
    assert re.match(r"^(UP|DOWN) \d+\.\d$", live.lead_text())
    assert re.match(r"^League median \d+\.\d · you [+−]\d+\.\d$", live.median_line())
    # his lineup is the one mirrored on the left, benches included
    assert live.left_half_count("Smith-Njigba") == 1
    assert live.right_half_count("St. Brown") == 1
    # the Games tab and the sheet count the picked team's players: Smith-Njigba (SEA) is his, St. Brown (DET) David's
    live.open_tab("games")
    assert live.mine_tile_yours_count() >= 1
    live.set_tab("league")
    live.open_game_of("SEA")
    sheet = GameSheetPage(live.page)
    assert "Smith-Njigba" in sheet.yours_text()
    live.press_escape()
    live.wait_for_game_sheet_closed()
    live.open_game_of("DET")
    yours = sheet.yours_text()                 # TeamMinh's Lions D/ST, not David's St. Brown
    assert "Lions" in yours and "St. Brown" not in yours
    live.press_escape()
    assert errors == []


def test_the_picked_team_decides_the_league_and_a_followed_one_only_without_a_pick(mount):
    live, errors = LiveMinePage.open_bare(mount, team=MATE)
    # the pick plays in ESPN; following a Yahoo team does not move Live off it
    live.follow_and_repaint(["yahoo"])
    assert live.league_key() == "espn" and "TeamMinh" in live.my_side_text()
    # with no pick, the first followed team that plays here decides
    live.forget_pick_and_repaint()
    assert live.picks_follows_and_league() == [None, ["yahoo"], "yahoo"]
    assert live.who_card_count() == 0 and live.my_side_count() == 1
    assert errors == []


def test_nothing_followed_is_nothing_not_davids_teams(mount):
    live, errors = LiveMinePage.open_bare(mount)
    assert live.follows() == []
    live.store_team("yahoo")
    assert live.follows() == ["yahoo"]                # the picked team, and only it
    live.toggle_follow("espn")
    assert live.follows() == ["yahoo", "espn"]
    assert errors == []


def test_the_switch_still_lets_a_reader_with_nothing_followed_pick(mount):
    live, errors = LiveMinePage.open_bare(mount, team="yahoo", follow=[])
    # David's Yahoo team is picked and nothing is followed: the header bar's team switch (a phone's; the
    # score head shows the plain name there) opens on that team's league
    live.open_header_switch()
    assert live.header_team_count("yahoo") == 1        # the league's teams, each pickable
    live.tap_header_back()
    assert live.header_empty_count() == 1                      # nothing followed: the menu says so
    assert live.header_league_count() >= 1                     # and every league is one tap away
    live.open_header_league("espn")
    # The drill-in redraws the menu: wait for the league's own list, then take a team that is on screen
    live.pick_first_header_team("espn-")
    assert live.stored_team() != "yahoo"
    assert live.view_and_league() == ["live", "espn"]     # the reader stays on Live
    assert errors == []


def test_no_live_view_reads_davids_team_as_the_readers():
    """lg.me stays in the data (the build and its tests use it); the Live files go through gdMine."""
    for path in (SRC / "surface" / "live").glob("*.js"):
        assert not re.search(r"\.me\b", path.read_text(encoding="utf-8")), path.name
