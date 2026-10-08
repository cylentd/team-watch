"""Slips by kickoff window, one pick per line (David 2026-10-08, ledger #33; storyboard "Slips" B + C).

The fixture's Claude calls (tests/fixtures/README.md): Brown RUSH 65.5 Higher, the model Higher Very confident
(agree: our pick); Burrow PASS 245.5 Higher, the model Lower Confident (split); Kittle REC 45.5, the model has no
pick (neither). Which lines agree is Node-tested (test_js_ourpicks.py); this file holds the drawing and the taps."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.slips import SlipsPage
from wording import words

pytestmark = pytest.mark.req("Parlay and DFS", ac="Slips by kickoff window, one pick per line")

GRADED = {"through_week": 4, "agree": {"w": 7, "l": 5, "push": 1, "void": 0}, "alone": {"w": 8, "l": 9, "push": 0, "void": 2}}


@pytest.fixture
def morning(mount):
    s, errors = SlipsPage.open(mount, "morning")
    yield s
    assert errors == []


def test_a_window_is_headed_and_its_games_lead_with_our_pick(morning):
    assert len(morning.window_names()) == 1, "one window: the tab chose one"
    picks = morning.picks()
    assert picks[0]["name"] == "Chase Brown"
    assert picks[0]["side"] == f"{words('slips.side.higher')} {words('matchups.stat.rush')} 65.5"
    assert picks[0]["tier"] == "72% " + words("slips.tier.very")
    assert "Joe Burrow" not in [p["name"] for p in picks], "a split shows no side"
    assert morning.claude_badges() == 0, "no C badge and no Claude-only reason"
    assert morning.fits()


def test_the_split_fold_holds_the_split_line_with_no_side(morning):
    assert morning.split_label().startswith(words("slips.split.title").replace("{n}", "1"))
    assert morning.split_lines() == []
    morning.toggle_split()
    lines = morning.split_lines()
    assert len(lines) == 1 and "Joe Burrow" in lines[0] and "245.5" in lines[0]
    assert morning.split_sides_drawn() == 0


def test_a_game_opens_in_place_to_its_players_and_closes(morning):
    game = morning.game_titles()[0]
    assert morning.player_row_count() == 0, "closed games draw no player rows"
    morning.toggle_game(game)
    assert morning.expanded(game) == "true" and morning.player_row_count() > 0
    morning.toggle_game(game)
    assert morning.expanded(game) == "false" and morning.player_row_count() == 0


def test_the_plus_puts_our_side_on_the_slip_and_again_takes_it_off(morning):
    morning.add_first_pick()
    assert morning.slip() == [["Chase Brown", "RUSH", "higher"]] and morning.add_pressed() == "true"
    morning.add_first_pick()
    assert morning.slip() == []


def test_a_game_claude_has_not_called_says_when_its_picks_come(morning):
    morning.forget_claude()
    assert morning.picks() == []
    assert set(morning.game_counts()) == {words("slips.game.pending")}


def test_the_record_is_one_our_picks_line_with_the_unproven_note(morning):
    assert words("slips.record.ours") in morning.record_text()
    assert words("slips.record.from").replace("{n}", "5") in morning.record_text()
    assert morning.record_note() == words("slips.record.note")
    morning.grade_ours(GRADED)
    assert "58%" in morning.record_text() and "7-5" in morning.record_text()
    assert "47%" not in morning.record_text(), "no alone row"


def test_the_sheet_outlines_our_pick_and_names_a_split(morning):
    morning.open_sheet("chase-brown")
    brown = morning.sheet_line(words("matchups.stat.rush").capitalize())
    assert brown["pick"] == [words("slips.side.higher")]
    assert brown["named"] == [words("slips.our.name").replace("{side}", words("slips.side.higher"))]
    morning.close_sheet()
    morning.open_sheet("joe-burrow")
    burrow = morning.sheet_line(words("matchups.stat.pass").capitalize())
    assert burrow["pick"] == [] and burrow["under"] == words("slips.our.split")
    morning.close_sheet()
    assert morning.claude_badges() == 0
