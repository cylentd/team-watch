"""LIVE_D_STARTERS (2026-10-06): ff-jarvis's d_starters block, cut by design/d_starters.py for the Preview
chips and the profile's matchup note. A displayed fact: the cut moves no number and drops none.

The fixture (tests/fixtures/data/d_starters.json) is week 2 over the Preview fixture's five games: NO is missing
Elliss and Granderson (both front seven, Out), CAR a lineman (IR) and a corner (Doubtful), NYJ a starter who left
the team with no unit, LA has no earlier game (null counts), and PIT @ CLE is the game with none missing.
"""
import copy
import json
import pathlib

import pytest

import contract
from d_starters import live_d_starters, problems, report

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "d_starters.json"
REQ = "Defenders out"


@pytest.fixture(scope="module")
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def block(raw):
    return live_d_starters(raw)


@pytest.mark.req(REQ, ac="the cut keys each defense by the page's team spelling and sends the alias")
def test_the_cut_keys_defenses_by_the_pages_team_codes(block):
    assert sorted(block["teams"]) == ["ATL", "CAR", "CLE", "DET", "JAX", "LAR", "NO", "NYJ", "PIT", "SF"]
    assert block["teams"]["LAR"]["team"] == "LAR" and block["teams"]["JAX"]["opp"] == "LAR"   # nflverse LA is the page's LAR
    assert block["alias"]["LA"] == "LAR"


@pytest.mark.req(REQ, ac="a missing starter keeps his name, position, unit, status and snap share, most snaps first")
def test_a_defense_carries_its_missing_starters_whole(block):
    no = block["teams"]["NO"]
    assert (no["n_missing"], no["front7_missing"], no["secondary_missing"], no["share"]) == (2, 2, 0, 0.188)
    assert no["players"] == [
        {"name": "Kaden Elliss", "pos": "LB", "unit": "front7", "status": "Out", "snap_share": 0.114},
        {"name": "Carl Granderson", "pos": "DE", "unit": "front7", "status": "Out", "snap_share": 0.074}]
    assert block["teams"]["NYJ"]["players"][0]["unit"] is None


@pytest.mark.req(REQ, ac="a team with no earlier game keeps its null counts, never a zero")
def test_no_earlier_game_stays_null(block):
    la = block["teams"]["LAR"]
    assert (la["n_missing"], la["front7_missing"], la["secondary_missing"], la["share"], la["players"]) == (None, None, None, None, [])


@pytest.mark.req(REQ, ac="a game side the producer left null or unnamed is skipped, never a crash or a blank defense")
def test_a_malformed_game_side_is_skipped(raw):
    bad = copy.deepcopy(raw)
    bad["games"][0]["away"] = None
    bad["games"][1]["home"] = {"opp": "JAX"}                       # a record with no team name
    got = live_d_starters(bad)
    assert "PIT" not in got["teams"] and "LAR" not in got["teams"] and "CLE" in got["teams"]
    assert "" not in got["teams"] and None not in got["teams"]


@pytest.mark.req(REQ, ac="the rules and the evidence pass through for the page to quote")
def test_the_rules_pass_through_verbatim(raw, block):
    assert block["rules"] == raw["rules"] and "2028" in block["rules"]["evidence"]
    assert (block["season"], block["week"], block["asof"]) == (2026, 2, "2026-09-12T09:00:00Z")


@pytest.mark.req(REQ, ac="no file, an empty one or a null block is no block")
@pytest.mark.parametrize("raw_in", [None, {}, {"games": []}, {"week": 2, "games": None}])
def test_no_games_means_no_block(raw_in):
    assert live_d_starters(raw_in) is None
    assert "no d_starters" in report(None)


@pytest.mark.req(REQ, ac="the block meets the contract, and a missing field is named")
def test_the_block_meets_the_contract_and_names_a_gap(block):
    assert contract.problems("LIVE_D_STARTERS", block) == []
    assert contract.problems("LIVE_D_STARTERS", None) == []
    bad = copy.deepcopy(block)
    del bad["teams"]["NO"]["front7_missing"]
    del bad["rules"]
    assert contract.problems("LIVE_D_STARTERS", bad) == ["LIVE_D_STARTERS.rules", "LIVE_D_STARTERS.teams['NO'].front7_missing"]


@pytest.mark.req(REQ, ac="a player row missing a field, or a unit the page does not know, fails by name")
def test_a_bad_player_row_fails_by_name(block):
    bad = copy.deepcopy(block)
    del bad["teams"]["NO"]["players"][0]["status"]
    bad["teams"]["CAR"]["players"][0]["unit"] = "linebacker"
    assert problems(bad) == ["LIVE_D_STARTERS.teams['CAR'].players[0].unit 'linebacker'",
                             "LIVE_D_STARTERS.teams['NO'].players[0].status"]


@pytest.mark.req(REQ, ac="the feed block is read first, then the file, else nothing")
def test_the_feed_block_beats_the_file_and_neither_means_none(raw, tmp_path, monkeypatch):
    import d_starters
    import sources
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"d_starters": {"data": {**raw, "week": 9}, "fetched": "x"}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    monkeypatch.setattr(d_starters, "DWR", tmp_path / "nowhere")
    assert d_starters.load_d_starters()["week"] == 9                       # the feed's, though no file exists
    feed.write_text(json.dumps({"d_starters": {"data": None, "fetched": None}}), encoding="utf-8")
    assert d_starters.load_d_starters() is None                            # a feed from before the step, no file
    (tmp_path / "nowhere").mkdir()
    (tmp_path / "nowhere" / "d_starters.json").write_text(json.dumps(raw), encoding="utf-8")
    assert d_starters.load_d_starters()["week"] == 2                       # the file, once the feed has none


def test_the_report_says_what_it_holds(block):
    assert report(block) == "Defenders out: week 2, 10 defenses, 3 with a starter out"
