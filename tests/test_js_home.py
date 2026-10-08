"""Home (ledger #52, draft B, David 2026-10-08), in Node: the nav's Home tab, the day plan's cards, the week tier
sheet and Injury watch's top rows. Data in, data out (data/navmap.js, data/tiers.js, data/dayplan.js); what the
cards draw is tests/test_digest*.py."""
import pytest

NOON = {"sun": "2026-10-04T19:00:00Z", "mon": "2026-10-05T19:00:00Z", "tue": "2026-10-06T19:00:00Z",
        "wed": "2026-10-07T19:00:00Z", "thu": "2026-10-08T19:00:00Z", "fri": "2026-10-09T19:00:00Z",
        "sat": "2026-10-10T19:00:00Z"}


def ms(iso):
    from datetime import datetime
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


@pytest.fixture(scope="module")
def js(node_js):
    return node_js("data/schedule.js", "data/navmap.js", "data/tiers.js", "data/dayplan.js", "data/hero.js",
                   globals={"LIVE_SCHEDULE": {"games": [], "alias": {}}})


# ---------------------------------------------------------------- the bar

@pytest.mark.req("Home", ac="Home is its own tab, first, holding today's Digest")
def test_home_is_the_first_group_and_holds_only_the_digest(js):
    assert js("NAV.map(([g]) => g)") == ["home", "team", "week", "scouting", "league"]
    assert js("NAV[0][1]") == ["digest"]
    assert js("navGroupOf", "digest") == "home"


@pytest.mark.req("Home", ac="Bets moves under Matchup and keeps its leaves")
def test_the_bets_views_sit_under_matchup_with_their_own_leaves(js):
    week = js("NAV.find(([g]) => g === 'week')[1]")
    assert [k for k in ("parlay", "build", "dfs") if k in week] == ["parlay", "build", "dfs"]
    assert [js("navLeafOf", k) for k in ("parlay", "build", "dfs")] == ["parlay", "build", "dfs"]
    assert js("NAV.some(([g]) => g === 'bets')") is False


def test_a_name_no_group_holds_falls_to_homes_group(js):
    assert js("navGroupOf", "nonsense") == "home"


# ---------------------------------------------------------------- the day plan

@pytest.mark.req("Home", ac="Thursday is one Tonight card, then the tiers, Injury watch, Top calls")
def test_thursday_is_one_tonight_card_then_tiers(js):
    assert js("ms => dgCardOrder(dgDayPlan(ms))", ms(NOON["thu"])) == ["tonight", "tiers", "status", "calls"]


@pytest.mark.req("Home", ac="the tier sheet follows the day's job on every day")
@pytest.mark.parametrize("day", list(NOON))
def test_the_tier_sheet_follows_the_days_job(js, day):
    order = js("ms => dgCardOrder(dgDayPlan(ms))", ms(NOON[day]))
    lead = 2 if day in ("wed", "sun") else 1        # the night game sits second on those two days
    assert order.index("tiers") == lead, order


@pytest.mark.req("Home", ac="Sunday before kickoff: Need to know, Sunday night, tiers, Weather, Top calls")
def test_sunday_before_kickoff_keeps_weather(js):
    got = js("ms => { const p = dgDayPlan(ms), d = {}; dgCardOrder(p).forEach(id => { d[id] = id === 'now' ? '' : '<' + id + '>'; }); return dgCardList(p, d); }",
             ms(NOON["sun"]))
    assert got == ["need", "night", "tiers", "weather", "calls"]


@pytest.mark.req("Home", ac="from the first kickoff Right now takes Weather's place")
def test_right_now_takes_weathers_place(js):
    got = js("ms => { const p = dgDayPlan(ms), d = {}; dgCardOrder(p).forEach(id => { d[id] = '<' + id + '>'; }); return dgCardList(p, d); }",
             ms(NOON["sun"]))
    assert got == ["need", "night", "tiers", "now", "calls"]


def test_weather_stays_on_a_day_with_no_right_now(js):
    got = js("ms => dgCardList(dgDayPlan(ms), {status: '<s>', tiers: '<t>', weather: '<w>'})", ms(NOON["fri"]))
    assert got == ["status", "tiers", "weather"]


@pytest.mark.req("Home", ac="five cards at most")
@pytest.mark.parametrize("day", list(NOON))
def test_no_day_draws_more_than_five(js, day):
    got = js("ms => { const p = dgDayPlan(ms), d = {}; dgCardOrder(p).forEach(id => { d[id] = '<' + id + '>'; }); return dgCardList(p, d); }",
             ms(NOON[day]))
    assert len(got) <= js("DG_MAX_CARDS") and got[0] == js("ms => dgDayPlan(ms).cards[0]", ms(NOON[day]))


# ---------------------------------------------------------------- the tier sheet

def rows(sizes, pos="RB"):
    """One row per player, `sizes[i]` players in tier i+1, ranked 1..n."""
    out, n = [], 0
    for tier, size in enumerate(sizes, 1):
        for _ in range(size):
            n += 1
            out.append({"slug": f"{pos.lower()}{n}", "n": f"P {n}", "pos": pos, "rank": n, "tier": tier})
    return out


