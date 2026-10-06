"""League > Teams, the League board (leaf `teams`, 2026-10-05): design/teams.py cuts every team's best
lineup by position from ff-jarvis's roster files and this week's projections, and the page draws it as a
grid with a page for each team. The cut is tested on small invented leagues; the page on the fixture build."""
import copy
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
import teams  # noqa: E402
from test_render import LOAD_MS, SEED  # noqa: E402,F401


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
    sched = {"alias": {}, "games": [{"week": 1, "home": "XXX", "away": "YYY", "kickoff": "2026-09-13T17:00:00Z"},
                                    {"week": 2, "home": "XXX", "away": "YYY", "kickoff": "2026-09-20T17:00:00Z"}]}
    raw = proj(qa=20, qb=18)
    raw["players"][1]["kickoff"] = "2026-09-20 17:00:00"      # qb's next game is week 2; qa's is week 1
    _, pts, _ = teams._points(raw, slug, None, sched)
    assert pts["qa"] == 20 and pts["qb"] == 0


def test_the_block_carries_the_projections_week_not_the_pages():
    """The label's week (2026-10-05): the week most players' next games fall in, so after Sunday it is
    already next week while the page's week waits for Monday night. A bye that week counts 0."""
    sched = {"alias": {}, "games": [{"week": 4, "home": "XXX", "away": "YYY", "kickoff": "2026-10-06T00:15:00Z"},
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


# ---- the page ----------------------------------------------------------------------------------------

def phone(browser, page_file, pick=None, w=360, h=800):
    """The fixture page at `w` x `h` as a reader who picked `pick` (a TEAMS key), or the suite's own pick."""
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED + (f'try {{ localStorage.setItem("tw-team", "{pick}"); }} catch (e) {{}}' if pick else ""))
    page.goto(page_file.as_uri() + "#teams", timeout=LOAD_MS)
    page.wait_for_selector("#view[data-view='teams'] > *")
    return ctx, page, errors


def plant(page, roster, key="yahoo", season=None):
    """Gives league `key` a board from an invented roster file, and draws it."""
    block = teams.live_league(key, roster, season, *teams._points(proj(**PTS), slug, None, None)[1:], slug)
    page.evaluate("b => { LIVE_TEAMS.leagues = LIVE_TEAMS.leagues.filter(l => l.key !== b.key); LIVE_TEAMS.leagues.push(b); render(); }", block)


def names(page):
    return page.locator(".lb-row .lb-team b").all_inner_texts()


@pytest.mark.render
def test_teams_opens_on_the_readers_league_and_the_one_chip_moves_it(browser, page_file):
    """One chip since 2026-10-05: the team switch. It named the league beside it; a team picked in it is the league.
    On a phone the switch is the header bar's (#hdrswitch) and the chip keeps the league's name."""
    ctx, page, errors = phone(browser, page_file, pick="espn")
    assert page.locator(".lgchip-lg").inner_text().lower() == "espn"
    assert page.locator(".lg-switch, [data-lgpick]").count() == 0, "no league chips of their own"
    assert page.locator(".navitem[data-s='league']").count() == 1
    assert page.locator(".mode-sub[aria-pressed='true']").inner_text().lower() == "teams"
    assert names(page) == ["Purdy Big in Japan", "Run It Back"]
    assert page.locator(".lgchip .teamswitch").is_hidden()
    page.locator("#hdrswitch [data-tsbtn]").click()
    page.locator("#hdrswitch [data-tsleague='ayo']").click()
    page.locator("#hdrswitch .ts-item[data-k='ayo']").click()
    assert page.locator(".lgchip-lg").inner_text().lower() == "ayo"
    assert names(page) == ["Taylor Made for Sundays", "Don Wick"]
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_only_the_readers_own_team_is_pinned_with_a_lime_outline(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="espn")
    plant(page, league(me="Gamma"), key="espn")                  # Gamma is the reader's, and last on total
    assert page.locator(".lb-row.mine").count() == 1
    assert names(page)[0] == "Gamma", "the reader's team is pinned above Alpha, who leads on total"
    assert page.evaluate("getComputedStyle(document.querySelector('.lb-row.mine')).boxShadow").count("200, 255, 46") == 1, "lime"
    page.locator("[data-lbsort='QB']").click()
    assert names(page)[0] == "Gamma" and names(page)[1] == "Alpha", "a sort moves the others, never the pin"
    ctx.close()
    ctx, page, _ = phone(browser, page_file, pick="espn-run-it-back")
    assert page.locator(".lb-row.mine").count() == 1, "a leaguemate's team is the reader's, whatever it is"
    page.evaluate("pickTeam('ayo')")
    assert page.locator(".lb-row.mine").count() == 1 and names(page)[0] == "Taylor Made for Sundays", "the new league pins the new team"
    ctx.close()


@pytest.mark.render
def test_a_header_sorts_by_its_column_and_a_second_tap_goes_back_to_the_total(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="nothing")
    plant(page, league(), key="yahoo")
    assert names(page) == ["Alpha", "Beta", "Gamma"]
    assert page.locator("[data-lbsort='']").get_attribute("aria-pressed") == "true", "the total is what is sorted"
    page.locator("[data-lbsort='RB']").click()
    assert page.locator("[data-lbsort='RB']").get_attribute("aria-pressed") == "true"
    assert page.locator("[role=columnheader][aria-sort='descending']").count() == 1
    assert names(page) == ["Alpha", "Gamma", "Beta"], "RB: 15, 11, 10"
    page.locator("[data-lbsort='TE']").focus()                   # real buttons: operable from the keyboard
    page.keyboard.press("Enter")
    assert page.locator("[data-lbsort='TE']").get_attribute("aria-pressed") == "true"
    assert names(page) == ["Alpha", "Beta", "Gamma"], "TE: 8, 7, 6"
    page.locator("[data-lbsort='TE']").click()
    assert page.locator("[data-lbsort='']").get_attribute("aria-pressed") == "true" and names(page) == ["Alpha", "Beta", "Gamma"]
    ctx.close()


@pytest.mark.render
def test_a_cell_is_tinted_only_8_percent_off_the_median_and_a_spare_is_marked(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="nothing")
    plant(page, league(), key="yahoo")
    cells = page.evaluate("""[...document.querySelectorAll('.lb-row')].map(r =>
        [r.querySelector('b').innerText, [...r.querySelectorAll('.lb-c')].map(c => c.className.replace('lb-c', '').trim() + (c.querySelector('.lb-plus') ? '+' : ''))])""")
    # Medians: QB 18, RB 11, WR 10, TE 7, FLX 6. 8% either side is the tint; WR is Alpha's spare.
    assert dict(cells) == {"Alpha": ["up", "up", "up+", "up", "up"], "Beta": ["", "dn", "dn", "", ""],
                           "Gamma": ["dn", "", "", "dn", "dn"]}
    assert page.locator(".lb-key .lb-k").count() == 3
    ctx.close()


@pytest.mark.render
def test_a_row_opens_the_team_as_a_page_that_the_link_and_back_both_close_and_that_leaves_the_pick_alone(browser, page_file):
    ctx, page, errors = phone(browser, page_file, pick="espn")
    page.locator(".lb-row >> nth=1").click()
    page.wait_for_selector(".lbp-title")
    assert page.locator(".lbp-title").inner_text() == "Run It Back"
    assert page.locator(".lb-grid").count() == 0, "the page replaces the board in the view"
    assert page.locator("#lbsheet, #tbsheet, .lbs-scrim").count() == 0, "a page, not a sheet: nothing slides up, no scrim"
    assert page.locator(".navitem[data-s='league']").is_visible() and page.locator(".mode-sub[aria-pressed='true']").inner_text().lower() == "teams"
    assert page.locator(".lbp-back").inner_text() == "Teams"
    rows = page.locator(".lbp-r").all_inner_texts()
    assert any("B. Robinson" in r for r in rows) and any("C. Hubbard" in r for r in rows), "names as initials, bench after the lineup"
    assert page.locator(".lbp h2").all_inner_texts() == ["LINEUP", "BENCH"]
    assert page.locator(".lbp-sub").inner_text().endswith("projected")
    assert page.evaluate("localStorage.getItem('tw-team')") == "espn", "opening a team never picks it"
    assert page.evaluate("location.hash") == "#teams", "pages are history entries, not URLs: a reload lands on the board"
    page.go_back()
    page.wait_for_selector(".lb-grid")
    assert page.evaluate("location.hash") == "#teams", "Back closed the page, not the view"
    assert page.evaluate("document.activeElement.dataset.lbopen") == "espn-run-it-back", "focus returns to the row"
    page.locator(".lb-row >> nth=0").click()
    page.wait_for_selector(".lbp-title")
    page.locator(".lbp-back").click()
    page.wait_for_selector(".lb-grid")
    assert page.evaluate("history.state") is None, "the link took its history entry back too"
    assert page.evaluate("[VIEW, localStorage.getItem('tw-team')]") == ["espn", "espn"]
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_board_comes_back_at_the_scroll_the_reader_left_whichever_way_they_step_back(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="espn", h=500)
    plant(page, league({f"T{i}": [row(f"q{i}", "QB", "QB")] for i in range(20)}), key="espn")
    for way in ("link", "back"):
        page.evaluate("window.scrollTo(0, 260)")
        y = page.evaluate("scrollY")
        assert y > 200, "the board is long enough to scroll"
        page.locator(".lb-row >> nth=6").click()
        page.wait_for_selector(".lbp-title")
        assert page.evaluate("scrollY") == 0, "a page starts at its top"
        if way == "link":
            page.locator(".lbp-back").click()
        else:
            page.go_back()
        page.wait_for_selector(".lb-grid")
        page.wait_for_function(f"scrollY === {y}")
    ctx.close()


@pytest.mark.render
def test_the_board_asks_for_a_team_only_while_the_reader_has_none_in_the_league(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="espn")
    assert page.locator(".lb-pick").count() == 0, "their team is in this league"
    ctx.close()
    ctx, page, _ = phone(browser, page_file, pick="nothing")             # no pick: the league on screen is the team on screen's
    page.evaluate("VIEW = 'espn'; render()")
    assert page.locator(".lb-pick").inner_text() == "Tap your team to set it"
    top = page.evaluate("document.querySelector('.lb-grid').getBoundingClientRect().top")
    assert top <= 200, f"the line still leaves the grid at {top:.0f}px"
    ctx.close()


@pytest.mark.render
def test_a_league_with_no_rosters_draws_an_empty_state_and_keeps_the_chip(browser, page_file):
    ctx, page, _ = phone(browser, page_file)                    # the suite's reader is on the Madden Curse: no slots in the fixture
    assert page.locator(".lb-empty").is_visible() and page.locator(".lb-grid").count() == 0
    assert page.locator(".lgchip").count() == 1
    page.evaluate("pickTeam('espn')")
    assert page.locator(".lb-grid").count() == 1
    ctx.close()


@pytest.mark.render
def test_the_board_fits_a_phone_and_starts_near_the_top(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="espn")
    plant(page, league({f"T{i}": [row(f"q{i}", "QB", "QB")] for i in range(9)}), key="espn")
    top = page.evaluate("document.querySelector('.lb-grid').getBoundingClientRect().top")
    assert top <= 200, f"the grid starts at {top:.0f}px"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.evaluate("[...document.querySelectorAll('.lb-team b')].every(b => b.clientWidth > 40)"), "a name keeps room"
    one = page.evaluate("[...document.querySelectorAll('.lb-c')].slice(0, 5).map(c => Math.round(c.getBoundingClientRect().width))")
    assert len(set(one)) == 1, "the cells are one width, so the numbers line up"
    ctx.close()


@pytest.mark.render
def test_the_board_is_capped_on_a_desktop(browser, page_file):
    ctx, page, _ = phone(browser, page_file, pick="espn", w=1280, h=900)
    w = page.evaluate("document.querySelector('.lb-grid').getBoundingClientRect().width")
    left = page.evaluate("document.querySelector('.lb-grid').getBoundingClientRect().left - document.querySelector('.lgchip').getBoundingClientRect().left")
    assert w <= 721 and left == 0, f"{w}px wide, {left}px from the frame's edge"
    ctx.close()
