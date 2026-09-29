"""design/startsit.py: the Takes block, from ff-jarvis's calls, Pitcher List's and the record."""
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


def test_fixture_block_is_whole_and_holds_takes_only():
    """The best spot is not a take (2026-09-29: the matchup is a Ranks tag), so Gibbs and Kittle,
    the fixture's two best spots, are gone; the page orders the rest across positions by `gap`."""
    b = _block()
    contract.validate("LIVE_STARTSIT", b)
    assert [(r["pos"], r["tag"], r["n"], r["gap"]) for r in b["calls"]] == [
        ("QB", "start", "Brock Purdy", 1.67), ("RB", "start", "Chase Brown", 1.33),
        ("WR", "start", "Tee Higgins", 1.33), ("WR", "sit", "Amon-Ra St. Brown", 1.67)]


def test_row_keeps_reason_text_and_places_home_by_the_opponent():
    rows = {r["n"]: r for r in _block()["calls"]}
    assert rows["Tee Higgins"]["why"][1] == {"k": "mx", "t": "PIT D vs WRs: 3rd softest"}
    assert rows["Tee Higgins"]["but"] == ["No red-zone targets in 2 games"]
    assert rows["Tee Higgins"]["home"] is False              # "CIN @ PIT"
    assert rows["Amon-Ra St. Brown"]["home"] is True         # "CHI @ DET"
    assert rows["Amon-Ra St. Brown"]["slug"] == slugify("Amon-Ra St. Brown")


def test_record_comes_from_the_newest_graded_week():
    assert _block()["record"] == {"through": 2, "weeks": [1, 2],
                                  "ours": {"n": 31, "score": 0.324, "score_no_dnp": 0.337},
                                  "pl": {"n": 12, "score": 0.667, "score_no_dnp": 0.667},
                                  "fp": None,   # a grade file from before ff-jarvis graded FantasyPros
                                  "v2": None}   # and before any v2 week (4+) was graded


def test_fantasypros_side_comes_through_when_graded():
    """FantasyPros on our takes (2026-09-29): the other call on each, so its n is ours."""
    calls, pl, grade = load_startsit()
    g = json.loads(json.dumps(grade))
    g["startsit_record"]["fantasypros"] = {"n": 31, "score": 0.676, "score_no_dnp": 0.663}
    assert live_startsit(calls, pl, g, slugify)["record"]["fp"] == {"n": 31, "score": 0.676, "score_no_dnp": 0.663}


def test_last_weeks_pitcher_list_column_is_dropped():
    calls, pl, grade = load_startsit()
    old = json.loads(json.dumps(pl))
    old["week"] = 2
    b = live_startsit(calls, old, grade, slugify)
    assert b["pl"] == [] and b["article"] is None


def test_experts_week_rides_along_so_the_page_can_tell_early_from_agreed():
    """Tuesday the calls are next week's and the expert ranks last week's: no takes because nobody
    has ranked yet, which Blip says differently from 'we agree with the experts' (2026-09-29)."""
    b = _block()
    assert (b["week"], b["experts_week"]) == (3, 3)
    calls, pl, grade = load_startsit()
    early = json.loads(json.dumps(calls))
    early["inputs"]["expert_week"] = 2
    assert live_startsit(early, pl, grade, slugify)["experts_week"] == 2
    early.pop("inputs")
    assert live_startsit(early, pl, grade, slugify)["experts_week"] is None


def test_a_take_carries_its_reasons_and_a_gut_call_none():
    rows = {r["n"]: r for r in _block()["calls"]}
    assert rows["Chase Brown"]["backed"] is True
    assert [w["k"] for w in rows["Chase Brown"]["reasons"]] == ["script", "role"]
    assert rows["Tee Higgins"]["backed"] is False and rows["Tee Higgins"]["reasons"] == []


V2 = {"ours_v2": {"n": 16, "score": 0.47, "clean": {"n": 15, "score": 0.5}, "backed": {"n": 6, "score": 0.58},
                  "gut": {"n": 10, "score": 0.4}, "causes": {"injury": 1, "role": 2, "td": 3, "read": 3}},
      "fantasypros_v2": {"n": 16, "score": 0.53, "clean": {"n": 15, "score": 0.5}}}
CALLS_V2 = [{"name": "Chase Brown", "pos": "RB", "team": "CIN", "call": "START", "score": 1, "cause": "hit",
             "backed": True, "finish": 14},
            {"name": "Tee Higgins", "pos": "WR", "team": "CIN", "call": "START", "score": 0, "cause": "injury",
             "cause_note": "did not play", "backed": False, "finish": None}]


def test_v2_record_and_review_come_through_once_a_v2_week_is_graded():
    """From week 4 (METHODOLOGY 12.64): the clean, backed/gut and causes split, and last week's takes
    with their causes, David's 'let's learn from it'. None before a v2 week is graded."""
    calls, pl, grade = load_startsit()
    assert _block()["record"]["v2"] is None and _block()["review"] is None
    g = json.loads(json.dumps(grade))
    g["week"] = 4
    g["startsit_record"].update(V2)
    g.setdefault("startsit", {})["ours_v2"] = {"calls": CALLS_V2}
    b = live_startsit(calls, pl, g, slugify)
    contract.validate("LIVE_STARTSIT", b)
    v2 = b["record"]["v2"]
    assert v2["ours"]["clean"] == {"n": 15, "score": 0.5} and v2["ours"]["causes"]["injury"] == 1
    assert (v2["ours"]["backed"]["n"], v2["ours"]["gut"]["n"]) == (6, 10)
    assert v2["fp"]["clean"]["score"] == 0.5
    assert b["review"]["week"] == 4
    assert [(r["n"], r["call"], r["cause"]) for r in b["review"]["rows"]] == [
        ("Chase Brown", "start", "hit"), ("Tee Higgins", "start", "injury")]


def test_no_calls_file_is_no_block():
    assert live_startsit(None, None, None, slugify) is None
    contract.validate("LIVE_STARTSIT", None)


def test_no_graded_week_is_no_record():
    calls, pl, _ = load_startsit()
    assert live_startsit(calls, pl, None, slugify)["record"] is None
