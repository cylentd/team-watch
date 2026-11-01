"""The strip of closed trades on Trade history's Best and Worst cards (2026-11-01, David: "People vs trades"), in Node.

`trFormOf` is one mark per closed trade, oldest first, on held weeks: the basis of the ranking's W-L, which is
ff-jarvis's `by_manager` (`par` beside `par`). A tie is a margin of 0. The strip's counts must equal the record
printed beside it. `trFormCols` sets the strip's columns: 2 to 25 marks take one or two lines at 360px.
"""
import pytest

ME = "7"


def trade(season, week, win, lose, held_win, margin, open_=False):
    return {"season": season, "week": week, "open": open_, "win": {"m": win}, "lose": {"m": lose},
            "held": {"win": held_win, "margin": margin}}


@pytest.fixture(scope="module")
def form(node_js):
    return node_js("data/tradeform.js")


@pytest.mark.req("Trade history", ac="one mark per closed trade, oldest to newest")
def test_marks_run_oldest_to_newest_whatever_order_the_file_has(form):
    trades = [trade(2024, 3, ME, "1", ME, 4.0), trade(2022, 9, "2", ME, "2", 5.0),
              trade(2024, 1, "3", ME, ME, 6.0), trade(2022, 2, ME, "4", "4", 7.0)]
    assert [m["r"] for m in form("trFormOf", trades, ME)] == ["l", "l", "w", "w"]


@pytest.mark.req("Trade history", ac="won and lost are held weeks, not the trade tree")
def test_the_result_is_the_held_result_on_either_side_of_the_tree(form):
    tree_loser_held_winner = trade(2023, 1, "1", ME, ME, 3.0)
    tree_winner_held_loser = trade(2023, 2, ME, "1", "1", 3.0)
    assert [m["r"] for m in form("trFormOf", [tree_loser_held_winner, tree_winner_held_loser], ME)] == ["w", "l"]


@pytest.mark.req("Trade history", ac="a tie is margin 0")
def test_a_margin_of_zero_is_a_tie_for_both_sides(form):
    tied = trade(2023, 15, ME, "1", ME, 0)
    assert [m["r"] for m in form("trFormOf", [tied], ME)] == ["t"]
    assert [m["r"] for m in form("trFormOf", [tied], "1")] == ["t"]


@pytest.mark.req("Trade history", ac="open trades are left out, matching the record")
def test_open_trades_and_other_managers_trades_draw_no_mark(form):
    trades = [trade(2026, 4, ME, "1", ME, 9.0, open_=True), trade(2025, 4, "2", "3", "2", 9.0)]
    assert form("trFormOf", trades, ME) == []


@pytest.mark.req("Trade history", ac="the strip's counts name its aria-label")
def test_counts_add_up_the_marks(form):
    marks = [{"r": r} for r in "wwlwt"]
    assert form("trFormCounts", marks) == {"w": 3, "l": 1, "t": 1}
    assert form("trFormCounts", []) == {"w": 0, "l": 0, "t": 0}


@pytest.mark.req("Trade history", ac="2 to 25 marks fit one or two lines")
@pytest.mark.parametrize("n,cols", [(2, 6), (5, 6), (6, 6), (7, 7), (12, 12), (13, 7), (14, 7), (24, 12), (25, 13)])
def test_columns_fill_one_line_then_split_into_two(form, n, cols):
    assert form("trFormCols", n) == cols


@pytest.mark.req("Trade history", ac="the letter grows with its mark")
@pytest.mark.parametrize("n,big", [(5, True), (8, True), (9, False), (12, False), (13, True), (16, True), (17, False)])
def test_a_mark_wide_enough_takes_the_bigger_letter(form, n, big):
    assert form("trFormBig", n) is big


@pytest.mark.req("Trade history", ac="2 to 25 marks fit one or two lines")
def test_every_count_from_2_to_25_takes_at_most_two_lines(form):
    lines = {n: -(-n // form("trFormCols", n)) for n in range(2, 26)}
    assert max(lines.values()) == 2, lines
