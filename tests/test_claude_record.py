"""Claude's row under the Slips record line (2026-10-05, LIVE_CLAUDE_RECORD, design/slips.py): how often
Claude's frozen prop call hit where he took the model's side ("agrees") and where he took the other one ("alone").
The data cut needs no browser. Since 2026-10-08 (ledger #33) the page draws only `agree`, as "Our picks"
(tests/test_slips_windows.py); the Claude row and its agrees/alone tiles are gone."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402  (before slips: slips puts api/ first on sys.path, where another clips.py lives)
import slips  # noqa: E402

GRADED = {"season": 2026, "week": 5, "through_week": 4,
          "agree": {"w": 7, "l": 5, "push": 1, "void": 0}, "alone": {"w": 8, "l": 9, "push": 0, "void": 2}}


def block(built):
    m = re.search(r"^const LIVE_CLAUDE_RECORD = (.*);$", built.fragment, re.M)
    assert m, "LIVE_CLAUDE_RECORD not injected"
    return json.loads(m.group(1))


# ---------------------------------------------------------------- data (no browser)
def test_the_fixture_has_calls_but_nothing_graded(built):
    b = block(built)
    assert b == {"season": 2026, "week": 4, "through_week": None, "agree": None, "alone": None}
    assert contract.problems("LIVE_CLAUDE_RECORD", b) == []


def test_only_the_record_is_cut_out():
    raw = {"season": 2026, "week": 5, "calls": [{"name": "must not ride along"}], "games": {},
           "record": {"agree": {"w": 7, "l": 5, "push": 1, "void": 0, "n": 12, "hit": 0.583},
                      "disagree": {"claude": {"w": 8, "l": 9, "push": 0, "void": 2, "n": 17, "hit": 0.471},
                                   "model": {"w": 9, "l": 8, "push": 0, "void": 2}},
                      "claude": {"w": 15, "l": 14}, "weeks": [{"week": 3}, {"week": 4}]}}
    assert slips.claude_record(raw) == GRADED
    assert contract.problems("LIVE_CLAUDE_RECORD", GRADED) == []


def test_no_file_or_no_record_is_optional():
    assert slips.claude_record(None) is None, "no file: no row at all"
    assert contract.problems("LIVE_CLAUDE_RECORD", None) == []
    assert slips.claude_record({"season": 2026, "week": 4, "record": None})["agree"] is None


def test_the_contract_names_a_missing_field():
    assert contract.problems("LIVE_CLAUDE_RECORD", {"season": 2026, "week": 4, "agree": None, "alone": None}) == ["LIVE_CLAUDE_RECORD.through_week"]
    assert contract.problems("LIVE_CLAUDE_RECORD", {**GRADED, "agree": {"w": 1}}) == ["LIVE_CLAUDE_RECORD.agree.l"]
    assert contract.problems("LIVE_CLAUDE_RECORD", {**GRADED, "alone": None}) == ["LIVE_CLAUDE_RECORD.agree and .alone are both there or both null"]
