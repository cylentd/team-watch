"""The roster's "This week" checklist (2026-09-25): a line per thing to check, the lineup check
always among them; a phone shows three and "Show all", a desktop every line beside the rows."""

import pytest

from test_render import browser, drive, go, open_page  # noqa: F401  (browser is a fixture)


def lines(page):
    return page.evaluate("[...document.querySelectorAll('.brief-line')].map(e => ({kind: e.className.match(/k-(\\w+)/)[1], shown: e.offsetParent !== null}))")


@pytest.mark.render
def test_the_lineup_check_is_always_there(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    for view in ("yahoo", "espn"):
        drive(page, go("roster"))
        page.evaluate(f"VIEW='{view}'; render()")
        got = lines(page)
        assert [x["kind"] for x in got].count("lu") == 1, got
        assert all(x["shown"] for x in got), "a desktop shows every line"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_phone_shows_three_then_all(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    drive(page, go("roster"))
    got = lines(page)
    if len(got) <= 3:
        assert page.locator("[data-briefall]").count() == 0
        pytest.skip("the fixture's roster has three things or fewer to check")
    assert sum(x["shown"] for x in got) == 3
    page.locator("[data-briefall]").click()
    assert all(x["shown"] for x in lines(page))
    assert errors == []
    ctx.close()


def test_a_bench_player_fits_the_slots_his_position_can_fill(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    fits = page.evaluate("""[briefFits('RB2','RB'), briefFits('FLEX','WR'), briefFits('FLX','QB'),
      briefFits('WR1','RB'), briefFits('OP','QB'), briefFits('TE','TE')]""")
    assert fits == [True, True, False, False, True, True]
    assert errors == []
    ctx.close()
