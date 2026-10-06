"""Live's sideways swipes. In the game sheet a swipe walks the games in the NFL tab's order, and a step
row names the game on each side (2026-10-04). On My league a swipe does nothing since 2026-10-05: the
league is the reader's team's, and the league swipe and chips went with Live's own league setting.
Browser tests on the week 2 fixture (tests/fixtures/gameday.json)."""
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
    page.wait_for_selector("[data-gdboard] .gd-tabs", state="attached")   # a phone hides it: the tab row holds the tabs
    return ctx, page, errors


def test_a_swipe_on_my_league_leaves_the_league_alone(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    assert page.evaluate("GD.leagues.length") >= 2, "the fixture needs two leagues"
    before = page.evaluate("[gdLeague().key, gdMine(gdLeague())]")
    for dx in (-120, 120):
        page.evaluate(SWIPE, ["[data-gdboard]", dx])
        assert page.evaluate("[gdLeague().key, gdMine(gdLeague())]") == before
    assert "turn-" not in page.locator("[data-gdboard]").get_attribute("class")
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
