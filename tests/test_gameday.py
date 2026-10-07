"""This week > Live (2026-09-28): the scoring table (api/_scoring.py), the build's block (design/gameday.py),
the trimmed stats endpoint (api/stats.py) and the page's scorer and board (js/data/gameday, surface/live).

tests/fixtures/gameday.json is a real slice of week 2: two games from each league with every starter's
Sleeper id, his Sleeper stats and the points his league officially gave him. Scoring those stats with the
league's rules must give the official number, which is the whole claim the Live view rests on.
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
# api/ goes last: it has a clips.py too, and contract.py must get design's. First, it broke this file
# run on its own (2026-10-05); the full suite only passed because another file imported design's first.
sys.path.append(str(REPO / "api"))

import pytest  # noqa: E402

import _scoring  # noqa: E402
import contract  # noqa: E402
import stats as api_stats  # noqa: E402
from _espn import slugify  # noqa: E402
from build import norm_name  # noqa: E402
from gameday import live_gameday  # noqa: E402
from mates import live_mates  # noqa: E402
from sources import DWR, read_first, load_status, load_kickers  # noqa: E402
from component import mount  # noqa: E402,F401  (the fixture)
from pages.gamesheet import SUMMARY, GameSheetPage  # noqa: E402
from pages.live_mine import LiveMinePage  # noqa: E402

FIX =json.loads((REPO / "tests" / "fixtures" / "gameday.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- the rules table

def test_espn_rules_report_unknown_ids_and_known_gaps():
    r = _scoring.espn_rules([[7, 1.0, None], [99, 0.0, 1.0], [209, 1.0, 1.0], [999, 2.0, None], [53, 0.0, None]])
    assert r["off"] == [{"s": ["pass_yd"], "per": 20, "p": 1.0}]
    assert r["dst"] == [{"s": ["sack"], "p": 1.0}]            # the D/ST's own points, from slot 16
    assert (r["unknown"], r["gaps"]) == (["999"], ["209"])      # a zero-point rule is simply absent


def test_yahoo_rules_read_yahoos_words():
    r = _scoring.yahoo_rules([["Offense", "Passing Yards", "25 yards per point"], ["Offense", "Receptions", "0.5"],
                              ["Defense/Special Teams", "Points Allowed 35+ points", "-4"],
                              ["Defense/Special Teams", "Points Allowed 1-6 points", "7"],
                              ["Defense/Special Teams", "Points Allowed 21-27 points", "0"],
                              ["Offense", "Something New", "3"]])
    assert r["off"] == [{"s": ["pass_yd"], "p": 1.0, "frac": 25.0}, {"s": ["rec"], "p": 0.5}]
    assert r["dst"] == [{"s": ["pts_allow"], "lo": 35, "hi": None, "p": -4.0},
                        {"s": ["pts_allow"], "lo": 1, "hi": 6, "p": 7.0}]
    assert r["unknown"] == ["Something New"]


def test_a_defense_scores_its_special_teams_fumbles():
    """Sleeper files a fumble forced or recovered on a kick or punt apart. KC D/ST, week 4 2026:
    ESPN gave 2.75; without def_st_ff and def_st_fum_rec the page said 0.25."""
    terms = _scoring.espn_rules(FIX["espn_items"])["dst"]
    s = {"def_st_ff": 1.0, "def_st_fum_rec": 1.0}
    pts = sum(t["p"] for t in terms if t["s"][0] in ("ff", "fum_rec") for k in t["s"] if s.get(k))
    assert pts == 2.5
    yahoo = _scoring.yahoo_rules([["Defense/Special Teams", "Fumble Recovery", "2"]])["dst"]
    assert "def_st_fum_rec" in yahoo[0]["s"]


def test_the_fixture_rules_are_the_leagues_own():
    """The fixture's rules are what the table makes of the leagues' raw settings today."""
    assert FIX["espn"]["rules"] == _scoring.espn_rules(FIX["espn_items"])
    assert FIX["yahoo"]["rules"] == _scoring.yahoo_rules(FIX["yahoo_rows"])
    assert FIX["espn"]["rules"]["unknown"] == [] and FIX["yahoo"]["rules"]["unknown"] == []


# --------------------------------------------------------------------------- the build's block

def test_block_meets_the_contract_and_keys_defenses_by_team():
    b = live_gameday(read_first(DWR / "espn_league.json"), read_first(DWR / "espn_rosters.json"),
                     read_first(DWR / "yahoo_league.json"), read_first(DWR / "league_rosters.json"),
                     read_first(DWR / "yahoo_settings.json"), load_status(), load_kickers(), slugify, norm_name)
    assert contract.problems("LIVE_GAMEDAY", b) == []
    rows = [r for lg in b["leagues"] for tm in lg["teams"].values() for r in tm["lineup"]]
    assert rows
    assert [r for r in rows if set(r) != {"slot", "n", "slug", "pos", "team", "sid"}] == []
    assert [r for r in rows if r["pos"] == "DEF" and r["sid"] != r["team"]] == []


def test_a_defense_and_a_kicker_find_their_sleeper_ids():
    season = {"week": 3, "league": "L", "bonus": None, "teams": {"1": {"name": "Me"}, "2": {"name": "You"}},
              "games": [{"week": 3, "home": 1, "away": 2}, {"week": 2, "home": 2, "away": 1}]}
    rosters = {"me": "Me", "detail": {"Me": [{"name": "Cam Little", "pos": "K", "team": "JAC", "slot": "K"},
                                             {"name": "Rams D/ST", "pos": "D/ST", "team": "LA", "slot": "D/ST"},
                                             {"name": "Matthew Stafford", "pos": "QB", "team": "LA", "slot": "QB"}],
                                      "You": []}}
    b = live_gameday(season, rosters, None, None, None, {"matthew stafford": {"sleeper_id": "421"}},
                     {"cam little": "7"}, slugify, norm_name)
    lg = b["leagues"][0]
    assert (lg["me"], lg["games"], lg["median"]) == ("1", [["2", "1"]], False)
    assert [(r["slot"], r["team"], r["sid"]) for r in lg["teams"]["1"]["lineup"]] == [
        ("QB", "LAR", "421"), ("K", "JAX", "7"), ("D/ST", "LAR", "LAR")]      # slot order, Sleeper's codes


def test_every_team_carries_the_page_key_the_reader_is_found_by():
    """The page finds the reader's team in a league by `key` (live.js gdMine): David's is the league's
    own key, any other the league plus the name's slug, the key mates.live_mates gives that team."""
    season = {"week": 3, "league": "L", "bonus": None, "teams": {"1": {"name": "Me"}, "2": {"name": "Run It Back"}},
              "games": [{"week": 3, "home": 1, "away": 2}]}
    rosters = {"me": "Me", "detail": {"Me": [], "Run It Back": []}}
    lg = live_gameday(season, rosters, None, None, None, {}, {}, slugify, norm_name)["leagues"][0]
    assert {tid: tm["key"] for tid, tm in lg["teams"].items()} == {"1": "espn", "2": "espn-run-it-back"}
    mates = live_mates(rosters, None, set(), lambda n, s: None, slugify)
    assert [t["key"] for t in mates["teams"]] == ["espn-run-it-back"]


