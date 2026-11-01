"""League > Trade history for the ESPN league (2026-11-01): the build side.

ff-jarvis writes data/espn_trade_verdicts.json in yahoo_trade_verdicts.json's shape and
data/espn_league_managers.json in yahoo_league_managers.json's. Neither is on ff-jarvis main yet, so a build
without them must carry a null block. The ESPN block is the Yahoo fixture's file read as ESPN's: the shape is
the same by agreement, and the numbers are ff-jarvis's, never computed here.
"""
import json
import re
import shutil

import pytest

import build
import contract
import league_trades as T
import leagues
import sources
from conftest import FIXTURES

DATA = FIXTURES / "data"
# David's rule (2026-11-01): first initial plus the full last name; names already initials stay; a defense whole.
SHORT_NAMES = [("Ja'Marr Chase", "J. Chase"), ("Malik Nabers", "M. Nabers"), ("A.J. Brown", "A.J. Brown"),
               ("C.J. Stroud", "C.J. Stroud"), ("J.K. Dobbins", "J.K. Dobbins"), ("T.J. Hockenson", "T.J. Hockenson"),
               ("AJ Dillon", "A. Dillon"), ("Amon-Ra St. Brown", "A. St. Brown"), ("Marvin Harrison Jr.", "M. Harrison Jr."),
               ("Raiders D/ST", "Raiders D/ST"), ("Bills", "Bills")]


def injected(fragment, name):
    m = re.search(rf"^const {name} = (.*);$", fragment, re.M)
    assert m, f"{name} not injected"
    return json.loads(m.group(1).replace("<\\/", "</"))


@pytest.mark.req("Trade history", ac="players go by first initial and full last name; initials and defenses stay whole")
@pytest.mark.parametrize("name,want", SHORT_NAMES, ids=[n for n, _ in SHORT_NAMES])
def test_a_player_is_a_first_initial_and_the_full_last_name(name, want):
    assert T.short(name) == want


@pytest.mark.req("Trade history", ac="ESPN names its trade files and its block")
def test_espn_names_its_trade_files_and_block():
    assert leagues.file("espn", "trade_verdicts") == "espn_trade_verdicts.json"
    assert leagues.file("espn", "league_managers") == "espn_league_managers.json"
    assert leagues.blocks("espn").trades == "LIVE_TRADES_ESPN"
    assert contract.SHARES_SPEC == {"LIVE_TRADES_ESPN": "LIVE_TRADES"}


@pytest.mark.req("Trade history", ac="live_trades(key='espn') passes the contract and names managers by first name")
def test_the_espn_block_passes_the_contract_with_its_managers_named():
    managers = {"managers": {"1": "Will", "12": "David", "former-1": "Max"}}
    verdicts = json.loads((DATA / "yahoo_trade_verdicts.json").read_text(encoding="utf-8"))
    b = T.live_trades(verdicts, managers, key="espn")
    assert contract.problems("LIVE_TRADES_ESPN", b) == []
    assert b["names"] == managers["managers"]
    assert contract.problems("LIVE_TRADES_ESPN", {k: v for k, v in b.items() if k != "curses"}) == ["LIVE_TRADES_ESPN.curses"]
    assert T.report(b, "espn").startswith("Trades (espn): ")
    assert T.report(None, "espn") == "Trades (espn): none (no ff-jarvis espn_trade_verdicts.json)"


@pytest.mark.req("Trade history", ac="without ESPN's files the block is null and the page behaves as before")
def test_the_fixture_build_has_no_espn_trades_block(built):
    assert injected(built.fragment, "LIVE_TRADES_ESPN") is None, "no verdicts file, no block: never invented"
    assert injected(built.fragment, "LIVE_TRADES")["n"] > 0, "the Yahoo league's block is untouched"


@pytest.mark.integration      # a real build of the page
@pytest.mark.req("Trade history", ac="the build reads espn_trade_verdicts.json and espn_league_managers.json")
def test_the_build_injects_the_espn_block_from_its_two_files(tmp_path, monkeypatch):
    data = tmp_path / "data"
    shutil.copytree(DATA, data)
    shutil.copy(DATA / "yahoo_trade_verdicts.json", data / "espn_trade_verdicts.json")
    (data / "espn_league_managers.json").write_text(json.dumps({"managers": {"1": "Will", "former-1": "Max"}}), encoding="utf-8")
    monkeypatch.setattr(sources, "DWR", data)
    fragment = build.render().fragment
    block = injected(fragment, "LIVE_TRADES_ESPN")
    assert block["names"] == {"1": "Will", "former-1": "Max"}
    assert block["n"] == injected(fragment, "LIVE_TRADES")["n"]
