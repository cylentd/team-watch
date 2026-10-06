"""Stats > Schedule (#schedule, 2026-10-05, unit U7c): the layout and the taps, in the browser. The ranking, the
bye cell and the empty state are test_js_sos.py, in Node.

Hidden from the sub-row like Weather (NAV_HIDDEN), because Stats' five tabs end at 326 of the 332 px a phone
holds. The control row is one line at 360 px; the first data starts under the heading and the file's label,
which is three lines there, so it sits near 226 px against STYLE.md's ~200 (DESIGN.md "Schedule" says why)."""
import json
import re

import pytest

from test_render import open_at, open_page  # noqa: F401

LABEL = "Context only"


def _page_without_the_file(page_file):
    html = page_file.read_text(encoding="utf-8")
    m = re.search(r"const LIVE_SOS = (.*?);\n", html)
    assert m, "LIVE_SOS is not in the built page"
    out = page_file.with_name("sos-variant.html")
    out.write_text(html[:m.start()] + f"const LIVE_SOS = {json.dumps(None)};\n" + html[m.end():], encoding="utf-8")
    return out


@pytest.mark.render
def test_the_hash_opens_the_view_and_no_sub_button_is_pressed(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    assert page.locator(".navitem[aria-current='true']").get_attribute("data-s") == "scouting"
    assert page.locator("#subnav .mode-sub[aria-pressed='true']").count() == 0
    assert page.evaluate("document.getElementById('view').dataset.view") == "schedule"
    assert page.locator(".sos-row").count() == 32
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_stats_sub_row_keeps_its_five_tabs_inside_the_phone(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    assert page.locator("#subnav .mode-sub").all_inner_texts() == ["Highlights", "Ranks", "Leaders", "Work vs points", "Usage"]
    assert page.evaluate("Math.max(...[...document.querySelectorAll('#subnav .mode-sub')].map(b => b.getBoundingClientRect().right))") <= 360
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("size", [(360, 800), (390, 844)])
def test_the_control_row_is_one_line_and_the_label_is_shown(browser, page_file, size):
    ctx, page, errors = open_at(browser, page_file, size, "#schedule")
    ys = page.evaluate("[...document.querySelectorAll('.sos-ctl .chip')].map(b => Math.round(b.getBoundingClientRect().y))")
    assert len(ys) == 7 and len(set(ys)) == 1, ys                      # position and weeks share one line
    assert LABEL in page.locator(".sos-head p").inner_text()
    assert page.locator(".sos-head p").is_visible()
    first = page.evaluate("document.querySelector('.sos-row').getBoundingClientRect().y")
    assert first <= 240, first                                          # ~200 plus the label's three lines
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("win,weeks", [("next4", 4), ("ros", 13), ("playoffs", 3)])
def test_every_window_fits_a_phone_with_nothing_hidden(browser, page_file, win, weeks):
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    page.click(f"[data-soswin='{win}']")
    assert page.locator(".sos-row").count() == 32
    assert page.locator(".sos-row:first-child .sos-c").count() == weeks
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert page.evaluate("[...document.querySelectorAll('.sos-cells')].every(c => c.scrollWidth <= c.clientWidth)")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_position_and_weeks_redraw_the_heading_and_the_order(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    assert page.locator(".sos-head h2").inner_text() == "Easiest RB schedules, weeks 5–8"
    page.click("[data-sospos='TE']")
    page.click("[data-soswin='playoffs']")
    assert page.locator(".sos-head h2").inner_text() == "Easiest TE schedules, weeks 15–17"
    assert page.locator("[data-sospos='TE']").get_attribute("aria-pressed") == "true"
    assert page.locator("[data-soswin='playoffs']").get_attribute("aria-pressed") == "true"
    pts = page.evaluate("[...document.querySelectorAll('.sos-pts b')].map(b => parseFloat(b.textContent))")
    assert pts == sorted(pts, reverse=True)
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_bye_is_marked_in_its_week(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    byes = page.locator(".sos-c.bye")
    assert byes.count() >= 1
    assert byes.first.inner_text().replace("\n", " ").endswith("BYE")
    assert "bye" in byes.first.get_attribute("aria-label")
    ctx.close()


@pytest.mark.render
def test_a_desktop_joins_the_opponents_to_the_teams_line(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (1280, 900), "#schedule")
    row = page.evaluate("(r => [r.height, document.querySelector('.sos-cells').getBoundingClientRect().y - r.y])(document.querySelector('.sos-row').getBoundingClientRect())")
    assert row[0] < 70 and row[1] < 20, row
    ctx.close()


@pytest.mark.render
def test_no_file_is_a_stated_empty_state_with_no_controls(browser, page_file):
    ctx, page, errors = open_page(browser, _page_without_the_file(page_file), (360, 800))
    page.evaluate("navGo('schedule')")
    assert page.locator(".state-empty").inner_text().startswith("NO SCHEDULE YET")
    assert page.locator(".sos-row").count() == 0 and page.locator(".sos-ctl").count() == 0
    assert errors == []
    ctx.close()
