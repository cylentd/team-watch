"""Defense form (TODO "Outcome ranges" d, 2026-11-14), in Node: data/defform.js.

ff-jarvis's sos.json gains `defense_recent[<DEF>]` ({games, QB|RB|WR|TE: {last3_pts_pg, season_pts_pg, trend}},
RB adding last3_rush_yds_pg, season_rush_yds_pg, rush_trend) and `recent`. `trend` is "up" (the defense allowed
more lately), "down", or null; the last-3 fields are null before 3 games. The page computes nothing: a form is the
file's own two numbers and its own trend word, or nothing. Context only: form failed as a price (ff-jarvis
METHODOLOGY 12.73). How the two views draw it is test_defform_view.py."""
import pytest

JAX_RB = {"last3_pts_pg": 20.0, "season_pts_pg": 12.5, "trend": "up",
          "last3_rush_yds_pg": 112.0, "season_rush_yds_pg": 68.2, "rush_trend": "up"}
RAW = {"from_week": 5, "defense_recent": {
    "JAX": {"games": 4, "RB": JAX_RB, "WR": {"last3_pts_pg": 30.2, "season_pts_pg": 29.0, "trend": None}},
    "CIN": {"games": 4, "RB": {"last3_pts_pg": 24.3, "season_pts_pg": 19.1, "trend": "up",
                               "last3_rush_yds_pg": 121.0, "season_rush_yds_pg": 110.4, "rush_trend": None}},
    "LA": {"games": 4, "WR": {"last3_pts_pg": 14.0, "season_pts_pg": 19.5, "trend": "down"}},
    "LV": {"games": 2, "RB": {"last3_pts_pg": None, "season_pts_pg": 25.0, "trend": None,
                              "last3_rush_yds_pg": None, "season_rush_yds_pg": 140.0, "rush_trend": None}},
    "BAD": {"games": 4, "QB": {"last3_pts_pg": 21.0, "season_pts_pg": 15.0, "trend": "sideways"}},
}}


@pytest.fixture(scope="module")
def df(node_js):
    return node_js("data/defform.js")


def test_a_back_against_a_run_defense_that_flagged_reads_its_rush_yards(df):
    assert df("dfForm", RAW, "JAX", "RB") == {"def": "JAX", "pos": "RB", "kind": "rush",
                                              "last3": 112.0, "season": 68.2, "trend": "up"}


def test_a_back_with_only_the_points_flag_reads_its_points(df):
    assert df("dfForm", RAW, "CIN", "RB") == {"def": "CIN", "pos": "RB", "kind": "pts",
                                              "last3": 24.3, "season": 19.1, "trend": "up"}


def test_a_receiver_reads_points_and_a_down_trend_stays_down(df):
    assert df("dfForm", RAW, "LA", "WR") == {"def": "LA", "pos": "WR", "kind": "pts",
                                             "last3": 14.0, "season": 19.5, "trend": "down"}


@pytest.mark.parametrize("raw,team,pos", [
    (RAW, "JAX", "WR"),       # no trend: a small move is not a form
    (RAW, "LV", "RB"),        # under 3 games: never a short average
    (RAW, "BAD", "QB"),       # a word the file does not define
    (RAW, "NYG", "RB"),       # a defense the file does not carry
    ({"from_week": 5}, "JAX", "RB"),   # a file from before ff-jarvis wrote the block
    (None, "JAX", "RB"),      # no file at all
])
def test_no_flag_or_no_data_is_no_form(df, raw, team, pos):
    assert df("dfForm", raw, team, pos) is None


def test_a_schedule_row_reads_the_next_opponent_skipping_a_bye(df):
    cells = [{"week": 5, "opp": None, "bye": True}, {"week": 6, "opp": "CIN", "bye": False},
             {"week": 7, "opp": "JAX", "bye": False}]
    assert df("dfNext", RAW, "RB", [5, 6, 7], cells)["def"] == "CIN"


def test_a_window_that_starts_later_than_this_week_has_no_next_form(df):
    cells = [{"week": 15, "opp": "JAX", "bye": False}]
    assert df("dfNext", RAW, "RB", [15], cells) is None       # the playoff weeks: today's form says nothing


def test_preview_lists_each_offense_against_the_defense_it_faces_away_first(df):
    sides = df("dfSides", RAW, "JAX", "LA")
    assert [(s["off"], s["def"], [f["pos"] for f in s["forms"]]) for s in sides] == [("JAX", "LA", ["WR"]),
                                                                                  ("LA", "JAX", ["RB"])]


def test_preview_draws_no_side_when_its_defense_flagged_nothing(df):
    assert df("dfSides", RAW, "NYG", "LV") == []
