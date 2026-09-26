"""design/league_recap.py against the 4-team fixture: keys match the team switch's, awards,
head-to-head both ways, champions, records, and no past team name ever reaches the page."""
import json
import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))
import contract                              # noqa: E402
from league_recap import live_league         # noqa: E402
from _espn import slugify                    # noqa: E402

FIX = REPO / "tests" / "fixtures" / "data"


@pytest.fixture(scope="module")
def league():
    read = lambda n: json.loads((FIX / n).read_text(encoding="utf-8"))
    b = live_league(read("espn_league.json"), read("espn_league_history.json"), read("espn_rosters.json"), slugify)
    contract.validate("LIVE_LEAGUE", b)
    return b


def test_keys_match_the_team_switch(league):
    keys = {t["id"]: t["key"] for t in league["teams"]}
    assert keys[12] == "espn" and keys[1] == "espn-run-it-back" and keys[15] == "espn-teamminh"


def test_record_is_espns_own_standing(league):
    """The hero's record: ESPN's standing, which counts the top-half bonus win (3-1 in the fixture
    after 1-1 head to head), never a count of games won."""
    me = next(t for t in league["teams"] if t["id"] == 12)
    assert (me["w"], me["l"], me["t"]) == (3, 1, 0)


def test_week_awards(league):
    assert [w["week"] for w in league["weeks"]] == [1, 2]
    a = league["weeks"][0]["awards"]
    assert a["top"] == {"id": 14, "v": 137.35} and a["low"] == {"id": 12, "v": 101.35}
    assert a["blow"] == {"id": 14, "opp": 15, "v": 26.45} and a["close"] == {"id": 1, "opp": 12, "v": 16.05}
    assert a["luck"] == {"id": 1, "v": 117.4} and a["unluck"] == {"id": 15, "v": 110.9}


def test_this_weeks_pairings_and_head_to_head(league):
    assert league["now"] == [{"a": 14, "b": 12}, {"a": 1, "b": 15}]
    me, salty = league["h2h"]["12"]["14"], league["h2h"]["14"]["12"]
    assert (me["w"], me["l"], me["since"]) == (1, 1, 2024)
    assert me["big"] == {"v": 60.0, "y": 2024, "wk": 2}
    assert me["last"] == {"y": 2025, "wk": 2, "won": False, "tie": False}
    assert (salty["w"], salty["l"]) == (1, 1) and salty["big"]["v"] == 5.0


def test_champions_and_records(league):
    assert [(c["y"], c["id"]) for c in league["champs"]] == [(2025, 1), (2024, 12)]
    f = {x["k"]: x for x in league["facts"]}
    assert f["high"] == {"k": "high", "id": 1, "v": 150.5, "y": 2024, "wk": 2}
    assert f["blow"]["id"] == 12 and f["blow"]["v"] == 60.0
    assert f["low"]["id"] == 2          # a team that has left: the page draws it as a former team
    assert "streak" not in f and "titles" not in f   # under 3 straight, nobody with 2 titles
    assert f["pf"] == {"k": "pf", "id": 1, "v": 260.5, "y": 2024}
    assert league["since"] == 2024


def test_no_past_name_ships(league):
    text = json.dumps(league)
    for old in ("Team Oldname", "The Evil Twin", "Team Gone", "Back Crack"):
        assert old not in text


def test_no_season_file_is_none():
    assert live_league(None, None, None, slugify) is None
    contract.validate("LIVE_LEAGUE", None)
