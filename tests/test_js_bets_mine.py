"""Whose lines are "mine" in Bets (2026-10-06), in Node.

David, 2026-10-06: "mine" is the players on the teams the reader follows. Bets read a flag the build wrote from David's
rosters (`p.mine`), so a leaguemate who tapped Mine only saw David's players, and "My players" built a slip of his.
Now Build's Mine only filter, the "My players" slip and the sort's tie-break read the teams the reader follows
(data/mates.js `mineSlugs`), matched to a line by slug (a line with no headshot slug: the slug rule of its name).
"""
import pytest

TEAMS = {
    "yahoo": {"roster": [{"slug": "a-back"}, {"slug": "b-wideout"}]},
    "espn": {"roster": [{"slug": "c-tight-end"}]},
    "espn-run-it-back": {"roster": [{"slug": "d-passer"}], "mate": True},
}
FUTURE = "2099-01-01 17:00:00"   # every kickoff is still to come


def line(n, game, slug="", **more):
    slug = n.lower().replace(" ", "-") if slug == "" else slug
    return {"n": n, "slug": slug, "pos": "WR", "mkt": "REC", "line": 40.5, "game": game, "commence": FUTURE, "kick": "Sun",
            "win": "morning", "book": "DraftKings", "model": 55, "edge": 3.0, **more}


PROPS = [
    line("A Back", "AAA @ BBB"),
    line("B Wideout", "CCC @ DDD"),
    line("C Tight End", "EEE @ FFF"),
    line("D Passer", "GGG @ HHH"),
    line("E Other", "AAA @ BBB"),
    # no headshot, so no slug on the line: his slug is his name's
    line("Zed Unshot", "CCC @ DDD", slug=None),
]
GLOBALS = {"KICK_TZ": "America/Los_Angeles", "BETS_NOW": 1791205200000,
           "LIVE_PROPS": {"props": PROPS, "windows": [], "days": [], "books": ["DraftKings"], "model": {"week": 4}},
           "LIVE_SCHEDULE": {"week": 4, "games": [], "alias": {}},
           "LIVE_RANKS": {"week": 5},
           "TEAMS": TEAMS, "FOLLOWED": []}
FILES = ("lib/kick.js", "data/schedule.js", "data/market.js", "data/mates.js", "builder/slips.js", "builder/state.js",
         "surface/parlay/gamelog.js", "surface/parlay/parlay.js")


@pytest.fixture(scope="module")
def bets(node_js):
    js = node_js(*FILES, globals=GLOBALS)
    # What the switch holds and what the helpers builder/ and lib/odds.js own: not what is under test.
    js("(() => { globalThis.tsFollowed = () => FOLLOWED; globalThis.lineMoved = () => 0; "
       "globalThis.udPick = () => ({}); globalThis.bestOdds = () => true; return 1; })()")
    return js


def follow(js, *keys):
    js("(ks) => { FOLLOWED = ks; MKT_MINE = true; MKT_SORT = 'edge'; PARLAY_BOOK = 'dk'; return 1; }", list(keys))


def listed(js):
    return sorted(js("buildLines().map(p => p.n)"))


def test_mine_only_lists_the_players_on_the_teams_the_reader_follows(bets):
    follow(bets, "yahoo")
    assert listed(bets) == ["A Back", "B Wideout"]


def test_following_more_teams_adds_their_players_and_a_leaguemates_team_counts(bets):
    follow(bets, "yahoo", "espn", "espn-run-it-back")
    assert listed(bets) == ["A Back", "B Wideout", "C Tight End", "D Passer"]


def test_unfollowing_a_team_takes_its_players_off_the_list(bets):
    follow(bets, "yahoo", "espn")
    assert listed(bets) == ["A Back", "B Wideout", "C Tight End"]
    follow(bets, "espn")
    assert listed(bets) == ["C Tight End"]


def test_a_line_with_no_slug_is_matched_by_its_names_slug(bets):
    bets("() => { TEAMS.espn.roster.push({slug: 'zed-unshot'}); return 1; }")
    follow(bets, "espn")
    assert listed(bets) == ["C Tight End", "Zed Unshot"]
    bets("() => { TEAMS.espn.roster.pop(); return 1; }")


def test_a_reader_who_follows_nobody_has_no_mine_so_the_filter_hides_nothing(bets):
    """The chip is gone then (test_build_mine.py), so a filter left on must not leave an empty list nobody can clear."""
    follow(bets)
    assert bets("betsMineOn()") is False
    assert len(listed(bets)) == len(PROPS)


def test_the_filter_is_on_only_when_it_was_tapped_and_there_is_someone_to_show(bets):
    follow(bets, "yahoo")
    assert bets("betsMineOn()") is True
    bets("MKT_MINE = false")
    assert bets("betsMineOn()") is False
    assert len(listed(bets)) == len(PROPS)


def mine_slip(js, book="dk"):
    return [PROPS[i]["n"] for i in js("(b) => mineSlip(b)", book)]


def test_my_players_builds_a_slip_of_the_followed_players_one_a_game(bets):
    follow(bets, "yahoo", "espn")
    assert mine_slip(bets) == ["A Back", "B Wideout", "C Tight End"]
    follow(bets, "espn")
    assert mine_slip(bets) == ["C Tight End"]


def test_my_players_builds_nothing_for_a_reader_who_follows_nobody(bets):
    follow(bets)
    assert mine_slip(bets) == []


def test_among_lines_the_sort_cannot_tell_apart_the_readers_players_come_first(bets):
    follow(bets, "espn-run-it-back")
    bets("() => { MKT_MINE = false; MKT_SORT = 'edge'; PROPS.forEach(p => { p.edge = 3.0; }); return 1; }")
    assert bets("buildLines().map(p => p.n)")[0] == "D Passer"
    follow(bets, "espn")
    bets("MKT_MINE = false")
    assert bets("buildLines().map(p => p.n)")[0] == "C Tight End"
