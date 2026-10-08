"""Claude's prop calls on the page (2026-10-05, storyboard "Claude Calls" A): a round "C" on the side Claude
picked, in the line sheet and on the Slips board. The data wiring is in tests/test_slip_reasons.py.

The fixture's calls, against the model's tier on the same line (tests/fixtures/README.md):
  Brown RUSH 65.5   Claude Higher, the model Higher (Very confident)        -> agree: lime badge on the outlined side
  Burrow PASS 245.5 Claude Higher, the model Lower (Confident)              -> disagree: ink badge on Higher, one line of why
  Kittle REC 45.5   Claude Lower, the model has no pick                     -> ink badge on Lower, one line of why
  Purdy PASS 230.5  Claude Lower, but the lines shown are 220.5 / 220.5     -> no badge until a book shows 230.5
  St. Brown REC 75.5 no call                                                -> nothing"""
import pytest

from test_render import open_page
from wording import words

pytestmark = pytest.mark.render

RESET = """() => { 'use strict';
  PROPS.splice(0, PROPS.length, ...JSON.parse(__PROPS));
  for (const k of Object.keys(LIVE_CLAUDE_PROPS.calls)) delete LIVE_CLAUDE_PROPS.calls[k];
  Object.assign(LIVE_CLAUDE_PROPS.calls, JSON.parse(__CALLS));
  SLIP.length = 0; SL_CHIP = {}; SL_FOCUS = null; PV_OPEN = false; PV_I = null;
  PARLAY_BOOK = 'dk'; GAL_WIN = 'evening-mon'; SURFACE = 'parlay'; render(); }"""

BURROW_WHY = "Over 245.5 in 4 of his last 5, and CIN trail late more often than not."


@pytest.fixture(scope="module")
def shared(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, (360, 780))
    pg.evaluate("() => { window.__PROPS = JSON.stringify(PROPS); window.__CALLS = JSON.stringify(LIVE_CLAUDE_PROPS.calls); }")
    assert errors == []
    yield pg, errors
    ctx.close()


@pytest.fixture
def page(shared):
    pg, errors = shared
    left, errors[:] = list(errors), []
    assert left == []
    pg.evaluate(RESET)
    yield pg
    assert errors == [], errors


def open_sheet(page, slug):
    page.evaluate(f"playerSheetOpen({slug!r})")
    return page.locator("#legsheet.on")


def close_sheet(page):
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")


def line(sheet, label):
    return sheet.locator(f".sl-ln:has(.sl-mk:has-text('{label}'))").first


def colour(loc, prop="backgroundColor"):
    return loc.evaluate(f"e => getComputedStyle(e).{prop}")


def token(page, name):
    """A colour token as the browser computes it, through a probe element."""
    return page.evaluate("n => { const e = document.createElement('i'); e.style.color = `var(${n})`; document.body.append(e);"
                         " const c = getComputedStyle(e).color; e.remove(); return c; }", name)


def all_chips(page):
    page.locator("[data-slchip='all']").first.click()


def row(page, slug):
    return page.locator(f".sl-row[data-slplayer='{slug}']")


def test_agree_is_a_lime_badge_on_the_models_outlined_side(page):
    sheet = open_sheet(page, "chase-brown")
    ln = line(sheet, "Rush yds")
    higher = ln.locator(".sl-side.higher")
    badge = higher.locator(".sl-cb")
    assert "pick" in higher.get_attribute("class").split(), "the model's outlined side"
    assert badge.count() == 1 and badge.inner_text() == "C" and ln.locator(".sl-cb").count() == 1
    assert "agree" in badge.get_attribute("class").split() and badge.get_attribute("aria-hidden") == "true"
    assert colour(badge) == token(page, "--lime") and colour(badge, "color") == token(page, "--on-lime")
    assert ln.locator(".sl-cwhy").count() == 0, "Claude agreeing needs no second line"
    assert higher.get_attribute("aria-label") == "Higher, Claude picks this"
    assert ln.locator(".sl-side.lower").get_attribute("aria-label") is None
    assert ln.locator(".sl-conf").all_inner_texts() == [words("slips.tier.very")], "the model's tier word stays the only confidence word"
    b, h = badge.bounding_box(), higher.bounding_box()
    assert (round(b["width"]), round(b["height"])) == (18, 18)
    # offset -7px from the padding box, which sits 1px inside the border
    assert abs((b["x"] + b["width"]) - (h["x"] + h["width"] + 6)) <= 1.5 and abs(b["y"] - (h["y"] - 6)) <= 1.5, "on the top-right corner"
    assert colour(badge, "fontWeight") == "800" and "Bricolage" in colour(badge, "fontFamily")
    close_sheet(page)


