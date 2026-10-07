"""Stats > Ranks > Rest of season (data/ros.js, 2026-10-06): the rows, the chart and the scoring, in Node.

The numbers are ff-jarvis's (LIVE_ROS via design/ros.py, METHODOLOGY 12.97); the page sorts nothing but a tie, picks the
reader's scoring, and places points on a chart. The fixture is the real 2026-10-06 run (week 5, history weeks 3-5)."""
import copy
import json
import pathlib

import pytest

import ros as ros_cut

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "data" / "ros_value.json"
BLOCK = ros_cut.live_ros(json.loads(FIXTURE.read_text(encoding="utf-8")))
BOX = {"w": 330, "h": 236, "l": 26, "r": 104, "t": 10, "b": 20}


@pytest.fixture(scope="module")
def ros(node_js):
    return node_js("data/ros.js", globals={"LIVE_ROS": BLOCK})


def slugs(rows):
    return [r["slug"] for r in rows]


@pytest.mark.req("Ranks", ac="Rest of season: a position's list is in the file's rank order")
def test_a_position_lists_in_the_files_rank_order_with_the_row_the_page_draws(ros):
    rows = ros("rosRows", BLOCK, "WR", "half")
    assert rows[0]["slug"] == "jaxon-smithnjigba" and rows[1]["slug"] == "amonra-st-brown"
    assert [r["rank"] for r in rows] == sorted(r["rank"] for r in rows)
    assert {r["pos"] for r in rows} == {"WR"}
    allen = ros("rosRows", BLOCK, "QB", "half")[0]
    assert allen == {"slug": "josh-allen", "n": "Josh Allen", "pos": "QB", "team": "BUF", "rank": 1, "pts": 231.4, "pg": 23.61,
                     "games": 9.8, "of": 12, "hist": [[3, 1], [4, 1], [5, 1]], "fp": None}


@pytest.mark.req("Ranks", ac="Rest of season: a Playoffs toggle ranks the playoff weeks")
def test_the_playoff_span_lists_by_playoff_rank_with_playoff_points_and_games(ros):
    rows = ros("rosRows", BLOCK, "WR", "half", "po")
    raw = {p["slug"]: p for p in BLOCK["players"]}
    assert [r["rank"] for r in rows] == sorted(r["rank"] for r in rows)
    assert rows[0]["rank"] == raw[rows[0]["slug"]]["po_rank"] and rows[0]["pts"] == raw[rows[0]["slug"]]["po_pts"]
    assert (rows[0]["games"], rows[0]["of"]) == (raw[rows[0]["slug"]]["po_games"], 3), "of = the three playoff weeks"
    assert rows[0]["hist"] == []
    espn = ros("rosRows", BLOCK, "WR", "espn", "po")
    assert slugs(espn) == slugs(rows) and [r["pts"] for r in espn] == [r["pts"] for r in rows], "playoff numbers are half-PPR only"


def test_a_playoff_rank_tie_goes_to_more_points_and_a_missing_number_counts_as_none(ros):
    tie = copy.deepcopy(BLOCK)
    qbs = [p for p in tie["players"] if p["pos"] == "QB"][:2]
    qbs[0].update(po_rank=1, po_pts=None)
    qbs[1].update(po_rank=1, po_pts=0.5)
    rows = ros("rosRows", tie, "QB", "half", "po")
    assert slugs(rows[:2]) == [qbs[1]["slug"], qbs[0]["slug"]]


def test_the_playoff_span_shows_the_playoff_rank_not_the_season_rank(ros):
    hall = next(r for r in ros("rosRows", BLOCK, "RB", "half", "po") if r["slug"] == "breece-hall")
    assert hall["rank"] == 30 and next(r for r in ros("rosRows", BLOCK, "RB", "half") if r["slug"] == "breece-hall")["rank"] == 29


def test_a_player_with_no_playoff_numbers_is_blank_and_last_not_an_error(ros):
    gap = copy.deepcopy(BLOCK)
    qb = next(p for p in gap["players"] if p["slug"] == "josh-allen")
    qb.update(po_rank=None, po_pts=None, po_games=None)
    rows = ros("rosRows", gap, "QB", "half", "po")
    assert rows[-1]["slug"] == "josh-allen" and rows[-1]["rank"] is None and rows[-1]["pts"] is None


@pytest.mark.req("Ranks", ac="Rest of season: no playoff fields, no Playoffs toggle")
def test_the_toggle_exists_only_when_the_file_has_playoff_numbers(ros):
    assert ros("rosHasPlayoffs", BLOCK) is True
    old = copy.deepcopy(BLOCK)
    old["po_weeks"] = None
    assert ros("rosHasPlayoffs", old) is False
    assert ros("rosHasPlayoffs", None) is False


