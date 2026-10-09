"""The nav's table and the row deep link, in Node (data/navmap.js, data/navrow.js; 2026-10-05, unit U8).

The groups, which leaf sits in which, the old hashes that still land, and which leaves a league shows
are all data: no DOM, so no browser. What the bar and the sub-row look like at 360 and 390 px is
test_render.py and test_nav_merge.py, in the browser."""
import pytest

from wording import words

# `trades` is the trade finder since 2026-10-06 (chrome/nav.js navFacts): every league with rosters has it, like `teams`.
YAHOO = {"waivers": True, "teams": True, "recap": True, "records": True, "trades": True}
ESPN = {"waivers": True, "teams": True, "recap": True, "records": False, "trades": True}
AYO = {**YAHOO}
CONNECTED = {"waivers": False, "teams": True, "recap": True, "records": False, "trades": True}


@pytest.fixture(scope="module")
def nav(node_js):
    return node_js("data/navmap.js", "data/navrow.js")


def test_the_bottom_bar_is_team_matchup_players_league_bets(nav):
    """Nav regroup, step 1 (David 2026-10-08, ledger #32): the Yahoo, ESPN and Sleeper sections. Group ids keep
    their old spelling where a group was renamed (`week` reads Matchup, `scouting` Players); `team` is new.
    Home draft B (David 2026-10-08, ledger #52): Home leads, Bets moved under Matchup."""
    assert nav("NAV.map(([g]) => g)") == ["home", "team", "week", "scouting", "league"]
    assert [nav("navGroupLabel", g, False) for g in ("home", "team", "week", "scouting", "league")] == ["Home", "Team", "Matchup", "Players", "League"]


def test_team_holds_your_teams_views_and_league_holds_the_leagues(nav):
    assert nav("NAV.some(([g]) => g === 'teams')") is False
    assert nav("NAV.find(([g]) => g === 'team')[1]") == ["roster", "waivers", "trades"]
    assert nav("NAV.find(([g]) => g === 'league')[1]") == ["recap", "teams", "records", "tradehist"]


def test_no_sub_row_holds_more_than_six_leaves(nav):
    """Six fit in the 332 px row of a 360 px phone (316 px for This week's), seven took 383 px (measured in the
    browser, 2026-10-05; the figures are in data/navmap.js). Stats holds six since Schedule came back (2026-10-06)."""
    assert nav("NAV_SUBROW_MAX") == 6
    # Matchup holds seven since Bets moved under it (Home draft B, 2026-10-08): it scrolls as one row, like Players'.
    assert nav("NAV.map(([g, tabs]) => tabs.filter(k => !NAV_HIDDEN.includes(k)).length)") == [1, 3, 7, 6, 4]
    assert nav("NAV_DENSE").count("week") == 1


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
    assert nav("NAV.find(([g]) => g === 'scouting')[1]") == ["news", "ranks", "board", "movers", "usage", "schedule"]
    assert nav("navGroupOf", "usage") == "scouting"


def test_schedule_is_a_stats_leaf_in_the_sub_row_and_weather_is_the_only_hidden_one(nav):
    """Schedule left NAV_HIDDEN on 2026-10-06 (David, plan dbd T4): Stats shows six tabs, the most a sub-row holds.
    It was hidden on 2026-10-05 (U7c) while Stats' five tabs ended at 326 of 332 px. A decision change, not a loosened test."""
    assert nav("navLeafOf", "schedule") == "schedule" and nav("navGroupOf", "schedule") == "scouting"
    assert nav("NAV_HIDDEN") == ["weather"]
    assert nav("navLabel", "schedule") == "Schedule"
    tabs = nav("navLeavesFor", "scouting", ESPN, False)
    assert tabs[-1] == "schedule" and nav("navFallback", "schedule", tabs) == "schedule"


def test_the_matchups_tab_is_labelled_start_sit_and_the_old_names_still_land(nav):
    """Start/Sit became Matchups on 2026-10-06 (David) and Start/Sit again on 2026-10-08, so it never echoes the
    Matchup group; the leaf id stays, and #startsit and #takes still open it."""
    assert nav("navLabel", "matchups") == "Start/Sit"
    assert [nav("navLeafOf", n) for n in ("matchups", "startsit", "takes")] == ["matchups"] * 3


@pytest.mark.parametrize("leaf,group", [("roster", "team"), ("waivers", "team"), ("teams", "league"), ("trades", "team"),
                                        ("recap", "league"), ("records", "league"), ("weekrecap", "week"), ("digest", "home")])
