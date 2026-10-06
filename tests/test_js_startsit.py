"""Start/Sit's shared pieces (data/startsit.js) in Node: the kickoff and matchup words a row prints,
and the record's own reading. The rows that print them are checked in the browser (test_startsit*)."""
import pytest


@pytest.fixture(scope="module")
def ss(node_js):
    return node_js("data/startsit.js")


def test_kickoff_is_pacific_wall_clock_without_a_comma(ss):
    assert ss("muKick", {"kick": "2026-10-04T17:00:00Z"}) == "Sun 10:00 AM"
    assert ss("muKick", {"kick": "2026-10-05T00:15:00Z"}) == "Sun 5:15 PM"     # still Sunday in Pacific
    assert ss("muKick", {"kick": None}) is None


def test_the_calls_own_club_comes_first(ss):
    assert ss("muVs", {"team": "DAL", "opp": "BAL", "home": True}) == "DAL vs BAL"
    assert ss("muVs", {"team": "LAC", "opp": "BUF", "home": False}) == "LAC @ BUF"
    assert ss("muVs", {"team": "LAC", "opp": None}) == "LAC"


def test_clubs_are_escaped(ss):
    assert ss("muVs", {"team": "<i>", "opp": "BUF", "home": True}) == "&lt;i&gt; vs BUF"


def test_the_game_line_adds_the_kickoff_only_when_there_is_one(ss):
    row = {"team": "CIN", "opp": "PIT", "home": False}
    assert ss("muGame", {**row, "kick": "2026-10-04T17:00:00Z"}) == "CIN @ PIT · Sun 10:00 AM"
    assert ss("muGame", row) == "CIN @ PIT"


def blank():
    return {k: {"hit": 0, "miss": 0, "void": 0} for k in ("smash", "start", "sit")} | {"weeks": []}


def test_a_record_counts_once_any_call_is_graded(ss):
    assert ss("ss3Graded", blank()) is False
    assert ss("ss3Graded", blank() | {"weeks": [4]}) is True
    voided = blank()
    voided["sit"]["void"] = 1                     # a voided call was graded all the same
    assert ss("ss3Graded", voided) is True
    assert ss("ss3Wl", {"hit": 5, "miss": 2}) == "5-2"
