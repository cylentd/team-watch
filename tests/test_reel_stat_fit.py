"""The Week plays card's stat line at 360px (David, 2026-10-07: "7-25-0" reads as a date). The words are
tested in Node (test_js_weekstat.py); this proves the screen: the line is words with units, it fits the card
whole (never cut with an ellipsis), and a narrower card drops the smaller yardage kind and keeps the touchdowns.
Runs on the ESPN fixture team: Purdy (QB), Kittle (TE) and C. Brown (RB) each have a card."""
import time

import pytest

from component import mount as base_mount  # noqa: F401  (the fixture, `mount` below)
from pages.reel_stat import ReelStatPage
from pages.warm import warm

PHONE = (360, 800)
BIG_WEEK = {
    "brock-purdy": {"pass_yds": 288, "pass_td": 2, "rush_yds": 31, "rush_td": 0},
    "george-kittle": {"rec": 7, "rec_yds": 81, "rec_td": 0, "tgt": 9},
    "chase-brown": {"car": 22, "rush_yds": 128, "rush_td": 1, "rec": 8, "rec_yds": 104, "rec_td": 1, "tgt": 9},
}


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the phone's context opened once for the module (pages/warm.py)."""
    return warm(base_mount, ("roster", PHONE))


def planted(mount):
    page, errors = mount("roster", size=PHONE)
    rail = ReelStatPage(page)
    rail.show(mode="cards", pack_opened=True)
    return rail, errors


def by_name(lines):
    return {x["nm"]: x for x in lines}


@pytest.mark.req("Clips", ac="the stat line says yards with a unit and fits the card whole")
def test_the_longest_line_fits_its_card_whole_at_360px(mount):
    rail, errors = planted(mount)
    start = time.perf_counter()
    rail.plant_box_scores(BIG_WEEK)
    got = by_name(rail.lines())
    took = time.perf_counter() - start
    assert [x["fits"] for x in got.values()] == [True] * 3, got
    assert got["C. Brown"]["text"].startswith("128 rush yds") and got["C. Brown"]["text"].endswith("2 TD"), got["C. Brown"]
    assert got["B. Purdy"]["text"].startswith("288 pass yds") and got["B. Purdy"]["text"].endswith("2 TD"), got["B. Purdy"]
    assert got["G. Kittle"]["text"] == "81 rec yds", "no touchdown, no TD text"
    assert took < 0.2, f"{took * 1000:.0f} ms"
    assert errors == []


def test_no_line_is_a_date_shaped_run_of_numbers_or_a_count(mount):
    rail, errors = planted(mount)
    rail.plant_box_scores(BIG_WEEK)
    texts = [x["text"] for x in rail.lines()]
    assert not [s for s in texts if "tgt" in s or "-" in s], texts
    assert errors == []


def test_a_narrower_card_drops_the_smaller_kind_and_keeps_the_touchdowns(mount):
    rail, errors = planted(mount)
    rail.plant_box_scores(BIG_WEEK)
    rail.narrow_to(60)
    got = by_name(rail.lines())
    assert got["C. Brown"]["text"] == "2 TD", got["C. Brown"]
    assert got["B. Purdy"]["text"] == "2 TD", got["B. Purdy"]
    assert got["G. Kittle"]["text"] == "81 rec yds", "with no touchdown the biggest kind stays, even when it does not fit"
    assert errors == []
