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
sys.path.insert(0, str(REPO / "api"))

import pytest  # noqa: E402

import _scoring  # noqa: E402
import contract  # noqa: E402
import stats as api_stats  # noqa: E402
from _espn import slugify  # noqa: E402
from build import norm_name  # noqa: E402
from gameday import live_gameday  # noqa: E402
from sources import DWR, read_first, load_status, load_kickers  # noqa: E402
from test_render import LIVE_PLANT as plant, browser, go, open_page  # noqa: E402,F401  (the suite's one Chromium)

FIX = json.loads((REPO / "tests" / "fixtures" / "gameday.json").read_text(encoding="utf-8"))


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
    for lg in b["leagues"]:
        for tm in lg["teams"].values():
            for r in tm["lineup"]:
                assert set(r) == {"slot", "n", "slug", "pos", "team", "sid"}
                if r["pos"] == "DEF":
                    assert r["sid"] == r["team"]


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


# --------------------------------------------------------------------------- the trimmed endpoint

def test_stats_query_is_checked_before_sleeper_is_asked():
    assert api_stats.parse("week=3&ids=8183,SEA")[0] == (3, frozenset({"8183", "SEA"}), frozenset())
    assert api_stats.parse("week=3&teams=CHI,PHI")[0] == (3, frozenset(), frozenset({"CHI", "PHI"}))
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


def test_stats_keep_only_wanted_players_and_scored_fields():
    rows = [{"player_id": "1", "updated_at": 5, "stats": {"rec": 3, "rec_yd": 40, "gp": 1, "rec_td": 0}},
            {"player_id": "2", "updated_at": 9, "stats": {"rec": 9}}]
    assert api_stats.trim(rows, frozenset({"1"})) == ({"1": {"rec": 3, "rec_yd": 40}}, 5)
    games = [{"week": 3, "home": "CHI", "away": "PHI", "status": "in_game"}, {"week": 4, "home": "GB", "away": "TB"}]
    assert api_stats.states(games, 3) == {"CHI": "in_game", "PHI": "in_game"}


# --------------------------------------------------------------------------- the page

