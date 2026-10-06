"""The live game's names and ball, in Node (U9, 2026-10-05).

Two pure reads of ESPN's JSON, pinned without a build or a browser:
  data/gameday/plays.js      gsBoldNames: every player name in a play line bold, by ESPN's play
                             participants when it sends them, else by the "J.Goff" initial-dot pattern
  data/gameday/situation.js  gdSitShape: who has the ball, down and distance, and the red zone, from the
                             `situation` of the scoreboard or of a game summary

ESPN refuses servers and headless browsers, so the shapes below are ESPN's field names as the summary code
already reads them (espn.js) and as the saved game shows them (tests/fixtures/data/espn_summary.json); the
scoreboard's `situation` was not read live when this was written (see DESIGN.md "Live").
"""
import json
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SUMMARY = json.loads((REPO / "tests" / "fixtures" / "data" / "espn_summary.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def plays(node_js):
    return node_js("data/gameday/plays.js")


@pytest.fixture(scope="module")
def sit(node_js):
    return node_js("data/gameday/situation.js", "data/gameday/clock.js")


def who(name):
    return {"athlete": {"displayName": name}}


# ---- names in a play line ----------------------------------------------------------------------

def test_every_name_in_the_saved_game_is_bold_by_the_pattern(plays):
    """The fixture's plays carry no participants, so this is the fallback on real ESPN text."""
    line = SUMMARY["drives"]["previous"][0]["plays"][1]["text"]
    assert line == "J.Allen pass short left to K.Shakir pushed ob at BUF 24 for 9 yards (D.White)."
    assert plays("gsBoldNames", line, []) == (
        "<b>J.Allen</b> pass short left to <b>K.Shakir</b> pushed ob at BUF 24 for 9 yards (<b>D.White</b>).")


def test_participants_are_used_when_espn_sends_them(plays):
    out = plays("gsBoldNames", "Josh Allen pass short left to Khalil Shakir for 9 yards.", ["Josh Allen", "Khalil Shakir"])
    assert out == "<b>Josh Allen</b> pass short left to <b>Khalil Shakir</b> for 9 yards."


def test_a_participant_written_as_an_initial_is_bold_and_one_not_in_the_text_is_ignored(plays):
    out = plays("gsBoldNames", "J.Allen pass incomplete.", ["Josh Allen", "Stefon Diggs"])
    assert out == "<b>J.Allen</b> pass incomplete."


def test_a_participant_the_pattern_cannot_see_is_still_bold(plays):
    """ESPN writes a lowercase-led surname with no initial in a few penalty lines; the participant has it."""
    out = plays("gsBoldNames", "PENALTY on DET, Holding, declined. de la Cruz in coverage.", ["Marcus de la Cruz"])
    assert out == "PENALTY on DET, Holding, declined. de la Cruz in coverage."  # 'de la Cruz' is not 'Marcus de la Cruz'
    out = plays("gsBoldNames", "Marcus de la Cruz rushes up the middle.", ["Marcus de la Cruz"])
    assert out == "<b>Marcus de la Cruz</b> rushes up the middle."


def test_participants_win_over_the_pattern_and_the_pattern_fills_the_rest(plays):
    """A defender ESPN leaves out of the participants is still a name in the line."""
    out = plays("gsBoldNames", "J.Allen pass to K.Shakir (D.White).", ["Josh Allen"])
    assert out == "<b>J.Allen</b> pass to <b>K.Shakir</b> (<b>D.White</b>)."


@pytest.mark.parametrize("text, bolded", [
    ("A.J.Brown pass to A.St. Brown for 12 yards.", ["A.J.Brown", "A.St. Brown"]),
    ("M.Harrison Jr. pass short right to J.Smith-Njigba.", ["M.Harrison Jr.", "J.Smith-Njigba"]),
    ("PENALTY on DET-P.Sewell, Holding, 10 yards, enforced at DET 30.", ["P.Sewell"]),
    ("J.Bates 45 yard field goal is GOOD, Center-J.Cardona, Holder-J.Fox.", ["J.Bates", "J.Cardona", "J.Fox"]),
    ("D.O'Neal sacks J.Love for -7 yards.", ["D.O'Neal", "J.Love"]),
])
def test_the_initial_dot_pattern_reads_real_espn_lines(plays, text, bolded):
    out = plays("gsBoldNames", text, [])
    found = [chunk.split("</b>")[0] for chunk in out.split("<b>")[1:]]
    assert found == bolded


def test_nothing_else_is_bold(plays):
    line = "1st & 10 at BUF 15. No Huddle, Shotgun. END QUARTER 1."
    assert plays("gsBoldNames", line, []) == "1st &amp; 10 at BUF 15. No Huddle, Shotgun. END QUARTER 1."


def test_the_line_is_escaped(plays):
    assert plays("gsBoldNames", "J.Allen <script>&", []) == "<b>J.Allen</b> &lt;script&gt;&amp;"


def test_no_text_is_an_empty_string(plays):
    assert plays("gsBoldNames", "", []) == ""
    assert plays("gsBoldNames", None, None) == ""
    assert plays("gsBoldNames", "No names here.", ["Josh Allen"]) == "No names here."


def test_the_shape_reads_participants_from_a_play(plays):
    play = {"participants": [who("Josh Allen"), {"athlete": {"fullName": "Khalil Shakir"}}, {"displayName": "Dalton Kincaid"},
                             {"athlete": {}}, None]}
    assert plays("gsPlayNames", play) == ["Josh Allen", "Khalil Shakir", "Dalton Kincaid"]
    assert plays("gsPlayNames", {}) == []


# ---- the ball ----------------------------------------------------------------------------------

ABBR = {"2": "BUF", "8": "DET"}


def test_possession_down_distance_and_a_red_zone_read_off_the_situation(sit):
    got = sit("gdSitShape", {"possession": "2", "down": 3, "distance": 4, "downDistanceText": "3rd & 4 at DET 15",
                             "shortDownDistanceText": "3rd & 4", "possessionText": "DET 15", "isRedZone": True}, ABBR)
    assert got == {"ball": "BUF", "dd": "3rd & 4 at DET 15", "short": "3rd & 4", "red": True, "ytez": None}


def test_a_team_in_its_own_end_is_not_in_the_red_zone(sit):
    got = sit("gdSitShape", {"possession": "2", "downDistanceText": "1st & 10 at BUF 15", "possessionText": "BUF 15",
                             "isRedZone": False}, ABBR)
    assert got["ball"] == "BUF" and got["red"] is False


def test_the_red_zone_is_read_from_the_spot_when_the_flag_is_missing(sit):
    """Inside the opponent's 20, the 20 itself included; a spot on the team's own side never counts."""
    def red(spot):
        return sit("gdSitShape", {"possession": "2", "possessionText": spot}, ABBR)["red"]
    assert red("DET 20") is True and red("DET 1") is True
    assert red("DET 21") is False and red("BUF 15") is False and red("50") is False


def test_the_flag_wins_over_the_spot(sit):
    assert sit("gdSitShape", {"possession": "2", "possessionText": "DET 15", "isRedZone": False}, ABBR)["red"] is False


def test_a_kickoff_has_the_ball_but_no_down(sit):
    got = sit("gdSitShape", {"possession": "8", "downDistanceText": "", "isRedZone": False}, ABBR)
    assert got["ball"] == "DET" and got["dd"] == ""


def test_no_possession_is_no_situation(sit):
    assert sit("gdSitShape", {"downDistanceText": "1st & 10"}, ABBR) is None
    assert sit("gdSitShape", {"possession": "99"}, ABBR) is None
    assert sit("gdSitShape", None, ABBR) is None


def test_the_short_text_stands_in_for_a_missing_long_one(sit):
    got = sit("gdSitShape", {"possession": "2", "shortDownDistanceText": "2nd & 7"}, ABBR)
    assert got["dd"] == "2nd & 7"


def test_the_scoreboard_event_carries_the_situation_of_a_live_game_only(sit):
    def event(state, situation):
        return {"competitions": [{"status": {"period": 3, "displayClock": "4:12", "type": {"state": state, "name": "STATUS_IN_PROGRESS"}},
                                  "competitors": [{"team": {"id": "2", "abbreviation": "BUF"}}, {"team": {"id": "8", "abbreviation": "DET"}}],
                                  "situation": situation}]}
    sitn = {"possession": "8", "downDistanceText": "2nd & 3 at BUF 12", "possessionText": "BUF 12", "isRedZone": True}
    live = sit("gdClockShape", event("in", sitn))
    assert live["sit"] == {"ball": "DET", "dd": "2nd & 3 at BUF 12", "short": "", "red": True, "ytez": None}
    assert live["clubs"] == ["BUF", "DET"]
    assert sit("gdClockShape", event("post", sitn))["sit"] is None
    assert sit("gdClockShape", event("pre", sitn))["sit"] is None
    assert sit("gdClockShape", event("in", None))["sit"] is None


def test_a_club_reads_its_games_situation(node_js):
    js = node_js("surface/live/nflnow.js", "data/gameday/situation.js", "data/gameday/clock.js", globals={"GD_ALIAS": {"WSH": "WAS"}})
    js("(() => { GD_CLOCK = {DET: {state: 'in', sit: {ball: 'DET', dd: '1st & 10', red: false}}, WSH: {state: 'in', sit: null}}; })()")
    assert js("gdSitOf('DET')") == {"ball": "DET", "dd": "1st & 10", "red": False}
    assert js("gdSitOf('WSH')") is None
    assert js("gdSitOf('NYJ')") is None


def test_the_ball_line_is_the_down_or_the_club(sit):
    assert sit("gdSitText", {"ball": "BUF", "dd": "3rd & 4 at DET 15", "short": "3rd & 4"}) == "3rd & 4"
    assert sit("gdSitText", {"ball": "BUF", "dd": "3rd & 4 at DET 15", "short": ""}) == "3rd & 4 at DET 15"
    assert sit("gdSitText", {"ball": "BUF", "dd": "", "short": ""}) == "BUF ball"
