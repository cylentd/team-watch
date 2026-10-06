"""design/league_recap.py against the 4-team fixture: keys match the team switch's, awards,
head-to-head both ways, champions, records, and no past team name ever reaches the page."""
import json
import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))
import contract                              # noqa: E402
from league_recap import live_league, live_league_yahoo, case_rosters, _past_name   # noqa: E402
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
    pick = lambda d, *k: {x: d[x] for x in k}
    assert pick(a["top"], "id", "v") == {"id": 14, "v": 137.35} and pick(a["low"], "id", "v") == {"id": 12, "v": 101.35}
    assert pick(a["blow"], "id", "opp", "v") == {"id": 14, "opp": 15, "v": 26.45}
    # Two games: Stole one is the closer (16.05), so it is the nail-biter too.
    assert pick(a["close"], "id", "opp", "v") == {"id": 1, "opp": 12, "v": 16.05}
    assert pick(a["luck"], "id", "v") == {"id": 1, "v": 117.4} and pick(a["unluck"], "id", "v") == {"id": 15, "v": 110.9}


def test_the_nail_biter_is_the_closest_game_even_when_robbed_or_stole_one_names_it():
    from league_recap import awards
    g = lambda h, a, hp, ap: {"home": h, "away": a, "hp": hp, "ap": ap, "winner": "home" if hp > ap else "away"}
    # 1-2: the highest losing score (2 robbed by 2.18) is also the closest game, so it is the nail-biter too.
    a = awards([g(1, 2, 114.24, 112.06), g(3, 4, 146.62, 96.46), g(5, 6, 101.0, 95.5), g(7, 8, 80.0, 60.0)])
    assert (a["unluck"]["id"], a["unluck"]["opp"]) == (2, 1)
    assert (a["close"]["id"], a["close"]["opp"], a["close"]["v"]) == (1, 2, 2.18)


def test_the_nail_biter_is_the_smallest_margin_of_all_decided_games():
    from league_recap import awards
    g = lambda h, a, hp, ap: {"home": h, "away": a, "hp": hp, "ap": ap, "winner": "home" if hp > ap else "away"}
    # Week 4 shape: Phillip-Jon (2.50) holds Robbed or Stole one; David-Theo (5.90) is the closest of the rest.
    a = awards([g(1, 2, 90.0, 87.5), g(3, 4, 120.0, 114.1), g(5, 6, 140.0, 80.0), g(7, 8, 70.0, 130.0)])
    assert (a["close"]["id"], a["close"]["opp"], a["close"]["v"]) == (1, 2, 2.5)


def test_awards_carry_their_proof(league):
    """Each superlative carries what its proof line says: the opponent, the margin, the rank."""
    a = league["weeks"][0]["awards"]
    top, low = a["top"], a["low"]
    assert top["rank"] == 1 and low["rank"] == low["of"] == 4
    assert (a["luck"]["m"], a["luck"]["rank"]) == (16.05, 2) and (a["unluck"]["m"], a["unluck"]["rank"]) == (-26.45, 3)
    assert round(a["blow"]["p"] - a["blow"]["op"], 2) == a["blow"]["v"]


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


@pytest.fixture(scope="module")
def yahoo():
    read = lambda n: json.loads((FIX / n).read_text(encoding="utf-8"))
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify)
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    return b


def test_yahoo_keys_scope_and_record(yahoo):
    keys = {t["id"]: t["key"] for t in yahoo["teams"]}
    assert keys[9] == "yahoo" and keys[10] == "yahoo-jaxon-the-box"
    assert yahoo["scope"] == "all" and yahoo["since"] == 2024
    me = next(t for t in yahoo["teams"] if t["id"] == 9)
    assert (me["w"], me["l"]) == (1, 1)


def test_yahoo_head_to_head_joins_past_seasons_by_owner(yahoo):
    """2025's team 10 is today's 9 and 2025's team 2 is today's 7 (the owner map), so their 2025
    games count toward 9 v 7; 2025's team 9 has left (former-1) and counts toward no one today."""
    assert yahoo["h2h"]["9"]["7"] == {"w": 1, "l": 1, "t": 0, "since": 2025, "big": {"v": 10.0, "y": 2025, "wk": 1},
                                      "last": {"y": 2025, "wk": 2, "won": False, "tie": False},
                                      "m": [[2025, 1, 10.0, 0], [2025, 2, -1.0, 0]]}
    assert yahoo["h2h"]["9"]["10"]["since"] == 2026
    assert yahoo["now"] == [{"a": 9, "b": 3}, {"a": 10, "b": 7}]


def test_yahoo_champions_carry_that_years_name_and_todays_team(yahoo):
    assert [(c["y"], c["id"], c["name"]) for c in yahoo["champs"]] == [(2025, 10, "Am I COOKed?"), (2024, 3, None)]


def test_yahoo_records_name_a_past_team_as_it_was_that_year(yahoo):
    """A record from a past season carries that year's name and, when the manager is still here,
    today's id (the page adds "now ..."); a manager who left has no id, and a default-shaped name
    ("Team Smith") ships as nothing."""
    f = {x["k"]: x for x in yahoo["facts"]}
    assert f["high"] == {"k": "high", "id": 10, "name": "Am I COOKed?", "v": 170.0, "y": 2025, "wk": 1}
    assert f["low"]["id"] is None and f["low"]["name"] is None           # former-1 was "Team Smith", 30.0
    assert (f["blow"]["id"], f["blow"]["name"], f["blow"]["opp"], f["blow"]["v"]) == (10, "Am I COOKed?", None, 140.0)
    assert (f["pf"]["id"], f["pf"]["v"]) == (10, 290.0)
    assert "titles" not in f and "Team Smith" not in json.dumps(yahoo)


def test_yahoo_without_an_owner_map_stays_this_season():
    read = lambda n: json.loads((FIX / n).read_text(encoding="utf-8"))
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), None,
                          read("league_rosters.json"), slugify)
    assert b["scope"] == "season" and b["h2h"]["9"].get("7") is None
    assert {x["k"]: x for x in b["facts"]}["high"]["id"] is None


def test_no_season_file_is_none():
    assert live_league_yahoo(None, None, None, None, slugify) is None
    assert live_league(None, None, None, slugify) is None
    contract.validate("LIVE_LEAGUE", None)


def test_case_rosters_keep_only_the_shelves_seasons_and_the_sheets_fields():
    p = {"name": "Joe Burrow", "pos": "QB", "nfl": "CIN", "slot": "QB", "pts": 20.4, "yahoo_id": 1}
    raw = {"seasons": {"2025": {"champ": {"week": 17, "players": [p]}, "last": {"week": 17, "players": []}},
                       "2018": {"champ": None, "last": None},
                       "2017": {"champ": {"week": 16, "players": [p]}}}}
    out = case_rosters(raw, [{"y": 2025}, {"y": 2018}], [{"y": 2025}])
    # 2025's empty last-place side and 2018's unread one stay out, so their slots do not open;
    # 2017 is on no shelf.
    assert out == {"2025": {"champ": {"week": 17, "players": [{k: p[k] for k in ("name", "pos", "nfl", "slot", "pts")}]}}}
    assert case_rosters(None, [{"y": 2025}], []) == {}


def test_a_chosen_name_shaped_like_the_site_default_is_kept():
    assert _past_name("Team Mahomie") == "Team Mahomie"
    assert _past_name("Team Smith") is None
