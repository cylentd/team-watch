"""Stats > Ranks > Rest of season, the data side (2026-10-06): ff-jarvis's ros_value.json cut to LIVE_ROS.

The fixture is the real 2026-10-06 run (week 5, stats through week 4, half-PPR), cut to the top 12 at each position
by either scoring plus the fixture's seven players. No browser: the view's own tests are test_ros_view.py and Node's
test_js_ros.py. Until ff-jarvis lands the producer the live data has no block, so absent must build and draw as today."""
import json
import pathlib

import pytest

import build
import contract
import ros
import sources
from test_build import injected

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data" / "ros_value.json"
RAW = json.loads(FIXTURE.read_text(encoding="utf-8"))
PLAYER_KEYS = {"slug", "n", "pos", "team", "rank", "ros_pg", "ros_pts", "games_left", "sched_left", "hist", "espn"}


def player(block, slug):
    return next(p for p in block["players"] if p["slug"] == slug)


def test_the_cut_keeps_only_what_the_page_reads():
    block = ros.live_ros(RAW)
    assert set(block) == {"season", "week", "through_week", "last_week", "generated", "players"}
    assert (block["season"], block["week"], block["last_week"]) == (2026, 5, 17)
    assert len(block["players"]) == len(RAW["players"])
    espn_keys = {"ros_pg", "ros_pts", "rank", "hist"}
    assert [p["slug"] for p in block["players"] if set(p) != PLAYER_KEYS] == []
    assert [p["slug"] for p in block["players"] if set(p["espn"]) != espn_keys] == []


def test_a_players_numbers_pass_through_and_history_is_week_and_rank_only():
    allen = player(ros.live_ros(RAW), "josh-allen")
    assert (allen["n"], allen["pos"], allen["team"], allen["rank"]) == ("Josh Allen", "QB", "BUF", 1)
    assert (allen["ros_pg"], allen["ros_pts"], allen["games_left"], allen["sched_left"]) == (23.61, 231.4, 9.8, 12)
    assert allen["hist"] == [[3, 1], [4, 1], [5, 1]], "rank by week, never points: they fall for everyone"
    assert allen["espn"]["hist"] == [[3, 1], [4, 1], [5, 1]]
    assert (allen["espn"]["ros_pg"], allen["espn"]["ros_pts"]) == (27.26, 267.3), "ESPN's own scaling, as the file has it"
    miller = player(ros.live_ros(RAW), "kendre-miller")
    assert miller["hist"] == [[4, 48], [5, 47]], "a player with a shorter history keeps just those weeks"


def test_no_file_or_no_players_is_none():
    assert ros.live_ros(None) is None
    assert ros.live_ros({}) is None
    assert ros.live_ros({**RAW, "players": []}) is None


def test_the_cut_meets_the_contract():
    assert contract.problems("LIVE_ROS", ros.live_ros(RAW)) == []
    assert contract.problems("LIVE_ROS", None) == []
    broken = ros.live_ros(RAW)
    del broken["players"][3]["ros_pts"]
    assert contract.problems("LIVE_ROS", broken) == ["LIVE_ROS.players[3].ros_pts"], "a dropped field fails by name"


def test_the_feed_block_wins_over_the_file(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"ros_value": {"data": {"week": 9, "players": [{"slug": "x"}]}}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert ros.load_ros_value()["week"] == 9
    feed.write_text("{}", encoding="utf-8")
    assert ros.load_ros_value()["week"] == 5, "no feed block: the file is read"


def test_the_fixture_build_carries_the_block(built):
    block = injected(built.fragment)["LIVE_ROS"]
    assert block["week"] == 5 and len(block["players"]) == len(RAW["players"])
    assert any("LIVE_ROS" in line or "Rest of season" in line for line in built.report), "the build report says so"


@pytest.mark.integration      # a real build of the page
def test_no_block_builds_and_injects_null(monkeypatch):
    """Today's live data: ff-jarvis has not written the file, and the feed has no block."""
    real = sources.read_first
    monkeypatch.setattr(sources, "read_first", lambda *paths: None if any(p.name == "ros_value.json" for p in paths) else real(*paths))
    made = build.render()
    assert "const LIVE_ROS = null;" in made.fragment
    assert any("Rest of season: none" in line for line in made.report), made.report
