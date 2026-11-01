"""Schedule's "context only" mark is the file's `label` (design/sos.py, data/sos.js). A LIVE_SOS with no usable
label would draw an empty line and no mark, so the build fails instead (David, 2026-11-01). No file at all
(LIVE_SOS null) still builds."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
from sos import live_sos  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "data" / "sos.json"


def _block(**over):
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw.pop("label", None) if over.pop("drop", False) else None
    raw.update(over)
    return live_sos(raw)


@pytest.mark.req("Schedule", ac="a file with its label builds")
def test_a_present_label_passes_the_contract():
    assert contract.problems("LIVE_SOS", _block()) == []


@pytest.mark.req("Schedule", ac="a missing or blank label fails the build")
@pytest.mark.parametrize("over", [{"drop": True}, {"label": None}, {"label": ""}, {"label": "   \n"}],
                         ids=["missing", "null", "empty", "whitespace"])
def test_a_missing_or_blank_label_fails_the_build_naming_it(over):
    with pytest.raises(contract.ContractError) as err:
        contract.validate("LIVE_SOS", _block(**over))
    assert "LIVE_SOS.label" in str(err.value)


@pytest.mark.req("Schedule", ac="no sos.json still builds")
def test_an_absent_block_still_builds():
    assert contract.problems("LIVE_SOS", None) == []
    assert live_sos(None) is None
