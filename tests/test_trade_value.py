"""Team > Trades > Value, the data side (2026-11-03): ff-jarvis's trade_value.json cut to LIVE_TRADE_VALUE.

The fixture is ff-jarvis's trade_value rules run on the committed 2026-10-28 trade_offers.json values (every rostered
QB/RB/WR/TE in all three leagues), with Rashee Rice's healthy what-if as the live run gave it on 2026-11-03. No browser:
Node's test_js_tradevalue.py holds the rows, test_trade_value_view.py the screen."""
import copy
import json
import pathlib

import trade_value as tv

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data" / "trade_value.json"
RAW = json.loads(FIXTURE.read_text(encoding="utf-8"))
PLAYER_KEYS = {"slug", "n", "pos", "team", "holder", "ros_pg", "games", "par", "po_par", "games_healthy", "par_healthy",
               "perc", "gap", "last2", "injury", "ir", "rank", "pos_rank"}


def one(block, league, name):
    return next(p for p in block["leagues"][league]["players"] if p["n"] == name)


def test_the_cut_keeps_only_what_the_page_reads():
    block = tv.live_trade_value(RAW)
    assert set(block) == {"generated", "week", "ros_generated", "leagues"}
    assert set(block["leagues"]) == {"espn", "yahoo", "ayo"}
    yahoo = block["leagues"]["yahoo"]
    assert set(yahoo) == {"replacement", "me", "teams", "weeks_left", "players"}
    assert [p["n"] for lg in block["leagues"].values() for p in lg["players"] if set(p) != PLAYER_KEYS] == []
    assert len(yahoo["players"]) == len(RAW["leagues"]["yahoo"]["players"])


def test_a_players_numbers_pass_through_unchanged():
    rice = one(tv.live_trade_value(RAW), "yahoo", "Rashee Rice")
    assert (rice["slug"], rice["pos"], rice["holder"]) == ("rashee-rice", "WR", "Chat Take the Wheel")
    assert (rice["ros_pg"], rice["games"], rice["par"]) == (11.98, 5.1, 13.3)
    assert (rice["games_healthy"], rice["par_healthy"]) == (8.5, 22.1)
    assert tv.live_trade_value(RAW)["leagues"]["yahoo"]["replacement"] == {"QB": 17.06, "RB": 9.46, "WR": 9.38, "TE": 8.22}


def test_no_file_or_no_players_is_none_and_a_league_with_no_players_is_left_out():
    assert tv.live_trade_value(None) is None and tv.live_trade_value({}) is None
    raw = copy.deepcopy(RAW)
    raw["leagues"]["ayo"]["players"] = []
    assert set(tv.live_trade_value(raw)["leagues"]) == {"espn", "yahoo"}
    for lg in raw["leagues"].values():
        lg["players"] = []
    assert tv.live_trade_value(raw) is None


def test_problems_flag_an_unknown_position_a_missing_replacement_and_a_list_out_of_order():
    block = tv.live_trade_value(RAW)
    assert tv.problems(block) == []
    bad = copy.deepcopy(block)
    bad["leagues"]["yahoo"]["players"][0]["pos"] = "K"
    bad["leagues"]["espn"]["players"].reverse()
    del bad["leagues"]["ayo"]["replacement"]["TE"]
    got = tv.problems(bad)
    assert any("yahoo" in g and "position K" in g for g in got)
    assert any("espn" in g and "PAR order" in g for g in got)
    assert any("ayo" in g and "replacement" in g for g in got)


def test_the_build_report_names_the_leagues_or_says_there_is_no_tab():
    assert tv.report(None) == "Trade value: none, so Trades has no Value tab"
    assert tv.report(tv.live_trade_value(RAW)).startswith("Trade value: espn ")
