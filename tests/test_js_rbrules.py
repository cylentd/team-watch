"""The Start/Sit call and a tier's range (data/rbrules.js), in Node.

Our own points decide every call, running backs too (ledger #94, 2026-10-09; VISION 2026-10-08, David: "the rank
was always supposed to be our own ranking system"). The books' implied points (`rank_pts`, ff-jarvis METHODOLOGY
12.86) called two priced backs from 2026-10-05 until then; a lane's books number is now ignored. Ranks orders by
`pts` too, and the No line tag and the books note are gone (ledger #96)."""
import pytest


@pytest.fixture(scope="module")
def rb(node_js):
    return node_js("data/rbrules.js")


def lanes(*rows):
    return [{"pos": p, "pts": pts, "rp": rp} for p, pts, rp in rows]


def test_two_priced_backs_are_called_by_our_points_not_the_books(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("RB", 15.0, 16.6)), 0.5)
    assert v == {"flip": False, "win": {"pos": "RB", "pts": 16.2, "rp": 15.4}, "gap": 1.2}


def test_the_gap_shown_is_in_points_never_the_books_number(rb):
    v = rb("rbVerdict", lanes(("RB", 15.0, 16.6), ("RB", 14.0, 15.0)), 0.5)
    assert v["win"]["pts"] == 15.0 and v["gap"] == 1.0, "points: 15.0 over 14.0, not the books' 1.6"


def test_the_books_never_turn_a_start_into_a_coin_flip(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("RB", 15.0, 15.7)), 0.5)
    assert v["flip"] is False and v["win"]["pts"] == 16.2, "points say start; the books' near-tie changes nothing"


def test_one_back_unpriced_is_called_the_same_way(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("RB", 15.0, None)), 0.5)
    assert v["win"]["pts"] == 16.2 and v["gap"] == 1.2


def test_a_back_against_another_position_is_decided_by_points(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("WR", 15.0, None)), 0.5)
    assert v["win"]["pts"] == 16.2
    v = rb("rbVerdict", lanes(("RB", 14.0, 20.0), ("WR", 15.0, None)), 0.5)
    assert v["win"]["pts"] == 15.0, "an RB's books number never outranks a receiver's points"


def test_three_backs_all_priced_are_called_by_points(rb):
    v = rb("rbVerdict", lanes(("RB", 14.0, 16.0), ("RB", 15.0, 15.0), ("RB", 16.0, 14.0)), 0.5)
    assert v["win"]["pts"] == 16.0 and v["gap"] == 1.0


def test_a_close_call_inside_half_a_point_is_a_coin_flip_as_before(rb):
    v = rb("rbVerdict", lanes(("WR", 15.0, None), ("WR", 14.6, None)), 0.5)
    assert v == {"flip": True, "gap": 0.4}


def test_a_player_with_no_points_is_left_out_and_one_player_is_no_verdict(rb):
    assert rb("rbVerdict", lanes(("RB", None, 9.0), ("RB", 15.0, 16.0)), 0.5) is None


def test_a_tier_names_its_highest_and_lowest_points_not_its_first_and_last_row(rb):
    assert rb("rbTierSpan", [{"pts": 15.0}, {"pts": 16.2}, {"pts": 15.6}]) == {"hi": "16.2", "lo": "15.0"}
