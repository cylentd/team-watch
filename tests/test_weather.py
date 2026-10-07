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

Component tests (Weather mounted at 390x844, tests/component.py; every locator in tests/pages/weather.py).
The retractable-roof wording runs in Node on the build's own blocks; the rest are build-side Python.
"""
import json
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.weather import WeatherPage

pytestmark = pytest.mark.render

SIZE = (390, 844)


@pytest.fixture
def weather(mount):
    """Weather mounted on the fixture build: (WeatherPage, page errors)."""
    page, errors = mount("weather", size=SIZE)
    return WeatherPage(page), errors


def test_only_the_windy_wet_game_is_a_card(weather):
    wx, _ = weather
    assert [c["match"] for c in wx.cards()] == ["DET @ SEA"]


def test_wind_and_rain_add_up_per_position(weather):
    wx, _ = weather
    card = wx.cards()[0]
    assert card["cond"] == "15 to 22 mph wind · 70% chance of rain · 61°F"
    assert card["fx"] == "QBs about 1.5 fewer points · WRs about 1 fewer · TEs about 0.5 fewer · kickers about 1.5 fewer"


def test_the_card_says_only_what_moves(weather):
    wx, _ = weather
    text = wx.cards()[0]["text"]
    for gone in ("RB", "no clear effect", "No clear effect", "not proven", "Not proven"):
        assert gone not in text, gone


def test_no_method_notes(weather):
    """Show, don't tell (2026-09-30): no projection note, no "How we know", no method or source line."""
    wx, _ = weather
    text = wx.view_text()
    for gone in ("Our projections", "Not in our projections", "Kickers aren't projected", "How we know",
                 "Tested with no effect", "METHODOLOGY", "National Weather Service"):
        assert gone not in text, gone
    assert wx.details_count() == 0


def test_the_heading_says_which_way_and_counts_in_words(weather):
    wx, _ = weather
    rule = wx.rule_text()
    assert "Games where weather lowers scoring".upper() in rule.upper() and "1 game" in rule
    assert not re.search(r"\b0\d\b", rule)


def test_every_other_game_is_one_compact_row(weather):
    """Outdoors first (they carry a forecast), then indoors; a dome is only ever a row."""
    wx, _ = weather
    got = wx.rows()
    assert [r.split(" ")[0:3] for r in got] == [["MIA", "@", "NE"], ["JAX", "@", "IND"], ["WSH", "@", "LAR"]]
    assert "No forecast yet" in got[0] and "74°F · 7 mph" in got[1]
    assert "°F" not in got[2] and "mph" not in got[2]
    assert not any("your" in r for r in got)


def test_a_week_with_no_qualifying_game_says_so_plainly(weather):
    wx, errors = weather
    html = wx.calm_week_html()
    assert "The weather won't move scoring in any game this week." in html
    assert 'class="wt-card"' not in html
    assert errors == []


def test_who_it_hits_is_the_projections_top_qb_wr_te_with_wx(weather):
    wx, _ = weather
    assert wx.hits() == ["WR|A. St. Brown|DET|−1.1"]


def test_a_book_priced_hit_says_in_the_odds_and_why_on_tap(weather):
    """A `src: "line"` row carries no wx: its blank would read as zero, so it says so, and the why
    opens on a tap or Enter (a popover), not on hover only."""
    wx, errors = weather
    wx.plant_hits([{"slug": "x-y", "n": "Xavier Young", "pos": "WR", "team": "DET", "wx": None, "src": "line"},
                   {"slug": "z-z", "n": "Zed Zee", "pos": "TE", "team": "DET", "wx": None, "src": "model"}], 9)
    assert wx.probe_odds_label(0) == "in the odds"
    assert wx.probe_odds_count(1) == 0 and wx.probe_adj_count(1) == 0
    assert not wx.odds_tip_visible()
    wx.open_odds_tip_by_keyboard(0)
    assert wx.odds_tip_visible()
    assert wx.odds_tip_text() == "His projection comes from sportsbook lines, which already price the forecast."
    wx.press_escape()
    wx.unplant()
    head = wx.hits_head()
    assert "Who it hits" in head and "already in his projection" in head
    assert errors == []


def test_the_view_shows_no_roster(weather):
    wx, _ = weather
    text = wx.view_text()
    for gone in ("Gibbs", "Your players", "of your players", "ESPN", "Yahoo"):
        assert gone not in text, gone


def test_a_hit_with_no_wx_has_no_number(weather):
    wx, _ = weather
    assert wx.adj_html(None) == "" and wx.adj_html({"adj": -0.5}).endswith(">−0.5</span>")


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


def test_the_roster_card_shows_what_is_in_his_projection(weather):
    """St. Brown's next game is at SEA, windy and wet in the fixture, and his row carries wx."""
    wx, _ = weather
    html = wx.roster_card_wx("Amon-Ra St. Brown")
    assert html[0] == "−1.1"
    assert "−1.1 in his projection" in html[1]


def test_a_retractable_roof_says_it_may_close(node_js, built):
    """The Weather view's own data, read from the build, in Node (no browser): the fixture's JAX @ IND
    game, under a retractable roof, with a 20 mph wind and no rain."""
    blocks = {n: json.loads(re.search(rf"const {n} = (.*?);\n", built.fragment).group(1))
              for n in ("LIVE_SCHEDULE", "LIVE_WEATHER", "LIVE_WX_HISTORY")}
    js = node_js("data/schedule.js", "ui/weather.js", "data/wxhistory.js", "data/weather.js",
                 "surface/weather/weather.js", "surface/weather/card.js", globals=blocks)
    said = js("""() => { const r = wtRows().open.find(x => x.g.home === 'IND');
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


def test_no_backtest_file_means_no_cards_and_no_error(mount, tmp_path, monkeypatch):
    """The backtest is rerun by hand, so a machine without it must still build, and the view must
    draw its games as rows rather than break. It builds its own page (the fixture build with the
    file missing), so it mounts that build's blocks on a Mounter of its own, as test_sos_view's does."""
    import build
    import sources
    monkeypatch.setattr(sources, "WEATHER_BACKTEST", tmp_path / "absent.json")
    out = build.render()
    assert "const LIVE_WX_HISTORY = null;" in out.fragment
    mounter = Mounter(mount.browser, tmp_path / "component-weather-nofile", out.fragment)
    try:
        page, errors = mounter("weather", size=SIZE)
        wx = WeatherPage(page)
        assert wx.card_count() == 0 and wx.row_count() == 4
        assert errors == []
    finally:
        mounter.pages.close()


def test_no_verdict_words(weather):
    wx, _ = weather
    text = wx.view_text().lower()
    for word in ("good for", "bad for", "boost", "fade", "start ", "sit ", "↑", "↓", "favor", "favour"):
        assert word not in text, word


def test_the_sky_moves_only_with_motion_allowed(weather):
    """The icon's streaks and drops are the forecast itself (STYLE.md: a loop only where the motion
    is the content); reduced motion gets the still icon and nothing loops. The page loads with reduced
    motion; the second half switches the media feature on the same page (the CSS is one media query)."""
    wx, _ = weather
    assert wx.looping_animations() == []
    # The still frame is a drawn icon: the wind's three strokes, the rain's cloud and drops.
    assert wx.sky_path_count("wind") == 3
    assert wx.sky_path_count("rain") == 4 and wx.first_sky_is_visible()
    wx.allow_motion()
    try:
        names = wx.looping_animations()
        assert set(names) == {"wt-gust", "wt-drop"}
        assert names.count("wt-gust") == 3 and names.count("wt-drop") == 3   # a 70% chance: 3 drops
    finally:
        wx.reduce_motion()
