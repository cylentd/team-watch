"""The nav's table and the row deep link, in Node (data/navmap.js, data/navrow.js; 2026-10-05, unit U8).

The groups, which leaf sits in which, the old hashes that still land, and which leaves a league shows
are all data: no DOM, so no browser. What the bar and the sub-row look like at 360 and 390 px is
test_render.py and test_nav_merge.py, in the browser."""
import pytest

YAHOO = {"waivers": True, "teams": True, "recap": True, "records": True, "trades": True}
ESPN = {"waivers": True, "teams": True, "recap": True, "records": False, "trades": False}
AYO = {**YAHOO, "trades": False}
CONNECTED = {"waivers": False, "teams": True, "recap": True, "records": False, "trades": False}


@pytest.fixture(scope="module")
def nav(node_js):
    return node_js("data/navmap.js", "data/navrow.js")


def test_the_top_bar_is_week_league_stats_bets(nav):
    assert nav("NAV.map(([g]) => g)") == ["week", "league", "scouting", "bets"]
    assert [nav("navGroupLabel", g, False) for g in ("week", "league", "scouting", "bets")] == ["This week", "League", "Stats", "Bets"]


def test_the_group_called_teams_is_gone_and_league_holds_six_leaves(nav):
    assert nav("NAV.some(([g]) => g === 'teams')") is False
    assert nav("NAV.find(([g]) => g === 'league')[1]") == ["roster", "waivers", "teams", "trades", "recap", "records"]


def test_no_sub_row_holds_more_than_six_leaves(nav):
    """Six fit in the 332 px row of a 360 px phone (316 px for This week's), seven took 383 px (measured in the
    browser, 2026-10-05; the figures are in data/navmap.js)."""
    assert nav("NAV_SUBROW_MAX") == 6
    assert nav("NAV.map(([g, tabs]) => tabs.filter(k => !NAV_HIDDEN.includes(k)).length)") == [6, 6, 5, 3]


def test_every_leaf_is_in_one_group_only(nav):
    assert nav("(() => { const all = NAV.flatMap(([, t]) => t); return all.length === new Set(all).size; })()") is True


@pytest.mark.parametrize("name,leaf", [
    ("myrecap", "recap"),      # My recap (Yahoo) and League (ESPN) merged into Recap, 2026-10-05
    ("league", "recap"),
    ("recap", "recap"),
    ("pool", "movers"),
    ("takes", "matchups"),
    ("startsit", "matchups"),
    ("board", "board"),        # Leaders keeps its leaf and hash
    ("movers", "movers"),
    ("usage", "usage"),
    ("teams", "teams"),        # League > Teams, the board: its own leaf, not the old group
    ("weekrecap", "weekrecap"),
    ("nonsense", None),
    ("", None),
])
def test_old_and_new_hashes_land(nav, name, leaf):
    assert nav("navLeafOf", name) == leaf


def test_the_stats_group_keeps_its_id_and_its_leaves(nav):
    assert nav("NAV.find(([g]) => g === 'scouting')[1]") == ["highlights", "ranks", "board", "movers", "usage", "schedule"]
    assert nav("navGroupOf", "usage") == "scouting"


def test_schedule_is_a_stats_leaf_kept_out_of_the_sub_row(nav):
    """Stats' five tabs end at 326 of 332 px at 360 px, so Schedule opens by hash and link only (2026-10-05, U7c)."""
    assert nav("navLeafOf", "schedule") == "schedule" and nav("navGroupOf", "schedule") == "scouting"
    assert nav("NAV_HIDDEN") == ["weather", "schedule"]
    assert nav("navLabel", "schedule") == "Schedule"
    tabs = nav("navLeavesFor", "scouting", ESPN, False)
    assert nav("navFallback", "schedule", [k for k in tabs if k != "schedule"]) == "schedule"


@pytest.mark.parametrize("leaf,group", [("roster", "league"), ("waivers", "league"), ("teams", "league"), ("trades", "league"),
                                        ("recap", "league"), ("records", "league"), ("weekrecap", "week"), ("digest", "week")])
def test_a_leaf_finds_its_group(nav, leaf, group):
    assert nav("navGroupOf", leaf) == group


def test_a_yahoo_league_shows_all_six(nav):
    assert nav("navLeavesFor", "league", YAHOO, False) == ["roster", "waivers", "teams", "trades", "recap", "records"]


def test_espn_shows_fewer_leaves(nav):
    """ESPN has no record book and no graded trades: the filters hide those two leaves."""
    assert nav("navLeavesFor", "league", ESPN, False) == ["roster", "waivers", "teams", "recap"]


def test_ayo_has_no_trades_yet(nav):
    assert nav("navLeavesFor", "league", AYO, False) == ["roster", "waivers", "teams", "recap", "records"]


def test_a_connected_league_has_no_waivers(nav):
    assert "waivers" not in nav("navLeavesFor", "league", CONNECTED, False)


