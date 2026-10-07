"""Stats > Ranks > Rest of season, the playoff weeks and FantasyPros (2026-10-07): ff-jarvis's ros_value po_* fields
and ros_compare.json cut into LIVE_ROS. Data side only, no page: the view's tests are test_ros_view.py and test_js_ros.py."""
import json
import pathlib

import pytest

import contract
import ros
import sources

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data" / "ros_value.json"
RAW = json.loads(FIXTURE.read_text(encoding="utf-8"))
COMPARE = json.loads((FIXTURE.parent / "ros_compare.json").read_text(encoding="utf-8"))
ROW = {"key": "jared goff", "fp_pos_rank": 8, "fp_pts": 252.0}


def player(block, slug):
    return next(p for p in block["players"] if p["slug"] == slug)


def test_the_playoff_weeks_and_each_players_playoff_numbers_pass_through():
    block = ros.live_ros(RAW)
    assert block["po_weeks"] == [15, 16, 17]
    allen = player(block, "josh-allen")
    assert (allen["po_rank"], allen["po_pts"], allen["po_games"]) == (1, 57.9, 2.45)
    hall = player(block, "breece-hall")
    assert (hall["rank"], hall["po_rank"]) == (29, 30), "the playoff order is its own"


def test_a_file_without_playoff_fields_has_none_and_still_builds():
    old = json.loads(json.dumps(RAW))
    old["rules"].pop("playoffs")
    for p in old["players"]:
        for k in ("po_rank", "po_pts", "po_games"):
            p.pop(k)
    block = ros.live_ros(old)
    assert block["po_weeks"] is None
    assert {p["po_rank"] for p in block["players"]} == {None}
    assert contract.problems("LIVE_ROS", block) == []


def test_fantasypros_joins_by_name_key_with_the_gap_against_our_current_rank():
    block = ros.live_ros(RAW, COMPARE)
    assert block["fp"] == {"experts": 6, "updated": "2026-10-07T01:20Z"}
    goff = player(block, "jared-goff")
    assert goff["fp"] == {"rank": 8, "gap": 8 - goff["rank"], "pts": 252.0}
    hall = player(block, "breece-hall")
    assert hall["fp"] == {"rank": 20, "gap": -9, "pts": hall["fp"]["pts"]}, "gap is FP's position rank less ours (29)"
    assert player(block, "josh-allen")["fp"] is None, "a player the compare file lacks is blank, not an error"
    assert contract.problems("LIVE_ROS", block) == []


@pytest.mark.parametrize("positions", [
    {"QB": {"players": [ROW], "higher": [], "lower": []}},
    {"QB": {"higher": [ROW], "lower": []}},
    {"QB": {"lower": [ROW]}},
], ids=["players list", "old gap lists", "lower list only"])
def test_every_player_in_the_players_list_gets_fp_and_old_files_fall_back_to_the_gap_lists(positions):
    goff = player(ros.live_ros(RAW, {"experts": 6, "positions": positions}), "jared-goff")
    assert goff["fp"] == {"rank": 8, "gap": 8 - goff["rank"], "pts": 252.0}


def test_a_fantasypros_row_under_another_position_does_not_match_a_same_named_player():
    compare = {"experts": 6, "positions": {"WR": {"players": [ROW]}}}
    assert player(ros.live_ros(RAW, compare), "jared-goff")["fp"] is None


def test_a_fantasypros_row_with_no_position_rank_is_blank():
    compare = {"experts": 6, "positions": {"QB": {"players": [{**ROW, "fp_pos_rank": None}]}}}
    assert player(ros.live_ros(RAW, compare), "jared-goff")["fp"] is None


def test_no_compare_file_means_no_fp_anywhere():
    block = ros.live_ros(RAW, None)
    assert block["fp"] is None and {p["fp"] for p in block["players"]} == {None}


def test_the_compare_loader_prefers_the_feed_block(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"ros_compare": {"data": {"experts": 9, "positions": {"QB": {}}}}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert ros.load_ros_compare()["experts"] == 9
    feed.write_text("{}", encoding="utf-8")
    assert ros.load_ros_compare()["experts"] == 6, "no feed block: the file is read"
