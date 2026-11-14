"""Boom and bust reach LIVE_RANKS (2026-11-13): design/ranks.py carries ff-jarvis's `boom`, `bust` and `p95` off each
player_projections row (b064481, METHODOLOGY 12.136), the way `floor` and `ceil` arrive, and the file's `ranges.bars`
block as LIVE_RANKS.bars. Null when ff-jarvis has not written them (the jobs data before its next refresh), and the
contract still passes. Plain dicts in, plain dicts out; the page side is tests/test_js_outcome.py and
tests/test_ranks_odds_view.py."""
import pytest

import contract
from ranks import live_ranks

BARS = {"boom": {"QB": 25, "RB": 20, "WR": 20, "TE": 15}, "bust": {"QB": 12, "RB": 8, "WR": 8, "TE": 5},
        "unit": "half-PPR points"}


def slug(name):
    return name.lower().replace(" ", "-")


def player(name, pos, pts, **more):
    return {"name": name, "pos": pos, "team": "BBB", "game": "AAA @ BBB", "pts": pts, **more}


def lists(*names):
    rows = [{"key": n.lower(), "name": n, "pos": "RB", "team": "BBB", "opp": "AAA", "kickoff": "2026-09-13T17:00:00Z",
             "rank": i + 1, "tier": 1, "val": -float(i), "pts": 9.0 - i, "src": "ours"} for i, n in enumerate(names)]
    empty = {k: [] for k in ("QB", "RB", "WR", "TE", "FLEX")}
    return {"v": 1, "generated": "2026-11-13T07:35:00Z", "ros": None,
            "weekly": {"season": 2026, "week": 11, "scoring": "half", "off": [], "lists": {**empty, "RB": rows, "FLEX": rows}}}


ODDS = {"boom": 0.31, "bust": 0.18, "p95": 33.4}
BACK = player("Bo Back", "RB", 16.8, floor=7.6, ceil=28.4, **ODDS)
OLD = player("Al Old", "RB", 12.0, floor=5.0, ceil=20.0)   # a row from before the odds


def odds(r):
    return {k: r[k] for k in ("boom", "bust", "p95")}


@pytest.mark.req("Ranks", ac="boom and bust reach the rows")
def test_the_old_cut_carries_the_files_boom_bust_and_p95():
    got = {r["slug"]: r for r in live_ranks({"players": [BACK, OLD]}, slug)["rows"]}
    assert odds(got["bo-back"]) == ODDS
    assert odds(got["al-old"]) == {"boom": None, "bust": None, "p95": None}, "no odds in the file: null, never computed"


@pytest.mark.req("Ranks", ac="boom and bust reach the rows")
def test_a_week_ranks_row_takes_the_odds_off_his_projections_row():
    block = live_ranks({"players": [BACK]}, slug, None, None, lists("Bo Back", "Cy Nobody"))
    rb = {r["slug"]: r for r in block["rows"]}
    assert odds(rb["bo-back"]) == ODDS
    assert odds(rb["cy-nobody"]) == {"boom": None, "bust": None, "p95": None}, "no projections row: null"
    assert odds(block["flex"][0]) == ODDS, "FLEX rows carry them too"


@pytest.mark.parametrize("cut", [None, lists("Bo Back")], ids=["old cut", "week_ranks"])
def test_the_bars_come_from_the_files_ranges_block(cut):
    raw = {"players": [BACK], "ranges": {"floor": "10th percentile", "bars": BARS}}
    assert live_ranks(raw, slug, None, None, cut)["bars"] == {"boom": BARS["boom"], "bust": BARS["bust"]}


@pytest.mark.parametrize("ranges", [None, {"floor": "10th percentile"}, {"bars": {"boom": {"RB": 20}}}],
                         ids=["no ranges block", "ranges without bars", "bars without bust"])
def test_no_bars_in_the_file_is_null(ranges):
    assert live_ranks({"players": [BACK], "ranges": ranges}, slug)["bars"] is None


@pytest.mark.parametrize("players", [[BACK], [OLD]], ids=["with odds", "without odds"])
def test_the_ranks_contract_passes_with_or_without_the_odds(players):
    block = live_ranks({"players": players}, slug)
    assert contract.problems("LIVE_RANKS", block) == []


def test_the_contract_names_the_new_fields():
    assert {"boom", "bust", "p95"} <= set(contract.RANK_ROW)
    assert "bars" in contract.CONTRACT["LIVE_RANKS"]["keys"]
