"""Team > Trades > Value (data/tradevalue.js, 2026-11-03): the league's rows under a chip, the cap, and the words, in
Node. The numbers are ff-jarvis's (LIVE_TRADE_VALUE via design/trade_value.py); the page computes no points."""
import json
import pathlib

import pytest

import trade_value as tv_cut

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data" / "trade_value.json"
BLOCK = tv_cut.live_trade_value(json.loads(FIXTURE.read_text(encoding="utf-8")))
YAHOO = BLOCK["leagues"]["yahoo"]
ME = "Chat Take the Wheel"


@pytest.fixture(scope="module")
def tv(node_js):
    return node_js("data/tradevalue.js", globals={"LIVE_TRADE_VALUE": BLOCK})


@pytest.mark.req("Trade value", ac="a chip per position, everyone, or the reader's own team")
def test_the_chips_are_everyone_mine_and_the_four_positions_and_mine_needs_a_team_in_the_league(tv):
    assert tv("tvFilters", YAHOO, ME) == ["all", "mine", "QB", "RB", "WR", "TE"]
    assert tv("tvFilters", YAHOO, None) == ["all", "QB", "RB", "WR", "TE"]
    assert tv("tvFilters", YAHOO, "Nobody Here") == ["all", "QB", "RB", "WR", "TE"]
    assert tv("tvFilter", YAHOO, None, "mine") == "all" and tv("tvFilter", YAHOO, ME, "TE") == "TE"


@pytest.mark.req("Trade value", ac="the list is in PAR order")
def test_a_chip_keeps_the_files_par_order(tv):
    for chip in ("all", "mine", "QB", "TE"):
        rows = tv("tvRows", YAHOO, chip, ME)
        assert rows and [r["par"] for r in rows] == sorted((r["par"] for r in rows), reverse=True), chip
    assert {r["pos"] for r in tv("tvRows", YAHOO, "TE", ME)} == {"TE"}
    mine = tv("tvRows", YAHOO, "mine", ME)
    assert {r["holder"] for r in mine} == {ME} and "Rashee Rice" in [r["n"] for r in mine]


def test_the_all_list_stops_at_the_cap_until_asked_and_a_chips_list_is_whole(tv):
    rows = tv("tvRows", YAHOO, "all", ME)
    assert len(tv("tvShown", rows, "all", False)) == 40 and tv("tvMore", rows, "all", False) == len(rows) - 40
    assert len(tv("tvShown", rows, "all", True)) == len(rows) and tv("tvMore", rows, "all", True) == 0
    te = tv("tvRows", YAHOO, "TE", ME)
    assert tv("tvShown", te, "TE", False) == te and tv("tvMore", te, "TE", False) == 0


def test_signed_numbers_use_one_decimal_and_a_true_minus(tv):
    assert [tv("tvSigned", x) for x in (12.44, -3, 0, -0.04, 0.05)] == ["+12.4", "−3.0", "0.0", "0.0", "+0.1"]


@pytest.mark.req("Trade value", ac="a healthy what-if beside a player priced for missed games")
def test_the_healthy_what_if_is_the_par_it_adds_and_none_without_one(tv):
    rice = next(p for p in YAHOO["players"] if p["n"] == "Rashee Rice")
    assert tv("tvHealthyAdd", rice) == 8.8
    assert tv("tvHealthyAdd", {**rice, "par_healthy": None}) is None


@pytest.mark.req("Trade value", ac="his manager's view beside ours, as a number")
def test_the_gap_shows_from_two_points_a_game_either_way(tv):
    assert tv("tvGap", {"gap": 4.66}) == 4.7 and tv("tvGap", {"gap": -2.0}) == -2.0
    assert tv("tvGap", {"gap": 1.99}) is None and tv("tvGap", {"gap": None}) is None


def test_the_replacement_caption_is_in_position_order(tv):
    assert tv("tvReplacement", YAHOO) == [["QB", 17.06], ["RB", 9.46], ["WR", 9.38], ["TE", 8.22]]


def test_no_block_is_none(node_js):
    assert node_js("data/tradevalue.js", globals={"LIVE_TRADE_VALUE": None})("tvBlock") is None
    assert node_js("data/tradevalue.js")("tvBlock") is None


@pytest.mark.req("Trade value", ac="a Playoffs toggle ranks the fantasy playoff weeks")
def test_the_playoff_span_orders_by_playoff_par_and_ranks_each_position_in_that_order(tv):
    assert tv("tvSpans", BLOCK, YAHOO) == ["ros", "po"]
    rows = tv("tvRows", YAHOO, "all", ME, "po")
    assert [r["show_par"] for r in rows] == sorted((r["show_par"] for r in rows), reverse=True)
    assert all(r["show_par"] == r["po_par"] and r["show_games"] == r["po_games"] for r in rows)
    te = tv("tvRows", YAHOO, "TE", ME, "po")
    assert [r["show_rank"] for r in te] == list(range(1, len(te) + 1))
    ros = tv("tvRows", YAHOO, "all", ME)
    assert all(r["show_par"] == r["par"] and r["show_rank"] == r["pos_rank"] for r in ros), "the rest of season is the file's own"


def test_no_playoff_weeks_or_numbers_is_one_span_and_the_what_if_is_rest_of_season_only(tv):
    assert tv("tvSpans", {**BLOCK, "po_weeks": None}, YAHOO) == ["ros"]
    assert tv("tvSpans", BLOCK, {**YAHOO, "players": [{**p, "po_par": None} for p in YAHOO["players"]]}) == ["ros"]
    rice = next(p for p in YAHOO["players"] if p["n"] == "Rashee Rice")
    assert tv("tvHealthyAdd", rice, "po") is None and tv("tvHealthyAdd", rice, "ros") == 8.8