# --------------------------------------------------------------------------- the trimmed endpoint

def test_stats_query_is_checked_before_sleeper_is_asked():
    assert api_stats.parse("week=3&ids=8183,SEA")[0] == (3, frozenset({"8183", "SEA"}), frozenset(), False)
    assert api_stats.parse("week=3&teams=CHI,PHI")[0] == (3, frozenset(), frozenset({"CHI", "PHI"}), False)
    assert api_stats.parse("week=3&ids=1&lead=1")[0][3] is True
    assert api_stats.parse("week=30&ids=1")[0] is None
    assert api_stats.parse("week=3&ids=1;drop")[0] is None
    assert api_stats.parse("week=3")[0] is None
    assert api_stats.parse("week=3&teams=1234")[0] is None
    assert api_stats.parse("week=3&teams=" + ",".join(["CHI"] * (api_stats.TEAMS_MAX + 1)))[0] is None


def test_the_box_is_every_player_of_the_two_clubs_named_and_no_defense():
    rows = [{"player_id": "1", "team": "CHI", "player": {"first_name": "D'Andre", "last_name": "Swift", "position": "RB"},
             "stats": {"rush_att": 6, "rush_yd": 22, "gp": 1}},
            {"player_id": "2", "team": "CHI", "player": {"position": "OL"}, "stats": {"gp": 1}},
            {"player_id": "CHI", "team": "CHI", "player": {"position": "DEF"}, "stats": {"pts_allow": 7}},
            {"player_id": "3", "team": "GB", "player": {"position": "WR"}, "stats": {"rec": 2}},
            {"player_id": "4", "team": "PHI", "player": {"first_name": "A", "last_name": "B", "position": "WR"}, "stats": {"gp": 1}}]
    assert api_stats.box(rows, frozenset({"CHI", "PHI"})) == {
        "1": {"n": "D'Andre Swift", "pos": "RB", "team": "CHI", "s": {"rush_att": 6, "rush_yd": 22}}}


