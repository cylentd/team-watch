"""Whose rows are "mine" in the DFS pool and the chat (2026-10-06), in Node.

David, 2026-10-06: "mine" is the players on the teams the reader follows. The DFS pool's lime edge and the chat's
`rostered_by_me` read a flag the build wrote from David's rosters, so a leaguemate's chat was told David's players
were theirs ("my highest-projected players"). Both now read data/mates.js `mineSlugs`, by slug. And no row the page
carries (the samples included) holds the flag any more.
"""
import pytest

TEAMS = {
    "yahoo": {"roster": [{"slug": "a-back"}, {"slug": "b-wideout"}]},
    "espn-run-it-back": {"roster": [{"slug": "d-passer"}], "mate": True},
}
POOL = [
    {"n": "A Back", "slug": "a-back", "pos": "RB", "team": "AAA", "ppg": 14.0},
    {"n": "B Wideout", "slug": "b-wideout", "pos": "WR", "team": "BBB", "ppg": 12.0},
    {"n": "D Passer", "slug": "d-passer", "pos": "QB", "team": "DDD", "ppg": 20.0},
    {"n": "E Other", "slug": "e-other", "pos": "WR", "team": "EEE", "ppg": 18.0},
]
DFS_ROW = {"n": "A Back", "slug": "a-back", "pos": "RB", "team": "AAA", "sal": 20, "proj": 15.0}


@pytest.fixture(scope="module")
def chat(node_js):
    js = node_js("data/mates.js", "surface/chat/context.js", globals={"TEAMS": TEAMS, "POOL": POOL, "FOLLOWED": []})
    js("(() => { globalThis.tsFollowed = () => FOLLOWED; return 1; })()")
    return js


def following(js, *keys):
    js("(ks) => { FOLLOWED = ks; return 1; }", list(keys))


def test_the_chats_default_players_are_the_readers_own_best_first(chat):
    following(chat, "yahoo")
    assert [r["name"] for r in chat("chatMine()")] == ["A Back", "B Wideout"]
    following(chat, "yahoo", "espn-run-it-back")
    assert [r["name"] for r in chat("chatMine()")] == ["D Passer", "A Back", "B Wideout"]


def test_unfollowing_a_team_takes_its_players_out_of_the_chats_default(chat):
    following(chat, "yahoo", "espn-run-it-back")
    following(chat, "espn-run-it-back")
    assert [r["name"] for r in chat("chatMine()")] == ["D Passer"]


def test_a_reader_who_follows_nobody_has_no_players_of_their_own_in_the_chat(chat):
    following(chat)
    assert chat("chatMine()") == []


def test_a_named_player_is_marked_mine_only_when_the_reader_follows_his_team(chat):
    following(chat, "espn-run-it-back")
    assert [(r["name"], r["rostered_by_me"]) for r in chat("chatNamed('start A Back or D Passer')")] == [
        ("A Back", False), ("D Passer", True)]
    following(chat, "yahoo")
    assert [(r["name"], r["rostered_by_me"]) for r in chat("chatNamed('start A Back or D Passer')")] == [
        ("A Back", True), ("D Passer", False)]


@pytest.fixture(scope="module")
def dfs(node_js):
    return node_js("surface/dfs/rows.js", globals={"HEADS": {}, "INJ": {}})


def row_html(js, mine):
    return js("(p, mine) => dfsPoolRow(p, 0, 200, new Set(), new Map(), 0, null, new Set(mine))", DFS_ROW, mine)


def test_a_dfs_row_wears_the_lime_edge_only_for_a_player_the_reader_follows(dfs):
    assert 'class="prow dfsrow mine ' in row_html(dfs, ["a-back"])
    assert 'class="prow dfsrow  ' in row_html(dfs, ["b-wideout"])
    assert 'class="prow dfsrow  ' in row_html(dfs, [])


def test_a_dfs_row_with_no_slug_is_never_mine(dfs):
    html = dfs("(p, mine) => dfsPoolRow(p, 0, 200, new Set(), new Map(), 0, null, new Set(mine))",
               {**DFS_ROW, "slug": None, "abbr": "SEA"}, ["a-back", None])
    assert "mine" not in html.split('data-dfs=')[0]


@pytest.fixture(scope="module")
def samples(node_js):
    return node_js("data/pool.js", "data/dfs.js", globals={"LIVE_POOL": None, "LIVE_DFS_YAHOO": None})


@pytest.mark.parametrize("rows", ["SAMPLE_POOL", "DFSPOOL_DK", "DFSPOOL_YAHOO_SAMPLE", "POOL"])
def test_no_sample_row_carries_the_build_time_mine_flag(samples, rows):
    assert samples(f"{rows}.filter(r => 'mine' in r).map(r => r.n)") == []


# What the sample rows show when the build finds no live file (data/dfs.js, data/pool.js, data/market.js). Taking
# `mine:1` off these rows left their numbers as they were; this pins the ones the flag sat beside.
DK_SAMPLE = {   # slug: (salary, projected points, owned %)
    "devon-achane": (8400, 21.1, 32), "amonra-st-brown": (8100, 19.8, 27), "derrick-henry": (7900, 18.9, 24),
    "tee-higgins": (6800, 15.4, 16), "jared-goff": (6200, 18.4, 14), "tetairoa-mcmillan": (5600, 13.1, 12),
    "brock-purdy": (5400, 17.2, 9), "george-kittle": (5200, 13.6, 21),
}


def test_the_dk_sample_keeps_the_salary_projection_and_ownership_of_the_rows_that_lost_the_flag(samples):
    got = samples("DFSPOOL_DK.map(r => [r.slug, r.sal, r.proj, r.own])")
    assert {s: (a, b, c) for s, a, b, c in got if s in DK_SAMPLE} == DK_SAMPLE


def test_the_pool_sample_keeps_jerry_jeudys_snaps_red_zone_and_ownership(samples):
    jeudy = samples("SAMPLE_POOL.find(r => r.slug === 'jerry-jeudy')")
    assert (jeudy["snaps"], jeudy["rz"], jeudy["own"]) == (49, 0, 44)


MARKET_SAMPLE = {   # (slug, market): model chance, edge in points
    ("devon-achane", "RUSH"): (62, 8.5), ("amonra-st-brown", "RECS"): (64, 7.5), ("jared-goff", "PASS"): (57, 5.8),
    ("george-kittle", "TD"): (39, 3.9), ("derrick-henry", "RUSH"): (56, 3.4), ("amonra-st-brown", "REC"): (54, 1.9),
    ("tetairoa-mcmillan", "REC"): (53, 1.4), ("tee-higgins", "REC"): (49, -3.2),
}


def test_the_market_sample_keeps_the_model_chance_and_edge_of_the_rows_that_lost_the_flag(node_js):
    js = node_js("lib/kick.js", "data/market.js", globals={"KICK_TZ": "America/Los_Angeles"})
    got = js("PROPS_SAMPLE.map(r => [r.slug, r.mkt, r.model, r.edge])")
    assert {(s, m): (model, edge) for s, m, model, edge in got if (s, m) in MARKET_SAMPLE} == MARKET_SAMPLE
