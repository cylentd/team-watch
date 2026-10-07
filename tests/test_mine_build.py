"""What design/build.py and design/myteams.py do now that the page carries no "mine" flag (2026-10-06). No page.

Whose lines are "mine" is the reader's follow list. The build still reads David's rosters for three things, and
these tests call the functions directly: the position and team of a name only the touchdown market lists
(myteams.roster_index), the order of the lines the model has no price for (build.live_props), and the count in
the build report (build.report_sources).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import build  # noqa: E402
from myteams import roster_index  # noqa: E402


def test_the_roster_index_gives_each_players_position_and_team_once_and_skips_a_league_with_no_file():
    espn = {"roster": [{"n": "Zed Wide", "pos": "WR", "team": "AAA"}, {"n": "Abe Back", "pos": "RB", "team": "BBB"}]}
    yahoo = {"roster": [{"n": "Zed Wide", "pos": "WR", "team": "ZZZ"}]}
    assert roster_index(("espn", espn), ("ayo", None), ("yahoo", yahoo)) == {
        "zed-wide": {"pos": "WR", "team": "AAA"}, "abe-back": {"pos": "RB", "team": "BBB"}}


def line(name, pos, commence):
    return {"market": "REC", "player": name, "position": pos, "team": "AAA", "side": "Over", "line": 40.5,
            "price": -110, "game": "AAA @ BBB", "commence": commence, "updated": "2026-09-12 00:00:00",
            "book": "DraftKings"}


@pytest.fixture
def unpriced(monkeypatch):
    """live_props over six lines the model prices none of; one is marked out for the week."""
    rows = [line("Early Tight", "TE", "2026-09-13 17:00:00"), line("Zed Wide", "WR", "2026-09-13 17:00:00"),
            line("Abe Back", "RB", "2026-09-13 17:00:00"), line("Undated Quarter", "QB", None),
            line("Late Back", "RB", "2026-09-13 20:00:00"), line("Out Guy", "WR", "2026-09-10 17:00:00")]
    raw = {"props": rows, "source": "test", "fetched": "2026-09-12", "events": 1, "failed": []}
    model = {"lines": [{"name": "Out Guy", "market": "REC", "line": 40.5, "p_over": None, "flag": "out"}],
             "through": "2026 wk1", "week": 1, "generated": "2026-09-12", "status_fetched": None, "not_playing": 1}
    monkeypatch.setattr(build, "load_props_raw", lambda: (raw, "test"))
    monkeypatch.setattr(build, "load_model_raw", lambda: model)
    monkeypatch.setattr(build, "load_wrcb", lambda: None)
    monkeypatch.setattr(build, "nfl_roster", lambda: {})
    return build.live_props(set(), {})


def test_lines_the_model_has_no_price_for_go_by_kickoff_then_position_then_name_and_an_out_player_last(unpriced):
    assert [p["n"] for p in unpriced["props"]] == [
        "Undated Quarter", "Abe Back", "Zed Wide", "Early Tight", "Late Back", "Out Guy"]


def test_a_line_carries_no_roster_of_his(unpriced):
    assert [p["n"] for p in unpriced["props"] if {"mine", "leagues"} & set(p)] == []


def test_the_report_counts_the_lines_on_my_rosters_once_each():
    mine = [("espn", {"roster": [{"n": "Zed Wide"}, {"n": "Abe Back"}], "league": "L", "updated": "u"}), ("ayo", None)]
    props = {"props": [{"n": "Zed Wide"}, {"n": "Zed Wide"}, {"n": "Other One"}], "players": 2, "events": 1,
             "books": ["DraftKings"], "fetched": "f", "origin": "o", "windows": [], "model": None}
    report = []
    build.report_sources(report, mine, props, None, None, None, [])
    assert [r for r in report if r.startswith("Props:")] == [
        "Props: 3 lines, 2 players, 1 games, DraftKings, pulled f (from o), 2 on my rosters"]
