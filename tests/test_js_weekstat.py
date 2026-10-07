"""The stat line under a name on the Roster's Week plays card (David, 2026-10-07: "7-25-0" reads as a date).
`wsLine` (data/weekstat.js) says what a week's box score row holds in words: yards with their unit, the
biggest kind first ("25 rush yds · 68 rec yds"), touchdowns of every kind summed ("· 2 TD") only when there
is one. No counts (carries, catches, targets, attempts), no turnovers. When the line is wider than the card,
the smaller yardage kinds go first and the touchdowns stay; the line is never cut with an ellipsis.
`fit` is a width budget in characters here; in the browser it is a function that measures the card."""
import pytest


@pytest.fixture(scope="module")
def ws(node_js):
    return node_js("data/weekstat.js")


def test_a_back_with_rush_and_receiving_yards_and_a_touchdown_reads_biggest_first(ws):
    row = {"car": 8, "rush_yds": 68, "rush_td": 1, "rec": 3, "rec_yds": 25, "rec_td": 0, "tgt": 4}
    assert ws("wsLine", "RB", row) == "68 rush yds · 25 rec yds · 1 TD"


def test_the_bigger_kind_leads_whichever_it_is(ws):
    row = {"car": 7, "rush_yds": 25, "rush_td": 0, "rec": 5, "rec_yds": 68, "rec_td": 0, "tgt": 6}
    assert ws("wsLine", "RB", row) == "68 rec yds · 25 rush yds"


def test_a_receiver_with_no_touchdown_has_no_td_text(ws):
    row = {"rec": 6, "rec_yds": 102, "rec_td": 0, "tgt": 8}
    assert ws("wsLine", "WR", row) == "102 rec yds"


def test_a_passer_with_two_touchdowns_says_pass_yds_and_2_td(ws):
    row = {"pass_yds": 288, "pass_td": 2, "rush_yds": 0, "rush_td": 0}
    assert ws("wsLine", "QB", row) == "288 pass yds · 2 TD"


def test_touchdowns_of_every_kind_are_summed(ws):
    row = {"pass_yds": 250, "pass_td": 1, "rush_yds": 31, "rush_td": 1}
    assert ws("wsLine", "QB", row) == "250 pass yds · 31 rush yds · 2 TD"


def test_no_yards_and_one_touchdown_is_just_the_touchdown(ws):
    assert ws("wsLine", "TE", {"rec": 1, "rec_yds": 0, "rec_td": 1, "tgt": 2}) == "1 TD"


def test_an_all_zero_week_is_an_empty_line(ws):
    assert ws("wsLine", "WR", {"rec": 0, "rec_yds": 0, "rec_td": 0, "tgt": 3}) == ""
    assert ws("wsLine", "WR", {}) == ""


def test_negative_yards_are_left_out(ws):
    assert ws("wsLine", "QB", {"pass_yds": 190, "pass_td": 0, "rush_yds": -3, "rush_td": 0}) == "190 pass yds"


def test_counts_and_turnovers_never_appear(ws):
    row = {"car": 20, "rush_yds": 90, "rush_td": 0, "rec": 4, "rec_yds": 30, "rec_td": 0, "tgt": 9,
           "pass_att": 33, "pass_int": 2, "fum_lost": 1}
    got = ws("wsLine", "RB", row)
    assert got == "90 rush yds · 30 rec yds"
    assert not any(w in got for w in ("tgt", "car", "int", "fum"))


ROW = {"rush_yds": 81, "rush_td": 1, "rec": 3, "rec_yds": 39, "rec_td": 0}
FULL = "81 rush yds · 39 rec yds · 1 TD"


def test_the_candidates_run_from_the_whole_line_to_the_touchdowns_alone(ws):
    assert ws("wsCandidates", ws("wsParts", "RB", ROW)) == [FULL, "81 rush yds · 1 TD", "1 TD"]


def test_a_line_that_fits_is_kept_whole(ws):
    assert ws("wsLine", "RB", ROW, len(FULL)) == FULL


def test_one_character_short_drops_the_smaller_yardage_kind_and_keeps_the_td(ws):
    assert ws("wsLine", "RB", ROW, len(FULL) - 1) == "81 rush yds · 1 TD"


def test_a_budget_under_the_biggest_kind_and_td_leaves_the_td_alone(ws):
    assert ws("wsLine", "RB", ROW, len("81 rush yds · 1 TD") - 1) == "1 TD"


def test_with_three_kinds_the_smallest_goes_first_then_the_next(ws):
    row = {"pass_yds": 250, "pass_td": 0, "rush_yds": 40, "rush_td": 0, "rec_yds": 12, "rec_td": 0}
    assert ws("wsCandidates", ws("wsParts", "QB", row)) == [
        "250 pass yds · 40 rush yds · 12 rec yds", "250 pass yds · 40 rush yds", "250 pass yds"]
    assert ws("wsLine", "QB", row, 26) == "250 pass yds · 40 rush yds"
    assert ws("wsLine", "QB", row, 20) == "250 pass yds"


def test_without_a_touchdown_the_biggest_kind_stays_even_when_it_does_not_fit(ws):
    assert ws("wsLine", "WR", {"rec_yds": 102, "rec_td": 0}, 3) == "102 rec yds"


def test_no_budget_means_the_whole_line(ws):
    assert ws("wsLine", "RB", ROW) == FULL
