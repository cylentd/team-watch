"""This week > Weather (2026-09-26, reworked the same day to say only what matters), rendered from
the fixture build.

The fixture's week 2 (SEED pins the clock to 2026-09-12) holds one of each case the view draws:
WAS @ LA in a dome, DET @ SEA outdoors in 15-22 mph wind with a 70% chance of rain, JAX @ IND
under a retractable roof in a calm forecast, and MIA @ NE outdoors with no forecast yet.
LIVE_WEATHER keys the Rams as nflverse's `LA` while the schedule says `LAR`, so the dome row also
proves the club-code bridge. Only DET @ SEA moves scoring; the other three are compact rows.

The view is league-wide and public, so it never shows a roster: "Who it hits" comes from the
projections (Amon-Ra St. Brown, DET's top WR, carries wx -1.06), and Jahmyr Gibbs, on a fixture
roster in the same game but an RB, never appears.
"""
import re

import pytest

from test_render import SEED  # noqa: F401

pytestmark = pytest.mark.render


def open_weather(browser, page_file, motion="reduce"):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion=motion)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + "#weather")
    pg.wait_for_function("document.getElementById('view').children.length > 0")
    return ctx, pg


@pytest.fixture(scope="module")
def page(browser, page_file):
    ctx, pg = open_weather(browser, page_file)
    yield pg
    ctx.close()


def cards(page):
    return page.evaluate("""() => [...document.querySelectorAll('.wt-card')].map(g => ({
        match: g.querySelector('.wt-match').textContent,
        cond: g.querySelector('.wt-cond').textContent.replace(/\\s+/g, ' ').trim(),
        fx: g.querySelector('.wt-fx').textContent.replace(/\\s+/g, ' ').trim(), text: g.textContent}))""")


def rows(page):
    return page.evaluate("""() => [...document.querySelectorAll('.wt-row')].map(r =>
        r.textContent.replace(/\\s+/g, ' ').trim())""")


def test_only_the_windy_wet_game_is_a_card(page):
    assert [c["match"] for c in cards(page)] == ["DET @ SEA"]


def test_wind_and_rain_add_up_per_position(page):
    card = cards(page)[0]
    assert card["cond"] == "15 to 22 mph wind · 70% chance of rain · 61°F"
    assert card["fx"] == "QBs about 1.5 fewer points · WRs about 1 fewer · TEs about 0.5 fewer · kickers about 1.5 fewer"


def test_the_card_says_only_what_moves(page):
    text = cards(page)[0]["text"]
    for gone in ("RB", "no clear effect", "No clear effect", "not proven", "Not proven"):
        assert gone not in text, gone


def test_no_method_notes(page):
    """Show, don't tell (2026-09-30): no projection note, no "How we know", no method or source line."""
    text = page.inner_text("#view")
    for gone in ("Our projections", "Not in our projections", "Kickers aren't projected", "How we know",
                 "Tested with no effect", "METHODOLOGY", "National Weather Service"):
        assert gone not in text, gone
    assert page.locator("#view details").count() == 0


def test_the_heading_says_which_way_and_counts_in_words(page):
    rule = page.locator(".wt-sec .rule").first.inner_text().replace("\n", " ")
    assert "Games where weather lowers scoring".upper() in rule.upper() and "1 game" in rule
    assert not re.search(r"\b0\d\b", rule)


def test_every_other_game_is_one_compact_row(page):
    """Outdoors first (they carry a forecast), then indoors; a dome is only ever a row."""
    got = rows(page)
    assert [r.split(" ")[0:3] for r in got] == [["MIA", "@", "NE"], ["JAX", "@", "IND"], ["WSH", "@", "LAR"]]
    assert "No forecast yet" in got[0] and "74°F · 7 mph" in got[1]
    assert "°F" not in got[2] and "mph" not in got[2]
    assert not any("your" in r for r in got)


def test_a_week_with_no_qualifying_game_says_so_plainly(page):
    html = page.evaluate("""() => { const f = LIVE_WEATHER.teams.SEA, keep = [f.wind, f.precip_pct];
        f.wind = '8 mph'; f.precip_pct = 10; const h = wtViewHTML(); [f.wind, f.precip_pct] = keep; return h; }""")
    assert "The weather won't move scoring in any game this week." in html
    assert 'class="wt-card"' not in html