@pytest.mark.req("Ranks", ac="Rest of season: FantasyPros' rank and the gap sit beside ours")
def test_a_row_carries_fantasypros_rank_and_gap_or_none(ros):
    fp = copy.deepcopy(BLOCK)
    allen = next(p for p in fp["players"] if p["slug"] == "josh-allen")
    allen["fp"] = {"rank": 3, "gap": 2, "pts": 250.0}
    rows = ros("rosRows", fp, "QB", "half")
    assert rows[0]["fp"] == {"rank": 3, "gap": 2, "pts": 250.0} and rows[1]["fp"] is None
    assert ros("rosRows", fp, "QB", "half", "po")[0]["fp"] is None, "FantasyPros ranks the whole rest of season, not the playoff weeks"


@pytest.mark.req("Ranks", ac="Rest of season: FantasyPros' rank and the gap sit beside ours")
def test_the_espn_view_has_no_fantasypros_column(ros):
    fp = copy.deepcopy(BLOCK)
    next(p for p in fp["players"] if p["slug"] == "josh-allen")["fp"] = {"rank": 3, "gap": 2, "pts": 250.0}
    assert ros("rosRows", fp, "QB", "espn")[0]["fp"] is None, "FantasyPros is half-PPR; the gap is against our half-PPR rank"
    assert ros("rosOne", fp, "josh-allen", "espn")["fp"] is None


@pytest.mark.req("Ranks", ac="Rest of season: ESPN readers read ESPN's numbers and order")
def test_the_espn_scoring_reads_its_own_points_rank_and_history(ros):
    half, espn = ros("rosRows", BLOCK, "WR", "half"), ros("rosRows", BLOCK, "WR", "espn")
    assert [r["rank"] for r in espn] == sorted(r["rank"] for r in espn), "ordered by ESPN's rank"
    by = {r["slug"]: r for r in espn}
    raw = next(p for p in BLOCK["players"] if p["slug"] == "michael-wilson")
    assert raw["rank"] == 10 and raw["espn"]["rank"] == 13, "the fixture's one WR the two scorings order apart"
    assert by["michael-wilson"]["rank"] == 13 and by["michael-wilson"]["pts"] == raw["espn"]["ros_pts"]
    assert by["michael-wilson"]["pg"] == raw["espn"]["ros_pg"] and by["michael-wilson"]["hist"] == raw["espn"]["hist"]
    assert slugs(half) != slugs(espn)
    assert by["michael-wilson"]["games"] == raw["games_left"], "games left do not depend on the scoring"


@pytest.mark.req("Ranks", ac="Rest of season: a position with no rows says so")
def test_a_position_with_no_rows_is_an_empty_list(ros):
    no_te = {**BLOCK, "players": [p for p in BLOCK["players"] if p["pos"] != "TE"]}
    assert ros("rosRows", no_te, "TE", "half") == []
    assert ros("rosRows", None, "TE", "half") == []
    assert ros("rosRows", BLOCK, "FLEX", "half") == [], "FLEX has no rest-of-season list"


def test_a_tie_in_rank_breaks_by_points_then_name(ros):
    tied = copy.deepcopy(BLOCK)
    qbs = [p for p in tied["players"] if p["pos"] == "QB"][:3]
    for p, pts, name in zip(qbs, (100.0, 110.0, 110.0), ("Zed", "Bea", "Abe")):
        p.update(rank=99, ros_pts=pts, n=name)
    got = [r["n"] for r in ros("rosRows", tied, "QB", "half") if r["rank"] == 99]
    assert got == ["Abe", "Bea", "Zed"], "more points first, then the name"


def test_the_block_is_absent_without_a_file_or_players(node_js):
    none = node_js("data/ros.js")
    assert none("rosBlock") is None, "LIVE_ROS undefined"
    empty = node_js("data/ros.js", globals={"LIVE_ROS": {"players": []}})
    assert empty("rosBlock") is None
    nul = node_js("data/ros.js", globals={"LIVE_ROS": None})
    assert nul("rosBlock") is None
    assert node_js("data/ros.js", globals={"LIVE_ROS": BLOCK})("rosBlock")["week"] == 5


@pytest.mark.req("Ranks", ac="Rest of season: ESPN numbers only for a team picked in the ESPN league")
@pytest.mark.parametrize("picked,focus,want", [
    (True, "espn", "espn"), (True, "yahoo", "half"), (True, "ayo", "half"), (False, "espn", "half"), (False, None, "half")])
def test_only_a_team_picked_in_the_espn_league_reads_espn_numbers(ros, picked, focus, want):
    assert ros("rosScoring", picked, focus, BLOCK) == want