@pytest.mark.req("Home", ac="the tier sheet shows whole tiers until a 12-team league's starters are in")
def test_the_sheet_takes_whole_tiers_until_the_starters_are_in(js):
    """RB tiers of 1, 1, 3, 3, 3, 9, 8, 32 (the storyboard's week 5): 24 starters land inside tier 7, so tiers 1-7 show,
    28 backs of 60."""
    got = js("([l, d]) => dgTierLines(l, d)", [rows([1, 1, 3, 3, 3, 9, 8, 32]), 24])
    assert [t["tier"] for t in got["tiers"]] == [1, 2, 3, 4, 5, 6, 7]
    assert [len(t["rows"]) for t in got["tiers"]] == [1, 1, 3, 3, 3, 9, 8]
    assert (got["shown"], got["of"]) == (28, 60)


def test_a_tier_that_ends_on_the_line_is_the_last(js):
    got = js("([l, d]) => dgTierLines(l, d)", [rows([6, 6, 6]), 12])
    assert [t["tier"] for t in got["tiers"]] == [1, 2] and got["shown"] == 12


def test_a_short_list_shows_every_tier(js):
    got = js("([l, d]) => dgTierLines(l, d)", [rows([2, 3]), 24])
    assert (got["shown"], got["of"], len(got["tiers"])) == (5, 5, 2)


def test_an_empty_list_has_no_tiers(js):
    assert js("([l, d]) => dgTierLines(l, d)", [[], 24]) == {"tiers": [], "shown": 0, "of": 0}
    assert js("([l, d]) => dgTierLines(l, d)", [None, 24]) == {"tiers": [], "shown": 0, "of": 0}


def test_a_row_keeps_its_place_in_the_list(js):
    got = js("([l, d]) => dgTierLines(l, d)", [rows([2, 2]), 3])
    assert [r["slug"] for t in got["tiers"] for r in t["rows"]] == ["rb1", "rb2", "rb3", "rb4"]


@pytest.mark.parametrize("pos,starters", [("QB", 12), ("RB", 24), ("WR", 24), ("TE", 12)])
def test_the_depth_is_a_12_team_leagues_starters(js, pos, starters):
    assert js("p => DG_TIER_DEPTH[p]", pos) == starters


def test_flex_goes_deeper_than_any_one_position(js):
    assert js("DG_TIER_DEPTH.FLEX") > max(js("p => DG_TIER_DEPTH[p]", p) for p in ("QB", "RB", "WR", "TE"))


@pytest.mark.req("Home", ac="the sheet opens on RB on Thursday and WR on Sunday; a pick wins")
@pytest.mark.parametrize("day,want", [("thu", "RB"), ("sun", "WR"), ("tue", "RB"), ("sat", "RB")])
def test_the_sheet_opens_on_the_days_position(js, day, want):
    assert js("([d]) => dgTierPos(d, null)", [day]) == want


def test_the_readers_pick_wins_over_the_day(js):
    assert js("([d, p]) => dgTierPos(d, p)", ["thu", "TE"]) == "TE"
    assert js("([d, p]) => dgTierPos(d, p)", ["thu", "K"]) == "RB", "a position the sheet has no chip for is ignored"


def test_the_chips_are_qb_rb_wr_te_flex(js):
    assert js("DG_TIER_POSITIONS") == ["QB", "RB", "WR", "TE", "FLEX"]


# ---------------------------------------------------------------- Injury watch

HURT = [{"slug": "a", "pos": "QB", "rank": 9, "status": "Questionable"},
        {"slug": "b", "pos": "WR", "rank": 2, "status": "Questionable"},
        {"slug": "c", "pos": "RB", "rank": 1, "status": "Out"},
        {"slug": "d", "pos": "TE", "rank": 3, "status": "Questionable"},
        {"slug": "e", "pos": "WR", "rank": 30, "status": "Questionable"}]
RANKS = {"rows": [{"slug": "a", "pos": "QB", "rank": 9, "pts": 15.0}, {"slug": "b", "pos": "WR", "rank": 2, "pts": 17.5},
                  {"slug": "c", "pos": "RB", "rank": 1, "pts": 19.0}, {"slug": "d", "pos": "TE", "rank": 3, "pts": 11.0},
                  {"slug": "e", "pos": "WR", "rank": 30, "pts": 6.0}]}


@pytest.mark.req("Home", ac="Injury watch shows the highest-ranked questionable players league-wide")
def test_injury_watch_is_the_top_questionable_by_projection(js):
    got = js("([d, r]) => dgWatchRows(d, r)", [{"hurt": HURT}, RANKS])
    assert [r["slug"] for r in got["rows"]] == ["b", "a", "d"]
    assert got["of"] == 4, "four questionable in all; the Out back is not one"


def test_injury_watch_holds_at_most_its_cap(js):
    many = [{"slug": f"q{i}", "pos": "WR", "rank": i, "status": "Questionable"} for i in range(1, 10)]
    got = js("([d, r]) => dgWatchRows(d, r)", [{"hurt": many}, None])
    assert len(got["rows"]) == js("DG_WATCH_N") and got["of"] == 9
    assert [r["slug"] for r in got["rows"]] == [f"q{i}" for i in range(1, js("DG_WATCH_N") + 1)]


