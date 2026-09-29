"""This week > Preview (2026-09-29, storyboard option A): a slate of every game by kickoff window,
and a tap opens the game's dossier. Rendered from the fixture build.

The fixture (tests/fixtures/data/game_previews.json) holds five games, one per window: PIT @ CLE on
Thursday (both on a short week), JAX @ LA on Sunday morning at Wembley (neutral site, wind 17 mph,
LA off a bye, Claude picks the underdog), DET @ CAR at 1:00 (rain 56%, Coker out, St. Brown
questionable, the only game with defense ranks), SF @ NYJ late (SF flew 3 zones east; the line
flipped), and ATL @ NO on Monday in a dome with no take, no rest, travel or site. SEED pins the clock
before all five.
"""
import json
import pathlib
import re

import pytest

from preview import live_preview
from test_render import SEED, browser  # noqa: F401  (browser is a fixture)

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "game_previews.json"


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


@pytest.fixture(scope="module")
def block():
    return live_preview(json.loads(FIXTURE.read_text(encoding="utf-8")), slug)


def by_key(block):
    return {g["key"].split("_", 2)[2]: g for g in block["games"]}


def test_the_block_sorts_by_kickoff_into_windows(block):
    assert [(g["key"], g["slot"], g["et"]) for g in block["games"]] == [
        ("2026_02_PIT_CLE", "thu", "8:15 PM"), ("2026_02_JAX_LA", "sunam", "9:30 AM"),
        ("2026_02_DET_CAR", "sun1", "1:00 PM"), ("2026_02_SF_NYJ", "sunlate", "4:25 PM"),
        ("2026_02_ATL_NO", "mon", "8:15 PM")]


def test_the_line_is_a_favourite_and_a_margin_never_a_signed_spread(block):
    g = by_key(block)
    assert g["PIT_CLE"]["line"]["fav"] == "PIT" and g["PIT_CLE"]["line"]["by"] == 2.5   # spread_home +2.5: away favoured
    assert g["SF_NYJ"]["line"]["fav"] == "NYJ" and g["SF_NYJ"]["line"]["open"] == {"fav": "SF", "by": 3.0, "total": 43.5}
    assert g["ATL_NO"]["line"]["open"] is None                                           # no first line seen


def test_flags_are_at_most_two_in_priority_order(block):
    g = by_key(block)
    assert g["PIT_CLE"]["flags"] == [{"k": "short", "teams": ["CLE", "PIT"]}]
    assert g["JAX_LA"]["flags"] == [{"k": "upset"}, {"k": "wx", "wind": 17}]
    assert g["DET_CAR"]["flags"] == [{"k": "wx", "rain": 56}, {"k": "out", "n": "Jalen Coker", "slug": "jalen-coker"}]
    assert g["SF_NYJ"]["flags"] == [{"k": "upset"}, {"k": "moved", "flip": True, "by": 4.5}]
    assert g["ATL_NO"]["flags"] == []


def test_injuries_rest_travel_and_matchup(block):
    g = by_key(block)
    assert g["DET_CAR"]["inj"] == {"CAR": [{"n": "Jalen Coker", "slug": "jalen-coker", "pos": "WR", "s": "out", "avg": 14.4}],
                                   "DET": [{"n": "Amon-Ra St. Brown", "slug": "amon-ra-st-brown", "pos": "WR", "s": "q", "avg": None}]}
    assert g["DET_CAR"]["matchup"]["DET"]["pos"]["RB"] == {"pts": 29.4, "rank": 31}   # keyed by the offense
    assert g["SF_NYJ"]["travel"]["SF"] == {"zones": 3, "body": "13:25", "miles": 2570}
    assert g["JAX_LA"]["rest"]["LA"] == {"days": 13, "short": False, "bye": True}
    assert g["JAX_LA"]["site"] == {"stadium": "Wembley Stadium", "neutral": True}
    atl = g["ATL_NO"]
    assert (atl["rest"], atl["travel"], atl["site"], atl["matchup"], atl["take"]) == (None, None, None, None, None)
    gibbs = g["DET_CAR"]["take"]["players"][0]
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
    pg.wait_for_function("document.querySelector('.pv-row') !== null")
    return ctx, pg


@pytest.fixture
def page(browser, page_file):
    ctx, pg = open_preview(browser, page_file)
    yield pg
    ctx.close()


def is_open(pg):
    return pg.evaluate("document.querySelector('.pv').classList.contains('open')")


def match(pg):
    return pg.inner_text(".pv-mt")


@pytest.mark.render
def test_the_slate_lists_every_game_by_window(page):
    wins = page.evaluate("""() => [...document.querySelectorAll('.pv-win')].map(w => [
        w.querySelector('.pv-wh span').textContent, [...w.querySelectorAll('.pv-rm')].map(r => r.textContent)])""")
    assert wins == [["Thu night", ["PIT @ CLE"]], ["Sun morning", ["JAX @ LA"]], ["Sun early", ["DET @ CAR"]],
                    ["Sun late", ["SF @ NYJ"]], ["Mon night", ["ATL @ NO"]]]
    assert page.inner_text(".pv-wh em >> nth=0") .upper() == "8:15 PM ET"
    assert not is_open(page) and not page.is_visible(".pv-dz")


