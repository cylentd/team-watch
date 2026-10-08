"""Running backs ordered by the books (ff-jarvis METHODOLOGY 12.86 and 12.87, 2026-10-05), in Node.

12.86: the books' implied points (`rank_pts`) order backs better than our projection (weekly Spearman
0.527 -> 0.551) but read about 0.5 high in level, so they order and are never shown. Only running
backs were tested, against running backs: FLEX and every other position order by `pts`.
12.87: a back the books leave unpriced beside a priced teammate scores about a third of his projection,
so ff-jarvis cuts his `pts` to 30% and flags him `unlined_backup`; the page tags him."""
import pytest

from wording import words


@pytest.fixture(scope="module")
def rb(node_js):
    return node_js("data/rbrules.js")


def test_a_back_with_the_books_number_is_ordered_by_it(rb):
    assert rb("rbOrderPts", {"pos": "RB", "pts": 15.0, "rank_pts": 16.6}) == 16.6


def test_a_back_without_one_falls_back_to_his_projection(rb):
    assert rb("rbOrderPts", {"pos": "RB", "pts": 15.0, "rank_pts": None}) == 15.0
    assert rb("rbOrderPts", {"pos": "RB", "pts": 15.0}) == 15.0, "a file from before the field"


@pytest.mark.parametrize("pos", ["QB", "WR", "TE"])
def test_no_other_position_is_ordered_by_it(rb, pos):
    assert rb("rbOrderPts", {"pos": pos, "pts": 15.0, "rank_pts": 20.0}) == 15.0


def test_a_row_with_no_points_has_no_key(rb):
    assert rb("rbOrderPts", {"pos": "RB", "pts": None, "rank_pts": 9.0}) is None


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


def test_a_list_says_reordered_only_when_a_back_sits_above_one_with_more_points(rb):
    rows = lambda *pts: [{"pts": p} for p in pts]
    assert rb("rbReordered", rows(16.6, 15.4, 15.4, 3.1)) is False
    assert rb("rbReordered", rows(15.0, 16.2, 3.1)) is True
    assert rb("rbReordered", []) is False


def test_points_that_print_the_same_are_not_a_reorder(rb):
    assert rb("rbReordered", [{"pts": 15.01}, {"pts": 15.04}]) is False


def test_a_tier_names_its_highest_and_lowest_points_not_its_first_and_last_row(rb):
    assert rb("rbTierSpan", [{"pts": 15.0}, {"pts": 16.2}, {"pts": 15.6}]) == {"hi": "16.2", "lo": "15.0"}


def test_the_tag_reads_in_plain_words_for_an_unlined_backup(rb):
    tag = rb("rbNoLine", {"pos": "RB", "unlined_backup": True, "pts": 3.1, "pts_before_unlined": 10.3})
    assert tag == {"word": words("ranks.noline.word"), "tip": words("ranks.noline.tip")}


def test_no_tag_for_a_back_the_books_priced_or_for_a_file_without_the_field(rb):
    assert rb("rbNoLine", {"pos": "RB", "unlined_backup": None}) is None
    assert rb("rbNoLine", {"pos": "RB"}) is None
    assert rb("rbNoLine", None) is None


def test_the_two_notes_say_why_in_plain_words(rb):
    assert rb("t", "ranks.rb.note") == ("Running backs are ordered by the sportsbooks' prices, "
                                        "which rank them better than our points do.")
    assert rb("t", "startsit.rb.note") == rb("t", "ranks.rb.note")
