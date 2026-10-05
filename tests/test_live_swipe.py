"""Live's sideways swipes (2026-10-04): on Matchup and League a swipe walks the leagues, the chips in
step; in the game sheet it walks the games in the Games tab's order, and a step row names the game on
each side. Browser tests on the week 2 fixture (tests/fixtures/gameday.json)."""
import pytest

from test_render import LIVE_PLANT as plant, go, open_page  # noqa: F401

pytestmark = pytest.mark.render

PHONE = (360, 780)

# A one-finger swipe on `sel`, `dx` px sideways: negative is a swipe left (the next one).
SWIPE = """([sel, dx]) => {
  const el = document.querySelector(sel);
  const at = x => new Touch({identifier: 1, target: el, clientX: x, clientY: 300});
  el.dispatchEvent(new TouchEvent('touchstart', {touches: [at(200)], changedTouches: [at(200)], bubbles: true}));
  el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [at(200 + dx)], bubbles: true}));
}"""


def live(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate(plant({"DET": "in_game", "SEA": "in_game"}))
    for _kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-tabs")
    return ctx, page, errors


def picked(page):
    return page.locator(".gd-leagues [aria-pressed='true']").get_attribute("data-gdleague")


def test_a_swipe_on_matchup_and_league_walks_the_leagues_and_stops_at_the_ends(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    keys = page.evaluate("GD.leagues.map(l => l.key)")
    assert len(keys) >= 2, "the fixture needs two leagues"
    assert picked(page) == keys[0]
    page.evaluate(SWIPE, ["[data-gdboard]", -120])
    assert picked(page) == keys[1]
    slides = 0 if page.evaluate("REDUCED()") else 1                # the suite's browser may ask for less motion
    assert page.locator("[data-gdboard]").get_attribute("class").split().count("turn-r") == slides
    page.evaluate("paintLive()")                                   # a poll's repaint drops the slide
    assert "turn-r" not in page.locator("[data-gdboard]").get_attribute("class")
    for _ in keys:                                                 # past the last league: stays on it
        page.evaluate(SWIPE, ["[data-gdboard]", -120])
    assert picked(page) == keys[-1]
    page.evaluate(SWIPE, ["[data-gdboard]", 30])                    # too short to be a swipe
    assert picked(page) == keys[-1]
    page.click("[data-gdtab='league']")
    page.evaluate(SWIPE, ["[data-gdboard]", 120])
    assert picked(page) == keys[-2]
    # Games is NFL-wide, so a swipe there leaves the league alone
    page.click("[data-gdtab='games']")
    page.evaluate(SWIPE, ["[data-gdboard]", 120])
    assert page.evaluate("gdLeague().key") == keys[-2]
    ctx.close()
    assert errors == []


def test_the_league_swipe_never_outlives_live(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    before = page.evaluate("gdLeague().key")
    for _kind, sel in go("news"):
        page.click(sel)
    page.evaluate(SWIPE, ["#view", -120])
    assert page.evaluate("gdLeague().key") == before
    ctx.close()
    assert errors == []


def test_the_sheet_walks_the_games_in_the_order_the_games_tab_lists_them(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    page.click("[data-gdtab='games']")
    tiles = page.locator(".gd-tiles [data-gdnfl]").evaluate_all("bs => bs.map(b => b.dataset.gdnfl.split(','))")
    assert len(tiles) >= 3, "the fixture needs three games"
    name = lambda g: f"{g[1]} @ {g[2]}"
    page.locator(".gd-tiles [data-gdnfl]").nth(1).click()
    page.wait_for_selector("#gamesheet.on")
    steps = page.locator(".gs-step span")
    assert [s.split("\n")[0] for s in steps.all_inner_texts()] == [name(tiles[0]), name(tiles[2])]
    # a tap on the next one opens it, and the step row moves with it
    page.click(".gs-step.next")
    assert page.evaluate("[GS.away, GS.home]") == tiles[2][1:]
    assert page.locator(".gs-step.prev span").inner_text().split("\n")[0] == name(tiles[1])
    # a swipe right goes back the same way
    page.evaluate(SWIPE, ["#gamesheet", 120])
    assert page.evaluate("[GS.away, GS.home]") == tiles[1][1:]
    # the first game has nothing before it: that side is empty and a swipe right stays put
    page.click(".gs-step.prev")
    assert page.locator(".gs-step.prev").count() == 0 and page.locator(".gs-step.next").count() == 1
    page.evaluate(SWIPE, ["#gamesheet", 120])
    assert page.evaluate("[GS.away, GS.home]") == tiles[0][1:]
    ctx.close()
    assert errors == []
