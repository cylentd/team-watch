"""design/schedule.py: the kickoff log becomes the block that decides when Live may poll.

The log is append-only and re-states the whole season on every pull, so the same game appears
many times with different `asof` stamps and sometimes different kickoffs. Picking the wrong one
moves a game by minutes, which is enough to have the gate shut while a game is still being
played. That is what most of this file is about.
"""
import json
import pathlib

import pytest

import schedule

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data"


@pytest.fixture(scope="module")
def block():
    return schedule.load_schedule(FIXTURE)


def by_teams(block, away, home):
    return next(g for g in block["games"] if g["away"] == away and g["home"] == home)


def test_a_missing_log_is_not_an_error(tmp_path):
    """The block is optional; without it the page falls back to its idle cadence. Failing the
    build here would mean a machine without ff-jarvis checked out could not build the page."""
    assert schedule.load_schedule(tmp_path) is None


def test_the_latest_asof_wins(block):
    """Both rows describe 2026_02_DET_SEA; the later pull moved kickoff by five minutes."""
    assert by_teams(block, "DET", "SEA")["kickoff"] == "2026-09-14T17:05:00Z"


def test_one_row_per_game(block):
    ids = [(g["away"], g["home"]) for g in block["games"]]
    assert len(ids) == len(set(ids))


def test_team_codes_come_out_in_espns_spelling(block):
    """nflverse says LA and WAS; the club codes /api/live returns say LAR and WSH. The join is
    against ESPN's table, so this block has to have already spoken its dialect."""
    g = by_teams(block, "WSH", "LAR")
    assert g["kickoff"] == "2026-09-14T20:25:00Z"
    assert not [x for x in block["games"] if x["home"] in ("LA", "WAS") or x["away"] in ("LA", "WAS")]


def test_a_row_with_no_kickoff_is_dropped(block):
    """It would read as a game that never starts, and the gate would sit idle through it."""
    assert not [g for g in block["games"] if g["away"] == "DAL"]


def test_a_malformed_line_is_stepped_over(block):
    """Half a schedule still gates better than none, so one bad line is not fatal."""
    assert len(block["games"]) == 3


def test_games_are_sorted_by_kickoff(block):
    kicks = [g["kickoff"] for g in block["games"]]
    assert kicks == sorted(kicks)


def test_every_row_meets_the_contract(block):
    import contract
    assert contract.problems("LIVE_SCHEDULE", block) == []


def test_no_build_clock_is_consulted(block):
    """The whole season ships rather than a window around 'now': this repo pins its fixtures so
    a build is reproducible, and a window would make the output depend on the day it ran."""
    again = schedule.load_schedule(FIXTURE)
    assert json.dumps(again, sort_keys=True) == json.dumps(block, sort_keys=True)
    assert "2026-09-21T20:25:00Z" in [g["kickoff"] for g in block["games"]], \
        "a week-3 game dropped out, so something is filtering by date after all"


def test_report_says_when_there_is_nothing(tmp_path):
    assert "no live file" in schedule.report(None)
    assert "3 games" in schedule.report(schedule.load_schedule(FIXTURE))
