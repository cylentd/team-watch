"""Stats > Ranks shows the number each rank is built on (David 2026-10-08, ledger #23 "ranks a"): week_ranks contract v2
gives every row `rank_pts`, the half-PPR number its list is ordered and tiered by. The row's `shown` is that number
(v1: `pts`); `pts` stays ours, for every other reader of LIVE_RANKS. The band and the matchup are ours, so a row keeps
them only where `rank_pts` is our own number. Light: dicts in, dicts out."""
import pytest

import contract
import week_ranks
from ranks import live_ranks
from test_week_ranks_units import slug


def row(name, pos, rank, tier, pts, rank_pts="absent", team="AAA"):
    r = {"key": name.lower(), "name": name, "pos": pos, "team": team, "opp": "BBB", "kickoff": "2026-09-13T17:00:00Z",
         "rank": rank, "tier": tier, "val": float(-rank), "pts": pts, "src": "books"}
    if rank_pts != "absent":
        r["rank_pts"] = rank_pts
    return r


def doc(lists, v=2):
    empty = {name: [] for name in week_ranks.LISTS}
    return {"v": v, "generated": "2026-09-10T07:35:00Z", "ros": None,
            "weekly": {"season": 2026, "week": 4, "scoring": "half", "off": [], "lists": {**empty, **lists}}}


def player(name, pos, pts, **more):
    return {"name": name, "pos": pos, "team": "AAA", "game": "AAA @ BBB", "pts": pts, **more}


def cut(lists, players=(), v=2):
    return live_ranks({"players": list(players)}, slug, None, None, doc(lists, v))


ALLEN = row("B Allen", "RB", 10, 2, 8.1, 14.5)
COOK = row("J Cook", "RB", 11, 2, 14.1, 12.0)


def test_a_row_shows_our_points_and_never_the_books_number():
    """(ledger #81, 2026-10-09; was: shows the number its rank is built on) rank_pts no longer orders or prints; the list
    arrives in our points' order (ff-jarvis #88) and is drawn as shipped (ledger #98)."""
    rows = cut({"RB": [row("B Bee", "RB", 1, 1, 14.1, 12.04), row("A Ace", "RB", 2, 1, 8.1, 14.5)]})["rows"]
    assert [(r["slug"], r["shown"], r["pts"]) for r in rows] == [("b-bee", 14.1, 14.1), ("a-ace", 8.1, 8.1)]


def test_shown_is_rounded_to_hundredths_like_pts():
    assert cut({"QB": [row("A Ace", "QB", 1, 1, 9.1256, 12.3456)]})["rows"][0]["shown"] == 9.13


def test_a_file_from_before_rank_pts_shows_pts():
    got = cut({"RB": [row("A Ace", "RB", 1, 1, 8.126)]}, v=1)["rows"][0]
    assert (got["shown"], got["pts"]) == (8.13, 8.13)


def test_flex_rows_show_the_same_number_as_the_position_list():
    lists = {"RB": [row("A Ace", "RB", 1, 1, 8.1, 14.5)], "FLEX": [row("A Ace", "RB", 1, 1, 8.1, 13.0)]}
    got = cut(lists)
    assert (got["rows"][0]["shown"], got["flex"][0]["shown"]) == (8.1, 8.1)


BAND = {"floor": 3.0, "ceil": 20.0, "matchup": {"pts": 1.4, "priced": 0.6}}


OURS = (3.0, 20.0, 1.4, 0.6)


@pytest.mark.parametrize("rank_pts", [8.1, 8.14, 8.2, 8.0, 14.5], ids=["same", "within a rounding", "a tenth over", "a tenth under", "books"])
def test_the_band_and_the_matchup_stay_whatever_the_books_price(rank_pts):
    """(ledger #81) The number shown is always ours, so the band and the matchup always describe it."""
    got = cut({"RB": [row("A Ace", "RB", 1, 1, 8.1, rank_pts)]}, [player("A Ace", "RB", 8.1, **BAND)])["rows"][0]
    assert (got["floor"], got["ceil"], got["mx"], got["mxp"]) == OURS


def test_a_file_from_before_rank_pts_keeps_the_band_and_the_matchup():
    got = cut({"RB": [row("A Ace", "RB", 1, 1, 8.1)]}, [player("A Ace", "RB", 8.1, **BAND)], v=1)["rows"][0]
    assert (got["floor"], got["ceil"], got["mx"]) == (3.0, 20.0, 1.4)


def test_a_row_the_projections_do_not_hold_has_no_band_either_way():
    got = cut({"RB": [row("A Ace", "RB", 1, 1, 8.1, 14.5)]})["rows"][0]
    assert (got["floor"], got["ceil"], got["mx"], got["mxp"]) == (None, None, None, None)


def test_the_old_cut_shows_its_points():
    got = live_ranks({"players": [player("A Ace", "RB", 8.126, rank_pts=14.5)]}, slug)["rows"][0]
    assert (got["shown"], got["pts"]) == (8.13, 8.13), "the old cut shows points; the books' number only orders"


def test_the_block_meets_the_contract_in_both_cuts():
    assert contract.problems("LIVE_RANKS", cut({"RB": [ALLEN, COOK]})) == []
    assert contract.problems("LIVE_RANKS", live_ranks({"players": [player("A Ace", "RB", 8.1)]}, slug)) == []


# ---- the shape check, at entry ----

def test_a_v2_file_is_whole_and_so_is_a_v1_file():
    lists = {"RB": [row("A Ace", "RB", 1, 1, 8.1, 14.5)]}
    assert week_ranks.problems(doc(lists)) == []
    assert week_ranks.problems(doc({"RB": [row("A Ace", "RB", 1, 1, 8.1)]}, v=1)) == []


def test_a_v2_row_without_rank_pts_is_named():
    bad = week_ranks.problems(doc({"RB": [row("A Ace", "RB", 1, 1, 8.1)]}))
    assert len(bad) == 1 and bad[0].startswith("weekly.lists.RB[0]: keys ") and "rank_pts" in bad[0], bad


@pytest.mark.parametrize("value", [None, "14.5", True, float("nan"), float("inf")], ids=["null", "text", "bool", "nan", "inf"])
def test_a_v2_rank_pts_that_is_not_a_number_is_named(value):
    assert week_ranks.problems(doc({"RB": [row("A Ace", "RB", 1, 1, 8.1, value)]})) == \
        [f"weekly.lists.RB[0].rank_pts: {value!r} is not a number"]


def test_a_v1_row_with_rank_pts_is_not_a_v1_row():
    bad = week_ranks.problems(doc({"RB": [row("A Ace", "RB", 1, 1, 8.1, 14.5)]}, v=1))
    assert len(bad) == 1 and bad[0].startswith("weekly.lists.RB[0]: keys "), bad


def test_a_version_other_than_one_or_two_is_named():
    assert week_ranks.problems(doc({}, v=3)) == ["v: 3, expected 1 or 2"]
    assert week_ranks.problems(doc({}, v=0)) == ["v: 0, expected 1 or 2"]


def test_rank_pts_may_step_up_down_a_file_list_and_the_page_still_prints_our_points_in_order():
    lists = {"WR": [row("A Ace", "WR", 1, 1, 12.0, 12.0), row("B Bee", "WR", 2, 1, 11.0, 13.0)]}
    assert week_ranks.problems(doc(lists)) == []
    assert [(r["slug"], r["shown"]) for r in cut(lists)["rows"]] == [("a-ace", 12.0), ("b-bee", 11.0)]
