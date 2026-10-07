"""A kicker's and a defense's card back (David, 2026-10-07): the same back as every other card, the matchup line
and kickoff on top, then facts with whole labels instead of a squeezed table, then the projection. No weekly
K or D/ST fantasy points exist anywhere on the page or in ff-jarvis's data (gamelog_weekly and live_week_stats
hold QB RB WR TE only), so there are no bars: `supportFacts` (data/supportback.js) says which two facts and
the projection a back draws, and `dstPointsFor` reads the projection from LIVE_DST (ff-jarvis's, per league
scoring; the page computes none)."""
import pytest


@pytest.fixture(scope="module")
def sb(node_js):
    return node_js("data/dst.js", "data/supportback.js")


def keys(rows):
    return [r["key"] for r in rows]


def test_a_kicker_in_a_dome_gets_the_roof_the_team_total_and_the_projection(sb):
    rows = sb("supportFacts", "K", {"roof": "dome", "windMph": None, "team": 24.8, "opp": 17.8, "spread": -7, "proj": 7.8})
    assert rows == [{"key": "roof", "v": "dome"}, {"key": "team", "v": 24.8}, {"key": "proj", "v": 7.8}]


def test_a_kicker_outdoors_gets_the_wind_in_place_of_the_roof(sb):
    rows = sb("supportFacts", "K", {"roof": "outdoor", "windMph": 12, "team": 24.8, "opp": 17.8, "spread": -7, "proj": 7.8})
    assert rows[0] == {"key": "wind", "v": 12}


def test_a_retractable_roof_is_open_air_to_a_kicker_so_it_shows_the_wind(sb):
    rows = sb("supportFacts", "K", {"roof": "retractable", "windMph": 6, "team": 20.0, "opp": 20.0, "spread": 0, "proj": None})
    assert rows[0] == {"key": "wind", "v": 6}


def test_a_kicker_with_no_forecast_has_a_wind_row_with_no_number(sb):
    rows = sb("supportFacts", "K", {"roof": "", "windMph": None, "team": 24.8, "opp": 17.8, "spread": -7, "proj": 7.8})
    assert rows[0] == {"key": "wind", "v": None}


def test_a_defense_gets_the_opponents_total_the_spread_and_the_projection(sb):
    rows = sb("supportFacts", "DST", {"roof": "dome", "windMph": None, "team": 24.8, "opp": 17.8, "spread": -7, "proj": 5.1})
    assert rows == [{"key": "opp", "v": 17.8}, {"key": "spread", "v": -7}, {"key": "proj", "v": 5.1}]


def test_no_projection_leaves_no_projection_row(sb):
    rows = sb("supportFacts", "DST", {"roof": "", "windMph": None, "team": None, "opp": None, "spread": None, "proj": None})
    assert keys(rows) == ["opp", "spread"] and [r["v"] for r in rows] == [None, None]


@pytest.mark.parametrize("n, text", [(-7, "−7"), (-2.5, "−2.5"), (3, "+3"), (0, "0"), (None, "—")])
def test_the_spread_reads_with_a_real_minus_and_a_plus_for_an_underdog(sb, n, text):
    assert sb("spreadText", n) == text


BLOCK = {
    "weeks": [5, 6],
    "leagues": {"espn": {"dst": "dst_espn", "k": None}, "yahoo": {"dst": "dst_yahoo", "k": "k_yahoo"}},
    "teams": [
        {"team": "LA", "weeks": [{"week": 5, "bye": False, "dst": {"dst_espn": 2.2, "dst_yahoo": 3.5}, "k": {"k_yahoo": 7.8}}]},
        {"team": "BUF", "weeks": [{"week": 5, "bye": True}]},
    ],
}


def test_the_projection_is_the_first_weeks_cell_on_the_leagues_scoring(sb):
    assert sb("dstPointsFor", BLOCK, "espn", "DST", "LA") == 2.2
    assert sb("dstPointsFor", BLOCK, "yahoo", "DST", "LA") == 3.5
    assert sb("dstPointsFor", BLOCK, "yahoo", "K", "LA") == 7.8


def test_a_roster_clubs_spelling_finds_the_files_club(sb):
    assert sb("dstPointsFor", BLOCK, "yahoo", "DST", "LAR") == 3.5


def test_the_pages_week_picks_the_files_week_and_a_missing_week_is_no_projection(sb):
    two = {**BLOCK, "teams": [{"team": "LA", "weeks": [{"week": 5, "bye": False, "dst": {"dst_yahoo": 3.5}},
                                                        {"week": 6, "bye": False, "dst": {"dst_yahoo": 4.1}}]}]}
    assert sb("dstPointsFor", two, "yahoo", "DST", "LA", 6) == 4.1
    assert sb("dstPointsFor", two, "yahoo", "DST", "LA", 9) is None


def test_a_league_with_no_kicker_slot_has_no_kicker_projection(sb):
    assert sb("dstPointsFor", BLOCK, "espn", "K", "LA") is None


def test_a_bye_a_missing_club_or_no_file_is_no_projection(sb):
    assert sb("dstPointsFor", BLOCK, "yahoo", "DST", "BUF") is None
    assert sb("dstPointsFor", BLOCK, "yahoo", "DST", "XXX") is None
    assert sb("dstPointsFor", None, "yahoo", "DST", "LA") is None
