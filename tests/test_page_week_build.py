"""The page week reaches the build from ff-jarvis, never computed here (2026-10-05).

sources.load_page_week reads the `page_week` feed block first and `page_week.json` second;
schedule.load_schedule puts its week in LIVE_SCHEDULE.week; a missing block leaves the week null and
the build report says WARNING. The fixture file says week 2, consistent with the fixture games log
(no game has a score, so week 2's first kickoff is the next one)."""
import json
import pathlib

import pytest

import schedule
import sources

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data"


def feed_with(tmp_path, block):
    path = tmp_path / "feed.json"
    path.write_text(json.dumps({"page_week": {"data": {"generated": "2026-10-06T00:00", **block}, "fetched": "2026-10-06T00:00"}}), encoding="utf-8")
    return path


def test_the_fixture_build_takes_its_week_from_the_page_week_file():
    assert schedule.load_schedule(FIXTURE)["week"] == 2
    assert json.loads((FIXTURE / "page_week.json").read_text(encoding="utf-8"))["week"] == 2


def test_the_week_is_read_not_derived_from_the_games(tmp_path, monkeypatch):
    """The log holds weeks 2 and 3; the block says 3, and the block wins."""
    monkeypatch.setattr(sources, "FEED", feed_with(tmp_path, {"season": 2026, "week": 3}))
    assert schedule.load_schedule(FIXTURE)["week"] == 3


def test_the_feed_block_beats_the_file(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "FEED", feed_with(tmp_path, {"season": 2026, "week": 7}))
    assert sources.load_page_week(FIXTURE)["week"] == 7


def test_a_feed_without_the_block_falls_back_to_the_file(tmp_path, monkeypatch):
    path = tmp_path / "feed.json"
    path.write_text(json.dumps({"status": {}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", path)
    assert sources.load_page_week(FIXTURE)["week"] == 2


def test_no_block_anywhere_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "FEED", tmp_path / "missing.json")
    assert sources.load_page_week(tmp_path) is None


def test_a_missing_block_makes_the_week_null_and_the_report_warns(tmp_path, monkeypatch):
    games = tmp_path / "history" / "games"
    games.mkdir(parents=True)
    (games / "2026-09-11.jsonl").write_text(
        json.dumps({"asof": "2026-09-11T05:51", "game_id": "g", "season": 2026, "week": 2,
                    "kickoff": "2026-09-14T17:05:00Z", "home": "SEA", "away": "DET"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", tmp_path / "missing.json")
    block = schedule.load_schedule(tmp_path)
    assert block["week"] is None
    assert "WARNING: no page week" in schedule.report(block)


def test_a_season_with_no_game_left_has_a_null_week(tmp_path, monkeypatch):
    """ff-jarvis publishes week null when every game is final; that is not an error and stays null."""
    monkeypatch.setattr(sources, "FEED", feed_with(tmp_path, {"season": 2026, "week": None}))
    assert sources.load_page_week(FIXTURE)["week"] is None
    assert schedule.load_schedule(FIXTURE)["week"] is None


def test_a_week_with_games_is_not_a_warning():
    assert "WARNING" not in schedule.report(schedule.load_schedule(FIXTURE))