def test_disagree_is_an_ink_badge_on_the_other_side_with_the_why_under_the_row(page):
    sheet = open_sheet(page, "joe-burrow")
    ln = line(sheet, "Pass yds")
    assert ln.locator(".sl-side.pick").all_inner_texts() == ["Lower"], "the model's side"
    badge = ln.locator(".sl-side.higher .sl-cb")
    assert badge.count() == 1 and "agree" not in badge.get_attribute("class").split()
    assert colour(badge) == token(page, "--ink") and colour(badge, "color") == token(page, "--void")
    assert ln.locator(".sl-side.lower .sl-cb").count() == 0
    why = ln.locator(".sl-cwhy")
    assert why.locator("span").inner_text() == BURROW_WHY
    assert why.locator(".sl-cb.static").count() == 1 and colour(why.locator(".sl-cb.static"), "position") == "static"
    assert colour(why, "color") == token(page, "--ink-2") and colour(why, "fontSize") == "12px"
    assert ln.locator(".sl-side.higher").get_attribute("aria-label") == "Higher, Claude picks this"
    assert ln.locator(".sl-conf").all_inner_texts() == ["Confident"] and "Slight" not in ln.inner_text(), "Claude's own confidence is never shown"
    assert ln.locator(".sl-mk").bounding_box()["y"] < why.bounding_box()["y"] - 10, "below the row"
    close_sheet(page)


def test_a_line_the_model_has_no_pick_on_still_shows_claudes_call(page):
    sheet = open_sheet(page, "george-kittle")
    ln = line(sheet, "Rec yds")
    assert ln.locator(".sl-side.pick").count() == 0
    assert ln.locator(".sl-side.lower .sl-cb").count() == 1 and ln.locator(".sl-cb.agree").count() == 0
    assert ln.locator(".sl-cwhy span:not(.sl-cb)").inner_text() == "Under 45.5 in 3 of his last 4 on 4, 3, 5 targets."
    close_sheet(page)


def test_no_call_is_nothing(page):
    sheet = open_sheet(page, "amonra-st-brown")
    assert sheet.locator(".sl-cb, .sl-cwhy").count() == 0
    assert sheet.locator(".sl-side[aria-label]").count() == 0
    assert "Claude" not in sheet.inner_text()
    close_sheet(page)
    page.evaluate("() => { for (const k of Object.keys(LIVE_CLAUDE_PROPS.calls)) delete LIVE_CLAUDE_PROPS.calls[k]; render(); }")
    sheet = open_sheet(page, "chase-brown")
    assert sheet.locator(".sl-cb, .sl-cwhy").count() == 0, "an empty block: no badge anywhere"
    close_sheet(page)


def test_a_touchdown_never_has_a_call(page):
    page.evaluate("""() => { LIVE_CLAUDE_PROPS.calls['chase-brown'].push({mkt: 'TD', line: null, side: 'higher', why: 'x'}); render(); }""")
    sheet = open_sheet(page, "chase-brown")
    assert line(sheet, "Anytime TD").locator(".sl-cb, .sl-cwhy").count() == 0
    close_sheet(page)


def test_a_call_for_another_line_gets_no_badge_on_underdog(page):
    """Purdy: the call is for 230.5 and both books show 220.5. Underdog moving to 230.5 makes it the line
    shown, so the call applies; moving it again takes it away. Brown: Underdog at 70.5, the call is 65.5."""
    sheet = open_sheet(page, "brock-purdy")
    assert line(sheet, "Pass yds").locator(".sl-cb").count() == 0, "220.5 is not 230.5"
    close_sheet(page)
    page.evaluate("() => { const p = PROPS.find(p => p.n === 'Brock Purdy' && p.mkt === 'PASS'); p.books.Underdog.line = 230.5; PARLAY_BOOK = 'underdog'; render(); }")
    sheet = open_sheet(page, "brock-purdy")
    ln = line(sheet, "Pass yds")
    assert ln.locator(".sl-mk b").inner_text() == "230.5" and ln.locator(".sl-side.lower .sl-cb").count() == 1
    close_sheet(page)
    page.evaluate("PARLAY_BOOK = 'dk'; render()")
    sheet = open_sheet(page, "brock-purdy")
    assert line(sheet, "Pass yds").locator(".sl-cb").count() == 0, "DraftKings still shows 220.5"
    close_sheet(page)
    page.evaluate("() => { const p = PROPS.find(p => p.n === 'Chase Brown' && p.mkt === 'RUSH'); p.books.Underdog.line = 70.5; PARLAY_BOOK = 'underdog'; render(); }")
    sheet = open_sheet(page, "chase-brown")
    ln = line(sheet, "Rush yds")
    assert ln.locator(".sl-mk b").inner_text() == "70.5" and ln.locator(".sl-cb, .sl-cwhy").count() == 0
    close_sheet(page)


def test_the_board_wears_the_lime_badge_only_where_claude_agrees(page):
    """Morning card: Brown (agrees), Burrow (disagrees, the board shows nothing). Sunday: Kittle has no pick."""
    page.evaluate("GAL_WIN = 'morning'; render()")
    all_chips(page)
    brown = row(page, "chase-brown").locator(".sl-pick .sl-cb")
    assert brown.count() == 1 and "agree" in brown.get_attribute("class").split() and brown.inner_text() == "C"
    assert colour(brown) == token(page, "--lime")
    assert row(page, "joe-burrow").locator(".sl-cb").count() == 0, "a disagreement shows nothing on the board"
    pick, b = row(page, "chase-brown").locator(".sl-pick").bounding_box(), brown.bounding_box()
    assert abs(b["y"] - (pick["y"] - 6)) <= 1.5 and abs((b["x"] + b["width"]) - (pick["x"] + pick["width"] + 6)) <= 1.5, "on the label's top-right corner"
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    page.evaluate("GAL_WIN = 'evening-sun'; render()")
    all_chips(page)
    assert page.locator(".sl-row .sl-cb").count() == 0
