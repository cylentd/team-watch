"""data/navmap.js, one rule a test (2026-10-08, nav regroup): which group a name belongs to, and when a leaf
the league on screen lacks keeps its own name. Node only."""
import pytest


@pytest.fixture(scope="module")
def nav(node_js):
    return node_js("data/navmap.js")


@pytest.mark.parametrize("leaf,group", [("roster", "team"), ("news", "scouting"), ("digest", "home"), ("dfs", "week")])
def test_a_known_leaf_names_its_own_group(nav, leaf, group):
    assert nav("navGroupOf", leaf) == group


@pytest.mark.parametrize("name", ["nonsense", ""])
def test_a_name_no_group_holds_belongs_to_matchup(nav, name):
    """The default view's group holds it: Home (Today, leaf `digest`) since Home draft B, 2026-10-08; Matchup before."""
    assert nav("navGroupOf", name) == "home"


def test_a_league_leaf_in_the_row_stays(nav):
    assert nav("navFallback", "teams", ["recap", "teams"]) == "teams"


def test_a_hidden_leaf_stays_though_the_row_lacks_it(nav):
    assert nav("navFallback", "weather", ["digest", "live"]) == "weather"


def test_a_leaf_outside_team_and_league_stays_though_the_row_lacks_it(nav):
    assert nav("navFallback", "usage", ["ranks"]) == "usage"


def test_a_league_leaf_the_row_lacks_moves_to_recap(nav):
    assert nav("navFallback", "records", ["recap", "teams"]) == "recap"
