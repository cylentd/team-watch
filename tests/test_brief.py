"""The roster's "This week" checklist (2026-09-25): a line per thing to check, the lineup check
always among them; a phone shows three and "Show all", a desktop every line beside the rows."""

import pytest

from test_render import drive, go, open_page  # noqa: F401


def lines(page):
    return page.evaluate("[...document.querySelectorAll('.brief-line')].map(e => ({kind: e.className.match(/k-(\\w+)/)[1], shown: e.offsetParent !== null}))")


def unfold(page):
    """On a phone the Week plays reel folds the list to its one row; Show opens it."""
    if page.locator("[data-briefunfold]").count():
        page.locator("[data-briefunfold]").click()


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
    unfold(page)
    got = lines(page)
    if len(got) <= 3:
        assert page.locator("[data-briefall]").count() == 0
        pytest.skip("the fixture's roster has three things or fewer to check")
    assert sum(x["shown"] for x in got) == 3
    page.locator("[data-briefall]").click()
    assert all(x["shown"] for x in lines(page))
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_got_it_folds_the_list_and_a_reload_keeps_it(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    drive(page, go("roster"))
    unfold(page)
    n = len(lines(page))
    page.locator("[data-briefok]").click()
    assert lines(page) == [] and page.locator(".brief.done").count() == 1
    page.reload()
    drive(page, go("roster"))
    assert page.locator(".brief.done").count() == 1, "checked lines stay checked this week"
    page.locator(".brief.done [data-briefpeek]").click()
    assert len(lines(page)) == n, "and come back on Show"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_swipe_checks_one_line(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    drive(page, go("roster"))
    unfold(page)
    n = len(lines(page))
    box =page.locator(".brief-line").first.bounding_box()
    y = box["y"] + box["height"] / 2
    page.mouse.move(box["x"] + 40, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .8, y, steps=6)
    page.mouse.up()
    page.wait_for_timeout(100)
    assert len(lines(page)) == n - 1
    assert page.locator("[data-briefpeek]").count() == 1, "the checked line is one tap away"
    assert page.locator("#modal.on").count() == 0, "a swipe is not a tap: no profile opened"
    assert errors == []
    ctx.close()


SITS = """(n) => { LIVE_INJURY.players = {};
  for (const tm of Object.values(TEAMS)){
    tm.roster.forEach(p => { p.status = null; });
    tm.roster.filter(p => p.start && p.slug && !['K','DST'].includes(p.pos)).slice(0, n)
      .forEach(p => { LIVE_INJURY.players[p.slug] = {s: 'OUT', code: 'IR', note: 'Knee'}; });
  }
  VIEW = 'espn'; ROSTER_MODE = __MODE__; render(); }"""


@pytest.mark.render
@pytest.mark.parametrize("mode", ["sheet", "cards"])
def test_a_starter_who_will_sit_is_a_red_pill_in_the_week_row_not_a_strip(browser, page_file, mode):
    """2026-10-05: the full-width strip above the roster became a pill in the "This week" row, on a
    phone (the folded row under the reel) and on a desktop (the column's heading)."""
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    drive(page, go("roster"))
    page.evaluate("packMark(TEAMS.espn, schedWeek())")
    page.evaluate(SITS.replace("__MODE__", f"'{mode}'"), 1)
    pill = page.locator(".brief-h .inj-warn")
    assert pill.count() == 1 and pill.inner_text() == "B. Purdy out" and "Knee" in pill.get_attribute("title")
    assert page.locator("div.inj-warn").count() == 0, "no strip above the roster"
    head, box = page.locator(".brief-h").bounding_box(), pill.bounding_box()
    assert head["y"] <= box["y"] and box["y"] + box["height"] <= head["y"] + head["height"] and box["x"] + box["width"] <= 360, "inside the row, on screen"
    assert page.evaluate("""() => { const p = document.querySelector('.inj-warn'), probe = document.createElement('i');
      probe.style.color = 'var(--down)'; document.body.append(probe);
      const same = getComputedStyle(p).color === getComputedStyle(probe).color; probe.remove(); return same; }"""), "red, the app's down colour"
    unfold(page)
    assert page.locator(".brief-h .inj-warn").count() == 1, "the open list keeps it"
    page.evaluate(SITS.replace("__MODE__", f"'{mode}'"), 2)
    assert page.locator(".brief-h .inj-warn").inner_text() == "2 starters out", "several: one pill with the count"
    page.evaluate(SITS.replace("__MODE__", f"'{mode}'"), 0)
    assert page.locator(".inj-warn").count() == 0, "a clean lineup has none"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_sit_pill_sits_in_the_desktop_columns_heading(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    drive(page, go("roster"))
    page.evaluate(SITS.replace("__MODE__", "'sheet'"), 2)
    head, box = page.locator(".brief-h").bounding_box(), page.locator(".brief-h .inj-warn").bounding_box()
    assert head["y"] <= box["y"] and box["y"] + box["height"] <= head["y"] + head["height"], "one line, with Got it"
    assert page.locator("[data-briefok]").bounding_box()["y"] < head["y"] + head["height"]
    assert errors == []
    ctx.close()


def test_a_bench_player_fits_the_slots_his_position_can_fill(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    fits = page.evaluate("""[briefFits('RB2','RB'), briefFits('FLEX','WR'), briefFits('FLX','QB'),
      briefFits('WR1','RB'), briefFits('OP','QB'), briefFits('TE','TE')]""")
    assert fits == [True, True, False, False, True, True]
    assert errors == []
    ctx.close()
