"""League > Teams (leaf `teams`, 2026-10-05): design/teams.py cuts every team's best lineup by position from
ff-jarvis's roster files and this week's projections, and the page draws one roster card per team (cards
since 2026-10-06, a table with a page per team before). The cut is tested on small invented leagues; the
page on the fixture build, through pages/teams.py."""
import copy
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
import teams  # noqa: E402
from component import mount  # noqa: E402,F401  (the fixture)
from pages.teams import open_teams  # noqa: E402
from wording import words  # noqa: E402


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def row(name, pos, slot):
    return {"name": name, "pos": pos, "slot": slot, "team": "XXX"}


def proj(**pts):
    """A player_projections file: name -> points, every player on the model."""
    return {"players": [{"name": n.replace("_", " "), "pos": "RB", "team": "XXX", "pts": p, "src": "model",
                         "kickoff": "2026-09-13 17:00:00"} for n, p in pts.items()]}


# ---- slots: read from the data ----------------------------------------------------------------------

def test_espn_slots_are_the_files_starters_with_flex_kept_and_defense_dropped():
    d = {"starters": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "D/ST": 1, "FLEX": 2}, "detail": {}}
    assert teams.slots(d) == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2}


def test_yahoo_slots_are_the_most_any_team_starts_with_w_r_t_as_flex():
    d = {"detail": {
        "A": [row("a", "QB", "QB"), row("b", "RB", "RB"), row("c", "RB", "RB"), row("d", "WR", "W/R/T"),
              row("e", "K", "K"), row("f", "RB", "BN"), row("g", "RB", "BN"), row("h", "WR", "IR")],
        "B": [row("i", "QB", "QB"), row("j", "RB", "RB"), row("k", "WR", "WR"), row("l", "WR", "WR"),
              row("m", "TE", "TE"), row("n", "WR", "W/R/T"), row("o", "DEF", "DEF")]}}
    assert teams.slots(d) == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1}, "bench, IR, K and DEF are not starting slots"


def test_a_file_with_no_slots_has_no_board():
    assert teams.slots({"detail": {"A": [{"name": "a", "pos": "QB"}]}}) == {}


# ---- the lineup --------------------------------------------------------------------------------------

def p(n, pos, pts):
    return {"n": n, "pos": pos, "pts": pts}


def test_dedicated_slots_fill_first_and_flex_takes_the_best_left_of_rb_wr_te():
    players = [p("q1", "QB", 20), p("q2", "QB", 19), p("r1", "RB", 15), p("r2", "RB", 14), p("r3", "RB", 13),
               p("w1", "WR", 12), p("w2", "WR", 11), p("w3", "WR", 18), p("t1", "TE", 9), p("t2", "TE", 13.5)]
    lineup, bench = teams.best_lineup(players, {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2})
    got = [(r["slot"], r["n"]) for r in lineup]
    assert got == [("QB", "q1"), ("RB", "r1"), ("RB", "r2"), ("WR", "w3"), ("WR", "w1"), ("TE", "t2"),
                   ("FLX", "r3"), ("FLX", "w2")]
    assert [b["n"] for b in bench] == ["q2", "t1"], "the bench is who is left, best first; a QB never takes a flex"


def test_a_team_short_of_a_position_starts_who_it_has():
    lineup, bench = teams.best_lineup([p("r1", "RB", 5)], {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1})
    assert [(r["slot"], r["n"]) for r in lineup] == [("RB", "r1")] and bench == []


# ---- a league ----------------------------------------------------------------------------------------

SLOTS = {"QB": 1, "RB": 1, "WR": 1, "TE": 1, "FLEX": 1}


def league(extra_rows=None, **kw):
    """Three teams in a league that starts QB, RB, WR, TE and one flex."""
    def team(q, r, w, t, bench=()):
        return [row(q, "QB", "QB"), row(r, "RB", "RB"), row(w, "WR", "WR"), row(t, "TE", "TE"),
                *[row(n, pos, "BN") for n, pos in bench]]
    detail = {
        "Alpha": team("qa", "ra", "wa", "ta", [("ra2", "RB"), ("wa2", "WR")]),
        "Beta": team("qb", "rb", "wb", "tb", [("rb2", "RB")]),
        "Gamma": team("qc", "rc", "wc", "tc", [("wc2", "WR")]),
    }
    detail.update(extra_rows or {})
    return {"me": "Alpha", "league": "Test League", "starters": {"QB": 1, "RB": 1, "WR": 1, "TE": 1, "FLEX": 1},
            "detail": detail, **kw}


