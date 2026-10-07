"""The matchup line on the Roster (David's pick "B . Row + back", 2026-10-07), in Node.

A row and a card back both say who the player faces: "vs BUF 5th" with the stadium's roof, and the kickoff
under it. `matchupLine` (data/matchupline.js) is the model both draw. The rank is ff-jarvis's own matchup
number for the player (profiles `next.factor`, 1 = toughest defense for his position, 32 = easiest), the
number his projection already uses; a player without one takes the opponent's form rank from LIVE_DEFENSE
(same direction), and one with neither still names the opponent. Ranks 1-8 read red, 9-24 neutral, 25-32
green: it explains the projection, it is not an edge claim."""
import pytest

KICK = "2026-10-13T00:15:00Z"          # Mon 5:15 PM Pacific
SCHED = {"week": 5, "alias": {"LA": "LAR"}, "games": [
    {"week": 5, "home": "BUF", "away": "LAR", "kickoff": KICK},
    {"week": 5, "home": "ATL", "away": "BAL", "kickoff": "2026-10-11T20:20:00Z"},
    {"week": 5, "home": "DET", "away": "TB", "kickoff": "2026-10-11T17:00:00Z"},
    {"week": 6, "home": "LAR", "away": "BAL", "kickoff": "2026-10-18T20:05:00Z"},
]}
WEATHER = {"teams": {"BUF": {"roof": "dome"}, "ATL": {"roof": "retractable"}, "DET": {"roof": "outdoor"}}}
PROFILES = {"players": {
    "qb-la": {"next": {"opp": "BUF", "home": True, "factor": {"rank": 5, "of": 32}}},
    "rb-bal": {"next": {"opp": "ATL", "home": False, "factor": {"rank": 7, "of": 32}}},
    "stale": {"next": {"opp": "MIA", "home": True, "factor": {"rank": 2, "of": 32}}},      # last week's opponent
}}


def form(**ranks):
    """LIVE_DEFENSE.form for the teams named: rank per position (1 = allows the fewest, 32 = the most)."""
    return {team: {"current": {pos: {"rank": r, "pts_pg": 20} for pos, r in by.items()}} for team, by in ranks.items()}


DEFENSE = {"form": {**form(BUF={"WR": 30, "QB": 29}, ATL={"RB": 7}, DET={"RB": 9, "WR": 24}),
                    "AAA": {"current": {"WR": {"rank": 1}}}, "ZZZ": {"current": {"WR": {"rank": 32}}}}}


@pytest.fixture(scope="module")
def ml(node_js):
    return node_js("data/schedule.js", "ui/matchup.js", "data/matchupline.js", globals={
        "LIVE_SCHEDULE": SCHED, "LIVE_WEATHER": WEATHER, "LIVE_PROFILES": PROFILES, "LIVE_DEFENSE": DEFENSE})


def who(slug, pos, team):
    return {"slug": slug, "n": "Test Player", "pos": pos, "team": team}


@pytest.mark.parametrize("rank, tone", [(1, "hard"), (8, "hard"), (9, "mid"), (24, "mid"), (25, "easy"), (32, "easy"),
                                        (None, ""), (0, "")])
def test_ranks_1_to_8_are_hard_9_to_24_middle_25_to_32_easy(ml, rank, tone):
    assert ml("mlTone", rank) == tone


def test_the_band_follows_the_field_size_when_it_is_not_32(ml):
    assert [ml("mlTone", r, 30) for r in (8, 9, 22, 23)] == ["hard", "mid", "mid", "easy"]


@pytest.mark.parametrize("row, roof", [({"roof": "dome"}, "dome"), ({"roof": "retractable"}, "retractable"),
                                       ({"roof": "outdoor", "temp_f": 60}, ""), ({}, ""), (None, "")])
def test_the_roof_is_solid_for_a_dome_outline_for_a_retractable_none_outdoors(ml, row, roof):
    assert ml("mlRoof", row) == roof


def test_a_game_takes_the_projections_own_matchup_number(ml):
    got = ml("matchupLine", who("qb-la", "QB", "LA"))
    assert got == {"opp": "BUF", "home": False, "rank": 5, "of": 32, "tone": "hard", "roof": "dome",
                   "kickoff": KICK, "src": "factor"}


