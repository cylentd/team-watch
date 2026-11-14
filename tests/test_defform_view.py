"""Defense form, drawn (2026-11-14): a note on Schedule's team rows, lines in Preview's box score. Context only:
form failed as a price (ff-jarvis METHODOLOGY 12.73), so no word of it says start, sit, bet or fade. Which form a
row or a game reads is Node's (test_js_defform.py); this file proves the screen draws it, in words as well as colour.

The fixture's `defense_recent`: CIN allowing more to backs (points), JAX allowing more on the ground (rush yards),
NYJ allowing less to backs, LA allowing less to receivers, LV under 3 games (no form). Schedule's week 5: MIA plays
CIN, PHI plays JAX, CLE plays NYJ, NE plays LV. Preview's game 1 is JAX @ LA; game 0, PIT @ CLE, has no form.
"""
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.defform import PreviewForm, ScheduleForm
from pages.preview import PreviewPage
from pages.schedule import SchedulePage
from wording import words

VERDICT = re.compile(r"\b(start|sit|bet|fade|lean|lock|smash|avoid|target|buy|sell)(s|ing)?\b", re.I)
UP, DOWN = words("dform.trend.up"), words("dform.trend.down")


@pytest.fixture(scope="module")
def no_file(mount, built, tmp_path_factory):
    """Preview on a page with no sos.json (`const LIVE_SOS = null`), built on `mount` so it stays a component test."""
    fragment = re.sub(r"^const LIVE_SOS = .*;$", "const LIVE_SOS = null;", built.fragment, flags=re.M)
    assert fragment != built.fragment, "the fixture build injects no LIVE_SOS to remove"
    m = Mounter(mount.browser, tmp_path_factory.getbasetemp() / "component-no-sos-form", fragment)
    yield m
    m.pages.close()


@pytest.mark.req("Schedule", ac="a row says its next opponent's form in words, and marks that opponent")
def test_a_row_says_allowing_more_or_less_and_marks_its_next_opponent(mount):
    page, errors = mount("schedule", size=(360, 800))
    form = ScheduleForm(page)
    notes, cells = form.notes(), form.marked_cells()
    up, down = words("dform.vs.up"), words("dform.vs.down")     # the note names the foe, not the row's team
    assert (notes["MIA"], notes["PHI"], notes["CLE"]) == (up.format(df="CIN"), up.format(df="JAX"), down.format(df="NYJ"))
    assert (cells["MIA"], cells["PHI"], cells["CLE"]) == (f"5 CIN{words('dform.arrow.up')}", f"5 JAX{words('dform.arrow.up')}",
                                                          f"5 NYJ{words('dform.arrow.down')}")
    assert "NE" not in notes and "NE" not in cells              # LV has 2 games: never a short average
    assert form.note("CLE")["trend"] == "down"
    assert errors == []


@pytest.mark.req("Schedule", ac="the note's numbers and the context mark are one tap of the tip away")
def test_the_note_tip_holds_the_files_two_numbers_and_the_context_mark(mount):
    page, errors = mount("schedule", size=(360, 800))
    tip = ScheduleForm(page).note("MIA")["tip"]
    assert "24.3" in tip and "19.1" in tip
    assert words("dform.markTip") in tip
    assert not VERDICT.search(tip)


@pytest.mark.req("Schedule", ac="the note keeps a phone row to two lines")
def test_the_note_fits_the_rows_first_line_at_360(mount):
    page, errors = mount("schedule", size=(345, 800))           # 360 less the 15px scrollbar a real phone browser draws
    form = ScheduleForm(page)
    assert (form.note_cut("MIA"), form.note_cut("CLE")) == (0, 0)  # the words show whole, on the team's line
    assert form.row_height("CLE") == form.row_height("NE")      # a note row is as tall as a games-count row (rows 4 and 2)
    assert SchedulePage(page).overflow() <= 0


@pytest.mark.req("Schedule", ac="a window that starts after this week draws no form")
def test_the_playoff_weeks_draw_no_note(mount):
    page, errors = mount("schedule", size=(360, 800))
    SchedulePage(page).pick_window("playoffs")
    assert ScheduleForm(page).note_count() == 0
    assert errors == []


@pytest.mark.req("Preview", ac="the box score says each defense's form, its two numbers and the trend in words")
def test_the_game_lists_each_flagged_defense_away_offense_first(mount):
    page, errors = mount("preview")
    PreviewPage(page).show_game(1)
    form = PreviewForm(page)
    assert form.lines() == [
        [words("preview.form.who.pts").format(df="LA", pos="WR") + f" {DOWN}",
         words("preview.form.pts").format(last="14.0", pos="WR", season="19.5")],
        [words("preview.form.who.rush").format(df="JAX") + f" {UP}",
         words("preview.form.rush").format(last="112", season="68")]]
    assert form.trends() == ["down", "up"]
    assert form.mark() == (words("dform.mark"), words("dform.markTip"))
    assert errors == []


@pytest.mark.req("Preview", ac="a game whose defenses flagged nothing draws no form section")
def test_a_game_with_no_flag_draws_no_section(mount):
    page, errors = mount("preview")
    PreviewPage(page).show_game(0)
    assert PreviewForm(page).section_count() == 0
    assert errors == []


@pytest.mark.req("Preview", ac="no sos.json draws the game whole with no form")
def test_no_file_draws_the_game_with_no_form(no_file):
    page, errors = no_file("preview")
    PreviewPage(page).show_game(1)
    assert PreviewForm(page).section_count() == 0
    assert errors == []
