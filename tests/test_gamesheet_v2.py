"""The game sheet, v2 (2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV): full
screen on a phone, the players of mine in the game pinned under the scoreboard, three tabs under them,
and a follow star that outlives the sheet.
Component tests (Live mounted, tests/component.py; every locator in tests/pages/gamesheet.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.gamesheet import GameSheetPage


@pytest.mark.render
def test_a_phone_gets_the_game_as_a_centred_modal_with_three_tabs(mount):
    """U9, 2026-10-05: a margin on all four sides, not full screen (the first line of the module is the 2026-10-04 design)."""
    sheet, errors = GameSheetPage.on_live(mount)
    sheet.open()
    sheet.settle()                                              # the spring settles
    box = sheet.margins()
    assert all(m >= 15 for m in box), box                       # top, left, right, bottom
    assert abs(box[1] - box[2]) <= 1 and abs(box[0] - box[3]) <= 1, box   # centred both ways
    assert sheet.tab_names() == ["Plays", "Box score", "Top scorers"]
    # Box score is the default; each tab shows its own card and no other
    for tab in ("box", "plays", "top"):
        sheet.select_tab(tab)
        assert sheet.tab_selected(tab) == "true"
        assert sheet.visible_pane_cards() == 1 and sheet.visible_pane(tab) == 1
    assert sheet.visible_top_stars() == 5          # any scorer can be followed from here
    # the last tab is remembered through a close and a reopen, and the pinned block never scrolls away
    sheet.close_with_escape()
    sheet.reopen()
    assert sheet.tab_selected("top") == "true"
    assert sheet.visible_yours() == 1 and sheet.visible_tab_bar() == 1
    assert errors == []


@pytest.mark.render
def test_a_phone_sheet_scrolls_as_one_body_with_the_tabs_stuck_to_its_top(mount):
    sheet, errors = GameSheetPage.on_live(mount)
    sheet.open()
    sheet.follow_twelve_players()
    sheet.select_tab("plays")
    m = sheet.scroll_to_bottom()
    assert m["scrollers"] == ["gs-main"], m                  # one scroller, not the pinned block and the pane as well
    assert m["rows"] >= 12 and m["ylScroll"] == m["ylClient"], m   # every pinned row shows, none behind a scrollbar
    assert m["mainScrolls"] and m["scrolled"], m
    assert m["tabsTop"] == m["mainTop"] < m["before"], m     # the tab bar rode up and stuck to the top of the scroll
    assert errors == []


@pytest.mark.render
def test_opening_the_sheet_drops_the_follow_keys_of_other_weeks(mount):
    sheet, errors = GameSheetPage.on_live(mount)
    sheet.store_follow_keys()
    sheet.open()
    keys = sheet.follow_keys()
    assert keys == ["tw-follow", "tw-gs-follow.2"]
    assert errors == []


@pytest.mark.render
def test_yours_in_this_game_lists_my_players_and_leads_with_the_one_i_came_from(mount):
    sheet, errors = GameSheetPage.on_live(mount)
    sheet.open(slug="amonra-st-brown")
    # "mine" is the reader's: the seed picks yahoo and follows all three, so St. Brown and Goff (DET)
    # in the fixture's espn league (tests/test_live_mine.py: a reader with no team has none)
    assert sheet.yours_row_count() >= 2
    first = sheet.first_yours_row()
    assert "St. Brown" in first["text"] and "focus" in first["cls"]
    assert sheet.focus_row_count() == 1
    assert "Goff" in sheet.yours_text()
    assert sheet.yours_icon_count() >= 2          # the star is a drawn shape, not a glyph
    # no player of mine is in this game: a sentence says so
    sheet.show_a_game_without_my_players()
    assert sheet.yours_quiet_count() == 1
    assert errors == []


@pytest.mark.render
def test_a_star_follows_a_player_and_survives_closing_the_sheet(mount):
    sheet, errors = GameSheetPage.on_live(mount)
    sheet.open(slug="amonra-st-brown")
    assert sheet.followed() == {}
    assert sheet.focus_star_pressed() == "false"
    sheet.tap_focus_star()
    assert list(sheet.followed()) == ["7547"]          # tw-gs-follow.<week>, never tw-follow
    assert sheet.stored_team_choice() == '["yahoo","espn","ayo"]'   # the seed's, untouched
    sheet.close_with_escape()
    sheet.reopen()                                     # no slug now
    sheet.refill()
    assert sheet.yours_star_pressed("7547") == "true"
    # a player in the top scorers follows from there and joins the pinned block
    before = sheet.yours_row_count()
    sheet.select_tab("top")
    sid = sheet.follow_first_top_scorer()
    assert sid in sheet.followed()
    assert sheet.yours_follows(sid) == 1
    assert sheet.yours_row_count() >= before
    # tapping it again lets him go
    sheet.unfollow_top_scorer(sid)
    assert sid not in sheet.followed()
    assert errors == []


@pytest.mark.render
def test_the_scoreboard_clock_stands_in_until_espns_summary_loads(mount):
    sheet, errors = GameSheetPage.on_live(mount, states={"DET": "in_game", "BUF": "in_game"}, clock_of=("DET", "BUF"))
    sheet.open_unfilled()
    sheet.show_no_summary()
    assert "Q3 4:12" in sheet.scoreboard_middle_text()
    assert errors == []