PTS = dict(qa=20, ra=15, wa=14, ta=8, ra2=13, wa2=12, qb=18, rb=10, wb=9, tb=7, rb2=6, qc=16, rc=11, wc=10, tc=6, wc2=5)


def board(roster=None, pts=None, status=None, season=None):
    roster = roster or league()
    return teams.live_league("test", roster, season, *teams._points(proj(**(pts or PTS)), slug, status, None)[1:], slug)


def by_name(b):
    return {t["name"]: t for t in b["teams"]}


def test_a_teams_cells_are_its_starters_per_position_and_flex_is_the_best_left():
    a = by_name(board())["Alpha"]
    assert a["cols"] == {"QB": 20.0, "RB": 15.0, "WR": 14.0, "TE": 8.0, "FLX": 13.0}, "FLX is ra2 (13), not wa2 (12)"
    assert a["tot"] == 70.0
    assert [b["n"] for b in a["bench"]] == ["wa2"]


def test_the_board_is_sorted_by_lineup_total_and_keyed_like_the_team_switch():
    b = board()
    assert [t["name"] for t in b["teams"]] == ["Alpha", "Beta", "Gamma"]
    assert [t["key"] for t in b["teams"]] == ["test", "test-beta", "test-gamma"], "my team is the league's own key"
    assert b["slots"] == SLOTS and b["name"] == "Test League"


def test_the_median_is_the_middle_teams_column():
    b = board()
    # QB 20, 18, 16; RB 15, 10, 11; flex: Alpha ra2 13, Beta rb2 6, Gamma wc2 5
    assert b["median"] == {"QB": 18.0, "RB": 11.0, "WR": 10.0, "TE": 7.0, "FLX": 6.0}


def test_a_spare_starter_is_a_bench_player_who_beats_the_median_teams_weakest_starter_there():
    b = by_name(board())
    # The median team's weakest WR starter is 9 (see the test below); Alpha's benched wa2 projects 12.
    assert b["Alpha"]["spare"] == ["WR"], "wa2 (12) beats 9; ra2 plays flex, so there is no spare RB"
    assert b["Beta"]["spare"] == [] and b["Gamma"]["spare"] == [], "their only extras (rb2, wc2) are playing flex"
    assert b["Beta"]["bench"] == [] and [x["slot"] for x in b["Beta"]["lineup"]][-1] == "FLX"


def test_the_flex_slots_count_as_starters_when_finding_the_weakest_starter():
    # Weakest RB starter: Alpha 13 (ra2 plays flex), Beta 6 (rb2 plays flex), Gamma 11 -> median 11.
    # Weakest WR starter: Alpha 14, Beta 9, Gamma 5 (wc2 plays flex) -> median 9.
    floors = teams._floors([t["lineup"] for t in board()["teams"]])
    assert floors["RB"] == 11 and floors["WR"] == 9 and floors["QB"] == 18


def test_out_players_ir_slots_and_unprojected_players_are_handled():
    roster = league({"Delta": [row("qd", "QB", "QB"), row("rd", "RB", "RB"), row("rd2", "RB", "IR"),
                               row("wd", "WR", "WR"), row("td", "TE", "TE"), row("kd", "K", "K"), row("dd", "DEF", "DEF")]})
    status = {"x": {"name": "wd", "injury": "Out"}}
    d = by_name(board(roster, dict(PTS, qd=17, rd=9, rd2=30, wd=30, td=5), status))["Delta"]
    assert d["cols"]["WR"] == 0.0, "Sleeper has him out, so the WR slot is empty"
    assert d["cols"]["RB"] == 9.0 and d["bench"] == [], "an IR player is neither a starter nor on the bench"
    assert all(r["pos"] in teams.POS for r in d["lineup"]), "no K or D/ST"
    unprojected = by_name(board(roster, PTS))["Delta"]
    assert unprojected["cols"]["QB"] == 0.0, "no projection counts 0"


def test_a_players_already_played_game_counts_zero():
    """The file projects each player's NEXT game: a team that has played this week's is next week's row."""
    sched = {"alias": {}, "week": 1, "games": [{"week": 1, "home": "XXX", "away": "YYY", "kickoff": "2026-09-13T17:00:00Z"},
                                    {"week": 2, "home": "XXX", "away": "YYY", "kickoff": "2026-09-20T17:00:00Z"}]}
    raw = proj(qa=20, qb=18)
    raw["players"][1]["kickoff"] = "2026-09-20 17:00:00"      # qb's next game is week 2; qa's is week 1
    _, pts, _ = teams._points(raw, slug, None, sched)
    assert pts["qa"] == 20 and pts["qb"] == 0


