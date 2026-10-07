"""Signed weeks are gold bars (David, 2026-10-07): every week a player finished top 3 at his position is a full
gold bar on his Sheet row and on his card's back (its points in gold, no star). Pure parts: test_js_goldweeks.py
and test_signed_weeks.py. Component layer: `mount`, `GoldBars` (tests/pages/roster_gold.py)."""
import re

import pytest

from component import Mounter, mount as base_mount
from pages.roster_gold import GoldBars
from pages.roster_motion import show_cards

REQ = "Phone layout"
PHONE = (360, 660)
SCENE = {"games": [{"week": 5, "home": "SF", "away": "ARI", "kickoff": "2026-10-11T20:05:00Z"}],
         "factors": {}, "form": {}, "weather": {"SF": {"roof": "dome"}}}


@pytest.fixture(scope="module")
def mount(base_mount, built):
    """`mount` over the same build with an empty LIVE_SIGNED for week 3 (the fixtures log too few teams for a
    completed week); its own folder, its context and cold first load the module's setup."""
    text, n = re.subn(r"^const LIVE_SIGNED = .*;$", 'const LIVE_SIGNED = {"wk": 3, "players": {}, "weeks": {}};', built.fragment, count=1, flags=re.M)
    assert n == 1
    m = Mounter(base_mount.browser, base_mount.folder / "gold", text)
    m.prepare("roster", size=PHONE)
    yield m
    m.pages.close()


@pytest.fixture
def sheet(mount):
    page, errors = mount("roster", size=PHONE)
    roster = GoldBars(page)
    roster.show("espn")
    roster.plant_points("brock-purdy", {1: 10.4, 2: 27.0, 3: 20.6, 4: 9.5}, 18.6)
    roster.plant(SCENE)
    yield roster
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a row's bars are gold on exactly the weeks he finished top three, never the projection")
def test_a_row_draws_gold_bars_on_exactly_the_signed_weeks(sheet):
    sheet.plant_weeks({"brock-purdy": [2, 4]})
    got = sheet.row_gold("B. Purdy")
    assert got["signed"] == [False, True, False, True, False]
    assert got["painted"] == got["signed"], "the signed bars are the gold token, full strength, the latest week included"


@pytest.mark.render
@pytest.mark.req(REQ, ac="a row with no signed weeks has no gold")
def test_a_row_without_signed_weeks_has_no_gold(sheet):
    sheet.plant_weeks({})
    got = sheet.row_gold("B. Purdy")
    assert got["signed"] == [False] * 5 and got["painted"] == [False] * 5


@pytest.fixture
def backs(mount):
    page, errors = mount("roster", size=PHONE)
    roster = GoldBars(page)
    assert show_cards(roster, "espn", "skip") == 1
    roster.plant(SCENE)
    yield roster
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a card's back draws a gold bar and gold points on exactly the signed weeks, and no star")
def test_a_back_draws_gold_bars_on_exactly_the_signed_weeks(backs):
    got = backs.gold_back([1, 3])
    assert got["signed"] == [True, False, True, False, False]
    assert got["painted"] == got["signed"] and got["points"] == got["signed"]
    assert got["stars"] == 0