@pytest.mark.render
def test_the_page_scores_week_2_as_both_leagues_did(browser, page_file):
    """Every started player and every team total, both leagues, to the hundredth."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    got = page.evaluate("""(fix) => {
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
    ctx.close()
    wrong = {k: v for k, v in got.items() if abs(v[0] - v[1]) > 0.011}
    assert not wrong, wrong
    assert len(got) > 60


@pytest.mark.render
def test_the_bench_is_scored_but_never_counted_and_proj_adds_who_is_left(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    got = page.evaluate("""(fix) => {
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
    ctx.close()
    assert got["nBench"] > 0 and got["benchSlots"]
    assert abs(got["total"] - got["starters"]) < 0.011
    assert abs(got["benchTotal"] - got["bench"]) < 0.011
    assert got["proj"] == 10 + 12 + 20 + 9 + 0     # done as scored; mid-game the larger; unplayed projected
    assert errors == []


@pytest.mark.render
def test_the_board_says_where_each_game_is_and_a_row_opens_his_profile(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(plant())
    for kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-row")
    # each row's game line: a lime LIVE while it is on, a lock and "Final" once done, the kickoff
    # before (and no stat line, and a dash for points); the second number is his projection, unlabelled
    states = page.evaluate("""() => [...document.querySelectorAll('.gd-lineup.mine .gd-row')].map(r =>
      [r.dataset.gdteam, r.querySelector('.gd-live') ? 'LIVE' : r.querySelector('.gd-game svg') ? 'FINAL'
        : !r.querySelector('.gd-stat') && r.querySelector('.gd-pts').textContent === '—' ? 'PRE' : '?',
       !!r.querySelector('.gd-slot.locked')])""")
    by_team = {team: (st, locked) for team, st, locked in states}
    assert by_team.get("SF") == ("LIVE", True) and by_team.get("DET") == ("PRE", False)
    assert ("FINAL", True) in by_team.values() and "?" not in {s for s, _ in by_team.values()}
    assert all(re.match(r"^(\d+\.\d)?$", s) for s in page.locator(".gd-lineup.mine .gd-proj").all_inner_texts())
    assert page.locator(".gd-median:not(.quiet)").count() == 1         # ESPN pays the top half
    # every game states itself on the line above its boxes; a box is a name and a score, and only a
    # finished game's winner carries the trophy
    tags = page.locator(".gd-gs").all_inner_texts()
    assert len(tags) == page.locator(".gd-g").count()
    assert all(re.match(r"^(LIVE · \d+ LEFT|\d+ LEFT|FINAL)$", s.strip()) for s in tags)
    assert page.locator(".gd-g").evaluate_all("gs => gs.every(g => g.firstElementChild.classList.contains('gd-gs'))")
    assert page.locator(".gd-cup").count() == sum(1 for s in tags if s.strip() == "FINAL")
    assert page.locator(".gd-g.on").count() == 1 and page.locator(".gd-g.mine.on").count() == 1
    # rows are shaded every other one and by nothing else: no row is lit for what it holds
    assert page.locator(".gd-lineup").evaluate_all("""ls => ls.every(l => {
      const rs = [...l.querySelectorAll('.gd-row')].map(r => getComputedStyle(r).backgroundColor);
      return rs.every((c, i) => c === rs[i % 2]) && rs[0] !== rs[1]; })""")
    # my game says who leads in words; the bench is drawn, dimmed, and left out of the total
    assert re.match(r"^(UP|DOWN) \d+\.\d$|^TIED$", page.locator(".gd-lead").inner_text())
    assert page.locator(".gd-lineup.mine .gd-row.bn").count() > 0
    page.locator(".gd-lineup.mine .gd-row").first.click()
    page.wait_for_selector("#modal.on")
    page.keyboard.press("Escape")
    page.click("[data-gdleague='yahoo']")
    assert page.locator(".gd-median.quiet").count() == 1               # Yahoo ranks for bragging
    assert "Chat Take the Wheel" in page.locator(".gd-head").inner_text()
    # another game in the league opens its two lineups, takes the outline from mine, and its chip
    # names no side
    other = page.locator(".gd-g:not(.mine)").first
    other.click()
    assert "Chat Take the Wheel" not in page.locator(".gd-head").inner_text()
    assert page.locator(".gd-g.on").count() == 1 and page.locator(".gd-g.mine.on").count() == 0
    assert re.match(r"^BY \d+\.\d$|^TIED$", page.locator(".gd-lead").inner_text())
    ctx.close()
    assert errors == []


# --------------------------------------------------------------------------- the game sheet

SUMMARY = json.loads((REPO / "tests" / "fixtures" / "data" / "espn_summary.json").read_text(encoding="utf-8"))
BOX = json.loads((REPO / "tests" / "fixtures" / "data" / "sleeper_box.json").read_text(encoding="utf-8"))


@pytest.mark.render
def test_where_the_ball_is_reads_as_espn_writes_it(browser, page_file):
    """gsWhere, from down, distance and yards to go, says what ESPN's own downDistanceText says, on
    every play of the saved game: it is the fallback when a live summary leaves the text out.
    Timeouts carry a stale text and no yards to go; the sheet drops them, so the test does too."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    got = page.evaluate("""(s) => {
      const cs = s.header.competitions[0].competitors, abbrOf = {};
      for (const c of cs) abbrOf[c.team.id] = c.team.abbreviation;
      const other = a => cs.map(c => c.team.abbreviation).find(x => x !== a);
      const out = [];
      for (const d of s.drives.previous) for (const p of d.plays)
        if (p.start && p.start.downDistanceText && !GS_NOT_PLAY.test(p.text) && !GS_NOT_PLAY.test(p.type.text)) out.push([gsWhere(p.start, abbrOf, other), p.start.downDistanceText]);
      return out;
    }""", SUMMARY)
    ctx.close()
    assert len(got) > 30
    assert [g for g in got if g[0] != g[1]] == []
    assert errors == []


@pytest.mark.render
def test_the_game_sheet_opens_from_nfl_now_and_draws_four_cards(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(plant({"DET": "in_game", "SEA": "in_game"}))
    for kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-row")
    # the card lists the games on now, each drawn like a league game: its state over two clubs
    tile = page.locator(".gd-now [data-gdnfl]")
    assert tile.count() == 1 and tile.get_attribute("data-gdnfl") == "401871234,DET,SEA"
    assert tile.locator(".gd-gs.live").inner_text().startswith("LIVE")
    tile.click()
    page.wait_for_selector("#gamesheet.on")
    page.evaluate("""([s, b]) => { GS = {event: "1", away: "DET", home: "BUF"}; GS_GAME = gsShape(s); GS_BOX = {box: b}; GS_ERR = ""; gsPaint(); }""",
                  [SUMMARY, BOX])
    sheet = page.locator("#gamesheet")
    assert sheet.locator(".gs-card").count() == 4
    assert sheet.locator(".gs-t.behind b").inner_text() == "31"            # DET 31, BUF 41: final
    # drives newest first, the newest open, the rest one line each; no "END QUARTER" rows
    drives = sheet.locator(".gs-drv")
    assert drives.count() == 5 and drives.first.get_attribute("open") is not None
    assert sheet.locator(".gs-drv[open]").count() == 1
    assert drives.first.locator(".gs-tm").inner_text() == "DET" and drives.first.locator("summary b.sc").count() == 1
    assert not any(t.startswith("END ") for t in sheet.locator(".gs-pl > span:last-child").all_inner_texts())
    # an earlier drive opened by hand stays open through the next poll's repaint
    drives.nth(2).locator("summary").click()
    page.evaluate("new Promise(r => setTimeout(() => { gsPaint(); r(); }, 0))")    # "toggle" is a task after the click
    assert sheet.locator(".gs-drv[open]").count() == 2
    # top scorers, best first, in the league's own scoring
    pts = [float(x) for x in sheet.locator(".gs-sc > b").all_inner_texts()]
    assert len(pts) == 5 and pts == sorted(pts, reverse=True)
    # the box score shows one club at a time
    assert sheet.locator(".gs-seg [aria-pressed='true']").inner_text() == "Lions"
    sheet.locator(".gs-seg button").nth(1).click()
    assert sheet.locator(".gs-seg [aria-pressed='true']").inner_text() == "Bills"
    assert sheet.locator(".gs-tbl").count() >= 2
    page.keyboard.press("Escape")
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    assert page.evaluate("GS") is None
    ctx.close()
    assert errors == []