@pytest.mark.render
def test_a_row_says_the_spread_in_words_and_its_flags(page):
    metas = page.evaluate("() => [...document.querySelectorAll('.pv-meta')].map(m => m.innerText.replace(/\\s+/g, ' '))")
    assert metas[0] == "PIT by 2.5 Total 38.5 Short week"
    assert metas[1] == "LA by 3 Total 46.5 UPSET Wind 17 mph"
    assert metas[2] == "DET by 3.5 Total 50.5 Rain 56% J. Coker out"
    assert metas[3] == "NYJ by 1.5 Total 41.5 UPSET Line flipped"
    assert not any(re.search(r"[-−]\d", m) for m in metas)
    assert "Claude's call arrives" in page.inner_text("[data-pvopen='4']")


@pytest.mark.render
def test_a_tap_opens_the_dossier_and_back_returns_to_the_slate_where_it_was(page):
    page.evaluate("window.scrollTo(0, 120)")
    y = page.evaluate("scrollY")
    page.click("[data-pvopen='3']")
    assert is_open(page) and match(page) == "SF @ NYJ"
    assert not page.is_visible(".pv-slate")
    assert page.evaluate("location.hash") == "#preview"          # the game is not in the URL
    lines = page.inner_text(".pvd-row.lines")
    assert "NYJ by 1.5" in lines and "opened SF by 3" in lines and "opened 43.5" in lines
    assert "+3 zones east · kicks off at 1:25 PM body time" in page.inner_text(".pvd-row.rest")
    page.go_back()
    page.wait_for_function("!document.querySelector('.pv').classList.contains('open')")
    page.wait_for_timeout(50)
    assert page.evaluate("scrollY") == y
    assert page.evaluate("location.hash") == "#preview"


@pytest.mark.render
def test_the_all_games_button_closes_the_dossier(page):
    page.click("[data-pvopen='0']")
    page.click("[data-pvback]")
    assert not is_open(page)
    page.click("[data-pvopen='1']")                             # and opening again still works
    assert is_open(page) and match(page) == "JAX @ LA"


@pytest.mark.render
def test_optional_rows_are_absent_without_data(page):
    rows = lambda: page.evaluate("() => [...document.querySelectorAll('.pvd-row')].map(r => r.classList[1])")
    page.click("[data-pvopen='4']")                              # ATL @ NO: dome, no take, no rest
    assert rows() == ["call", "lines", "inj", "wx"]              # no matchup, rest, players or risk
    assert "Dome" in page.inner_text(".pvd-row.wx")
    assert page.locator(".pv-pl").count() == 0 and page.locator(".pv-risk").count() == 0
    page.click("[data-pvstep='-1']")
    page.click("[data-pvstep='-1']")                             # DET @ CAR: the one with defense ranks
    assert match(page) == "DET @ CAR" and page.locator(".pv-mx").count() == 1
    assert page.locator(".pv-mx tr.dim").inner_text().startswith("WR")
    assert "Rain" in page.inner_text(".pv-eff")                  # rain 56% is past the backtest's threshold
    assert "J. Coker" in page.inner_text(".pv-inj >> nth=1")


@pytest.mark.render
def test_neutral_site_and_short_week(page):
    page.click("[data-pvopen='1']")
    assert "Neutral site: Wembley Stadium" in page.inner_text(".pvd-row.rest")
    assert "OFF A BYE" in page.inner_text(".pvd-row.rest")
    page.click("[data-pvstep='-1']")
    assert page.locator(".pvd-row.rest .pv-tag.short").count() == 2


def swipe(pg, dx):
    pg.evaluate("""dx => {
        const el = document.querySelector('[data-pvswipe]');
        const t = x => new Touch({identifier: 1, target: el, clientX: x, clientY: 300});
        el.dispatchEvent(new TouchEvent('touchstart', {touches: [t(200)], changedTouches: [t(200)], bubbles: true}));
        el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [t(200 + dx)], bubbles: true}));
    }""", dx)


@pytest.mark.render
def test_a_swipe_in_the_dossier_walks_the_games_and_stops_at_the_ends(page):
    page.click("[data-pvopen='0']")
    swipe(page, -120)
    assert match(page) == "JAX @ LA" and is_open(page)
    swipe(page, 120)
    assert match(page) == "PIT @ CLE"
    swipe(page, 120)                                  # past the first game: nothing
    assert match(page) == "PIT @ CLE"
    swipe(page, -20)                                  # a nudge is not a swipe
    assert match(page) == "PIT @ CLE"


@pytest.mark.render
def test_a_player_row_opens_his_profile(page):
    page.click("[data-pvopen='0']")
    page.evaluate("() => { window.__opened = []; openProfile = p => window.__opened.push(p.slug); }")
    page.click(".pv-p >> nth=0")
    assert page.evaluate("window.__opened") == ["dk-metcalf"]


@pytest.mark.render
def test_a_desktop_shows_the_rail_beside_the_dossier(browser, page_file):
    ctx, pg = open_preview(browser, page_file, 1280, 900)
    try:
        assert pg.is_visible(".pv-slate") and pg.is_visible(".pv-dz") and match(pg) == "PIT @ CLE"
        pg.click("[data-pvopen='2']")
        assert match(pg) == "DET @ CAR" and pg.locator(".pv-row.cur .pv-rm").inner_text() == "DET @ CAR"
        assert pg.evaluate("LAYERS.length") == 0 and not is_open(pg)   # a click on a desktop pushes no layer
        slate, dz = pg.evaluate("""() => [document.querySelector('.pv-slate'), document.querySelector('.pv-dz')]
            .map(e => e.getBoundingClientRect().left)""")
        assert slate < dz
    finally:
        ctx.close()


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360(page):
    for i in range(5):
        page.evaluate(f"() => {{ PV_I = {i}; PV_OPEN = true; render(); }}")
        assert page.evaluate("document.documentElement.scrollWidth") <= 360, f"game {i}"
