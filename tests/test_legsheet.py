"""The leg sheet (2026-09-27). A Build line's info button opens one bet from the bottom edge: the
last ten games against the line, three tiles, the matchup as one line, and Add; since 2026-10-03 a
Slips board row opens the player sheet in the same overlay. Back closes either before it changes
the view. The fixture gives Tee Higgins and Chase Brown per-game usage (`u`) and Amon-Ra St. Brown
none, and a defense block in which NYJ has two starters out."""
import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render

PHONE = (360, 780)


def index(page, name, mkt):
    return page.evaluate(f"PROPS.findIndex(p => p.n === {name!r} && p.mkt === {mkt!r})")


def no_sideways(page):
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_a_board_row_opens_the_player_sheet_and_back_closes_it(browser, page_file):
    """The Slips board's player sheet (2026-10-03) lives in the leg sheet's overlay: Chase Brown's
    work game by game (his log carries usage; his last four games are 2025's, faded only when the
    model's season is a later one -- the fixture's model runs through 2025), then his touchdown and
    rushing lines. Back closes it before the view."""
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='underdog'; GAL_WIN='morning'; render()")
    page.locator("[data-slchip='all']").first.click()
    before = page.evaluate("location.href")
    page.locator(".sl-row[data-slplayer='chase-brown']").click()
    sheet = page.locator("#legsheet.on")
    assert sheet.count() == 1 and page.evaluate("document.activeElement.hasAttribute('data-legclose')")
    old = page.evaluate("BUILD_SEASON") > 2025
    want = [f"2025 W{w}" if old else f"W{w}" for w in (15, 16, 17, 18)]
    assert sheet.locator(".ps-wk").all_inner_texts() == want
    assert sheet.locator(".ps-k").all_inner_texts() == ["Snaps", "Targets", "Carries", "RZ looks"]
    assert sheet.locator(".ps-v.old").count() == (16 if old else 0)
    assert sheet.locator(".sl-mk").all_inner_texts()[0].startswith("Anytime TD") and sheet.locator(".sl-ln:not(.sl-long)").count() == 2
    assert sheet.locator(".sl-long .sl-hist i").all_inner_texts() == ["9", "14", "7", "18"], "his longest catches, history only"
    assert "—" not in sheet.inner_text(), "absent data is not drawn, never a dash"
    assert no_sideways(page)
    page.go_back()
    page.wait_for_function("LEG_SHEET === null")
    assert page.locator("#legsheet.on").count() == 0
    assert page.evaluate("location.href") == before and page.evaluate("SURFACE") == "parlay", "Back closed the sheet, not the view"
    assert errors == []
    ctx.close()


def test_a_longest_reception_leg_sheet_draws_a_missing_catch_as_nothing(browser, page_file):
    """Build's ⓘ on a Longest reception line: a game with no catch logged (null) is an empty bar,
    never a crash, and no chance is printed for a line the model does not price."""
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='build'; PARLAY_BOOK='underdog'; render()")
    i = index(page, "Amon-Ra St. Brown", "LONG")
    page.evaluate(f"LIVE_MARKET.logs['amonra-st-brown'].v.LONG[0] = null; legSheetOpen({i})")
    sheet = page.locator("#legsheet.on")
    assert sheet.locator(".ls-bar").count() >= 1 and sheet.locator(".ls-pct").count() == 0
    assert "null" not in sheet.inner_text() and "NaN" not in sheet.inner_text()
    assert errors == []
    ctx.close()


def test_a_receptions_sheet_with_usage_fits_one_phone_screen(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='dk'; render()")
    i = index(page, "Tee Higgins", "RECS")
    page.evaluate(f"legSheetOpen({i})")
    sheet = page.locator("#legsheet")
    assert sheet.locator(".ls-bar").count() == 10, "the last 10 of his 11 games"
    assert sheet.locator(".ls-cell.drv").count() == 10, "targets under every bar"
    assert sheet.locator(".ls-cap b").inner_text().startswith("Over 4.5 in ")
    tiles = sheet.locator(".ls-tile span").all_inner_texts()
    assert tiles == ["Targets/gm", "Target share", "Catch rate"]
    match = sheet.locator("details.ls-match summary").inner_text()
    assert match.startswith("vs NYJ · allows 5% fewer WR receptions than average") and match.endswith("2 starters out")
    assert not sheet.locator("details.ls-match ul").is_visible(), "the names wait for a tap"
    assert "—" not in sheet.inner_text(), "absent data is not drawn, never a dash"
    assert page.evaluate("document.getElementById('legsheet').getBoundingClientRect().height") <= PHONE[1]
    assert page.evaluate("document.getElementById('legsheet').scrollHeight <= document.getElementById('legsheet').clientHeight")
    assert no_sideways(page)
    assert errors == []
    ctx.close()


def test_on_a_desktop_the_sheet_is_a_centred_dialog(browser, page_file):
    """A desktop has no thumb at the bottom edge (David, 2026-10-03): the sheet sits mid-screen."""
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='dk'; render()")
    page.evaluate(f"legSheetOpen({index(page, 'Tee Higgins', 'RECS')})")
    page.wait_for_timeout(700)
    box = page.evaluate("(() => { const r = document.getElementById('legsheet').getBoundingClientRect(); return [r.top, r.bottom]; })()")
    assert box[0] > 8 and abs((box[0] + box[1]) / 2 - 450) <= 2, box
    assert errors == []
    ctx.close()


def test_a_sheet_without_usage_draws_what_it_has(browser, page_file):
    """No `u` for St. Brown: no row under the bars, the tiles from this season's grid."""
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='dk'; render()")
    page.evaluate(f"legSheetOpen({index(page, 'Amon-Ra St. Brown', 'REC')})")
    sheet = page.locator("#legsheet")
    assert sheet.locator(".ls-bar").count() == 4 and sheet.locator(".ls-cell.drv").count() == 0
    # Yards/target needs his yards in the grid's weeks, and his fixture log ends in 2025: no tile.
    assert sheet.locator(".ls-tile span").all_inner_texts() == ["Targets/gm", "aDOT"]
    assert sheet.locator(".ls-match").count() == 0, "GB allows 2% more: noise, and no starter out, so no line"
    assert "—" not in sheet.inner_text()
    assert errors == []
    ctx.close()



def test_builds_info_button_opens_the_sheet_and_the_row_still_adds(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='build'; render()")
    page.locator(".bline[data-prop] .bl-ev").first.click()
    assert page.locator("#legsheet.on").count() == 1 and page.evaluate("SLIP.length") == 0
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")
    page.locator(".bline[data-prop] .bl-call").first.click()
    assert page.evaluate("SLIP.length") == 1
    assert errors == []
    ctx.close()
