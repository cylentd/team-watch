"""Live's game as a centred modal, the names in its plays, and the ball on a live card (U9, 2026-10-05).

David: "In This Week > Live > Games why cant you do a centered modal? Also, the game log should bold the
players name. The live scoreboard should show the direction of the ball or team and the redzone."

The logic (which names, which side has the ball, the red zone) is test_js_gamesituation.py, in Node. This
file is layout and taps only: the margins on four sides, every way to close it, a bold name per play line,
and the ball and red-zone mark on the Games tab's live tile."""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))

import pytest  # noqa: E402

from test_render import LIVE_PLANT as plant, go, open_page  # noqa: E402,F401

SUMMARY = json.loads((REPO / "tests" / "fixtures" / "data" / "espn_summary.json").read_text(encoding="utf-8"))
BOX = json.loads((REPO / "tests" / "fixtures" / "data" / "sleeper_box.json").read_text(encoding="utf-8"))

FILL = """([s, b]) => { GS_GAME = gsShape(s); GS_BOX = {box: b}; GS_ERR = ""; gsPaint(); }"""
SETTLE = "Promise.all(document.getAnimations().map(a => a.finished))"
EDGES = """(() => { const r = document.getElementById('gamesheet').getBoundingClientRect();
  return {top: r.top, left: r.left, right: innerWidth - r.right, bottom: innerHeight - r.bottom, width: r.width}; })()"""

LIVE_SIT = """() => { const g = {state: 'in', q: 3, clock: '4:12', half: false, detail: '', clubs: ['DET', 'SEA'],
    sit: {ball: 'SEA', dd: '3rd & 4 at DET 15', short: '3rd & 4', red: true, ytez: 15}};
  GD_CLOCK = {DET: g, SEA: g}; }"""


def open_live(page):
    page.evaluate(plant({"DET": "in_game", "SEA": "in_game"}))
    for _kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-mr")
    page.click("[data-gdtab='games']")


def open_game(page):
    page.evaluate("g => gsOpen(g, null)", {"event": "1", "away": "DET", "home": "BUF"})
    page.wait_for_selector("#gamesheet.on")
    page.evaluate(FILL, [SUMMARY, BOX])
    page.evaluate(SETTLE)


