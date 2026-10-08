"""Live's TDs tab (2026-10-04): who has scored (a rushing or receiving TD, from the league-wide
`lead`) and who of Parlay's top TD chances is still alive, with his game's state. Since 2026-10-05 a
switch (Feed, By game) and four chips (Mine, Pass, Rush, Rec) narrow it.
Component tests (Live mounted, tests/component.py; every locator in tests/pages/live_tds.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.live_tds import LiveTdsPage
from wording import words


@pytest.mark.render
def test_scored_lists_rushers_and_receivers_not_passers_and_the_board_keeps_who_is_alive(mount):
    live, errors = LiveTdsPage.mounted(mount)
    planted = live.plant_scorers()
    assert planted["n"] >= 3, "the fixtures carry too few TD lines for this test"
    club = planted["a"][1]
    scored, alive = live.rows_at(club, "in")
    names = [r["who"] for r in scored]
    assert names[0] == "T. Rusher" and scored[0]["line"] == "2 rush TD"          # most TDs first
    assert any(r["line"] == "1 rec TD" for r in scored)                            # a receiver counts
    assert not any("Passer" in n or "Nobody" in n for n in names)                  # a passing TD is no anytime TD
    # a board player who scored is in Scored and out of Still alive
    b_name = planted["b"][0].split(" ", 1)
    assert not any(r["who"].startswith(b_name[0][0] + ".") and r["who"].endswith(b_name[1]) for r in alive)
    # the top of the board, his game on and no TD: lime state with the game clock
    top = next(r for r in alive if r["who"].startswith(planted["a"][0][0] + "."))
    assert top["cls"] == "live" and top["clock"] == "Q3 4:12" and top["line"] == words("live.tds.none")
    # his game over with no TD: red, and at the bottom (a club-mate's row sinks with him)
    scored, alive = live.rows_at(club, "post")
    assert alive[-1]["cls"] == "missed" and alive[-1]["clock"] == "Final" and alive[-1]["line"] == "Missed"
    kinds = [r["cls"] == "missed" for r in alive]
    assert kinds == sorted(kinds)                                                  # missed rows are the tail
    # a scorer whose game is over is no miss: no `missed` class, a green TD line, a plain grey Final, a bright name
    colours = live.colours_at([club, "SF", planted["b"][1]])
    assert colours["scoredCls"] and not any("missed" in c for c in colours["scoredCls"])
    assert colours["line"] == colours["up"] and colours["clock"] == colours["grey"]
    assert colours["name"] != colours["grey"]
    assert colours["missLine"] == colours["down"]                                  # only a Still-alive miss is red
    # before any kickoff everyone is later, and Scored says so
    live.drop_lead()
    scored, alive = live.rows_at("ZZZ", "pre")
    assert scored == [] and alive and all(r["cls"] == "later" for r in alive)
    assert live.empty_text_built() == words("live.tds.noneYet")
    assert errors == []


@pytest.mark.render
def test_without_stats_the_tab_says_it_is_reading_and_a_row_opens_a_profile(mount):
    live, errors = LiveTdsPage.mounted(mount)
    live.plant_scorers()
    # a reply without `lead` (an older edge copy) is not "no touchdowns yet": the tab is still reading
    live.drop_lead_from_reply()
    assert live.rows_and_text_built() == [0, words("live.tds.loading")]
    live.drop_stats()
    assert live.rows_and_text_built() == [0, words("live.tds.loading")]
    live.plant_scorers()
    opened = live.profile_from_first_row_built()
    assert opened["n"] == "Test Rusher" and opened["slug"] == "test-rusher" and opened["pos"] == "RB"
    assert errors == []


def test_the_switch_keeps_the_feed_and_by_game_is_one_card_per_game(mount):
    live, mine, errors = LiveTdsPage.open_games_day(mount)
    assert live.by_game_pressed() == "false"                                         # the list stays the default
    assert live.card_count() == 2 and live.game_card_count() == 0
    live.toggle_by_game()
    assert live.by_game_pressed() == "true"
    cards = live.game_cards()
    # the game on now first, then the latest kickoff first; the header is the clubs, the score and the clock
    assert [c["head"] for c in cards] == ["KC 17 SF 24 Q3 4:12", "BUF 10 MIA 27 Final", "MIN 20 DET 13 Final"]
    assert [len(c["rows"]) for c in cards] == [3, 1, 1]
    assert cards[0]["rows"][0] == "T. Rusher" and "T. Passer" not in cards[0]["rows"]       # a passing TD is no anytime TD
    # a game's rows hold neither the clock nor the club; one card per subject, never a card in a card
    assert live.clock_or_club_in_game_cards() == 0
    assert live.cards_in_game_cards() == 0
    assert live.buttons_in_buttons_in_game_cards() == 0
    # the header opens that game's sheet
    live.tap_first_game_header()
    live.wait_for_game_sheet()
    live.press_escape()
    live.wait_for_game_sheet_closed()
    # the view is remembered; a store that will not answer still switches
    assert live.stored_mode() == "game"
    live.block_storage()
    live.toggle_by_game()
    assert live.game_card_count() == 0 and live.by_game_pressed() == "false"
    assert errors == []


def test_chips_narrow_both_views_and_an_empty_result_is_one_line(mount):
    live, mine, errors = LiveTdsPage.open_games_day(mount)
    chip = live.toggle_chip
    rows = live.rows
    alive = live.alive_card_count
    assert alive() == 1 and "T. Passer" not in rows()
    # a TD type: only that type, and Still alive (no TD type) steps aside
    chip("rush")
    assert set(rows()) == {"T. Rusher", "M. Runner", mine} and alive() == 0
    assert live.line_texts().count("2 rush TD") == 1
    chip("rush")
    chip("pass")                       # the only way a passer appears
    assert rows() == ["T. Passer"] and live.only_line_text() == "3 pass TD"
    chip("rec")
    assert set(rows()) == {"T. Passer", "T. Catcher", "D. Catcher"}
    chip("pass"); chip("rec")
    # Mine: only the reader's players, in both views; Still alive narrows to theirs
    chip("mine")
    assert len(rows()) >= 1 and "T. Rusher" not in rows() and live.chip_pressed("mine") == "true"
    live.toggle_by_game()
    cards = live.game_cards()
    assert len(cards) == 1 and cards[0]["rows"] == [mine]
    # nothing matches: one line, in either view
    chip("pass")
    assert live.empty_count() == 1 and live.empty_text() == words("live.tds.noMatch")
    live.toggle_by_game()
    assert live.empty_count() == 1 and live.row_count() == 0
    # filters clear on a visit; the view stays (Feed here, so By game is not pressed either)
    live.clear_filters()
    assert live.pressed_control_count() == 0
    assert errors == []


def test_mine_is_the_readers_pick_and_with_none_it_says_to_pick(mount):
    live, mine, errors = LiveTdsPage.open_games_day(mount)
    live.forget_team_and_filter_mine()
    assert live.empty_text() == words("live.tds.pickTeam")
    assert errors == []


def test_a_phone_holds_the_controls_in_one_row_and_nothing_scrolls_sideways(mount):
    live, mine, errors = LiveTdsPage.open_games_day(mount)
    live.toggle_by_game()
    m = live.controls_layout()
    assert m["w"] <= m["vw"]                                                  # the page never scrolls sideways
    assert m["n"] == 5 and m["last"] and m["tops"] == 1                       # Mine, Pass, Rush, Rec, By game: one line
    assert m["chips"]["height"] <= m["tallest"] + 1 and m["shortest"] >= 40
    assert m["sep"] == 1                                                      # one divider before By game
    assert errors == []