def test_tuesday_puts_waivers_first(nav):
    assert nav("navLeavesFor", "league", YAHOO, True)[0] == "waivers"
    assert nav("navLeavesFor", "league", ESPN, True) == ["waivers", "roster", "teams", "recap"]


def test_other_groups_are_not_filtered(nav):
    assert nav("navLeavesFor", "scouting", ESPN, False) == ["highlights", "ranks", "board", "movers", "usage", "schedule"]
    assert nav("navLeavesFor", "week", ESPN, False)[:2] == ["digest", "weekrecap"]


@pytest.mark.parametrize("leaf,tabs,want", [
    ("records", ["roster", "waivers", "teams", "recap"], "recap"),     # a #records link on an ESPN team
    ("trades", ["roster", "waivers", "teams", "recap"], "recap"),
    ("waivers", ["roster", "teams", "recap"], "roster"),               # a connected league
    ("recap", ["roster", "waivers", "teams", "recap"], "recap"),
    ("weather", ["digest", "weekrecap"], "weather"),                   # hidden from the sub-row, still reachable
    ("usage", ["highlights", "ranks", "board", "movers", "usage"], "usage"),
])
def test_a_leaf_a_league_lacks_falls_back(nav, leaf, tabs, want):
    assert nav("navFallback", leaf, tabs) == want


# ---- the one chip: pick a team and the league follows ----

KEYS = ["yahoo", "ayo", "espn"]


@pytest.mark.parametrize("team,want", [
    ({"key": "yahoo"}, "yahoo"),                                  # one of David's own: its own league
    ({"key": "espn"}, "espn"),
    ({"key": "espn-run-it-back", "mate": True, "league": "espn"}, "espn"),     # a leaguemate: his league
    ({"key": "yahoo-other", "mate": True, "league": "yahoo"}, "yahoo"),
    ({"key": "taco", "connected": True}, "yahoo"),                # a connected league has no data here: the first
    ({"key": "gone", "mate": True, "league": "nfl"}, "yahoo"),    # a league the page lacks
    (None, "yahoo"),
])
def test_the_league_follows_the_team(nav, team, want):
    assert nav("navFocusKey", team, KEYS) == want


def test_no_league_at_all_is_null(nav):
    assert nav("navFocusKey", {"key": "yahoo"}, []) is None


# ---- the deep link: where Grid or Role must stand for one player's row to be drawn ----

GRID = [
    {"slug": "a-rb", "pos": "RB", "wk": 4}, {"slug": "a-rb", "pos": "RB", "wk": 3},
    {"slug": "a-wr", "pos": "WR", "wk": 3},
    {"slug": "b-wr", "pos": "WR", "wk": 4},
]


def test_a_grid_row_opens_on_the_week_on_screen_when_he_has_one(nav):
    assert nav("navRowPlan", "usage", "a-rb", GRID, {"week": 3}) == {"leaf": "usage", "slug": "a-rb", "pos": "RB", "week": 3}


def test_a_grid_row_moves_to_his_newest_week_when_the_week_on_screen_has_none(nav):
    assert nav("navRowPlan", "usage", "a-wr", GRID, {"week": 4}) == {"leaf": "usage", "slug": "a-wr", "pos": "WR", "week": 3}


def test_a_player_the_grid_lacks_has_no_plan(nav):
    assert nav("navRowPlan", "usage", "nobody", GRID, {"week": 4}) is None
    assert nav("navRowPlan", "usage", "", GRID, {"week": 4}) is None
    assert nav("navRowPlan", "usage", "a-rb", None, {"week": 4}) is None


ROLE = [{"slug": f"p{i}", "pos": "WR" if i % 2 else "RB"} for i in range(30)]


def test_a_role_row_inside_the_first_page_needs_no_show_all(nav):
    assert nav("navRowPlan", "movers", "p3", ROLE, {"pos": "ALL", "first": 20}) == {"leaf": "movers", "slug": "p3", "pos": "ALL", "all": False}


def test_a_role_row_past_the_first_page_opens_show_all(nav):
    assert nav("navRowPlan", "movers", "p25", ROLE, {"pos": "ALL", "first": 20})["all"] is True


def test_a_role_filter_that_hides_him_resets_to_all(nav):
    plan = nav("navRowPlan", "movers", "p3", ROLE, {"pos": "RB", "first": 20})     # p3 is a WR
    assert plan["pos"] == "ALL"


def test_a_role_filter_that_holds_him_stays(nav):
    assert nav("navRowPlan", "movers", "p2", ROLE, {"pos": "RB", "first": 20})["pos"] == "RB"


def test_only_grid_and_role_take_a_row(nav):
    assert nav("navRowPlan", "digest", "a-rb", GRID, {"week": 4}) is None


def test_the_stats_views_are_named_by_what_they_hold(nav):
    """The group says Stats and each sub-tab says what is in it (2026-10-05, David: A + C). Leaves keep their ids."""
    assert [nav("navLabel", k) for k in ("board", "movers", "usage")] == ["Leaders", "Work vs points", "Usage"]