def test_injury_watch_with_no_questionable_is_empty(js):
    assert js("([d, r]) => dgWatchRows(d, r)", [{"hurt": [HURT[2]]}, RANKS]) == {"rows": [], "of": 0}
    assert js("([d, r]) => dgWatchRows(d, r)", [None, RANKS]) == {"rows": [], "of": 0}


def test_a_hurt_row_reads_its_rank_from_ranks(js):
    """Home shows one rank, Ranks' (the storyboard found B. Irving RB17 on one card and RB22 in Ranks)."""
    assert js("([r, k]) => dgRankOf(r, k)", [{"slug": "b", "pos": "WR", "rank": 7}, RANKS]) == "WR2"
    assert js("([r, k]) => dgRankOf(r, k)", [{"slug": "zz", "pos": "WR", "rank": 7}, RANKS]) == ""
    assert js("([r, k]) => dgRankOf(r, k)", [{"slug": "b", "pos": "WR"}, None]) == ""


# ---------------------------------------------------------------- the hero's ghost wall

@pytest.mark.req("Home", ac="the hero's split-flap ghost spells the lead's own ghost, the home side, or the week")
@pytest.mark.parametrize("lead,week,want", [
    ({"ghost": "RB1", "vs": ["TB", "DAL"]}, 5, "RB1"),      # the lead's own reason wins
    ({"vs": ["TB", "DAL"]}, 5, "DAL"),                       # a game: its home side
    ({"head": "x"}, 5, "WK5"),                               # nothing of its own: the week
    ({"vs": ["TB"]}, 6, "WK6"),
    (None, 5, "WK5"),
    ({}, None, ""),
])
def test_the_hero_ghost_follows_the_lead(js, lead, week, want):
    assert js("([l, w]) => dgHeroGhost(l, w)", [lead, week]) == want


def test_the_flap_cells_count_every_character_and_keep_a_space_as_a_gap(js):
    cells = js("dgFlapCells", "TB @")
    assert [(c["c"], c["i"], c["gap"]) for c in cells] == [("T", 0, False), ("B", 1, False), (" ", 2, True), ("@", 3, False)]


def test_an_entity_is_one_flap_cell(js):
    assert [c["c"] for c in js("dgFlapCells", "A&amp;M")] == ["A", "&amp;", "M"]
    assert js("dgFlapCells", "") == [] and js("dgFlapCells", None) == []


def test_flex_is_three_lineup_slots_deep(js):
    """FLEX: RB, WR and TE can all start there, so the sheet goes three slots of 12 teams deep."""
    assert js("DG_TIER_DEPTH.FLEX") == 3 * js("DG_TIER_TEAMS")


# ---------------------------------------------------------------- ranking hurt rows, tonight's hold

def test_hurt_rows_with_no_points_go_by_rank(js):
    rows = [{"slug": "c", "rank": 3, "status": "Questionable"}, {"slug": "a", "rank": 1, "status": "Questionable"},
            {"slug": "b", "rank": 2, "status": "Questionable"}]
    assert [r["slug"] for r in js("([d, r]) => dgWatchRows(d, r)", [{"hurt": rows}, None])["rows"]] == ["a", "b", "c"]


def test_fridays_pick_is_the_best_ranked_and_none_without_a_packet(js):
    rows = [{"slug": "two", "rank": 2}, {"slug": "one", "rank": 1}]
    assert js("([d, r]) => dgPickStatus(d, r).slug", [{"hurt": rows}, None]) == "one"
    assert js("([d, r]) => dgPickStatus(d, r)", [None, RANKS]) is None


@pytest.fixture(scope="module")
def cut(node_js):
    return node_js("data/schedule.js", "data/digest.js", globals={"LIVE_SCHEDULE": {"games": []}})


KO = "2026-10-09T00:15:00Z"


@pytest.mark.req("Home", ac="tonight's game keeps its players in the lists until kickoff")
def test_tonights_game_is_held_and_its_rows_stay_in_the_lists(cut):
    c = {"tonight": [{"ko": KO, "away": "TB", "home": "DAL"}], "tonight_last": True,
         "hurt": [{"team": "DAL", "slug": "x"}], "best": [], "top5": [], "wx": [], "near": None}
    got = cut("([c, ms]) => dgTonightCut(c, ms)", [c, ms("2026-10-08T19:00:00Z")])
    assert [g["home"] for g in got["tn"]] == ["DAL"] and got["tnLast"] is True
    assert [r["slug"] for r in got["hurt"]] == ["x"], "Injury watch ranks tonight's players with everyone"


def test_a_game_outside_its_window_is_not_held(cut):
    c = {"tonight": [{"ko": KO}], "tonight_last": True, "hurt": []}
    got = cut("([c, ms]) => dgTonightCut(c, ms)", [c, ms("2026-10-07T19:00:00Z")])
    assert got["tn"] == [] and got["tnLast"] is False and got["hurt"] == []
