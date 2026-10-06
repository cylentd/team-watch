"""Live's league, game and scoreboard strip (data/gameday/strip.js), in Node (2026-10-05, storyboard
https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP, option 2A).

The team the reader picked decides the league; Live has no league setting of its own. My league leads
with a strip of the league's matchups, the reader's first; a team with no game this week (a bye, out of
the fantasy playoffs, week 18) leads with the league's closest game and the score head says so."""
import pytest


def team(key, name):
    return {"key": key, "name": name, "lineup": []}


ESPN = {"key": "espn", "name": "We're Big in Japan", "week": 2, "games": [["12", "15"], ["5", "11"]],
        "teams": {"12": team("espn", "Purdy Big in Japan"), "15": team("espn-teamminh", "TeamMinh"),
                  "5": team("espn-fafo", "FAFO!"), "11": team("espn-half", "Half Asian Lives Matter"),
                  "7": team("espn-bye", "On a Bye")}}
YAHOO = {"key": "yahoo", "name": "The Madden Curse", "week": 2, "games": [["9", "4"], ["11", "1"]],
         "teams": {"9": team("yahoo", "Chat Take the Wheel"), "4": team("yahoo-bobo", "Bo-Bo Milk Tea"),
                   "11": team("yahoo-lamarley", "Lamarley & Me"), "1": team("yahoo-romo", "Let Romo Take the Wheel")}}
LEAGUES = [ESPN, YAHOO]


@pytest.fixture(scope="module")
def js(node_js):
    return node_js("data/gameday/strip.js")


def test_the_league_is_the_picked_teams_then_the_first_followed_one_that_plays_here(js):
    assert js("gdLeagueFor", LEAGUES, ["yahoo-bobo", "espn"])["key"] == "yahoo"
    assert js("gdLeagueFor", LEAGUES, ["espn-fafo"])["key"] == "espn"
    # a pick in a league Live has no data for (a connected league) falls through to what is followed
    assert js("gdLeagueFor", LEAGUES, ["espn-connected-x", "yahoo-romo"])["key"] == "yahoo"
    assert js("gdLeagueFor", LEAGUES, [None, "nobody"]) is None
    assert js("gdLeagueFor", LEAGUES, []) is None


def test_the_readers_team_id_is_found_by_its_page_key(js):
    assert js("gdTeamId", ESPN, [None, "espn-teamminh"]) == "15"
    assert js("gdTeamId", YAHOO, ["espn-teamminh"]) is None
    assert js("gdTeamId", None, ["yahoo"]) is None


def test_stored_tabs_from_before_the_merge_land_on_my_league_or_nfl(js):
    assert [js("gdTabOf", v) for v in ("matchup", "league", "games", "tds", "nonsense", None)] == \
        ["league", "league", "games", "tds", "league", "league"]


def test_the_strip_puts_the_readers_game_first_and_keeps_the_league_order_after_it(js):
    pts = {"12": 80, "15": 70, "5": 90, "11": 91}
    assert js("gdStripOrder", ESPN["games"], pts, "11") == [["5", "11"], ["12", "15"]]
    assert js("gdStripOrder", ESPN["games"], pts, "12") == [["12", "15"], ["5", "11"]]


def test_a_team_with_no_game_this_week_leads_with_the_closest_game(js):
    pts = {"12": 80, "15": 70, "5": 90, "11": 91}
    assert js("gdStripOrder", ESPN["games"], pts, "7") == [["5", "11"], ["12", "15"]]
    # level gaps keep the league's order; no games at all draws no chips
    assert js("gdStripOrder", ESPN["games"], {}, "7") == [["12", "15"], ["5", "11"]]
    assert js("gdStripOrder", [], pts, "7") == []


def test_the_game_on_screen_is_the_tapped_one_else_the_readers_else_none_on_a_bye(js):
    g = ESPN["games"]
    assert js("gdGameOn", g, ["5", "11"], "12") == ["5", "11"]
    assert js("gdGameOn", g, ["9", "4"], "12") == ["12", "15"]          # a tap from another league is ignored
    assert js("gdGameOn", g, None, "15") == ["12", "15"]
    assert js("gdGameOn", g, None, "7") is None                          # the head says no game this week
    assert js("gdGameOn", g, ["5", "11"], "7") == ["5", "11"]            # but another game can be tapped
    assert js("gdGameOn", [], None, "12") is None


def test_a_chip_says_live_then_how_many_are_left_then_final(js):
    side = lambda playing, left, done: {"playing": playing, "left": left, "done": done}
    assert js("gdChipState", side(1, 3, 5), side(0, 4, 5)) == {"k": "live", "n": 8}
    assert js("gdChipState", side(0, 3, 6), side(0, 2, 7)) == {"k": "left", "n": 5}
    assert js("gdChipState", side(0, 0, 9), side(0, 0, 9)) == {"k": "final", "n": 0}


def test_a_chip_names_a_team_in_a_few_whole_words(js):
    short = lambda n: js("gdShortName", n)
    assert short("TeamMinh") == "TeamMinh"
    assert short("Am I COOKed? 🧑‍🍳") == "Am I COOKed?"
    assert short("Purdy Big in Japan") == "Purdy Big"           # never ends on a joining word
    assert short("Chat Take the Wheel 👾") == "Chat Take"
    assert short("Lamarley & Me") == "Lamarley"
    assert short("Supercalifragilistic") == "Supercalifr…"