def test_the_lead_is_every_touchdown_and_the_top_scorers_league_wide():
    row = lambda pid, pos, s: {"player_id": pid, "team": "CHI", "stats": s,
                               "player": {"first_name": "P", "last_name": pid, "position": pos}}
    rows = [row(str(i), "WR", {"rec": 1, "rec_yd": 10 + i}) for i in range(api_stats.LEAD_TOP + 5)]
    rows += [row("td", "TE", {"rec": 1, "rec_yd": 2, "rec_td": 1}), row("ol", "OL", {"rush_td": 1}),
             row("half", "RB", {"rush_yd": 1, "pts_half_ppr": 99.04})]
    got = api_stats.lead(rows)
    assert got["td"]["s"]["rec_td"] == 1 and "ol" not in got           # a TD always rides; no linemen
    assert got["half"]["pts"] == 99.0                                    # Sleeper's own half-PPR wins
    assert "0" not in got and str(api_stats.LEAD_TOP + 4) in got         # the lowest scorers fall off
    assert len(got) == api_stats.LEAD_TOP                                # the TD is already a top scorer here


def test_stats_keep_only_wanted_players_and_scored_fields():
    rows = [{"player_id": "1", "updated_at": 5, "stats": {"rec": 3, "rec_yd": 40, "gp": 1, "rec_td": 0}},
            {"player_id": "2", "updated_at": 9, "stats": {"rec": 9}}]
    assert api_stats.trim(rows, frozenset({"1"})) == ({"1": {"rec": 3, "rec_yd": 40}}, 5)
    games = [{"week": 3, "home": "CHI", "away": "PHI", "status": "in_game"}, {"week": 4, "home": "GB", "away": "TB"}]
    assert api_stats.states(games, 3) == {"CHI": "in_game", "PHI": "in_game"}


# --------------------------------------------------------------------------- the page

@pytest.fixture(scope="module")
def scorer(node_js):
    """The scorer (data/gameday/score.js) in Node: data in, data out, no page (2026-10-06)."""
    return node_js("data/gameday/score.js")


@pytest.fixture(scope="module")
def espn_js(node_js):
    return node_js("data/gameday/espn.js")


def test_the_page_scores_week_2_as_both_leagues_did(scorer):
    """Every started player and every team total, both leagues, to the hundredth."""
    got = scorer("""(fix) => {
      const out = {};
      for (const key of ["espn", "yahoo"]){
        const lg = fix[key];
        for (const tm of Object.values(lg.teams)) for (const r of tm.lineup.filter(gdStarter))
          if (r.sid && fix.official[key][r.sid] !== undefined) out[key + ":" + r.sid] = [gdPts(lg.rules, r, fix.stats[r.sid] || {}), fix.official[key][r.sid], r.n];
        const final = {};
        for (const tm of Object.values(lg.teams)) for (const r of tm.lineup) final[r.team] = "complete";
        for (const id of Object.keys(lg.teams)) if (key === "espn")
          out["team:" + id] = [gdSide(lg, id, fix.stats, final).total, fix.totals.espn[id], lg.teams[id].name];
      }
      return out;
    }""", {**FIX, "official": FIX["official"], "totals": FIX["totals"]})
    wrong = {k: v for k, v in got.items() if abs(v[0] - v[1]) > 0.011}
    assert not wrong, wrong
    assert len(got) > 60


