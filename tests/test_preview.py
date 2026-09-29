"""This week > Preview (2026-09-29, storyboard option C): one game a screen, swiped through, with a
Thursday / Sunday / Monday marker. Rendered from the fixture build.

The fixture (tests/fixtures/data/game_previews.json) holds one game per day: PIT @ CLE on Thursday
with a take, DET @ CAR on Sunday with a take, rain at 56% and Coker out, and ATL @ NO on Monday with
no take yet. SEED pins the clock before all three, so the view opens on Thursday's.
"""
import re

import pytest

from preview import live_preview
from test_render import SEED, browser  # noqa: F401  (browser is a fixture)

import json
import pathlib

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "game_previews.json"


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def test_the_block_sorts_by_kickoff_and_keeps_rain_only_when_it_moves_scoring():
    b = live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)
    assert [g["key"] for g in b["games"]] == ["2026_02_PIT_CLE", "2026_02_DET_CAR", "2026_02_ATL_NO"]
    pit, det, atl = b["games"]
    assert pit["rain"] is None and det["rain"] == 56          # 15% is not rain that moves scoring
    assert det["out"] == [{"n": "Jalen Coker", "slug": "jalen-coker", "pos": "WR", "team": "CAR", "inj": "Out"}]
    assert atl["take"] is None
    gibbs = det["take"]["players"][0]
    assert gibbs == {"n": "Jahmyr Gibbs", "slug": "jahmyr-gibbs", "pos": "RB", "team": "DET", "proj": 18.8,
                     "call": "up", "why": "The rain and the matchup both point to carries."}


def test_no_file_means_no_block():
    assert live_preview(None, slug) is None
    assert live_preview({"games": {}}, slug) is None


def open_preview(browser, page_file, w=360, h=800):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", has_touch=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + "#preview")
    pg.wait_for_function("document.querySelector('.pv-card') !== null")
    return ctx, pg


@pytest.fixture
def page(browser, page_file):
    ctx, pg = open_preview(browser, page_file)
    yield pg
    ctx.close()


def state(pg):
    return pg.evaluate("""() => ({
        match: document.querySelector('.pv-mt').textContent,
        days: [...document.querySelectorAll('.pv-day')].map(d => [d.querySelector('b').textContent, d.querySelectorAll('.pv-dots i').length, d.classList.contains('on')]),
        prev: document.querySelector("[data-pvstep='-1']").disabled,
        next: document.querySelector("[data-pvstep='1']").disabled,
    })""")


@pytest.mark.render
def test_it_opens_on_the_next_game_with_one_day_button_per_day(page):
    s = state(page)
    assert s["match"] == "PIT @ CLE"
    assert s["days"] == [["Thu", 1, True], ["Sun", 1, False], ["Mon", 1, False]]
    assert s["prev"] and not s["next"]


@pytest.mark.render
def test_the_arrows_and_a_day_turn_the_game(page):
    page.click("[data-pvstep='1']")
    assert state(page)["match"] == "DET @ CAR"
    assert page.inner_text(".pv-chips") .replace("\n", " ").startswith("Rain 56%")
    assert "J. Coker" in page.inner_text(".pv-out")
    page.click(".pv-day:last-child")
    s = state(page)
    assert s["match"] == "ATL @ NO" and s["next"]
    assert page.locator(".pv-none").count() == 1 and page.locator(".pv-pl").count() == 0


def swipe(pg, dx):
    pg.evaluate("""dx => {
        const el = document.querySelector('[data-pvswipe]');
        const t = x => new Touch({identifier: 1, target: el, clientX: x, clientY: 300});
        el.dispatchEvent(new TouchEvent('touchstart', {touches: [t(200)], changedTouches: [t(200)], bubbles: true}));
        el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [t(200 + dx)], bubbles: true}));
    }""", dx)


@pytest.mark.render
def test_a_swipe_turns_the_game_and_stops_at_the_ends(page):
    swipe(page, -120)
    assert state(page)["match"] == "DET @ CAR"
    swipe(page, 120)
    assert state(page)["match"] == "PIT @ CLE"
    swipe(page, 120)                                  # past the first game: nothing
    assert state(page)["match"] == "PIT @ CLE"
    swipe(page, -20)                                  # a nudge is not a swipe
    assert state(page)["match"] == "PIT @ CLE"


@pytest.mark.render
def test_a_player_row_opens_his_profile(page):
    page.evaluate("() => { window.__opened = []; openProfile = p => window.__opened.push(p.slug); }")
    page.click(".pv-p >> nth=0")
    assert page.evaluate("window.__opened") == ["dk-metcalf"]


@pytest.mark.render
@pytest.mark.parametrize("w,h", [(360, 800), (1280, 800)])
def test_every_game_fits_one_screen(browser, page_file, w, h):
    ctx, pg = open_preview(browser, page_file, w, h)
    try:
        for i in range(3):
            bottom = pg.evaluate("i => { PV_I = i; render(); scrollTo(0, 0); return document.querySelector('.pv-card').getBoundingClientRect().bottom; }", i)
            assert bottom <= h, f"game {i} ends at {bottom}px of {h}"
    finally:
        ctx.close()
