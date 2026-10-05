"""design/player_names.py: LIVE_NAMES, each player's jersey number and nicknames for the live clip
matcher, cut from ff-jarvis's player_names.json (the fixture follows the contract ff-jarvis writes)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from player_names import live_names, report  # noqa: E402
from sources import load_player_names  # noqa: E402


def test_block_keeps_only_number_club_and_nicks():
    b = live_names(load_player_names())
    contract.validate("LIVE_NAMES", b)
    assert all(set(row) == {"n", "t", "k"} for row in b.values()), "name and pos stay in ff-jarvis"
    assert b["brock-purdy"] == {"n": 13, "t": "SF", "k": ["Mr. Irrelevant"]}
    assert {"amonra-st-brown", "cam-skattebo", "devon-achane", "jahmyr-gibbs", "tee-higgins", "chase-brown", "george-kittle"} <= set(b)


def test_team_codes_leave_in_the_schedules_spelling():
    b = live_names(load_player_names())
    assert b["puka-nacua"]["t"] == "LAR" and b["jayden-daniels"]["t"] == "WSH"
    assert b["amonra-st-brown"]["t"] == "DET", "a club with one spelling is untouched"


def test_missing_number_is_null_and_nicks_pass_through():
    raw = {"players": {"a": {"name": "A", "team": "SF", "pos": "WR", "nick": ["X", "Y"]},
                       "b": {"name": "B", "team": "LA", "pos": "K", "num": None},
                       "c": {"name": "C", "team": "SF", "pos": "QB", "num": 0, "nick": []}}}
    b = live_names(raw)
    assert b["a"] == {"n": None, "t": "SF", "k": ["X", "Y"]}
    assert b["b"] == {"n": None, "t": "LAR", "k": []}
    assert b["c"]["n"] == 0, "jersey 0 is a number, not a missing one"
    assert live_names(load_player_names())["amonra-st-brown"]["k"] == ["ARSB", "Sun God"]
    assert live_names(load_player_names())["test-rookie"]["n"] is None


def test_no_file_is_no_block():
    assert live_names(None) is None
    assert live_names({}) is None
    assert live_names({"players": {}}) is None
    contract.validate("LIVE_NAMES", None)
    assert "no player_names.json" in report(None)


def test_contract_names_a_missing_nested_field():
    b = live_names(load_player_names())
    del b["amonra-st-brown"]["k"]
    with pytest.raises(contract.ContractError, match=r"LIVE_NAMES\['amonra-st-brown'\].k"):
        contract.validate("LIVE_NAMES", b)


def test_the_build_injects_the_block(built):
    assert "const LIVE_NAMES = {" in built.fragment
    assert any(line.startswith("Names: 11 players") for line in built.report)


def test_a_build_without_the_file_injects_null(monkeypatch):
    import build
    monkeypatch.setattr(build, "load_player_names", lambda: None)
    out = build.render()
    assert "const LIVE_NAMES = null;" in out.fragment
    assert any(line.startswith("Names: no player_names.json") for line in out.report)