def test_a_home_game_says_home_and_an_outdoor_stadium_has_no_roof(ml):
    got = ml("matchupLine", who("home-wr", "WR", "DET"))
    assert (got["opp"], got["home"], got["roof"], got["rank"], got["tone"]) == ("TB", True, "", None, "")


def test_an_away_game_reads_the_home_clubs_roof_and_says_away(ml):
    got = ml("matchupLine", who("rb-bal", "RB", "BAL"))
    assert (got["opp"], got["home"], got["roof"], got["rank"], got["tone"]) == ("ATL", False, "retractable", 7, "hard")


def test_no_factor_takes_the_opponents_form_rank_for_his_position(ml):
    got = ml("matchupLine", who("wr-nobody", "WR", "LA"))
    assert (got["opp"], got["rank"], got["of"], got["tone"], got["src"]) == ("BUF", 30, 32, "easy", "form")


def test_a_factor_for_another_opponent_is_not_his_games_number(ml):
    got = ml("matchupLine", who("stale", "RB", "BAL"))
    assert (got["opp"], got["rank"], got["src"]) == ("ATL", 7, "form")


def test_no_rank_anywhere_still_names_the_opponent(ml):
    got = ml("matchupLine", who("nobody", "TE", "TB"))
    assert (got["opp"], got["rank"], got["tone"], got["src"]) == ("DET", None, "", None)
    assert got["home"] is False


def test_a_defense_has_no_matchup_rank(ml):
    got = ml("matchupLine", who("dst-lar", "DST", "LA"))
    assert (got["opp"], got["rank"]) == ("BUF", None)


def test_a_club_with_no_game_this_week_is_a_bye(ml):
    assert ml("matchupLine", who("qb", "QB", "MIA")) == {"bye": True}


def test_the_game_is_the_page_weeks_not_the_next_kickoff(ml):
    """LAR plays in week 6 too; the week-5 game is the one the line names."""
    assert ml("matchupLine", who("x", "WR", "LAR"))["kickoff"] == KICK


def test_with_no_schedule_there_is_no_line(node_js):
    bare = node_js("data/schedule.js", "ui/matchup.js", "data/matchupline.js")
    assert bare("matchupLine", who("x", "WR", "LAR")) is None


@pytest.mark.parametrize("p, start, slot, show", [
    ("RB", True, "RB1", False), ("QB", True, "QB", False), ("RB", True, "FLEX", True), ("WR", True, "FLX", True),
    ("TE", False, "BN", True), ("RB", False, None, True), ("DST", True, "D/ST", False), ("K", True, "K", False)])
def test_the_position_is_said_where_the_row_does_not_already_show_it(ml, p, start, slot, show):
    assert ml("mlSaysPos", {"pos": p, "start": start, "slot": slot}) is show


@pytest.fixture(scope="module")
def kick(node_js):
    """The row's and the back's kickoff text, both through the draw file, in a pinned zone."""
    return node_js("data/schedule.js", "lib/kick.js", "ui/matchup.js", "data/matchupline.js", "surface/teams/matchupline.js",
                   globals={"LIVE_SCHEDULE": SCHED, "LIVE_WEATHER": WEATHER, "LIVE_PROFILES": PROFILES, "LIVE_DEFENSE": DEFENSE,
                            "KICK_TZ": "America/Los_Angeles"})


def test_two_players_of_one_game_read_one_kickoff_on_the_row_and_on_the_back(kick):
    """David's 2026-10-07 report: a back read 'Mon 6:15 PM' beside a row's 'Mon 5:15 PM' for the same game. The
    data and the code agreed (both are kickFmt of the one schedule row; the 1x screenshot misread a 5 on a tinted
    back); this holds that: every row and back of the game's players print the same words."""
    qb, wr = who("qb-la", "QB", "LA"), who("wr-la", "WR", "LA")
    said = {n: kick("mlKickText", kick("matchupLine", p), p, False) for n, p in (("qb", qb), ("wr", wr))}
    assert said == {"qb": "Mon 5:15 PM", "wr": "Mon 5:15 PM"}


def test_the_row_adds_only_the_position_in_front_of_the_same_kickoff(kick):
    flex = {**who("rb-bal", "RB", "BAL"), "start": True, "slot": "FLEX"}
    m = kick("matchupLine", flex)
    assert kick("mlKickText", m, flex, False) == "Sun 1:20 PM"
    assert kick("mlKickText", m, flex, True) == "RB · Sun 1:20 PM"