def test_the_block_carries_the_page_week():
    """The label's week (2026-10-05): the site's page week from the schedule block, whatever week most
    players' next games fall in (until 2026-10-05 it was that vote). A bye that week counts 0."""
    sched = {"alias": {}, "week": 5, "games": [{"week": 4, "home": "XXX", "away": "YYY", "kickoff": "2026-10-06T00:15:00Z"},
                                    {"week": 5, "home": "XXX", "away": "ZZZ", "kickoff": "2026-10-11T17:00:00Z"},
                                    {"week": 6, "home": "WWW", "away": "VVV", "kickoff": "2026-10-18T17:00:00Z"}]}
    raw = proj(qa=20, qb=18, qc=16)
    for p, kick, team in zip(raw["players"], ("2026-10-11 17:00:00", "2026-10-11 17:00:00", "2026-10-18 17:00:00"),
                             ("XXX", "ZZZ", "WWW")):
        p["kickoff"], p["team"] = kick, team
    week, pts, _ = teams._points(raw, slug, None, sched)
    assert week == 5 and pts["qa"] == 20 and pts["qc"] == 0, "qc's next game is week 6: on a bye in week 5"
    assert teams.live_teams([("a", league(), None)], raw, slug, None, sched)["week"] == 5
    assert teams.live_teams([("a", league(), None)], proj(**PTS), slug)["week"] is None, "no schedule, no week"


@pytest.mark.req("Teams", ac="a player whose NFL team has no game in the page week shows BYE")
def test_a_starter_and_a_bench_player_carry_their_nfl_team_and_bye_is_true_only_with_no_game_in_the_page_week():
    sched = {"alias": {"LAR": "LA"}, "week": 5, "games": [
        {"week": 5, "home": "XXX", "away": "ZZZ", "kickoff": "2026-10-11T17:00:00Z"},
        {"week": 5, "home": "LA", "away": "SF", "kickoff": "2026-10-11T20:00:00Z"},
        {"week": 6, "home": "NOP", "away": "XXX", "kickoff": "2026-10-18T17:00:00Z"}]}
    detail = {"Alpha": [{**row("qa", "QB", "QB"), "team": "NOP"}, {**row("ra", "RB", "RB"), "team": "XXX"},
                        {**row("wa", "WR", "WR"), "team": "LAR"}, {**row("ta", "TE", "TE"), "team": "NOP"},
                        {**row("ra2", "RB", "BN"), "team": "NOP"}]}
    roster = {"me": "Alpha", "league": "L", "starters": {"QB": 1, "RB": 1, "WR": 1, "TE": 1}, "detail": detail}
    block = teams.live_teams([("a", roster, None)], proj(qa=20, ra=15, wa=14, ta=8, ra2=3), slug, None, sched)
    tm = block["leagues"][0]["teams"][0]
    got = {r["n"]: (r["team"], r["bye"]) for r in tm["lineup"] + tm["bench"]}
    assert got == {"qa": ("NOP", True), "ra": ("XXX", False), "wa": ("LAR", False), "ta": ("NOP", True),
                   "ra2": ("NOP", True)}, "NOP has no week-5 game (its week-6 one does not count); LAR plays as LA"
    none = teams.live_teams([("a", roster, None)], proj(qa=20, ra=15, wa=14, ta=8, ra2=3), slug)
    assert not any(r["bye"] for r in none["leagues"][0]["teams"][0]["lineup"]), "no schedule, no way to say bye"
    contract.validate("LIVE_TEAMS", block)
    del block["leagues"][0]["teams"][0]["lineup"][0]["bye"]
    with pytest.raises(SystemExit, match=r"lineup\[0\]\.bye"):
        contract.validate("LIVE_TEAMS", block)


def test_the_record_comes_from_the_leagues_standings_and_is_null_without_one():
    season = {"teams": {"1": {"name": "Alpha", "w": 3, "l": 1, "t": 0}, "2": {"name": "Beta", "w": 0, "l": 3, "t": 1}}}
    b = by_name(board(season=season))
    assert (b["Alpha"]["w"], b["Alpha"]["l"], b["Alpha"]["t"]) == (3, 1, 0)
    assert b["Beta"]["t"] == 1
    assert (b["Gamma"]["w"], b["Gamma"]["l"]) == (None, None)


