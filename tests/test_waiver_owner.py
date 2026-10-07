"""David's waiver advice shows only in his own browser (data/owner.js, 2026-09-27): everyone else's
Waivers is the league-wide Most added list, with no counts, no FAAB and no waiver rows in search.

Waivers and the roster mount (tests/component.py) and are read through pages/waivers.py. The search half
of the first test is data to data, so it runs in Node (tests/test_js_waiver.py). The wrong-link test needs
a fresh load of the whole page (it is about the address bar), so it is a journey."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster_brief import RosterBrief
from pages.waivers import WaiversPage
from test_render import LOAD_MS, open_page

pytestmark = pytest.mark.render


def test_a_visitor_gets_most_added_and_none_of_davids_advice(mount):
    """The visitor's search holds no waiver rows either: tests/test_js_waiver.py."""
    page, errors = mount("waivers", size=(390, 844))
    waivers = WaiversPage(page)
    waivers.view_as_visitor()
    assert waivers.most_added_count() == waivers.digest_adds_count()
    assert waivers.claim_card_count() == 0 and waivers.claim_row_count() == 0
    hero = waivers.hero_text()
    assert "must-claim" not in hero.lower() and "FAAB" not in hero
    assert waivers.subnav_count_badges() == 0
    assert errors == []


def test_most_added_reads_sleepers_count_when_that_is_the_source(mount):
    """Since 2026-09-28 the Digest's adds are Sleeper's adds over the last day; Most added says so."""
    page, errors = mount("waivers", size=(390, 844))
    waivers = WaiversPage(page)
    waivers.plant_digest({"adds_source": "sleeper", "adds_hours": 24, "adds_weeks": [], "adds": [
        {"n": "Ollie Gordon II", "slug": "ollie-gordon-ii", "pos": "RB", "team": "MIA", "count": 4039301, "was": None,
         "now": None, "delta": None}]})
    waivers.view_as_visitor()
    assert waivers.most_added_counts() == ["4.0M adds"]
    assert waivers.most_added_source() == "Adds on Sleeper, the last 24 hours."
    assert errors == []


def test_a_visitors_roster_has_no_waiver_line(mount):
    page, errors = mount("roster", size=(390, 844))
    waivers = WaiversPage(page)
    waivers.view_as_visitor("roster")
    assert RosterBrief(page).wire_line() == []
    assert errors == []


@pytest.mark.journey
def test_a_wrong_owner_link_unlocks_nothing_and_leaves_the_address_bar(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("localStorage.setItem('tw-owner', '')")
    tab = ctx.new_page()   # a fresh load: a hash change alone does not rerun main.js
    tab.goto(page_file.as_uri() + "#owner-notthetoken", timeout=LOAD_MS)
    waivers = WaiversPage(tab)
    waivers.wait_for_hash("#waivers")
    assert waivers.is_owner() is False
    assert errors == []
    ctx.close()
