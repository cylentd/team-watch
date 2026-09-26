"""design/startsit.py: the Matchups block, from ff-jarvis's calls, Pitcher List's and the record."""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
from sources import load_startsit  # noqa: E402
from startsit import live_startsit  # noqa: E402


def _block():
    return live_startsit(*load_startsit(), slugify)


def test_fixture_block_is_whole_and_ordered_by_position_then_tag():
    b = _block()
    contract.validate("LIVE_STARTSIT", b)
    assert [(r["pos"], r["tag"], r["n"]) for r in b["calls"]] == [
        ("QB", "start", "Brock Purdy"), ("RB", "best", "Jahmyr Gibbs"), ("RB", "start", "Chase Brown"),
        ("WR", "start", "Tee Higgins"), ("WR", "sit", "Amon-Ra St. Brown"), ("TE", "best", "George Kittle")]


def test_row_keeps_reason_text_and_places_home_by_the_opponent():
    rows = {r["n"]: r for r in _block()["calls"]}
    assert rows["Tee Higgins"]["why"][1] == {"k": "mx", "t": "PIT D vs WRs: 3rd softest"}
    assert rows["Tee Higgins"]["but"] == ["No red-zone targets in 2 games"]
    assert rows["Tee Higgins"]["home"] is False              # "CIN @ PIT"
    assert rows["Jahmyr Gibbs"]["home"] is True              # "CHI @ DET"
    assert rows["Amon-Ra St. Brown"]["slug"] == slugify("Amon-Ra St. Brown")


def test_record_comes_from_the_newest_graded_week():
    assert _block()["record"] == {"through": 2, "weeks": [1, 2],
                                  "ours": {"n": 31, "score": 0.324, "score_no_dnp": 0.337},
                                  "pl": {"n": 12, "score": 0.667, "score_no_dnp": 0.667}}


def test_last_weeks_pitcher_list_column_is_dropped():
    calls, pl, grade = load_startsit()
    old = json.loads(json.dumps(pl))
    old["week"] = 2
    b = live_startsit(calls, old, grade, slugify)
    assert b["pl"] == [] and b["article"] is None


def test_no_calls_file_is_no_block():
    assert live_startsit(None, None, None, slugify) is None
    contract.validate("LIVE_STARTSIT", None)


def test_no_graded_week_is_no_record():
    calls, pl, _ = load_startsit()
    assert live_startsit(calls, pl, None, slugify)["record"] is None
