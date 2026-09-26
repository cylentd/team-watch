"""This week > Weather (2026-09-26), rendered from the fixture build.

The fixture's week 2 (SEED pins the clock to 2026-09-12) holds one of each case the view draws:
WAS @ LA in a dome, MIA @ NE outdoors in 15-22 mph wind, JAX @ IND under a retractable roof with a
forecast, and DET @ SEA outdoors with no forecast yet. LIVE_WEATHER keys the Rams as nflverse's
`LA` while the schedule says `LAR`, so the dome row also proves the club-code bridge.
"""
import re

import pytest

from test_render import SEED, browser  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render


@pytest.fixture(scope="module")
def page(browser, page_file):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + "#weather")
    pg.wait_for_function("document.getElementById('view').children.length > 0")
    yield pg
    ctx.close()


def games(page):
    return page.evaluate("""() => [...document.querySelectorAll('.wt-game')].map(g => ({
        match: g.querySelector('.wt-match').textContent, text: g.textContent,
        facts: g.querySelectorAll('.wt-f').length}))""")


def test_a_dome_game_shows_no_temperature_or_wind(page):
    dome = next(g for g in games(page) if g["match"] == "WSH @ LAR")
    assert dome["facts"] == 0
    assert "°F" not in dome["text"] and "mph" not in dome["text"]
    assert "Dome" in dome["text"]


def test_indoors_first_then_most_wind_first(page):
    order = [g["match"] for g in games(page)]
    assert order == ["WSH @ LAR", "MIA @ NE", "JAX @ IND", "DET @ SEA"]


def test_retractable_keeps_the_caveat_and_no_forecast_says_so(page):
    by = {g["match"]: g for g in games(page)}
    assert "roof may close" in by["JAX @ IND"]["text"] and by["JAX @ IND"]["facts"] == 3
    assert "No forecast for this kickoff yet." in by["DET @ SEA"]["text"]
    assert by["DET @ SEA"]["facts"] == 0


def test_my_players_are_listed_under_their_game(page):
    sea = next(g for g in games(page) if g["match"] == "DET @ SEA")
    assert "St. Brown" in sea["text"] or "Gibbs" in sea["text"]


def history(page, match):
    return page.evaluate("""m => { const g = [...document.querySelectorAll('.wt-game')]
        .find(x => x.querySelector('.wt-match').textContent === m);
      return [...g.querySelectorAll('.wt-hl')].map(l => ({head: l.querySelector('.wt-hh').textContent,
        qs: [...l.querySelectorAll('.wt-hq')].map(q => q.textContent.replace(/\\s+/g, ' ').trim())})); }""", match)


def test_a_dome_game_says_no_clear_effect_and_why(page):
    """Kickers fail on season-to-season only, so they are the closest and the reason is named."""
    lines = history(page, "WSH @ LAR")
    assert [l["head"] for l in lines] == ["Domes"]
    assert lines[0]["qs"] == ["Does it matter? No clear effect. Kickers score a bit more indoors, "
                              "but it doesn't hold up season to season."]


def test_a_windy_game_answers_both_questions(page):
    lines = history(page, "MIA @ NE")   # 15 to 22 mph; a 40% chance of rain is under the 50% bar
    assert [l["head"] for l in lines] == ["Wind 15+ mph"]
    assert lines[0]["qs"] == [
        "Does it matter? Yes. Players score fewer points than usual: QB −1.5 · K −0.7 · WR −0.6. RBs: no clear effect.",
        "Already in our projections? QBs: yes, since Sep 26. WRs: not yet. We don't project kickers."]


def test_no_stats_talk_on_the_card(page):
    text = page.locator("#view").inner_text()
    for gone in ("Held out of sample", "Did not hold", "Baked into", "Not proven", "They catch"):
        assert gone not in text, gone


def test_cold_kickers_are_one_position_and_unprojected(page):
    """No fixture game is cold, so the words are read off the page's own functions."""
    said = page.evaluate("[wtMatters(wtSummary('cold'), 'cold'), wtInProj(wtSummary('cold'))]")
    assert said == ["Yes. Kickers score about 0.8 fewer points than usual. QBs: no clear effect.",
                    "We don't project kickers."]


def test_a_weather_adjusted_player_carries_a_small_wx_note(page):
    """ff-jarvis marks an adjusted row `wx: {adj, cond}`; the fixture has none, so one is planted."""
    html = page.evaluate("""() => { const slug = Object.keys(LIVE_PROJECTIONS.players)[0];
        LIVE_PROJECTIONS.players[slug].wx = {adj: -1.1, cond: 'wind'};
        const a = wtAdjHTML({slug}); LIVE_PROJECTIONS.players[slug].wx = null;
        return [a, wtAdjHTML({slug})]; }""")
    assert ">wx −1.1<" in html[0] and html[1] == ""


def test_projection_rows_pass_wx_through():
    from projections import live_projections
    raw = {"players": [{"name": "A B", "pos": "QB", "team": "NE", "pts": 15.0, "src": "model",
                        "wx": {"adj": -1.33, "cond": "wind"}}]}
    out = live_projections(raw, lambda n: n.lower().replace(" ", "-"), {"a-b"})
    assert out["players"]["a-b"]["wx"] == {"adj": -1.33, "cond": "wind"}


def test_without_the_adjust_block_the_projections_question_is_not_asked():
    import json
    from conftest import FIXTURES
    from wx_history import live_wx_history
    raw = json.loads((FIXTURES / "data" / "weather_backtest.json").read_text(encoding="utf-8"))
    block = live_wx_history(raw, {"players": []})
    assert block["since"] is None and all(s["inproj"] is None for s in block["conditions"].values())


def test_retractable_and_unforecast_games_carry_no_history(page):
    assert history(page, "JAX @ IND") == [] and history(page, "DET @ SEA") == []


def test_the_footnote_names_the_seasons_once(page):
    foot = page.locator(".wt-foot")
    assert foot.count() == 1 and "2011–2025" in foot.inner_text()


def test_the_block_is_summaries_not_cells():
    import json
    import contract
    from conftest import FIXTURES
    from wx_history import live_wx_history
    raw = json.loads((FIXTURES / "data" / "weather_backtest.json").read_text(encoding="utf-8"))
    block = live_wx_history(raw)
    assert sorted(block["conditions"]) == ["cold", "dome", "wind"] and "cells" not in block
    assert contract.problems("LIVE_WX_HISTORY", block) == []
    assert live_wx_history(None) is None and live_wx_history({"cells": []}) is None


def test_no_backtest_file_means_no_history_and_no_error(browser, tmp_path, monkeypatch):
    """The backtest is rerun by hand, so a machine without it must still build, and the view must
    draw its games without a line or a footnote rather than break."""
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
        pg.wait_for_function("document.querySelectorAll('.wt-game').length > 0")
        assert pg.locator(".wt-hist").count() == 0 and pg.locator(".wt-foot").count() == 0
        assert errors == []
    finally:
        ctx.close()


def test_no_verdict_words(page):
    """Facts only: nothing on the view says what the weather does to anyone."""
    text = page.locator("#view").inner_text().lower()
    for word in ("good for", "bad for", "boost", "fade", "↑", "↓", "favor", "favour"):
        assert word not in text, word