def test_a_leaf_finds_its_group(nav, leaf, group):
    assert nav("navGroupOf", leaf) == group


def test_a_yahoo_league_shows_all_six(nav):
    assert nav("navLeavesFor", "team", YAHOO, False) == ["roster", "waivers", "trades"]
    assert nav("navLeavesFor", "league", YAHOO, False) == ["recap", "teams", "records"]


def test_espn_has_no_record_book_but_has_the_trade_finder(nav):
    """ESPN has no record book, so no Records; Trades is the finder, which every league with rosters has."""
    assert nav("navLeavesFor", "team", ESPN, False) == ["roster", "waivers", "trades"]
    assert nav("navLeavesFor", "league", ESPN, False) == ["recap", "teams"]


def test_ayo_has_the_finder_even_with_no_graded_trades(nav):
    """Its graded history was the old Trades leaf (AYO had none); the finder needs only rosters."""
    assert nav("navLeavesFor", "team", AYO, False) == ["roster", "waivers", "trades"]
    assert nav("navLeavesFor", "league", AYO, False) == ["recap", "teams", "records"]


def test_a_connected_league_has_no_waivers(nav):
    assert "waivers" not in nav("navLeavesFor", "team", CONNECTED, False)


def test_tuesday_puts_waivers_first(nav):
    assert nav("navLeavesFor", "team", YAHOO, True)[0] == "waivers"
    assert nav("navLeavesFor", "team", ESPN, True) == ["waivers", "roster", "trades"]


def test_other_groups_are_not_filtered(nav):
    assert nav("navLeavesFor", "scouting", ESPN, False) == ["news", "ranks", "board", "movers", "usage", "schedule"]
    assert nav("navLeavesFor", "week", ESPN, False)[:2] == ["live", "matchups"]


@pytest.mark.parametrize("leaf,tabs,want", [
    ("records", ["roster", "waivers", "teams", "recap"], "recap"),     # a #records link on an ESPN team
    ("trades", ["roster", "waivers", "recap"], "recap"),               # a league with no rosters has neither Teams nor Trades
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


@pytest.mark.req("Navigation: one League group, Stats", ac="Matchup's views read Today, Live, Start/Sit, Preview, Results")
def test_matchup_reads_today_live_start_sit_preview_results(nav):
    """Storyboard B (2026-10-08): the Digest reads Today and the week's Recap reads Results, so League keeps the
    only Recap. Leaf ids and hashes stay."""
    row = nav("NAV.find(([g]) => g === 'week')[1].filter(k => !NAV_HIDDEN.includes(k))")
    # Today left for Home, its own tab (Home draft B, 2026-10-08).
    assert row[:4] == ["live", "matchups", "preview", "weekrecap"]
    assert [nav("navLabel", k) for k in row[:4]] == ["Live", "Start/Sit", "Preview", "Results"]


def test_matchup_ends_with_bets_three_and_news_leads_players(nav):
    """Highlights was dropped 2026-10-08 (David: "the information is not useful"): Matchup's row ends with Bets'
    three (Home draft B), and News leads Players (its Yahoo and ESPN home)."""
    assert nav("NAV.find(([g]) => g === 'week')[1].filter(k => !NAV_HIDDEN.includes(k)).slice(-4)") == ["weekrecap", "parlay", "build", "dfs"]
    assert nav("NAV.find(([g]) => g === 'scouting')[1][0]") == "news"


def test_the_dropped_highlights_hash_opens_ranks(nav):
    """David, 2026-10-08: the view is gone; an old #highlights bookmark lands on Players > Ranks."""
    assert nav("navLeafOf", "highlights") == "ranks"
    assert nav("navGroupOf", "ranks") == "scouting"
    assert nav("NAV.some(([, tabs]) => tabs.includes('highlights'))") is False


@pytest.mark.parametrize("leaf,tabs,want", [
    ("trades", ["roster", "waivers"], "roster"),     # a league with no rosters: Team's first view
    ("records", ["recap", "teams"], "recap"),         # an ESPN team: League's Recap
    ("waivers", ["roster", "trades"], "roster"),     # a connected league
])
def test_a_team_or_league_leaf_a_league_lacks_lands_in_its_own_group(nav, leaf, tabs, want):
    assert nav("navFallback", leaf, tabs) == want


def test_the_stats_views_are_named_by_what_they_hold(nav):
    """The group says Stats and each sub-tab says what is in it (2026-10-05, David: A + C). Leaves keep their ids."""
    assert [nav("navLabel", k) for k in ("board", "movers", "usage")] == [words(f"nav.tab.{k}") for k in ("board", "movers", "grid")]