def test_who_it_hits_is_the_projections_top_qb_wr_te_with_wx(page):
    hits = page.evaluate("""() => [...document.querySelectorAll('.wt-card .wt-hits li')].map(l =>
        [...l.querySelectorAll('.wt-p > span, .wt-adj')].map(s => s.textContent).join('|'))""")
    assert hits == ["WR|A. St. Brown|DET|−1.1"]


def test_a_book_priced_hit_says_in_the_odds_and_why_on_tap(page):
    """A `src: "line"` row carries no wx: its blank would read as zero, so it says so, and the why
    opens on a tap or Enter (a popover), not on hover only."""
    page.evaluate("""() => { const d = document.createElement('div'); d.id = 'wt-odds-probe';
        d.innerHTML = wtHitsHTML([{slug: 'x-y', n: 'Xavier Young', pos: 'WR', team: 'DET', wx: null, src: 'line'},
                                  {slug: 'z-z', n: 'Zed Zee', pos: 'TE', team: 'DET', wx: null, src: 'model'}], 9);
        document.querySelector('.wt').appendChild(d); }""")
    rows = page.locator("#wt-odds-probe li")
    assert rows.nth(0).locator(".wt-odds").inner_text() == "in the odds"
    assert rows.nth(1).locator(".wt-odds").count() == 0 and rows.nth(1).locator(".wt-adj").count() == 0
    tip = page.locator("#wt-odds-9-0")
    assert not tip.is_visible()
    rows.nth(0).locator(".wt-odds").focus()
    page.keyboard.press("Enter")
    assert tip.is_visible()
    assert tip.inner_text() == "His projection comes from sportsbook lines, which already price the forecast."
    page.keyboard.press("Escape")
    page.evaluate("document.getElementById('wt-odds-probe').remove()")
    head = page.locator(".wt-hits h3").inner_text().replace("\n", " ")
    assert "Who it hits" in head and "already in his projection" in head


def test_the_view_shows_no_roster(page):
    text = page.locator("#view").inner_text()
    for gone in ("Gibbs", "Your players", "of your players", "ESPN", "Yahoo"):
        assert gone not in text, gone


def test_a_hit_with_no_wx_has_no_number(page):
    assert page.evaluate("wtAdjHTML(null)") == "" and page.evaluate("wtAdjHTML({adj: -0.5})").endswith(">−0.5</span>")


def test_who_it_hits_skips_the_injured_and_keeps_qb_wr_wr_te():
    from wx_hits import live_wx_hits
    rows = [("Q One", "QB", 20), ("Q Two", "QB", 12), ("W One", "WR", 15), ("W Two", "WR", 14),
            ("W Three", "WR", 9), ("T One", "TE", 8), ("R One", "RB", 18), ("W Hurt", "WR", 16)]
    raw = {"players": [{"name": n, "pos": pos, "team": "NE", "pts": pts, "src": "line" if pos == "TE" else "model",
                        "wx": {"adj": -0.5, "cond": ["wind"]} if pos == "WR" else None} for n, pos, pts in rows]}
    status = {"1": {"name": "W Hurt", "injury": "Out"}}
    block = live_wx_hits(raw, lambda n: n.lower().replace(" ", "-"), status)
    got = [(r["n"], r["pos"], r["wx"]) for r in block["teams"]["NE"]]
    assert [g[:2] for g in got] == [("Q One", "QB"), ("W One", "WR"), ("W Two", "WR"), ("T One", "TE")]
    assert got[1][2] == {"adj": -0.5, "cond": ["wind"]} and got[0][2] is None
    assert [r["src"] for r in block["teams"]["NE"]] == ["model", "model", "model", "line"]


