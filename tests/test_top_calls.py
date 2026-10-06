"""Bets UX on the page (2026-10-05, plan "Bets UX"): Slips leads with Top calls, a player's sheet is a centred
modal while one bet stays a bottom sheet, Build speaks the tier words, and its first chip says what it keeps.
The choosing and ordering is Node-tested (tests/test_js_topcalls.py); this file holds layout and taps.

The fixture slate with ff-jarvis's tiers (tests/test_prop_picks.py): Chase Brown RUSH Higher very, Burrow PASS
Lower confident, Purdy PASS Lower slight, St. Brown REC Higher slight."""
import pytest

from test_render import open_page

pytestmark = pytest.mark.render

PHONE = (390, 844)
RESET = """() => { 'use strict';
  SLIP.length = 0; for (const k of Object.keys(SLIP_SIDE)) delete SLIP_SIDE[k];
  if (LEG_SHEET !== null) legSheetClose();
  PARLAY_BOOK = 'underdog'; GAL_WIN = 'ALL'; BETS_SHEET = false; navGo('parlay'); render(); }"""


@pytest.fixture(scope="module")
def shared(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, PHONE)
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


def test_top_calls_lead_slips_with_a_verdict_each(page):
    box = page.locator(".tpc").bounding_box()
    assert box["y"] + page.evaluate("window.scrollY") <= 212, "the first data starts by ~200px"
    assert page.evaluate("document.querySelector('.tpc').compareDocumentPosition(document.querySelector('.sl-board')) & Node.DOCUMENT_POSITION_FOLLOWING"), "above the board"
    assert page.locator(".tpc h2").inner_text() == "Top calls"
    rows = page.locator(".tpc-row")
    assert 1 <= rows.count() <= 5
    first = rows.first
    assert first.locator(".tpc-who b").inner_text() == "C. Brown"
    assert first.locator(".tpc-pick").inner_text().startswith("Higher rush yds"), "the side and the line"
    assert first.locator(".sl-pc").inner_text() == "72%" and first.locator(".sl-conf").inner_text() == "Very confident"
    assert first.locator(".tpc-edge").inner_text().endswith("break-even"), "the edge over the book's break-even"
    tiers = page.locator(".tpc .sl-conf").all_inner_texts()
    assert tiers == sorted(tiers, key=["Slight", "Confident", "Very confident"].index, reverse=True), "strongest first"


def test_one_tap_puts_the_calls_side_on_the_slip(page):
    first = page.locator(".tpc-add").first
    assert first.get_attribute("aria-pressed") == "false"
    first.click()
    assert page.evaluate("SLIP.length") == 1 and page.evaluate("slipSide(SLIP[0])") == "higher"
    assert page.locator(".tpc-add").first.get_attribute("aria-pressed") == "true"
    assert page.locator(".tray-n").inner_text() == "1"
    page.locator(".tpc-add").first.click()
    assert page.evaluate("SLIP.length") == 0, "the same side again takes it off"
    box = page.locator(".tpc-add").first.bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44, "a 44px target"


def test_a_players_sheet_is_a_centred_modal_and_one_bet_stays_at_the_bottom_edge(page):
    page.locator(".tpc-main").first.click()
    sheet = page.locator("#legsheet.on")
    assert sheet.count() == 1 and "ls-read" in sheet.get_attribute("class")
    b = sheet.bounding_box()
    w, h = PHONE
    assert b["x"] >= 16 and b["x"] + b["width"] <= w - 16, "a margin on both sides"
    assert b["y"] >= 16 and b["y"] + b["height"] <= h - 16, "a margin top and bottom: it floats, it does not dock"
    assert abs((b["x"] + b["width"] / 2) - w / 2) <= 1
    assert page.locator("#legsheet .grab").count() == 0 and page.locator("#legsheet .ps-x").count() == 1
    assert page.evaluate("document.activeElement.classList.contains('ps-x')"), "focus goes to the ✕"
    page.locator("#legsheet .ps-x").click()
    page.wait_for_function("LEG_SHEET === null")
    # One bet is a short action: it keeps the bottom edge.
    page.evaluate("legSheetOpen(PROPS.findIndex(p => p.n === 'Chase Brown' && p.mkt === 'RUSH'))")
    bet = page.locator("#legsheet.on")
    assert "ls-read" not in bet.get_attribute("class")
    bb = bet.bounding_box()
    assert abs(bb["y"] + bb["height"] - PHONE[1]) <= 1, "it sits on the bottom edge"
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")


def test_the_scrim_and_back_close_the_modal(page):
    page.locator(".tpc-main").first.click()
    page.locator("#legsheet-scrim").click(position={"x": 4, "y": 4})
    page.wait_for_function("LEG_SHEET === null")


def test_the_sheets_model_side_carries_its_chance_beside_the_tier_word(page):
    page.evaluate("playerSheetOpen('chase-brown')")
    ln = page.locator("#legsheet .sl-ln.tiered")
    assert ln.locator(".sl-tp").inner_text().replace("\n", " ") == "72% Very confident"
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")


def test_build_is_all_lines_and_says_what_its_first_chip_keeps(page):
    page.evaluate("navGo('build')")
    assert page.locator("#subnav").inner_text().split("\n")[:3] == ["Slips", "All lines", "DFS"]
    assert page.locator(".bets-best").inner_text() == "Better price"
    calls = page.locator(".bl-call")
    got = [c.inner_text().replace("\n", " ") for c in calls.all()[:6]]
    assert any(c.startswith("Higher 72% Very confident") for c in got), got
    assert any(c.startswith("Lower 64% Confident") for c in got), got
    assert not [c for c in got if c.startswith("Scores") and ("onfident" in c or "Slight" in c)], "a touchdown has no tier"
