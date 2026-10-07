"""The roster's "This week" checklist (2026-09-25): a line per thing to check, the lineup check
always among them; a phone shows three and "Show all", a desktop every line beside the rows.

Component tests (2026-10-06): the roster mounted (`mount`), read through `RosterBrief`
(tests/pages/roster_brief.py)."""

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster_brief import RosterBrief

PHONE = (360, 800)
DESKTOP = (1280, 900)


def on_roster(mount, size):
    """The roster mounted at a size, read through the list's page object: (RosterBrief, errors)."""
    page, errors = mount("roster", size=size)
    return RosterBrief(page), errors


@pytest.mark.render
@pytest.mark.parametrize("view", ["yahoo", "espn"])
def test_the_lineup_check_is_always_there(mount, view):
    brief, errors = on_roster(mount, DESKTOP)
    brief.show(view)
    got = brief.lines()
    assert brief.kinds().count("lu") == 1, got
    assert [x for x in got if not x["shown"]] == [], "a desktop shows every line"
    assert errors == []


@pytest.mark.render
def test_a_phone_shows_three_then_all(mount):
    brief, errors = on_roster(mount, PHONE)
    brief.unfold()
    got = brief.lines()
    assert len(got) > 3, f"the fixture's roster has more than three things to check, not {len(got)}"
    assert sum(x["shown"] for x in got) == 3
    brief.show_all()
    assert all(x["shown"] for x in brief.lines())
    assert errors == []


@pytest.mark.render
def test_got_it_folds_the_list_and_a_reload_keeps_it(mount):
    brief, errors = on_roster(mount, PHONE)
    brief.unfold()
    n = len(brief.lines())
    brief.got_it()
    assert brief.lines() == [] and brief.folded() == 1
    brief.reload()
    assert brief.folded() == 1, "checked lines stay checked this week"
    brief.show_checked()
    assert len(brief.lines()) == n, "and come back on Show"
    assert errors == []


@pytest.mark.render
def test_a_swipe_checks_one_line(mount):
    brief, errors = on_roster(mount, PHONE)
    brief.unfold()
    n = len(brief.lines())
    brief.swipe_first_line()
    brief.wait_for_line_count(n - 1)
    assert len(brief.lines()) == n - 1
    assert brief.peek_buttons() == 1, "the checked line is one tap away"
    assert not brief.profile_open(), "a swipe is not a tap: no profile opened"
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("mode", ["sheet", "cards"])
def test_a_starter_who_will_sit_is_a_red_pill_in_the_week_row_not_a_strip(mount, mode):
    """2026-10-05: the full-width strip above the roster became a pill in the "This week" row, on a
    phone (the folded row under the reel) and on a desktop (the column's heading)."""
    brief, errors = on_roster(mount, PHONE)
    brief.open_pack()
    brief.plant_sits(1, mode)
    pill = brief.sit_pill()
    assert pill["count"] == 1 and pill["text"] == "B. Purdy out" and "Knee" in pill["title"]
    assert brief.sit_strips() == 0, "no strip above the roster"
    fit = brief.pill_inside_head()
    assert fit["inside"] and fit["right"] <= 360, "inside the row, on screen"
    assert brief.pill_is_down_colour(), "red, the app's down colour"
    brief.unfold()
    assert brief.sit_pill()["count"] == 1, "the open list keeps it"
    brief.plant_sits(2, mode)
    assert brief.sit_pill()["text"] == "2 starters out", "several: one pill with the count"
    brief.plant_sits(0, mode)
    assert brief.warn_count() == 0, "a clean lineup has none"
    assert errors == []


@pytest.mark.render
def test_the_sit_pill_sits_in_the_desktop_columns_heading(mount):
    brief, errors = on_roster(mount, DESKTOP)
    brief.plant_sits(2, "sheet")
    assert brief.pill_inside_head()["inside"], "one line, with Got it"
    head = brief.head_box()
    assert brief.got_it_box()["y"] < head["y"] + head["height"]
    assert errors == []


def test_a_bench_player_fits_the_slots_his_position_can_fill(mount):
    brief, errors = on_roster(mount, DESKTOP)
    fits = brief.fits([("RB2", "RB"), ("FLEX", "WR"), ("FLX", "QB"), ("WR1", "RB"), ("OP", "QB"), ("TE", "TE")])
    assert fits == [True, True, False, False, True, True]
    assert errors == []