def test_a_file_without_espn_numbers_never_says_espn(ros):
    old = copy.deepcopy(BLOCK)
    old["players"][4]["espn"]["rank"] = None
    assert ros("rosScoring", True, "espn", old) == "half"


@pytest.mark.req("Ranks", ac="Rest of season: a bump chart of the top 10, rank by week")
def test_the_chart_is_the_top_ten_with_a_point_per_week(ros):
    rows = ros("rosRows", BLOCK, "WR", "half")
    chart = ros("rosChart", rows)
    assert [ln["slug"] for ln in chart["lines"]] == slugs(rows)[:10]
    assert chart["weeks"] == [3, 4, 5] and chart["dots"] is False
    assert [ln["lead"] for ln in chart["lines"]] == [True] * 3 + [False] * 7, "the top three wear the position colour"
    first = chart["lines"][0]
    assert [(p["week"], p["rank"]) for p in first["points"]] == [(3, 1), (4, 1), (5, 1)]


@pytest.mark.req("Ranks", ac="Rest of season: a rank below the axis sits on its bottom edge, hollow")
def test_a_rank_below_the_axis_is_clamped_and_marked(ros):
    rows = ros("rosRows", BLOCK, "WR", "half")
    chart = ros("rosChart", rows)
    deep = [p for ln in chart["lines"] for p in ln["points"] if p["rank"] > 12]
    assert deep, "the fixture's top ten has a WR who was ranked below 12 in an earlier week"
    assert all(p["over"] is True and p["shown"] == 12 for p in deep)
    assert all(p["over"] is False and p["shown"] == p["rank"] for ln in chart["lines"] for p in ln["points"] if p["rank"] <= 12)


@pytest.mark.req("Ranks", ac="Rest of season: a week with no earlier history draws dots, not lines")
def test_one_week_of_history_is_dots(ros):
    fresh = copy.deepcopy(BLOCK)
    for p in fresh["players"]:
        p["hist"] = p["hist"][-1:]
    chart = ros("rosChart", ros("rosRows", fresh, "RB", "half"))
    assert chart["weeks"] == [5] and chart["dots"] is True
    assert all(len(ln["points"]) == 1 for ln in chart["lines"])


def test_the_chart_places_rank_one_at_the_top_and_the_first_week_at_the_left(ros):
    weeks = [3, 4, 5]
    assert ros("rosX", 3, weeks, BOX) == 26 and ros("rosX", 5, weeks, BOX) == 330 - 104
    assert ros("rosX", 4, weeks, BOX) == pytest.approx(26 + (330 - 104 - 26) / 2)
    assert ros("rosY", 1, 12, BOX) == 10 and ros("rosY", 12, 12, BOX) == 236 - 20
    assert ros("rosY", 40, 12, BOX) == 236 - 20, "past the axis it sits on the bottom edge"
    assert ros("rosX", 5, [5], BOX) == pytest.approx(26 + (330 - 104 - 26) / 2), "one week sits mid-plot"


def test_the_bump_chart_box_follows_the_screen_and_is_taller_with_room(ros):
    phone, wide = ros("rosBox", 360), ros("rosBox", 1280)
    assert (phone["w"], phone["h"], phone["r"]) == (316, 236, 108), "a phone's box is its screen less the gutters"
    assert wide["w"] == 1100 and wide["h"] == 300 and wide["r"] == 150, "capped at the list's width, with room for names"
    assert ros("rosBox", 200)["w"] == 300, "never narrower than the labels need"
    assert ros("rosBox", 700)["w"] == 656 and ros("rosBox", 700)["h"] == 300


def test_the_profile_axis_fits_his_worst_week_and_is_never_shorter_than_six(ros):
    assert ros("rosAxis", [1, 1, 1]) == 6
    assert ros("rosAxis", [9, 15, 29]) == 29
    assert ros("rosAxis", []) == 6


@pytest.mark.req("The profile modal", ac="Rest of season block: his row, or none for a player not listed")
def test_a_player_has_one_row_on_the_readers_scoring_or_none(ros):
    raw = next(p for p in BLOCK["players"] if p["slug"] == "breece-hall")
    row = ros("rosOne", BLOCK, "breece-hall", "half")
    assert (row["rank"], row["pts"], row["pos"], row["hist"]) == (29, raw["ros_pts"], "RB", [[3, 9], [4, 15], [5, 29]])
    espn = ros("rosOne", BLOCK, "breece-hall", "espn")
    assert (espn["rank"], espn["pts"]) == (raw["espn"]["rank"], raw["espn"]["ros_pts"])
    assert ros("rosOne", BLOCK, "nobody-here", "half") is None
    assert ros("rosOne", None, "breece-hall", "half") is None
