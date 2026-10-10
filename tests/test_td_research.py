"""design/td_research.py (2026-10-09): ff-jarvis's td_research cut to LIVE_TD_RESEARCH, Slips' Anytime TDs card.
The fixture is week 2 (tests/fixtures/data/td_research.json); Noah Fant has no tier, Breece Hall's price is Consensus's."""
import json
import pathlib

import pytest

from td_research import live_td_research, pending_games, problems

DATA = pathlib.Path(__file__).parent / "fixtures" / "data"
RAW = json.loads((DATA / "td_research.json").read_text(encoding="utf-8"))
CLAUDE = json.loads((DATA / "claude_props.json").read_text(encoding="utf-8"))

pytestmark = pytest.mark.req("Parlay and DFS", ac="Anytime TDs card")


def test_the_cut_keeps_listed_players_with_rule_values_and_the_shown_book():
    b = live_td_research(RAW, CLAUDE)
    assert "Noah Fant" not in [p["name"] for p in b["players"]], "no tier, not listed"
    assert b["rules"] == {"lock_min_p": 0.55, "value_min_p": 0.3, "value_min_checks": 3, "list_min_p": 0.2}
    hall = next(p for p in b["players"] if p["name"] == "Breece Hall")
    assert hall["book"] == {"p": 0.5556, "price": -125, "book": "Consensus"}
    chase = next(p for p in b["players"] if p["name"] == "Ja'Marr Chase")
    assert chase["ours"] is None and chase["slug"]
    assert b["record"]["LOCK"]["w"] == 38 and b["record"]["VALUE"] is None
    assert problems(b) == []


def test_pending_carries_only_claudes_early_games():
    assert pending_games(CLAUDE) == [{"kickoff": "2026-09-13T17:00:00Z", "home": "NYJ", "away": "CIN", "expected_at": "2026-09-13T13:00:00Z"}]
    assert pending_games(None) == []


def test_no_file_or_nobody_listed_is_no_block_and_a_bad_tier_fails():
    assert live_td_research(None) is None
    assert live_td_research({**RAW, "players": [{**RAW["players"][0], "tier": None}]}) is None
    b = live_td_research(RAW)
    b["players"][0]["tier"] = "SMASH"
    assert problems(b) == ["LIVE_TD_RESEARCH.players[0].tier 'SMASH'"]