def test_a_league_without_slots_or_a_file_is_left_out_and_none_is_no_block():
    ok = ("a", league(), None)
    bare = {"me": "x", "detail": {"X": [{"name": "q", "pos": "QB"}]}}
    block = teams.live_teams([ok, ("b", bare, None), ("c", None, None)], proj(**PTS), slug)
    assert [lg["key"] for lg in block["leagues"]] == ["a"]
    assert teams.live_teams([("b", bare, None)], proj(**PTS), slug) is None
    assert teams.live_teams([], None, slug) is None


def test_the_contract_names_a_missing_field_and_passes_a_whole_block():
    block = teams.live_teams([("a", league(), None)], proj(**PTS), slug)
    contract.validate("LIVE_TEAMS", block)
    contract.validate("LIVE_TEAMS", None)
    broken = copy.deepcopy(block)
    del broken["leagues"][0]["teams"][1]["lineup"][0]["pts"]
    del broken["leagues"][0]["teams"][0]["cols"]["FLX"]
    with pytest.raises(SystemExit, match=r"teams\[1\]\.lineup\[0\]\.pts") as e:
        contract.validate("LIVE_TEAMS", broken)
    assert "teams[0].cols.FLX" in str(e.value)


def test_the_fixture_build_has_a_board_for_each_league_that_names_its_slots(built):
    line = next(x for x in built.report if x.startswith("Teams: "))
    assert line == "Teams: ayo 2, espn 2", "the Yahoo fixture is the old scrape with no slots, so it has no board"


# ---- the page: one card per team (2026-10-06) -------------------------------------------------------

def plant(board, roster, key="yahoo", season=None, bye=None):
    """Gives league `key` its cards from an invented roster file, and draws them."""
    board.plant(teams.live_league(key, roster, season, *teams._points(proj(**PTS), slug, None, None)[1:], slug, bye))


def fillers(n):
    return {f"T{i}": [row(f"q{i}", "QB", "QB")] for i in range(n)}


