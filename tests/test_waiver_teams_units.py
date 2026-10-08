"""The small pieces behind LIVE_WAIVER_TEAMS, one behaviour each (ledger #22): the contract check
(design/contract_waiver.py), the file read (design/sources.py `load_waiver_teams`) and the headshot list
(design/build.py `wanted_slugs`). tests/test_waiver_teams.py holds the whole-page half.
"""
import json

import pytest

import build
import contract_waiver
import sources

pytestmark = pytest.mark.req("Waivers")

FULL_TEAM = {"date": "d", "week": 1, "clears": "c", "leagues_meta": {}, "players": []}
FILE = {"date": "2026-09-22", "teams": {}}


def test_a_file_without_a_teams_key_has_no_problems():
    assert contract_waiver.teams_problems({"date": "2026-09-22"}) == []


def test_a_team_that_meets_live_waiver_has_no_problems():
    assert contract_waiver.teams_problems({"teams": {"k": FULL_TEAM}}) == []


def test_a_missing_field_is_named_under_the_teams_key():
    team = {k: v for k, v in FULL_TEAM.items() if k != "week"}
    assert contract_waiver.teams_problems({"teams": {"ayo-don-wick": team}}) == [
        "LIVE_WAIVER_TEAMS.teams['ayo-don-wick'].week"]


def test_only_the_leading_block_name_is_renamed():
    team = {**FULL_TEAM, "leagues_meta": {"LIVE_WAIVER": {}}}
    got = contract_waiver.teams_problems({"teams": {"k": team}})
    assert got == [f"LIVE_WAIVER_TEAMS.teams['k'].leagues_meta['LIVE_WAIVER'].{f}"
                   for f in contract_waiver.WAIVER_META]


def test_every_teams_problems_are_collected_in_order():
    bad = {k: v for k, v in FULL_TEAM.items() if k != "date"}
    got = contract_waiver.teams_problems({"teams": {"a": bad, "b": bad}})
    assert got == ["LIVE_WAIVER_TEAMS.teams['a'].date", "LIVE_WAIVER_TEAMS.teams['b'].date"]


def test_load_waiver_teams_reads_the_given_folder(tmp_path, monkeypatch):
    elsewhere = tmp_path / "default"
    elsewhere.mkdir()
    monkeypatch.setattr(sources, "DWR", elsewhere)
    given = tmp_path / "given"
    given.mkdir()
    (given / "waiver_teams.json").write_text(json.dumps(FILE), encoding="utf-8")
    assert sources.load_waiver_teams(given) == FILE


def test_load_waiver_teams_without_a_folder_reads_the_default(tmp_path, monkeypatch):
    (tmp_path / "waiver_teams.json").write_text(json.dumps(FILE), encoding="utf-8")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert sources.load_waiver_teams() == FILE


def wanted(pool, mates=None):
    return build.wanted_slugs(
        [{"roster": [{"slug": "m1"}]}], {"props": [{"slug": "pr"}]}, {"players": [{"slug": "d1"}]},
        {"players": [{"slug": "w1"}]}, pool, {"teams": {"k": {"players": [{"slug": "t1"}]}}}, mates)


def test_wanted_slugs_run_in_order_from_the_fixed_list_to_the_leaguemates():
    mates = {"teams": [{"roster": [{"slug": "x1"}]}]}
    assert wanted({"players": [{"slug": "p1"}]}, mates) == (
        list(build.SLUGS) + ["w1", "t1", "p1", "m1", "pr", "d1", "x1"])


def test_wanted_slugs_without_a_pool_still_lists_the_rest():
    assert wanted(None) == list(build.SLUGS) + ["w1", "t1", "m1", "pr", "d1"]
