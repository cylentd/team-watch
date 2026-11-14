"""Defense form rides in LIVE_SOS (design/sos.py, 2026-11-14): ff-jarvis's `defense_recent` and `recent` pass through
untouched, and the contract checks their shape where they enter. Both are optional, so a sos.json written before
ff-jarvis's o3-defense-form branch still builds. The page reads them in data/defform.js (test_js_defform.py)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from sos import live_sos  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "data" / "sos.json"


def _raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.req("Schedule", ac="defense form passes through")
def test_defense_recent_and_recent_pass_through_as_the_file_has_them():
    raw = _raw()
    block = live_sos(raw)
    assert block["defense_recent"] == raw["defense_recent"]
    assert block["recent"] == raw["recent"]
    assert contract.problems("LIVE_SOS", block) == []


@pytest.mark.req("Schedule", ac="a file before defense form still builds")
def test_a_file_without_defense_form_passes_none_and_builds():
    raw = _raw()
    del raw["defense_recent"], raw["recent"]
    block = live_sos(raw)
    assert block["defense_recent"] is None and block["recent"] is None
    assert contract.problems("LIVE_SOS", block) == []


@pytest.mark.req("Schedule", ac="a malformed defense form fails the build")
@pytest.mark.parametrize("pos,field", [("RB", "trend"), ("WR", "last3_pts_pg"), ("RB", "rush_trend"), ("QB", "season_pts_pg")])
def test_a_position_missing_a_field_the_page_reads_fails_naming_it(pos, field):
    raw = _raw()
    del raw["defense_recent"]["JAX"][pos][field]
    assert contract.problems("LIVE_SOS", live_sos(raw)) == [f"LIVE_SOS.defense_recent['JAX'].{pos}.{field}"]


@pytest.mark.req("Schedule", ac="a malformed defense form fails the build")
def test_a_trend_word_the_page_does_not_know_fails_naming_it():
    raw = _raw()
    raw["defense_recent"]["CIN"]["RB"]["trend"] = "sideways"
    assert contract.problems("LIVE_SOS", live_sos(raw)) == ["LIVE_SOS.defense_recent['CIN'].RB.trend"]