def test_the_bench_is_scored_but_never_counted_and_proj_adds_who_is_left(scorer):
    got = scorer("""(fix) => {
      const lg = fix.espn, id = Object.keys(lg.teams)[0], final = {};
      for (const tm of Object.values(lg.teams)) for (const r of tm.lineup) final[r.team] = "complete";
      const s = gdSide(lg, id, fix.stats, final);
      const starters = s.rows.reduce((a, r) => a + r.pts, 0), bench = s.bench.reduce((a, r) => a + r.pts, 0);
      const mixed = {rows: [{state: "complete", pts: 10}, {state: "in_game", pts: 4}, {state: "in_game", pts: 20},
                            {state: "pre_game", pts: null}, {state: "pre_game", pts: null}]};
      const proj = [null, 12, 15, 9, null];
      let i = 0;
      return {total: s.total, starters, benchTotal: s.benchTotal, bench, nBench: s.bench.length,
              benchSlots: s.bench.every(r => GD_BENCH.includes(r.slot)),
              proj: gdProj(mixed, () => proj[i++])};
    }""", FIX)
    assert got["nBench"] > 0 and got["benchSlots"]
    assert abs(got["total"] - got["starters"]) < 0.011
    assert abs(got["benchTotal"] - got["bench"]) < 0.011
    assert got["proj"] == 10 + 12 + 20 + 9 + 0   # done as scored; mid-game the larger; unplayed projected


@pytest.mark.render
def test_the_board_says_where_each_game_is_and_a_row_opens_his_profile(mount):
    live, errors = LiveMinePage.open_board(mount)           # David's ESPN team: Live opens on its league
    # each of my halves (the left one of a mirrored row, tabs: surface/live/tabs.js): tinted while his
    # game is on, the kickoff before (and a dash for points); the second number is his projection,
    # unlabelled
    by_team = dict(live.left_half_states())
    assert by_team.get("SF") == "LIVE" and by_team.get("DET") == "PRE" and "FINAL" in by_team.values()
    # a game's second line is its clock; a final game says so, and no lock sits in the row
    assert live.drawn_shape_count() == 0
    # lime points mean his game is on, and nothing else; a flame beside the points means he passed his
    # projection by the Digest's own Smashed margin, and nothing marks his face
    [lime_rgb] = live.colours("--lime")
    rows = live.half_readings()
    smash = live.smash_margin()
    known = lambda r: r["proj"] == r["proj"] and r["pts"] == r["pts"]
    assert all((r["lime"] == lime_rgb) == r["on"] for r in rows)
    assert all(r["fire"] == (known(r) and r["pts"] - r["proj"] >= smash) for r in rows)
    assert any(r["fire"] for r in rows) and not any(r["ring"] for r in rows)
    assert any(known(r) and 0 < r["pts"] - r["proj"] < smash for r in rows)    # a beat, not a smash: no flame
    assert all(re.match(r"^(\d+\.\d)?$", s) for s in live.left_projections())
    # rows are shaded every other one; a half whose game is on is tinted over that
    assert live.rows_are_striped()
    assert live.live_half_count() > 0 and live.first_live_half_background() != "rgba(0, 0, 0, 0)"
    # my game says who leads in words; the bench is drawn, dimmed, and left out of the total
    assert re.match(r"^(UP|DOWN) \d+\.\d$|^TIED$", live.lead_text())
    assert live.bench_count() == 0                  # shut until the Benches row opens it
    live.open_benches()
    assert live.bench_rows() > 0
    live.tap_first_name()
    live.wait_for_profile()
    live.press_escape()
    assert errors == []


@pytest.mark.render
def test_the_chip_strip_states_each_game_and_the_picked_team_decides_the_league(mount):
    live, errors = LiveMinePage.open_board(mount)           # David's ESPN team: Live opens on its league
    # the ranking under the lineups: ESPN pays the top half. Every chip in the strip states its game on
    # the line above two names and two scores; the reader's chip is the one on screen
    assert live.ladder_median_lines() == 1
    tags = live.chip_state_words()
    assert len(tags) == live.chip_count()
    assert all(re.match(r"^(LIVE|\d+ LEFT|FINAL)$", s.strip()) for s in tags)
    assert live.chip_states_lead_their_chips()
    assert live.picked_chip_count() == 1 and live.my_picked_chip_count() == 1
    # the team picked decides the league: Yahoo's, which ranks for bragging
    live.pick_team("yahoo")
    assert "Chat Take the Wheel" in live.head_text()
    assert live.ladder_quiet_median_count() == 1
    # another game in the league opens its two lineups in place, and its lead names no side
    live.tap_other_chip()
    assert "Chat Take the Wheel" not in live.head_text()
    assert re.match(r"^BY \d+\.\d$|^TIED$", live.lead_text())
    assert live.picked_chip_count() == 1 and live.my_picked_chip_count() == 0
    assert errors == []