@pytest.mark.render
@pytest.mark.req("Teams", ac="the board is the league of the reader's team, one chip")
def test_teams_opens_on_the_readers_league_and_the_one_chip_moves_it(mount):
    """One chip since 2026-10-05: the team switch. It named the league beside it; a team picked in it is the league.
    On a phone the switch is the header bar's (#hdrswitch) and the chip keeps the league's name."""
    board, errors = open_teams(mount, "espn")
    assert board.chip.league_name().lower() == "espn"
    assert board.chip.old_league_chips() == 0, "no league chips of their own"
    assert board.league_group_count() == 1
    assert board.open_leaf().lower() == "teams"
    assert board.names() == ["Purdy Big in Japan", "Run It Back"]
    assert board.chip.switch_hidden()
    board.pick_in_header("ayo", "ayo")
    assert board.chip.league_name().lower() == "ayo"
    assert board.names() == ["Taylor Made for Sundays", "Don Wick"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Teams", ac="the reader's own card is first with a lime outline whatever the sort")
def test_only_the_readers_own_card_is_pinned_first_with_a_lime_outline(mount):
    board, _ = open_teams(mount, "espn")
    plant(board, league(me="Gamma"), key="espn")                 # Gamma is the reader's, and last on total
    assert [c["mine"] for c in board.cards()] == [True, False, False]
    assert board.names()[0] == "Gamma", "the reader's card is pinned above Alpha, who leads on total"
    assert board.outline(board.cards()[0]["key"]).count("200, 255, 46") == 1, "lime"
    board.sort("QB")
    assert board.names()[:2] == ["Gamma", "Alpha"], "a sort moves the others, never the pin"
    board, _ = open_teams(mount, "espn-run-it-back")
    assert [c["mine"] for c in board.cards()] == [True, False], "a leaguemate's team is the reader's, whatever it is"
    board.pick_team("ayo")
    assert board.cards()[0]["mine"] and board.names()[0] == "Taylor Made for Sundays", "the new league pins the new team"


@pytest.mark.render
@pytest.mark.req("Teams", ac="a sort chip row reorders the cards")
def test_a_sort_chip_orders_the_cards_by_its_column_and_total_is_the_default(mount):
    board, _ = open_teams(mount, "nothing")
    plant(board, league(), key="yahoo")
    assert [s["label"] for s in board.sorts()] == ["Total", "QB", "RB", "WR", "TE"], "no FLX chip"
    assert [s["label"] for s in board.sorts() if s["pressed"]] == ["Total"]
    assert board.names() == ["Alpha", "Beta", "Gamma"]
    board.sort("WR")
    assert [s["label"] for s in board.sorts() if s["pressed"]] == ["WR"], "one chip is always pressed"
    assert board.names() == ["Alpha", "Gamma", "Beta"], "WR: 14, 10, 9"
    board.sort("RB")
    assert board.names() == ["Alpha", "Gamma", "Beta"], "RB: 15, 11, 10"
    board.sort_with_keyboard("TE")                               # real buttons: operable from the keyboard
    assert [s["label"] for s in board.sorts() if s["pressed"]] == ["TE"]
    assert board.names() == ["Alpha", "Beta", "Gamma"], "TE: 8, 7, 6"
    board.sort("Total")
    assert board.names() == ["Alpha", "Beta", "Gamma"]


@pytest.mark.render
@pytest.mark.req("Teams", ac="the strength strip tints 8% off the median and marks a spare")
def test_a_strip_cell_is_tinted_only_8_percent_off_the_median_and_a_spare_is_marked(mount):
    board, _ = open_teams(mount, "nothing")
    plant(board, league(), key="yahoo")
    got = {c["name"]: [(x["col"], x["value"], x["tone"] + ("+" if x["spare"] else "")) for x in c["strip"]] for c in board.cards()}
    # Medians: QB 18, RB 11, WR 10, TE 7, FLX 6. 8% either side is the tint; WR is Alpha's spare.
    assert got == {
        "Alpha": [("QB", "20.0", "up"), ("RB", "15.0", "up"), ("WR", "14.0", "up+"), ("TE", "8.0", "up"), ("FLX", "13.0", "up")],
        "Beta": [("QB", "18.0", ""), ("RB", "10.0", "dn"), ("WR", "9.0", "dn"), ("TE", "7.0", ""), ("FLX", "6.0", "")],
        "Gamma": [("QB", "16.0", "dn"), ("RB", "11.0", ""), ("WR", "10.0", ""), ("TE", "6.0", "dn"), ("FLX", "5.0", "dn")]}
    assert board.key_swatches() == 3


@pytest.mark.render
@pytest.mark.req("Teams", ac="one card per team, starters a row each, the bench one line, BYE or a dash for 0")
def test_every_team_gets_a_card_with_its_starters_its_bench_and_bye_or_a_dash_for_zero(mount):
    board, errors = open_teams(mount, "espn")
    delta = [{**row("Q Delta", "QB", "QB"), "team": "NOP"}, {**row("R Delta", "RB", "RB"), "team": "XXX"},
             {**row("W Delta", "WR", "WR"), "team": "NOP"}, {**row("T Delta", "TE", "TE"), "team": "XXX"},
             {**row("R Delta Two", "RB", "BN"), "team": "XXX"}]
    season = {"teams": {"1": {"name": "Alpha", "w": 3, "l": 1, "t": 0}}}
    plant(board, league({"Delta": delta, **fillers(8)}), key="espn", season=season, bye=lambda team: team == "NOP")
    cards = board.cards()
    assert len(cards) == 12, "every team in the league, not only the top"
    alpha = next(c for c in cards if c["name"] == "Alpha")
    assert (alpha["record"], alpha["total"]) == ("3–1", "70.0")
    assert [(s["slot"], s["name"], s["pts"]) for s in alpha["starters"]] == [
        ("QB", "qa", "20.0"), ("RB", "ra", "15.0"), ("WR", "wa", "14.0"), ("TE", "ta", "8.0"), ("FLX", "ra2", "13.0")]
    assert [(b["pos"], b["name"], b["pts"]) for b in alpha["bench"]] == [("WR", "wa2", "12.0")], "one wrapped line"
    d = next(c for c in cards if c["name"] == "Delta")
    assert [(s["slot"], s["name"], s["pts"]) for s in d["starters"]] == [
        ("QB", "Q. Delta", "BYE"), ("RB", "R. Delta", "–"), ("WR", "W. Delta", "BYE"), ("TE", "T. Delta", "–"),
        ("FLX", "R. Delta Two", "–")], "0 points is BYE only when his club has no game that week"
    assert board.bench_count() == 12
    assert board.fits()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Teams", ac="the foot offers This is my team with no pick, as a quiet text link, Your team on the reader's own card")
def test_with_no_team_every_foot_offers_this_is_my_team_as_a_quiet_link_and_a_tap_on_a_card_opens_nothing(mount):
    board, _ = open_teams(mount, "nothing")
    board.show_league("espn")
    assert [c["foot"] for c in board.cards()] == [words("lboard.team.mine")] * 2
    assert not any(c["mine"] or c["yours"] or c["tradeLink"] for c in board.cards()), "no team yet, so nobody to trade with"
    link = board.foot_box("espn-run-it-back")
    assert link["bg"] == "rgba(0, 0, 0, 0)", "a text link: lime is for the one primary action on a screen"
    assert link["w"] < 200 and link["h"] >= 44, f"not a full-width button, a 44px target: {link}"
    board.tap_card("espn-run-it-back")
    assert board.grid_count() == 1 and board.hash() == "#teams", "a card is not a button"
    board.set_as_mine("espn-run-it-back")
    cards = board.cards()
    assert [(c["name"], c["mine"], c["yours"], c["setButton"]) for c in cards] == [
        ("Run It Back", True, True, False), ("Purdy Big in Japan", False, False, False)]
    assert cards[0]["foot"] == words("lboard.team.yours")
    assert not cards[1]["setButton"] and not cards[1]["yours"], "once the reader has a team here no other card offers it"
    assert cards[1]["foot"] == words("lboard.team.trades"), "the other card ends in the trade link instead"
    assert board.stored_team() == "espn-run-it-back"


@pytest.mark.render
@pytest.mark.req("Teams", ac="a card of another team ends its foot with Trades with them, at the right end")
def test_another_teams_card_ends_in_trades_with_them_at_the_right_end_of_its_foot(mount):
    board, errors = open_teams(mount, "espn")
    cards = {c["key"]: c for c in board.cards()}
    assert cards["espn"]["foot"] == words("lboard.team.yours") and not cards["espn"]["tradeLink"], "the reader's own card has nobody to trade with"
    assert cards["espn-run-it-back"]["foot"] == words("lboard.team.trades")
    card, link = board.box("espn-run-it-back"), board.foot_box("espn-run-it-back")
    assert 0 <= (card["x"] + card["w"]) - (link["x"] + link["w"]) <= 14, f"flush with the card's right padding: {link} in {card}"
    assert link["h"] >= 44 and link["bg"] == "rgba(0, 0, 0, 0)"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Teams", ac="starters one 20px row each at the --t-2 step")
def test_a_starter_is_one_20px_row_at_the_t_2_step(mount):
    board, _ = open_teams(mount, "espn")
    plant(board, league(fillers(9)), key="espn")
    rows = board.starter_heights()
    assert rows and max(rows) <= 22, f"starter rows {rows}"
    assert board.starter_name_font() == "13.5px", "the --t-2 step, not below"


@pytest.mark.render
def test_a_league_with_no_rosters_draws_an_empty_state_and_keeps_the_chip(mount):
    board, _ = open_teams(mount)                                # the suite's reader is on the Madden Curse: no slots in the fixture
    assert board.is_empty_state()
    assert board.chip.chip_count() == 1
    board.pick_team("espn")
    assert len(board.cards()) == 2


@pytest.mark.render
@pytest.mark.req("Teams", ac="a phone gets one column of cards that start near the top")
def test_the_cards_fit_a_phone_in_one_column_and_the_first_starts_near_the_top(mount):
    board, _ = open_teams(mount, "espn")
    plant(board, league(fillers(9)), key="espn")
    first = board.box()
    assert first["y"] <= 260, f"the first card starts at {first['y']:.0f}px"
    assert board.fits()
    assert len(board.card_lefts()) == 1 and 330 <= first["w"] <= 340, "one column, the page's gutters either side"
    assert board.names_keep_room(), "a name keeps room"


@pytest.mark.render
@pytest.mark.req("Teams", ac="desktop: cards in a grid, three across at 1280")
def test_the_cards_are_three_across_on_a_desktop(mount):
    board, _ = open_teams(mount, "espn", size=(1280, 900))
    plant(board, league(fillers(9)), key="espn")
    lefts = board.card_lefts()
    assert len(lefts) == 3, f"columns at {lefts}"
    left = board.card_left_from_chip()
    assert left == 0, f"{left}px from the frame's edge"
    first_row = board.card_heights(3)
    assert len(set(first_row)) == 1, "cards of a row share a top and a bottom edge"
    assert board.fits()


