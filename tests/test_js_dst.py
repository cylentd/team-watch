"""Ranks > D/ST and K (data/dst.js, 2026-10-05, plan U6c): the rows the board draws, in Node.

The numbers are ff-jarvis's (LIVE_DST, METHODOLOGY 12.85); the function only picks the league's cell,
orders by the file's own rank and carries the flags. The fixture is the real 2026-10-05 run, weeks 5-8, renumbered 2-5 to sit on the fixture's page week:
CAR is on a bye in week 2, BUF in week 4, and week 2 is the only week with a posted line for ARI's
neighbours, so week 3 on wears `line: "rating"`."""
import copy
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = json.loads((ROOT / "tests" / "fixtures" / "data" / "dst_projections.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dst(node_js):
    return node_js("data/dst.js")


def row(board, team):
    return next(r for r in board["rows"] if r["team"] == team)


def raw(team):
    return next(t for t in BLOCK["teams"] if t["team"] == team)


def test_the_chosen_leagues_scoring_is_the_cell_the_row_reads(dst):
    espn, yahoo = dst("dstBoard", BLOCK, "espn", "DST"), dst("dstBoard", BLOCK, "yahoo", "DST")
    assert (espn["cell"], yahoo["cell"]) == ("dst_espn", "dst_yahoo")
    wrong = [r["team"] for board, cell in ((espn, "dst_espn"), (yahoo, "dst_yahoo")) for r in board["rows"]
             if r["pts"] != (None if (wk := raw(r["team"])["weeks"][0])["bye"] else wk["dst"][cell])]
    assert wrong == []
    assert row(espn, "ARI")["pts"] == 1.9 and row(yahoo, "ARI")["pts"] == 3.3
    ayo = dst("dstBoard", BLOCK, "ayo", "DST")
    assert ayo["cell"] == "dst_yahoo", "AYO is Yahoo's default scoring for a D/ST"


def test_rows_run_in_the_files_rank_order_and_byes_sit_last(dst):
    board = dst("dstBoard", BLOCK, "espn", "DST")
    ranks = [r["rank"] for r in board["rows"] if not r["bye"]]
    assert ranks == sorted(ranks) and ranks[0] == 1, ranks
    assert [r["rank"] for r in board["rows"] if not r["bye"]] == [raw(r["team"])["weeks"][0]["rank"]["dst_espn"] for r in board["rows"] if not r["bye"]]
    byes = [r["team"] for r in board["rows"] if r["bye"]]
    assert "CAR" in byes
    assert [r["bye"] for r in board["rows"]] == sorted(r["bye"] for r in board["rows"]), "every bye after every game"
    assert byes == sorted(byes), "byes in team order"
    assert len(board["rows"]) == 32


def test_teams_that_have_played_sit_after_the_teams_still_to_play_byes_last(dst):
    """Monday: the board leads with the games left. Each group keeps the file's rank order."""
    shown = copy.deepcopy(BLOCK)
    by_rank = sorted((t for t in shown["teams"] if not t["weeks"][0]["bye"]), key=lambda t: t["weeks"][0]["rank"]["dst_espn"])
    played = {by_rank[0]["team"], by_rank[2]["team"]}          # the #1 and #3 teams already played
    for t in by_rank:
        t["weeks"][0]["kicked_off"] = t["team"] in played
    board = dst("dstBoard", shown, "espn", "DST")
    got = [(r["team"], r["kicked_off"], r["bye"]) for r in board["rows"]]
    live = [r for r in got if not r[1] and not r[2]]
    done = [r for r in got if r[1]]
    byes = [r for r in got if r[2]]
    assert got == live + done + byes, "still to play, then played, then byes"
    assert {r[0] for r in done} == played
    assert [r[0] for r in live] == [t["team"] for t in by_rank if t["team"] not in played]
    assert [r[0] for r in done] == [t["team"] for t in by_rank if t["team"] in played]


def test_a_bye_week_has_no_points_and_the_next_weeks_say_bye(dst):
    board = dst("dstBoard", BLOCK, "espn", "DST")
    car = row(board, "CAR")
    assert car["bye"] and car["pts"] is None and car["rank"] is None and car["opp"] is None and car["streamer"] is False
    buf = row(board, "BUF")
    assert [c["week"] for c in buf["next"]] == [3, 4, 5]
    assert [c["bye"] for c in buf["next"]] == [False, True, False]
    assert buf["next"][1]["pts"] is None


def test_a_rating_week_is_marked_an_estimate_and_a_posted_one_is_not(dst):
    board = dst("dstBoard", BLOCK, "espn", "DST")
    ari = row(board, "ARI")
    assert ari["rating"] is False and ari["next"][0]["rating"] is True
    assert ari["next"][0]["pts"] == 3.0
    assert board["estimate"] is True
    shown = copy.deepcopy(BLOCK)
    for t in shown["teams"]:
        for w in t["weeks"]:
            if not w["bye"]:
                w["line"] = "posted"
    assert dst("dstBoard", shown, "espn", "DST")["estimate"] is False


def test_the_streamer_flag_is_the_files_for_that_league_and_never_after_kickoff(dst):
    board = dst("dstBoard", BLOCK, "espn", "DST")
    want = {t["team"] for t in BLOCK["teams"] if not t["weeks"][0]["bye"] and t["weeks"][0]["streamer"]["espn"]}
    assert want, "the fixture has at least one ESPN streamer"
    assert {r["team"] for r in board["rows"] if r["streamer"]} == want
    other = copy.deepcopy(BLOCK)
    pick = sorted(want)[0]
    next(t for t in other["teams"] if t["team"] == pick)["weeks"][0]["kicked_off"] = True
    assert row(dst("dstBoard", other, "espn", "DST"), pick)["streamer"] is False, "a team that has played cannot be streamed"
    # a streamer later in the horizon marks its small cell
    later = [(t["team"], i) for t in BLOCK["teams"] for i, w in enumerate(t["weeks"][1:]) if w["streamer"] and w["streamer"]["espn"]]
    assert later, "the fixture has a later-week ESPN streamer"
    team, i = later[0]
    assert row(board, team)["next"][i]["streamer"] is True


def test_who_rosters_it_in_that_league_or_free(dst):
    board = dst("dstBoard", BLOCK, "espn", "DST")
    def reads_espn_roster(r):
        held = raw(r["team"])["rostered"]["espn"]
        return r["free"] is (held["pct"] < 50 and not held["waiver"]) and r["owner"] == held["owner"] and r["mine"] is False
    assert [r["team"] for r in board["rows"] if not reads_espn_roster(r)] == []
    assert any(r["free"] for r in board["rows"]) and any(r["owner"] for r in board["rows"])
    # a different league reads its own roster
    yahoo = dst("dstBoard", BLOCK, "yahoo", "DST")
    assert [r["team"] for r in yahoo["rows"] if r["owner"] != raw(r["team"])["rostered"]["yahoo"]["owner"]] == []


def test_a_team_on_waivers_is_not_free_it_can_only_be_claimed(dst):
    """ESPN flags a D/ST nobody rosters but that is still on waivers (`rostered.espn.waiver`): FREE was wrong, the
    row says Waivers (2026-10-05)."""
    board = dst("dstBoard", BLOCK, "espn", "DST")
    claims = {t["team"] for t in BLOCK["teams"] if t["rostered"]["espn"]["waiver"]}
    assert claims and all(not r["free"] and r["waiver"] for r in board["rows"] if r["team"] in claims)
    assert not any(r["waiver"] for r in board["rows"] if r["team"] not in claims)
    assert not any(r["free"] and r["waiver"] for r in board["rows"])
    held = copy.deepcopy(BLOCK)
    next(t for t in held["teams"] if t["team"] == sorted(claims)[0])["rostered"]["espn"]["waiver"] = None
    assert row(dst("dstBoard", held, "espn", "DST"), sorted(claims)[0])["free"] is True


def test_k_is_a_yahoo_league_tab_and_never_espns(dst):
    assert dst("dstTabs", BLOCK, "espn") == ["DST"]
    assert dst("dstTabs", BLOCK, "yahoo") == ["DST", "K"]
    assert dst("dstTabs", BLOCK, "ayo") == ["DST", "K"]
    assert dst("dstBoard", BLOCK, "espn", "K") is None, "ESPN has no K slot"
    yahoo, ayo = dst("dstBoard", BLOCK, "yahoo", "K"), dst("dstBoard", BLOCK, "ayo", "K")
    assert (yahoo["cell"], ayo["cell"]) == ("k_yahoo", "k_ayo")
    assert row(yahoo, "ARI")["pts"] == 7.6 and row(ayo, "ARI")["pts"] == 7.8
    assert [r["team"] for r in yahoo["rows"] if r["owner"] != raw(r["team"])["k_rostered"]["yahoo"]["owner"]] == []


def test_a_position_the_league_lacks_falls_back_to_the_default(dst):
    """The reader switches from a Yahoo team on K to an ESPN one: the view must not draw an empty K."""
    assert dst("dstPos", "K", BLOCK, "espn") == "RB"
    assert dst("dstPos", "K", BLOCK, "yahoo") == "K"
    assert dst("dstPos", "DST", BLOCK, "espn") == "DST"
    assert dst("dstPos", "WR", BLOCK, "espn") == "WR"
    assert dst("dstPos", "DST", None, "espn") == "RB", "no file, no D/ST tab"


def test_the_note_knows_whether_the_cell_is_the_model_or_the_baseline(dst):
    assert dst("dstBoard", BLOCK, "espn", "DST")["source"] == "model"
    base = copy.deepcopy(BLOCK)
    base["source"]["dst_espn"] = "baseline"
    assert dst("dstBoard", base, "espn", "DST")["source"] == "baseline"
    assert dst("dstBoard", base, "yahoo", "DST")["source"] == "model"


def test_the_week_is_the_files_first_and_the_rest_are_the_next_three(dst):
    board = dst("dstBoard", BLOCK, "espn", "DST")
    assert board["week"] == 2 and board["weeks"] == [2, 3, 4, 5]
    assert [c["week"] for c in row(board, "ARI")["next"]] == [3, 4, 5]


def test_no_file_is_no_board(dst):
    assert dst("dstBoard", None, "espn", "DST") is None
    assert dst("dstTabs", None, "espn") == []


def test_the_league_follows_the_readers_team_and_defaults_to_espn(dst):
    assert dst("dstLeagueKey", "yahoo", True, BLOCK) == "yahoo"
    assert dst("dstLeagueKey", "ayo", True, BLOCK) == "ayo"
    assert dst("dstLeagueKey", "yahoo", False, BLOCK) == "espn", "no team picked: ESPN"
    assert dst("dstLeagueKey", None, True, BLOCK) == "espn"
    assert dst("dstLeagueKey", "mystery", True, BLOCK) == "espn", "a league the file lacks reads ESPN's"


# ---- who holds it is the reader's: the teams followed, never the file's David flag (2026-10-06) ----
# The file's `mine` says David holds the team, for every reader. A row is MINE when a team the reader follows,
# in the board's league, has that club's D/ST (or K) on its roster.
ROSTERS = {
    "espn": {"roster": [{"pos": "DST", "team": "SEA"}, {"pos": "QB", "team": "KC"}, {"pos": "K", "team": "JAX"}]},
    "yahoo": {"roster": [{"pos": "DST", "team": "CIN"}, {"pos": "K", "team": "KC"}]},
    "espn-run-it-back": {"roster": [{"pos": "DST", "team": "LAR"}, {"pos": "K", "team": "WSH"}], "mate": True, "league": "espn"},
    "ayo-don-wick": {"roster": [{"pos": "DST", "team": "JAC"}], "mate": True, "league": "ayo"},
    "connected": {"roster": [{"pos": "DST", "team": "DAL"}], "connected": True},
}


def held(dst, keys, lg, pos):
    return sorted(dst("dstHeld", ROSTERS, keys, lg, pos))


def test_the_clubs_held_are_the_followed_teams_in_the_boards_league_at_that_position(dst):
    assert held(dst, [], "espn", "DST") == [], "nothing followed, nothing held"
    assert held(dst, ["espn"], "espn", "DST") == ["SEA"], "his quarterback is no D/ST"
    assert held(dst, ["espn"], "espn", "K") == ["JAX"]
    assert held(dst, ["espn", "yahoo"], "espn", "DST") == ["SEA"], "a Yahoo team holds nothing on the ESPN board"
    assert held(dst, ["yahoo"], "yahoo", "K") == ["KC"]


def test_a_leaguemates_team_counts_when_followed_and_only_in_its_own_league(dst):
    assert held(dst, ["espn", "espn-run-it-back"], "espn", "DST") == ["LA", "SEA"]
    assert held(dst, ["ayo-don-wick"], "espn", "DST") == [], "an AYO team is not on the ESPN board"
    assert held(dst, ["ayo-don-wick"], "ayo", "DST") == ["JAX"]


def test_a_club_is_held_under_whichever_spelling_the_roster_uses(dst):
    """The roster says LAR, JAC and WSH; the file says LA, JAX and WAS."""
    assert held(dst, ["espn-run-it-back"], "espn", "DST") == ["LA"]
    assert held(dst, ["espn-run-it-back"], "espn", "K") == ["WAS"]
    assert held(dst, ["ayo-don-wick"], "ayo", "DST") == ["JAX"]


def test_a_connected_league_is_not_on_the_files_board(dst):
    """The file's holders are David's leagues'; a visitor's own league holds nothing here."""
    assert held(dst, ["connected"], "espn", "DST") == []


def test_a_row_is_mine_when_its_club_is_held_and_never_on_the_files_flag(dst):
    assert any(t["rostered"]["espn"]["mine"] for t in BLOCK["teams"]), "the file flags David's teams"
    assert not any(r["mine"] for r in dst("dstBoard", BLOCK, "espn", "DST", [])["rows"]), "a reader who holds none"
    mine = {r["team"] for r in dst("dstBoard", BLOCK, "espn", "DST", ["LA", "ARI"])["rows"] if r["mine"]}
    assert mine == {"LA", "ARI"}
    ayo = {r["team"] for r in dst("dstBoard", BLOCK, "ayo", "K", ["JAX"])["rows"] if r["mine"]}
    assert ayo == {"JAX"}