def test_the_roster_card_shows_what_is_in_his_projection(browser, page_file):
    """St. Brown's next game is at SEA, windy and wet in the fixture, and his row carries wx."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    try:
        pg.goto(page_file.as_uri() + "#roster")
        pg.wait_for_function("document.getElementById('view').children.length > 0")
        html = pg.evaluate("""() => { const p = Object.values(TEAMS).flatMap(t => t.roster || [])
            .find(x => x.n === 'Amon-Ra St. Brown'); return [cardWxAdj(p), cardBack(p, 9, 'espn', 0, cardGame(p.team))]; }""")
        assert html[0] == "−1.1"
        assert "−1.1 in his projection" in html[1]
    finally:
        ctx.close()


def test_a_retractable_roof_says_it_may_close(page):
    said = page.evaluate("""() => { const r = wtRows().open.find(x => x.g.home === 'IND');
        const fc = Object.assign({}, r.fc, {wind: '20 mph', precip_pct: 0});
        const x = Object.assign({}, r, {fc, mph: 20}); x.conds = wtConditions(x); x.effects = wtEffects(x.conds);
        return wtCondHTML(x); }""")
    assert "roof may close" in said


def test_projection_rows_pass_wx_through():
    from projections import live_projections
    raw = {"players": [{"name": "A B", "pos": "QB", "team": "NE", "pts": 15.0, "src": "model",
                        "wx": {"adj": -1.33, "cond": "wind"}}]}
    out = live_projections(raw, lambda n: n.lower().replace(" ", "-"), {"a-b"})
    assert out["players"]["a-b"]["wx"] == {"adj": -1.33, "cond": "wind"}


def test_without_the_adjust_block_rain_never_applies_and_nothing_is_counted():
    import json
    from conftest import FIXTURES
    from wx_history import live_wx_history
    raw = json.loads((FIXTURES / "data" / "weather_backtest.json").read_text(encoding="utf-8"))
    block = live_wx_history(raw, {"players": []})
    assert block["since"] is None and block["thresholds"]["precip_pct"] is None
    assert all(s["inproj"] is None for s in block["conditions"].values())


def test_the_block_is_summaries_not_cells():
    import json
    import contract
    from conftest import FIXTURES
    from wx_history import live_wx_history
    raw = json.loads((FIXTURES / "data" / "weather_backtest.json").read_text(encoding="utf-8"))
    proj = json.loads((FIXTURES / "data" / "player_projections.json").read_text(encoding="utf-8"))
    block = live_wx_history(raw, proj)
    assert sorted(block["conditions"]) == ["cold", "dome", "precip", "wind"] and "cells" not in block
    assert block["thresholds"] == {"wind_mph": 15.0, "cold_f": 32.0, "precip_pct": 50, "roof": "outdoor"}
    assert [m["pos"] for m in block["conditions"]["wind"]["matters"]] == ["QB", "WR", "TE", "K"]
    assert contract.problems("LIVE_WX_HISTORY", block) == []
    assert live_wx_history(None) is None and live_wx_history({"cells": []}) is None


def test_no_backtest_file_means_no_cards_and_no_error(browser, tmp_path, monkeypatch):
    """The backtest is rerun by hand, so a machine without it must still build, and the view must
    draw its games as rows rather than break."""
    import build
    import sources
    monkeypatch.setattr(sources, "WEATHER_BACKTEST", tmp_path / "absent.json")
    out = build.render()
    assert "const LIVE_WX_HISTORY = null;" in out.fragment
    p = tmp_path / "index.html"
    p.write_text(out.page, encoding="utf-8")
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    try:
        pg.goto(p.as_uri() + "#weather")
        pg.wait_for_function("document.querySelectorAll('.wt-row').length > 0")
        assert pg.locator(".wt-card").count() == 0 and pg.locator(".wt-row").count() == 4
        assert errors == []
    finally:
        ctx.close()


def test_no_verdict_words(page):
    text = page.locator("#view").inner_text().lower()
    for word in ("good for", "bad for", "boost", "fade", "start ", "sit ", "↑", "↓", "favor", "favour"):
        assert word not in text, word


def looping(pg):
    return pg.evaluate("""() => document.getAnimations().filter(a => a.playState === 'running'
        && a.effect && a.effect.getTiming().iterations === Infinity).map(a => a.animationName)""")


def test_the_sky_moves_only_with_motion_allowed(browser, page_file):
    """The icon's streaks and drops are the forecast itself (STYLE.md: a loop only where the motion
    is the content); reduced motion gets the still icon and nothing loops."""
    ctx, pg = open_weather(browser, page_file, motion="reduce")
    try:
        assert looping(pg) == []
        # The still frame is a drawn icon: the wind's three strokes, the rain's cloud and drops.
        assert pg.locator("svg.wt-sky.wind path").count() == 3
        assert pg.locator("svg.wt-sky.rain path").count() == 4 and pg.locator("svg.wt-sky").first.is_visible()
    finally:
        ctx.close()
    ctx, pg = open_weather(browser, page_file, motion="no-preference")
    try:
        names = looping(pg)
        assert set(names) == {"wt-gust", "wt-drop"}
        assert names.count("wt-gust") == 3 and names.count("wt-drop") == 3   # a 70% chance: 3 drops
    finally:
        ctx.close()
