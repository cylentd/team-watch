"""Stats > Schedule (#schedule, 2026-10-05, unit U7c): the layout and the taps, in the browser. The ranking, the
bye cell and the empty state are test_js_sos.py, in Node.

Component tests (Schedule mounted, tests/component.py; every locator in tests/pages/schedule.py), except the two
journeys: the hash opening a leaf and the Stats sub-row are the nav chrome, so they need the full page.

In the Stats sub-row since 2026-10-06 (hidden like Weather until then: five tabs ended at 326 of the 332 px a
phone holds; the row scrolls sideways as one row now). The control row is one line at 360 px (the weeks alone on a
phone since 2026-10-06: the position is Stats' strip above the bottom bar); the first data starts under the heading
and the file's label,
which is three lines there, so it sits near 226 px against STYLE.md's ~200 (DESIGN.md "Schedule" says why)."""
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.schedule import ScheduleNav, SchedulePage
from pages.statspos import StatsPosStrip
from test_render import open_at

LABEL = "Context only"


@pytest.fixture(scope="module")
def without_file(mount, built, tmp_path_factory):
    """A Schedule mounted on a build whose `const LIVE_SOS` is null (the sos.json file missing): (page, errors).
    It builds on `mount` (same browser), so a test that asks for it is a component test."""
    m = re.search(r"const LIVE_SOS = (.*?);\n", built.fragment)
    assert m, "LIVE_SOS is not in the built page"
    fragment = built.fragment[:m.start()] + "const LIVE_SOS = null;\n" + built.fragment[m.end():]
    mounter = Mounter(mount.browser, tmp_path_factory.getbasetemp() / "component-schedule-nofile", fragment)
    yield lambda: mounter("schedule", size=(360, 800))
    mounter.pages.close()


@pytest.mark.render
@pytest.mark.journey
def test_the_hash_opens_the_view_and_its_sub_button_is_the_pressed_one(browser, page_file):
    """Schedule is in the Stats sub-row again since 2026-10-06 (David, plan dbd T4); it was hidden, so no pill was pressed."""
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    nav, sched = ScheduleNav(page), SchedulePage(page)
    assert nav.group() == "scouting"
    assert nav.pressed_subs() == 1 and nav.pressed_sub_text() == "Schedule"
    assert nav.view() == "schedule"
    assert sched.row_count() == 32
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.journey
def test_the_stats_sub_row_keeps_its_six_tabs_inside_the_phone(browser, page_file):
    """Since 2026-10-05 a phone's tab row is pills that scroll sideways inside the row (chrome/phonenav.css):
    the six are all there (Schedule back in the row, 2026-10-06), and the page itself never scrolls sideways."""
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#schedule")
    nav = ScheduleNav(page)
    assert nav.sub_row() == ["Highlights", "Ranks", "Leaders", "Work vs points", "Usage", "Schedule"]
    assert nav.sub_row_overflow_x() == "auto"
    assert nav.page_scroll_width() <= 360
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("size", [(360, 800), (390, 844)])
def test_the_control_row_is_one_line_and_the_label_is_shown(mount, size):
    page, errors = mount("schedule", size=size)
    sched = SchedulePage(page)
    ys = sched.chip_tops()
    # On a phone the position is Stats' strip above the bottom bar (2026-10-06): the row is the weeks alone.
    assert len(ys) == 3 and len(set(ys)) == 1, ys
    assert StatsPosStrip(page).positions() == ["QB", "RB", "WR", "TE"]
    assert LABEL in sched.label()
    assert sched.label_is_visible()
    first = sched.first_row_top()
    assert first <= 240, first                                          # ~200 plus the label's three lines
    assert sched.overflow() <= 0


@pytest.mark.render
@pytest.mark.parametrize("win,weeks", [("next4", 4), ("ros", 13), ("playoffs", 3)])
def test_every_window_fits_a_phone_with_nothing_hidden(mount, win, weeks):
    page, errors = mount("schedule", size=(360, 800))
    sched = SchedulePage(page)
    sched.pick_window(win)
    assert sched.row_count() == 32
    assert sched.first_row_cell_count() == weeks
    assert sched.overflow() <= 0
    assert sched.cells_fit()
    assert errors == []


@pytest.mark.render
def test_position_and_weeks_redraw_the_heading_and_the_order(mount):
    page, errors = mount("schedule", size=(360, 800))
    sched = SchedulePage(page)
    assert sched.title() == "Easiest RB schedules, weeks 5–8"
    sched.pick_position("TE")
    sched.pick_window("playoffs")
    assert sched.title() == "Easiest TE schedules, weeks 15–17"
    assert sched.position_pressed("TE") == "true"
    assert sched.window_pressed("playoffs") == "true"
    pts = sched.points()
    assert pts == sorted(pts, reverse=True)
    assert errors == []


@pytest.mark.render
def test_a_bye_is_marked_in_its_week(mount):
    page, errors = mount("schedule", size=(360, 800))
    sched = SchedulePage(page)
    assert sched.bye_count() >= 1
    bye = sched.first_bye()
    assert bye["text"].endswith("BYE")
    assert "bye" in bye["aria"]


@pytest.mark.render
def test_a_desktop_joins_the_opponents_to_the_teams_line(mount):
    page, errors = mount("schedule", size=(1280, 900))
    row = SchedulePage(page).first_row_shape()
    assert row[0] < 70 and row[1] < 20, row


@pytest.mark.render
def test_no_file_is_a_stated_empty_state_with_no_controls(without_file):
    page, errors = without_file()
    sched = SchedulePage(page)
    assert sched.empty_text().startswith("NO SCHEDULE YET")
    assert sched.row_count() == 0 and sched.control_count() == 0
    assert errors == []
