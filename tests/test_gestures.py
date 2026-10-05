"""The page's touch gestures (lib/swipe.js, 2026-09-29), on a phone-sized touch page from the fixture build.

A sideways swipe turns to the next thing in a set already paged by buttons: the profile's tab and the game
sheet's game (Preview's game and the Leaders card's stat have their own tests). A pull down from the top
closes a sheet: the profile, search, the game sheet. A touch that starts on something with its own drag
(the orb sheet and its radar) is left alone, and a short pull springs back.
"""
import re

import pytest

from test_render import SEED, go, watch_errors  # noqa: F401

pytestmark = pytest.mark.render

TOUCH = """([sel, pts]) => {
  const el = document.querySelector(sel);
  const t = ([x, y]) => new Touch({identifier: 1, target: el, clientX: x, clientY: y});
  const fire = (type, p, on) => el.dispatchEvent(new TouchEvent(type, {touches: on ? [t(p)] : [], changedTouches: [t(p)], bubbles: true}));
  fire('touchstart', pts[0], true);
  for (const p of pts.slice(1)) fire('touchmove', p, true);
  fire('touchend', pts[pts.length - 1], false);
}"""


def touch(pg, sel, *pts):
    pg.evaluate(TOUCH, [sel, [list(p) for p in pts]])
    pg.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")   # the handlers' frame, not a clock


def swipe(pg, sel, dx):
    touch(pg, sel, (200, 400), (200 + dx / 2, 402), (200 + dx, 404))


def pull(pg, sel, dy):
    touch(pg, sel, (180, 200), (181, 200 + dy / 3), (182, 200 + 2 * dy / 3), (182, 200 + dy))


@pytest.fixture
def page(browser, page_file):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce", has_touch=True, is_mobile=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    errors = watch_errors(pg)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri())
    pg.wait_for_function("document.getElementById('view').children.length > 0")
    try:
        yield pg
        assert errors == []
    finally:
        ctx.close()


def open_profile(pg):
    pg.evaluate("openProfile({n: 'Amon-Ra St. Brown', pos: 'WR', team: 'DET', slug: 'amonra-st-brown'})")
    pg.wait_for_selector("#modal.on")


def tab(pg):
    return pg.evaluate("document.querySelector('#modal .pf-tabs [aria-selected=true]').dataset.pftab")


def tabs(pg):
    return pg.evaluate("[...document.querySelectorAll('#modal .pf-tabs [data-pftab]')].map(b => b.dataset.pftab)")


def test_a_swipe_on_the_profile_turns_its_tab_and_stops_at_the_ends(page):
    open_profile(page)
    order = tabs(page)
    assert len(order) >= 2 and tab(page) == order[0]
    swipe(page, "#modal .pf-tabpane", -120)
    assert tab(page) == order[1]
    swipe(page, "#modal .pf-tabpane", 120)
    assert tab(page) == order[0]
    swipe(page, "#modal .pf-tabpane", 120)            # before the first tab: nothing
    assert tab(page) == order[0]
    swipe(page, "#modal .pf-tabpane", -30)            # a nudge is not a swipe
    assert tab(page) == order[0]


def test_a_swipe_inside_the_orb_sheet_is_the_sheets_own(page):
    open_profile(page)
    assert page.locator("#modal .pf-orb").count(), "the fixture player draws a sphere"
    page.click("#modal .pf-orb")
    page.wait_for_selector("#modal .pf-orbsheet")
    before = tab(page)
    swipe(page, "#modal .pf-orbsheet", -120)
    assert tab(page) == before
    pull(page, "#modal .pf-orbsheet", 200)
    assert page.evaluate("document.getElementById('modal').classList.contains('on')")


def test_a_pull_down_closes_the_profile_and_a_short_one_does_not(page):
    open_profile(page)
    pull(page, "#modal .dr-body", 40)
    assert page.evaluate("document.getElementById('modal').classList.contains('on')")
    pull(page, "#modal .dr-body", 200)
    page.wait_for_selector("#modal:not(.on)", state="attached")
    assert page.evaluate("LAYERS.length") == 0                # the history entry went with it


def test_a_pull_from_mid_scroll_is_a_scroll(page):
    open_profile(page)
    # The fixture's profile fits a phone, so make it long enough to scroll, the way a real Usage pane is.
    scrolled = page.evaluate("""() => { const b = document.querySelector('#modal .dr-body');
        b.insertAdjacentHTML('beforeend', '<div style="height:2000px"></div>'); b.scrollTop = 120; return b.scrollTop; }""")
    assert scrolled == 120
    pull(page, "#modal .dr-body", 200)
    assert page.evaluate("document.getElementById('modal').classList.contains('on')")


def test_a_pull_down_closes_search(page):
    page.click("#navsearch")
    page.wait_for_selector("#search:not([hidden])")
    page.fill("#search-q", "brown")
    pull(page, "#search .search-in", 200)
    page.wait_for_function("document.getElementById('search').hidden")


def open_game(pg, i=0):
    for _kind, sel in go("live"):
        pg.click(sel)
    pg.wait_for_function("typeof GD !== 'undefined' && GD.leagues.length > 0")
    pg.evaluate("i => { const g = gdGamesSorted()[i].g; gsOpen({event: g.espn || '', away: g.away, home: g.home}); }", i)
    pg.wait_for_selector("#gamesheet.on")


def at(pg):
    return pg.evaluate("[GS.away, GS.home]")


def test_a_swipe_on_the_game_sheet_walks_the_weeks_games(page):
    open_game(page)
    # The fixture's league week holds one NFL game; a second, three hours later, gives the swipe somewhere to go.
    page.evaluate("""() => { const g = gdWeekGames()[0];
        GD_GAMES.push({...g, id: g.id + '-b', espn: '', away: 'NE', home: 'BUF',
                       kickoff: new Date(Date.parse(g.kickoff) + 3 * 3600e3).toISOString().replace('.000', '')}); }""")
    order = page.evaluate("gdGamesSorted().map(x => [x.g.away, x.g.home])")
    assert len(order) >= 2 and at(page) == order[0]
    swipe(page, "#gamesheet", -120)
    assert at(page) == order[1]
    assert page.evaluate("LAYERS.filter(l => l.id === 'gamesheet').length") == 1   # one Back still closes it
    swipe(page, "#gamesheet", 120)
    assert at(page) == order[0]
    swipe(page, "#gamesheet", 120)                    # before the first game: nothing
    assert at(page) == order[0]


def test_a_pull_down_closes_the_game_sheet(page):
    open_game(page)
    pull(page, "#gamesheet", 200)
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    assert page.evaluate("GS") is None
