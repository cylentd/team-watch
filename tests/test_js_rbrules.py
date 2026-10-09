"""Running backs called by the books (ff-jarvis METHODOLOGY 12.86, 2026-10-05), in Node.

12.86: the books' implied points (`rank_pts`) order backs better than our projection (weekly Spearman
0.527 -> 0.551) but read about 0.5 high in level, so they decide a call between two priced backs and are
never shown. Ranks no longer orders by them, and the No line tag and the books note are gone (ledger #96,
2026-10-09: David chose our own rank)."""
import pytest


@pytest.fixture(scope="module")
def rb(node_js):
    return node_js("data/rbrules.js")


def lanes(*rows):
    return [{"pos": p, "pts": pts, "rp": rp} for p, pts, rp in rows]


def test_two_priced_backs_are_called_by_the_books_not_the_points(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("RB", 15.0, 16.6)), 0.5)
    assert v["flip"] is False and v["win"]["pts"] == 15.0 and v["books"] is True and v["moved"] is True


def test_the_gap_shown_is_in_points_never_the_books_number(rb):
    v = rb("rbVerdict", lanes(("RB", 15.0, 16.6), ("RB", 14.0, 15.0)), 0.5)
    assert v["win"]["pts"] == 15.0 and v["gap"] == 1.0, "points: 15.0 over 14.0, not the books' 1.6"
    assert v["moved"] is False, "the books and the points agree: nothing to explain"


def test_the_books_decide_a_coin_flip_too(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("RB", 15.0, 15.7)), 0.5)
    assert v["flip"] is True and v["moved"] is True, "points say start, the books say a tie"


def test_one_back_unpriced_means_points_decide(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("RB", 15.0, None)), 0.5)
    assert v["books"] is False and v["win"]["pts"] == 16.2 and v["gap"] == 1.2 and v["moved"] is False


def test_a_back_against_another_position_is_decided_by_points(rb):
    v = rb("rbVerdict", lanes(("RB", 16.2, 15.4), ("WR", 15.0, None)), 0.5)
    assert v["books"] is False and v["win"]["pts"] == 16.2
    v = rb("rbVerdict", lanes(("RB", 14.0, 20.0), ("WR", 15.0, None)), 0.5)
    assert v["win"]["pts"] == 15.0, "an RB's books number never outranks a receiver's points"


def test_three_backs_all_priced_use_the_books_for_all_three(rb):
    v = rb("rbVerdict", lanes(("RB", 14.0, 16.0), ("RB", 15.0, 15.0), ("RB", 16.0, 14.0)), 0.5)
    assert v["win"]["pts"] == 14.0 and v["moved"] is True


def test_a_close_call_inside_half_a_point_is_a_coin_flip_as_before(rb):
    v = rb("rbVerdict", lanes(("WR", 15.0, None), ("WR", 14.6, None)), 0.5)
    assert v["flip"] is True and v["gap"] == 0.4 and v["books"] is False and v["moved"] is False


def test_a_player_with_no_points_is_left_out_and_one_player_is_no_verdict(rb):
    assert rb("rbVerdict", lanes(("RB", None, 9.0), ("RB", 15.0, 16.0)), 0.5) is None


def test_a_tier_names_its_highest_and_lowest_points_not_its_first_and_last_row(rb):
    assert rb("rbTierSpan", [{"pts": 15.0}, {"pts": 16.2}, {"pts": 15.6}]) == {"hi": "16.2", "lo": "15.0"}
