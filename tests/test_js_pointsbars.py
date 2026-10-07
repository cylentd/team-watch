"""The fantasy-points bars on a Roster row and a card's back (David, 2026-10-07: no usage numbers there, they are
noisy and only spikes or sustained trends matter, which a glance cannot show). `pbModel` (data/pointsbars.js)
is what both draw: one slot per NFL week this season up to the page's week, each his fantasy points that
week (LIVE_GAMELOG `pts`, ff-jarvis's half-PPR, the scoring this week's projection is in), a week he did not
play an empty slot kept in its place, then this week's projection last, drawn hollow, on the same scale. The
scale is 0 to the largest of his bars and the projection, per player. The page computes no points."""
import pytest


@pytest.fixture(scope="module")
def pb(node_js):
    return node_js("data/pointsbars.js")


def rows(**by_week):
    return [{"wk": int(k[1:]), "pts": v} for k, v in by_week.items()]


def test_one_slot_per_completed_week_then_the_projection_last(pb):
    m = pb("pbModel", rows(w1=10.0, w2=20.0, w3=5.0, w4=15.0), 12.0, 5)
    assert [s["wk"] for s in m["slots"]] == [1, 2, 3, 4]
    assert [s["pts"] for s in m["slots"]] == [10.0, 20.0, 5.0, 15.0]
    assert m["proj"] == {"wk": 5, "pts": 12.0, "h": 0.6}


def test_the_scale_is_zero_to_the_largest_bar(pb):
    m = pb("pbModel", rows(w1=10.0, w2=20.0), 12.0, 3)
    assert [s["h"] for s in m["slots"]] == [0.5, 1.0] and m["max"] == 20.0


def test_a_projection_above_every_bar_sets_the_scale(pb):
    m = pb("pbModel", rows(w1=10.0, w2=5.0), 20.0, 3)
    assert [s["h"] for s in m["slots"]] == [0.5, 0.25] and m["proj"]["h"] == 1.0


def test_a_week_he_did_not_play_is_an_empty_slot_in_its_place(pb):
    m = pb("pbModel", rows(w1=10.0, w3=20.0), 10.0, 4)
    assert [s["wk"] for s in m["slots"]] == [1, 2, 3]
    assert (m["slots"][1]["pts"], m["slots"][1]["h"]) == (None, None)


def test_a_row_with_no_points_is_an_empty_slot_too(pb):
    m = pb("pbModel", [{"wk": 1, "pts": None}, {"wk": 2, "pts": 8.0}], 8.0, 3)
    assert m["slots"][0]["pts"] is None and m["slots"][1]["h"] == 1.0


def test_no_projection_leaves_an_empty_last_slot(pb):
    m = pb("pbModel", rows(w1=10.0), None, 3)
    assert m["proj"] == {"wk": 3, "pts": None, "h": None} and m["max"] == 10.0


def test_a_negative_week_keeps_its_points_and_draws_no_height(pb):
    m = pb("pbModel", rows(w1=-1.5, w2=10.0), 10.0, 3)
    assert (m["slots"][0]["pts"], m["slots"][0]["h"]) == (-1.5, 0.0)


def test_a_player_who_scored_nothing_has_flat_bars_not_nan(pb):
    m = pb("pbModel", rows(w1=0.0, w2=0.0), 0.0, 3)
    assert [s["h"] for s in m["slots"]] == [0.0, 0.0] and m["proj"]["h"] == 0.0


def test_nothing_to_draw_is_no_model(pb):
    assert pb("pbModel", [], None, 5) is None
    assert pb("pbModel", [{"wk": 1, "pts": None}], None, 2) is None


def test_week_one_has_no_past_slot_only_the_projection(pb):
    m = pb("pbModel", [], 14.0, 1)
    assert m["slots"] == [] and m["proj"]["h"] == 1.0


def test_a_limit_keeps_the_latest_weeks_and_rescales_to_them(pb):
    m = pb("pbModel", rows(w1=40.0, w2=10.0, w3=20.0, w4=5.0, w5=10.0), 10.0, 6, 4)
    assert [s["wk"] for s in m["slots"]] == [3, 4, 5], "three weeks and the projection fit four slots"
    assert [s["h"] for s in m["slots"]] == [1.0, 0.25, 0.5] and m["max"] == 20.0


def test_two_rows_for_one_week_count_once_the_first(pb):
    m = pb("pbModel", [{"wk": 1, "pts": 6.0}, {"wk": 1, "pts": 99.0}], 6.0, 2)
    assert [s["pts"] for s in m["slots"]] == [6.0]


@pytest.mark.parametrize("wk, text", [(1, "W1"), (9, "W9"), (10, "10"), (17, "17")])
def test_a_week_is_W_and_a_number_until_the_number_has_two_digits(pb, wk, text):
    assert pb("pbWeekText", wk) == text


@pytest.mark.parametrize("pts, text", [(18.6, "19"), (4.4, "4"), (0.0, "0"), (-1.6, "-2"), (None, "")])
def test_points_read_as_whole_numbers(pb, pts, text):
    assert pb("pbPtsText", pts) == text
