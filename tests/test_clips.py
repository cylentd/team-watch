"""design/yt_clips.py: LIVE_CLIPS, the official YouTube clips per player and per game, cut from
ff-jarvis's clips.json (the fixture follows the contract ff-jarvis writes)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from yt_clips import live_clips, report  # noqa: E402
from sources import load_clips  # noqa: E402
from test_build import injected  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "data"


def test_no_design_module_shares_a_name_with_an_api_module():
    """design/ and api/ are both put on sys.path, often api/ first. A shared name hands whichever
    comes first to every `import`: design/clips.py lost to api/clips.py (the /api/clips endpoint),
    and test_digest.py failed to collect on its own, so it became design/yt_clips.py (2026-10-05)."""
    repo = Path(__file__).resolve().parents[1]
    shared = {p.stem for p in (repo / "design").glob("*.py")} & {p.stem for p in (repo / "api").glob("*.py")}
    assert not shared, f"rename one side: {sorted(shared)}"


def test_block_keeps_clip_order_and_drops_the_decision_cache():
    b = live_clips(load_clips())
    contract.validate("LIVE_CLIPS", b)
    assert set(b) == {"week", "players", "games", "alias"}
    assert b["alias"] == {"LA": "LAR", "WAS": "WSH"}
    assert b["week"] == 4
    purdy = b["players"]["brock-purdy"]
    assert [c["kind"] for c in purdy] == ["best_plays", "play", "play"], "best plays first, then plays, as ff-jarvis wrote them"
    assert set(purdy[0]) == {"id", "title", "kind", "secs", "embed", "shape", "posted"}, "the raw channel code stays in ff-jarvis"
    assert [c["kind"] for c in b["players"]["george-kittle"]] == ["play"]


def test_fixture_slugs_are_players_on_the_fixture_rosters():
    from _espn import slugify
    rosters = json.loads((FIXTURES / "espn_rosters.json").read_text(encoding="utf-8"))
    on_rosters = {slugify(p["name"]) for team in rosters["detail"].values() for p in team}
    assert set(live_clips(load_clips())["players"]) <= on_rosters


def test_team_codes_leave_in_the_schedules_spelling():
    raw = {"week": 4, "players": {}, "games": {
        "LA": {"id": "x", "title": "t", "secs": 1}, "WAS": {"id": "y", "title": "u", "secs": 2},
        "SF": {"id": "x", "title": "t", "secs": 1}}}
    assert set(live_clips(raw)["games"]) == {"LAR", "WSH", "SF"}
    assert set(live_clips(load_clips())["games"]) == {"SF", "LAR", "CIN", "BUF"}


def test_a_clip_with_no_id_and_a_player_with_no_clip_drop():
    raw = {"week": 4, "players": {"a": [{"title": "no id", "kind": "play", "channel": "NFL", "secs": 3}], "b": [{"id": "z", "title": "t", "kind": "play", "channel": "NFL", "secs": 3}]},
           "games": {"SF": {"title": "no id"}}}
    b = live_clips(raw)
    assert list(b["players"]) == ["b"] and b["games"] == {}


def test_embed_passes_through_on_clips_and_games():
    b = live_clips(load_clips())
    assert [c["embed"] for c in b["players"]["brock-purdy"]] == [False, False, True], "a mix: NFL channel clips blocked, a club's not"
    assert [c["embed"] for c in b["players"]["george-kittle"]] == [False]
    assert [c["embed"] for c in b["players"]["chase-brown"]] == [True, True]
    assert all(g["embed"] is False for g in b["games"].values())


def test_a_file_with_no_embed_field_plays():
    raw = {"week": 4, "players": {"a": [{"id": "z", "title": "t", "kind": "play", "secs": 3}]},
           "games": {"SF": {"id": "x", "title": "t", "secs": 1}, "LA": {"id": "y", "title": "u", "secs": 2, "embed": False}}}
    b = live_clips(raw)
    contract.validate("LIVE_CLIPS", b)
    assert b["players"]["a"][0]["embed"] is True
    assert b["games"]["SF"]["embed"] is True and b["games"]["LAR"]["embed"] is False


def test_shape_passes_through_and_defaults_to_wide():
    b = live_clips(load_clips())
    assert [c["shape"] for c in b["players"]["brock-purdy"]] == ["wide", "wide", "tall"], "a Short is tall"
    assert all(g["shape"] == "wide" for g in b["games"].values())
    old = live_clips({"week": 4, "players": {"a": [{"id": "z", "title": "t", "kind": "play", "secs": 3, "shape": "odd"}]}})
    assert old["players"]["a"][0]["shape"] == "wide", "missing or unknown reads as wide"


def test_contract_names_a_missing_embed_field():
    b = live_clips(load_clips())
    del b["games"]["SF"]["embed"]
    with pytest.raises(contract.ContractError, match=r"LIVE_CLIPS.games\['SF'\].embed"):
        contract.validate("LIVE_CLIPS", b)


def test_no_file_is_no_block():
    assert live_clips(None) is None
    assert live_clips({"week": 4, "players": {}, "games": {}}) is None
    contract.validate("LIVE_CLIPS", None)
    assert "no clips.json" in report(None)


def test_contract_names_a_missing_clip_field():
    b = live_clips(load_clips())
    del b["players"]["brock-purdy"][0]["id"]
    with pytest.raises(contract.ContractError, match=r"LIVE_CLIPS.players\['brock-purdy'\]\[0\].id"):
        contract.validate("LIVE_CLIPS", b)


def test_the_build_injects_the_block(built):
    block = injected(built.fragment)["LIVE_CLIPS"]
    assert block["players"]["brock-purdy"][0]["kind"] == "best_plays"
    assert any("Clips: week 4" in line for line in built.report)
