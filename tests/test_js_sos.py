"""Schedule (Stats > hash #schedule): the ranking per window and position, in Node (data/sos.js, 2026-10-05, unit U7c).

LIVE_SOS is ff-jarvis's sos.json passed through (design/sos.py). The page computes no number: it orders
the 32 teams by the file's own `rank` (1 = easiest), lays each team's opponents out week by week with the
byes marked, and prints the file's `pts_pg`. The fixture is the real 2026-10-05 run, from week 5.
What the view looks like at 360 px is test_sos_view.py, in the browser."""
import json
import pathlib

import pytest

FIX = json.loads((pathlib.Path(__file__).parent / "fixtures" / "data" / "sos.json").read_text(encoding="utf-8"))
POS = ["QB", "RB", "WR", "TE"]
WINS = ["next4", "ros", "playoffs"]


@pytest.fixture(scope="module")
def sos(node_js):
    return node_js("data/sos.js")


def team(rows, code):
    return next(r for r in rows if r["team"] == code)


@pytest.mark.parametrize("pos", POS)
@pytest.mark.parametrize("win", WINS)
def test_all_32_teams_come_easiest_first_by_the_files_own_rank(sos, pos, win):
    v = sos("sosView", FIX, pos, win)
    rows = v["rows"]
    assert len(rows) == 32
    ranks = [r["rank"] for r in rows]
    assert ranks == sorted(ranks) and ranks[0] == 1
    for r in rows:
        assert r["rank"] == FIX["teams"][r["team"]][pos][win]["rank"]      # never re-ranked on the page
        assert r["pts"] == FIX["teams"][r["team"]][pos][win]["pts_pg"]     # printed as the file has it
    pts = [r["pts"] for r in rows]
    assert pts == sorted(pts, reverse=True)                                 # easiest = most points allowed


def test_the_window_decides_the_weeks_drawn(sos):
    assert sos("sosView", FIX, "RB", "next4")["weeks"] == [5, 6, 7, 8]
    assert sos("sosView", FIX, "RB", "playoffs")["weeks"] == [15, 16, 17]
    assert sos("sosView", FIX, "RB", "ros")["weeks"] == list(range(5, 18))


def test_a_bye_is_a_marked_cell_and_not_a_game(sos):
    rows = sos("sosView", FIX, "QB", "next4")["rows"]
    kc = team(rows, "KC")["cells"]                       # KC is off in week 5 (the file's `bye`)
    assert kc[0] == {"week": 5, "opp": None, "bye": True}
    assert kc[1] == {"week": 6, "opp": "LAC", "bye": False}
    assert team(rows, "KC")["games"] == 3                # the file's own count, a bye is not a game


def test_a_team_with_no_bye_in_the_window_has_a_game_every_week(sos):
    cells = team(sos("sosView", FIX, "QB", "playoffs")["rows"], "KC")["cells"]
    assert [(c["week"], c["opp"], c["bye"]) for c in cells] == [(15, "NE", False), (16, "SF", False), (17, "LAC", False)]


def test_the_label_the_weights_and_the_span_come_from_the_file(sos):
    v = sos("sosView", FIX, "WR", "ros")
    assert v["label"] == FIX["label"]
    assert v["span"] == "5–17"
    assert sos("sosView", FIX, "WR", "playoffs")["span"] == "15–17"


def test_no_file_is_the_empty_state(sos):
    assert sos("sosView", None, "RB", "next4") is None
    assert sos("sosView", {"teams": {}}, "RB", "next4") is None


def test_an_unknown_position_or_window_is_the_empty_state(sos):
    assert sos("sosView", FIX, "K", "next4") is None
    assert sos("sosView", FIX, "RB", "week9") is None


def test_ties_share_a_rank_and_sort_by_team_and_a_team_with_no_game_goes_last(sos):
    cut = {"label": "L", "windows": {"next4": [5, 6]}, "teams": {
        "ZZZ": {"schedule": {"next4": {"games": 2, "bye": [], "opps": [{"week": 5, "opp": "AAA"}, {"week": 6, "opp": "BBB"}]}},
                "RB": {"next4": {"games": 2, "pts_pg": 20.0, "rank": 1}}},
        "BBB": {"schedule": {"next4": {"games": 2, "bye": [], "opps": [{"week": 5, "opp": "AAA"}, {"week": 6, "opp": "ZZZ"}]}},
                "RB": {"next4": {"games": 2, "pts_pg": 20.0, "rank": 1}}},
        "OFF": {"schedule": {"next4": {"games": 0, "bye": [5, 6], "opps": []}},
                "RB": {"next4": {"games": 0, "pts_pg": None, "rank": None}}},
        "AAA": {"schedule": {"next4": {"games": 2, "bye": [], "opps": [{"week": 5, "opp": "BBB"}, {"week": 6, "opp": "ZZZ"}]}},
                "RB": {"next4": {"games": 2, "pts_pg": 18.5, "rank": 3}}},
    }}
    rows = sos("sosView", cut, "RB", "next4")["rows"]
    assert [(r["team"], r["rank"]) for r in rows] == [("BBB", 1), ("ZZZ", 1), ("AAA", 3), ("OFF", None)]
    assert [c["bye"] for c in rows[3]["cells"]] == [True, True]


def test_the_view_has_no_verdict_word():
    """A descriptive page (plan U7): neither the file's label nor the page's own words say start, sit, buy or sell."""
    import re
    copy = json.loads((pathlib.Path(__file__).parents[1] / "design" / "src" / "content.json").read_text(encoding="utf-8"))
    words = [v for k, v in copy.items() if k.startswith("sos.")] + [FIX["label"]]
    assert len(words) > 10
    assert not [w for w in words if re.search(r"\b(start|sit|buy|sell|stream|add|drop|trade)\b", w, re.I)]
    assert FIX["label"].startswith("Context only") and "Not tested" in FIX["label"]
