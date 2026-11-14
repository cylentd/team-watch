"""Boom and bust on Ranks (2026-11-13), in Node: data/outcome.js.

ff-jarvis (b064481, METHODOLOGY 12.136) writes `boom` and `bust` on every `player_projections` row: the chance,
0-1 with 2 decimals, that he scores at or above his position's boom bar, or under its bust bar, if he plays. The
bars sit in the file's `ranges.bars` block. The page sorts by them and prints them; it never computes one.
A row without both numbers (a file from before them) draws no odds and sorts last."""
import pytest

BARS = {"boom": {"QB": 25, "RB": 20, "WR": 20, "TE": 15}, "bust": {"QB": 12, "RB": 8, "WR": 8, "TE": 5},
        "unit": "half-PPR points"}


def row(slug, pts, boom, bust, **kw):
    return {"slug": slug, "pos": "RB", "pts": pts, "shown": pts, "boom": boom, "bust": bust, **kw}


# Projection order as the build ships it (pts down), with odds that disagree with it on purpose.
LIST = [row("alpha", 19.8, .30, .18), row("bravo", 17.6, .34, .25), row("charlie", 17.2, .22, .12),
        row("delta", 16.8, .34, .20), row("echo", 16.3, .22, .12)]


@pytest.fixture(scope="module")
def oc(node_js):
    return node_js("data/outcome.js")


def slugs(rows):
    return [r["slug"] for r in rows]


def test_projection_keeps_the_builds_order(oc):
    assert slugs(oc("outcomeSort", LIST, "pts")) == ["alpha", "bravo", "charlie", "delta", "echo"]


def test_upside_puts_the_likeliest_boom_first_and_breaks_a_tie_on_points(oc):
    # bravo and delta both .34: bravo has more points; charlie and echo both .22: charlie has more.
    assert slugs(oc("outcomeSort", LIST, "boom")) == ["bravo", "delta", "alpha", "charlie", "echo"]


def test_safe_puts_the_least_likely_bust_first_and_breaks_a_tie_on_points(oc):
    # charlie and echo both .12: charlie has more points.
    assert slugs(oc("outcomeSort", LIST, "bust")) == ["charlie", "echo", "alpha", "delta", "bravo"]


def test_a_tie_breaks_on_the_shown_number_the_row_prints(oc):
    two = [row("low", 10.0, .30, .20, shown=9.0), row("high", 9.5, .30, .20, shown=12.0)]
    assert slugs(oc("outcomeSort", two, "boom")) == ["high", "low"]


@pytest.mark.parametrize("mode", ["boom", "bust"])
def test_a_row_without_odds_sorts_last_in_projection_order(oc, mode):
    mixed = [row("old1", 20.0, None, None), row("new", 12.0, .10, .40), row("old2", 18.0, None, None)]
    assert slugs(oc("outcomeSort", mixed, mode)) == ["new", "old1", "old2"]


def test_sorting_leaves_the_input_list_alone(oc):
    assert slugs(oc("(l => { outcomeSort(l, 'boom'); return l; })", LIST)) == slugs(LIST)


@pytest.mark.parametrize("r,want", [
    (row("a", 19.8, .30, .18), {"boom": 30, "bust": 18}),
    (row("a", 0.0, 0.0, 1.0), {"boom": 0, "bust": 100}),
    (row("a", 12.0, .29, .07), {"boom": 29, "bust": 7}),   # .29 * 100 is 28.999... in floating point
])
def test_odds_are_whole_percents_of_the_files_numbers(oc, r, want):
    assert oc("outcomeOf", r) == want


@pytest.mark.parametrize("r", [row("a", 19.8, None, None), row("a", 19.8, .3, None),
                               {"slug": "older", "pts": 11.0}, None])
def test_a_row_without_both_numbers_has_no_odds(oc, r):
    assert oc("outcomeOf", r) is None


def test_the_sorts_are_offered_only_when_a_row_has_odds(oc):
    assert oc("outcomeSorts", LIST) == ["pts", "boom", "bust"]
    assert oc("outcomeSorts", [row("a", 19.8, None, None)]) == ["pts"]
    assert oc("outcomeSorts", []) == ["pts"]


def test_one_positions_bars(oc):
    assert oc("outcomeBars", BARS, ["QB"]) == [{"pos": ["QB"], "boom": 25, "bust": 12}]


def test_flex_bars_group_the_positions_that_share_them_largest_group_first(oc):
    assert oc("outcomeBars", BARS, ["TE", "RB", "WR"]) == [
        {"pos": ["RB", "WR"], "boom": 20, "bust": 8}, {"pos": ["TE"], "boom": 15, "bust": 5}]


@pytest.mark.parametrize("bars", [None, {}, {"boom": {"RB": 20}}, {"boom": {"QB": 25}, "bust": {"QB": 12}}])
def test_no_bars_for_the_position_means_no_note(oc, bars):
    assert oc("outcomeBars", bars, ["RB"]) is None