@pytest.mark.render
@pytest.mark.parametrize("size", [(390, 844), (1280, 800)], ids=["phone", "desktop"])
def test_the_game_opens_centred_with_a_margin_on_all_four_sides(browser, page_file, size):
    ctx, page, errors = open_page(browser, page_file, size)
    open_live(page)
    open_game(page)
    e = page.evaluate(EDGES)
    assert min(e["top"], e["left"], e["right"], e["bottom"]) >= 15, e
    assert abs(e["left"] - e["right"]) <= 1 and abs(e["top"] - e["bottom"]) <= 1, e      # centred both ways
    assert e["width"] <= 1040, e                                                           # a desktop max-width
    assert page.evaluate("document.getElementById('gamesheet').getBoundingClientRect().width") == e["width"]
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_game_closes_by_the_x_a_tap_on_the_scrim_and_back(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    open_live(page)
    for how in ("x", "scrim", "back"):
        open_game(page)
        if how == "x":
            page.click("#gamesheet .gs-x")
        elif how == "scrim":
            page.mouse.click(4, 4)                       # the margin around the modal is the scrim
        else:
            page.evaluate("history.back()")
        page.wait_for_selector("#gamesheet:not(.on)", state="attached")
        assert page.evaluate("GS") is None and page.evaluate("LAYERS.length") == 0, how
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_phone_closes_the_game_from_a_48px_bar_at_the_bottom(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    open_live(page)
    page.click("[data-gdtab='games']")
    tile = page.locator(".gd-tiles [data-gdnfl]").nth(1)
    tile.click()
    page.wait_for_selector("#gamesheet.on")
    page.evaluate(SETTLE)
    got = page.evaluate("""() => { const r = e => document.querySelector(e).getBoundingClientRect();
      const c = r('.gs-close'), p = r('.gs-step.prev'), n = r('.gs-step.next'), s = r('#gamesheet');
      return {closeBottomGap: innerHeight - c.bottom, h: [c.height, p.height, n.height], left: p.right <= c.left, right: c.right <= n.left,
              inSheet: c.bottom <= s.bottom && c.top >= s.top}; }""")
    assert got["closeBottomGap"] <= 80 and got["inSheet"], got
    assert got["h"] == [48, 48, 48] and got["left"] and got["right"], got
    # the bar stays put while the body scrolls
    page.evaluate("document.querySelector('.gs-main').scrollTop = 400")
    assert page.evaluate("innerHeight - document.querySelector('.gs-close').getBoundingClientRect().bottom") == got["closeBottomGap"]
    page.click(".gs-close")
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    assert page.evaluate("GS") is None and page.evaluate("LAYERS.length") == 0
    assert page.locator(".gd-tiles [data-gdnfl]").nth(1).is_visible()                  # still on the Games tab, the tile in place
    assert page.evaluate("document.activeElement === document.querySelectorAll('.gd-tiles [data-gdnfl]')[1]")   # focus came home
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_every_name_in_a_play_line_is_bold(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    open_live(page)
    open_game(page)
    page.click("[data-gstab='plays']")
    page.evaluate("document.querySelectorAll('.gs-drv').forEach(d => { d.open = true; })")
    got = page.evaluate("""() => {
      const lines = [...document.querySelectorAll('.gs-pl > span:last-child')];
      let names = 0, bold = 0, missed = [];
      for (const el of lines){
        const b = [...el.querySelectorAll('b')].map(x => x.textContent);
        const text = el.firstChild ? [...el.childNodes].filter(n => n.nodeName !== 'SMALL').map(n => n.textContent).join('') : '';
        for (const m of text.match(/(?<![A-Za-z.])(?:[A-Z]\\.){1,3} ?(?:St\\. )?[A-Z][A-Za-z'-]*[A-Za-z]/g) || []){
          names++;
          if (b.some(x => x.includes(m))) bold++; else missed.push(m);
        }
      }
      return {lines: lines.length, names, bold, missed, weight: getComputedStyle(document.querySelector('.gs-pl b')).fontWeight};
    }""")
    ctx.close()
    assert got["lines"] > 30 and got["names"] > 30, got
    assert got["missed"] == [] and got["bold"] == got["names"], got
    assert int(got["weight"]) >= 700, got
    assert errors == []


@pytest.mark.render
def test_a_live_card_shows_who_has_the_ball_and_the_red_zone(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    open_live(page)
    tile = page.locator(".gd-tiles .gd-t.in")
    assert tile.locator(".gd-ball").count() == 0 and tile.locator(".gd-sit").count() == 0     # ESPN sent nothing: nothing guessed
    page.evaluate(LIVE_SIT)
    page.evaluate("paintLive()")
    assert tile.locator(".gd-ball").count() == 1
    # the ball sits beside the club that has it: SEA, the second row
    assert tile.locator(".gd-tr").nth(1).locator(".gd-ball").count() == 1 and tile.locator(".gd-tr").nth(0).locator(".gd-ball").count() == 0
    assert tile.locator(".gd-ball").get_attribute("aria-label") == "SEA has the ball"
    assert tile.locator(".gd-sit span").inner_text() == "3rd & 4"
    sit_box, rz_box = tile.locator(".gd-sit span").bounding_box(), tile.locator(".gd-rz").bounding_box()
    assert tile.locator(".gd-sit span").evaluate("e => e.scrollWidth <= e.clientWidth")         # the down is never cut off
    assert sit_box["x"] + sit_box["width"] <= rz_box["x"] + 1
    assert tile.locator(".gd-rz").inner_text().lower() == "red zone"
    box = tile.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 390
    # outside the 20 the tag goes and the ball stays
    page.evaluate("() => { GD_CLOCK.DET.sit = GD_CLOCK.SEA.sit = {ball: 'SEA', dd: '1st & 10 at SEA 35', short: '1st & 10', red: false, ytez: 65}; }")
    page.evaluate("paintLive()")
    assert tile.locator(".gd-rz").count() == 0 and tile.locator(".gd-ball").count() == 1
    ctx.close()
    assert errors == []
