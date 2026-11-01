"""S16 (David approved 2026-10-31): a reader opens News, Schedule, Search or another Players view, and the view draws its
data, and every leaf is reachable from the row or by hash.

The hash half is test_render.py::test_a_hash_opens_its_view, which lists every leaf. This file is the other two halves
for the views no test read: Schedule draws the fixture's own first team, points and opponents (tests/fixtures/data/sos.json),
and a Leaders card or row and a Usage row each open the profile of the player they name."""
import json
from pathlib import Path

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.profile import ProfilePage
from wording import words

pytestmark = pytest.mark.render

SOS = json.loads((Path(__file__).parent / "fixtures" / "data" / "sos.json").read_text(encoding="utf-8"))

# (view, the element a reader taps, the element inside it that names the player)
ROWS = [
    ("board", ".bd-hero", ".bd-hero-who b"),
    ("board", ".bd-row", ".bd-nm"),
    ("usage", ".urow", ".uname b"),
]


@pytest.mark.parametrize("view,tap,name", ROWS)
def test_s16_a_leaders_or_usage_row_opens_the_profile_of_the_player_it_names(mount, view, tap, name):
    page, errors = mount(view, size=(1280, 900))
    row = page.locator(tap).first
    shown = row.locator(name).first.inner_text().strip()
    row.click()
    title = ProfilePage(page).title()
    surname = shown.split(". ", 1)[-1]        # a row says "O. Hampton", the profile says "Omarion Hampton"
    assert title.upper().endswith(surname.upper()) and title[0].upper() == shown[0].upper(), f"{shown!r} opened {title!r}"
    assert errors == []


def test_s16_schedule_draws_the_easiest_team_with_the_points_and_opponents_the_file_holds(mount):
    page, errors = mount("schedule", size=(1280, 900))
    easiest = next(code for code, t in SOS["teams"].items() if t["RB"]["next4"]["rank"] == 1)
    first = page.get_by_test_id("schedule-row").first
    assert first.locator(".sos-team").inner_text() == easiest
    assert first.get_by_test_id("schedule-pts-value").inner_text() == f"{SOS['teams'][easiest]['RB']['next4']['pts_pg']:.1f}"
    week = SOS["teams"][easiest]["schedule"]["next4"]
    opponent = {o["week"]: o["opp"] for o in week["opps"]}
    assert first.locator("[data-testid=schedule-cell] b").all_inner_texts() == [
        words("sos.cell.bye") if w in week["bye"] else opponent[w] for w in SOS["windows"]["next4"]]
    assert errors == []