# --------------------------------------------------------------------------- the game sheet

def test_where_the_ball_is_reads_as_espn_writes_it(espn_js):
    """gsWhere, from down, distance and yards to go, says what ESPN's own downDistanceText says, on
    every play of the saved game: it is the fallback when a live summary leaves the text out.
    Timeouts carry a stale text and no yards to go; the sheet drops them, so the test does too."""
    got = espn_js("""(s) => {
      const cs = s.header.competitions[0].competitors, abbrOf = {};
      for (const c of cs) abbrOf[c.team.id] = c.team.abbreviation;
      const other = a => cs.map(c => c.team.abbreviation).find(x => x !== a);
      const out = [];
      for (const d of s.drives.previous) for (const p of d.plays)
        if (p.start && p.start.downDistanceText && !GS_NOT_PLAY.test(p.text) && !GS_NOT_PLAY.test(p.type.text)) out.push([gsWhere(p.start, abbrOf, other), p.start.downDistanceText]);
      return out;
    }""", SUMMARY)
    assert len(got) > 30
    assert [g for g in got if g[0] != g[1]] == []


@pytest.mark.render
def test_the_game_sheet_opens_from_nfl_now_and_draws_four_cards(mount):
    sheet, errors = open_saved_sheet(mount)
    assert sheet.card_count() == 5        # scoreboard, yours, then a card per tab (one shows)
    assert sheet.trailing_score() == "31"        # DET 31, BUF 41: final
    sheet.close_with_escape()
    assert sheet.current_game() is None
    assert errors == []


def open_saved_sheet(mount):
    """The game sheet opened from Live's Games tab (DET and SEA on now), its game swapped for the saved one."""
    sheet, errors = GameSheetPage.on_live(mount, size=(390, 844))     # DET and SEA on now
    live = LiveMinePage(sheet.page)
    # the Games tab lists every game of the week, the one on now first: its clock over two clubs
    live.open_tab("games")
    assert live.in_tile_count() == 1 and live.in_tile_game() == "401871234,DET,SEA"
    assert live.in_tile_label() == "Live"
    live.tap_in_tile()
    sheet.wait_for_open()
    sheet.swap_in_saved_game()
    return sheet, errors


@pytest.mark.render
def test_the_game_sheet_lists_drives_newest_first_and_keeps_one_open_through_a_repaint(mount):
    sheet, errors = open_saved_sheet(mount)
    # drives newest first, the newest open, the rest one line each; no "END QUARTER" rows
    sheet.select_tab("plays")
    assert sheet.drive_count() == 5 and sheet.first_drive_is_open()
    assert sheet.open_drive_count() == 1
    assert sheet.first_drive_club() == "DET" and sheet.first_drive_scoring_results() == 1
    assert not any(t.startswith("END ") for t in sheet.play_texts())
    # an earlier drive opened by hand stays open through the next poll's repaint
    sheet.toggle_drive(2)
    sheet.repaint()
    assert sheet.open_drive_count() == 2
    assert errors == []


@pytest.mark.render
def test_the_game_sheet_ranks_top_scorers_and_shows_one_boxscore_club_at_a_time(mount):
    sheet, errors = open_saved_sheet(mount)
    # top scorers, best first, in the league's own scoring
    sheet.select_tab("top")
    pts = sheet.top_scorer_points()
    assert len(pts) == 5 and pts == sorted(pts, reverse=True)
    # the box score shows one club at a time
    sheet.select_tab("box")
    assert sheet.box_club() == "Lions"
    sheet.tap_box_club(1)
    assert sheet.box_club() == "Bills"
    assert sheet.box_table_count() >= 2
    sheet.close_with_escape()
    assert sheet.current_game() is None
    assert errors == []
