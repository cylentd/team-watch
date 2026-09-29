"""The leg sheet and the TD board (2026-09-27). A pick on a slip, a Build line's info button or a
TD board row opens one bet from the bottom edge: the last ten games against the line, three
tiles, the matchup as one line, and Add. Back closes it before it changes the view. The fixture
gives Tee Higgins and Chase Brown per-game usage (`u`) and Amon-Ra St. Brown none, and a defense
block in which NYJ has two starters out."""
import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render

PHONE = (360, 780)


def index(page, name, mkt):
    return page.evaluate(f"PROPS.findIndex(p => p.n === {name!r} && p.mkt === {mkt!r})")


def no_sideways(page):
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_a_slip_pick_opens_its_sheet_and_back_closes_it(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='underdog'; render()")
    legs = page.locator(".ticket .tk-leg[data-legsheet]")
    if legs.count() == 0:
        pytest.skip("the fixture's market builds no gallery slip")
    k = page.evaluate("[...document.querySelectorAll('.ticket .tk-leg')].findIndex(el => legLog(PROPS[+el.dataset.legsheet]))")
    assert k >= 0, "some slip pick has a game log"
    before = page.evaluate("location.href")
    legs.nth(k).click()
    sheet = page.locator("#legsheet.on")
    assert sheet.count() == 1 and page.evaluate("document.activeElement.hasAttribute('data-legclose')")
    assert sheet.locator(".ls-bar").count() >= 1 and sheet.locator(".ls-tiles .ls-tile").count() >= 1
    assert no_sideways(page)
    page.go_back()
    page.wait_for_function("LEG_SHEET === null")
    assert page.locator("#legsheet.on").count() == 0
    assert page.evaluate("location.href") == before and page.evaluate("SURFACE") == "parlay", "Back closed the sheet, not the view"
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
    assert match.startswith("vs NYJ · allows 0.95× WR receptions") and match.endswith("2 starters out")
    assert not sheet.locator("details.ls-match ul").is_visible(), "the names wait for a tap"
    assert "—" not in sheet.inner_text(), "absent data is not drawn, never a dash"
    assert page.evaluate("document.getElementById('legsheet').getBoundingClientRect().height") <= PHONE[1]
    assert page.evaluate("document.getElementById('legsheet').scrollHeight <= document.getElementById('legsheet').clientHeight")
    assert no_sideways(page)
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
    assert sheet.locator("p.ls-match").inner_text() == "vs GB · allows 1.02× WR rec yds", "GB has no starter out"
    assert "—" not in sheet.inner_text()
    assert errors == []
    ctx.close()


def test_the_td_board_ranks_by_the_model_and_opens_the_sheet(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='underdog'; render()")
    page.locator("[data-scope='tds']").click()
    rows = page.locator(".tdb-row[data-legsheet]")
    assert rows.count() >= 2
    model = [int(x.rstrip("%")) for x in page.locator(".tdb-row[data-legsheet] .tdb-model").all_inner_texts()]
    assert model == sorted(model, reverse=True)
    assert page.evaluate("[...document.querySelectorAll('.tdb-row[data-legsheet]')].every(el => { const p = PROPS[+el.dataset.legsheet]; return p.mkt === 'TD' && playing(p) && upcoming(p); })")
    assert no_sideways(page)
    rows.first.click()
    sheet = page.locator("#legsheet.on")
    assert sheet.count() == 1 and sheet.locator(".ls-cap b").inner_text().startswith("Scored in ")
    i = int(rows.first.get_attribute("data-legsheet"))
    sheet.locator("[data-legadd]").click()
    page.wait_for_function("LEG_SHEET === null")
    assert page.evaluate("SLIP") == [i], "Add is the Build tap's own path into the slip"
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
