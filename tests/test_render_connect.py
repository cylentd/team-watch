"""A connected league in the rendered page. The page is opened from disk, where connectLoad()
asks nothing (PAGE_SERVED is false), so the test hands it a card in api/league.py's shape the way
the GET would. The endpoint itself is covered by test_league.py.

Component tests mount the Roster at 360x780 and add the league through ConnectPage (every locator is in
tests/pages/connect.py). The bookmark's arrival is a journey: it is a fresh page load with `#connect=...` in
the address, and the hash is wiped by that load, so it needs the whole page."""

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.connect import ConnectPage
from test_render import open_page

pytestmark = pytest.mark.render

CARD = {"key": "espn-777", "site": "espn", "league_id": 777, "team_id": 4,
        "league": "Friends League", "name": "Taco Corp", "record": "3-1",
        "roster": [
            {"n": "Brock Purdy", "pos": "QB", "team": "SF", "slot": "QB", "slug": "brock-purdy", "status": None},
            {"n": "Tony Pollard", "pos": "RB", "team": "TEN", "slot": "RB", "slug": "tony-pollard", "status": "Q"},
            {"n": "Jordan Mason", "pos": "RB", "team": "MIN", "slot": "OUT", "slug": "jordan-mason", "status": "OUT"},
            {"n": "Bo Nix", "pos": "QB", "team": "DEN", "slot": "BN", "slug": "bo-nix", "status": None},
        ]}


@pytest.fixture
def phone(mount):
    """The Roster mounted at 360x780 with CARD connected: (ConnectPage, page errors)."""
    page, errors = mount("roster", size=(360, 780))
    connect = ConnectPage(page)
    connect.add_league(CARD)
    return connect, errors


def test_a_connected_league_draws_its_roster_in_groups(phone):
    connect, errors = phone
    assert connect.header_team() == "Taco Corp"
    assert connect.row_count() == 4
    groups = connect.group_headings()
    assert groups[:2] == ["STARTERS", "BENCH"] and groups[2].startswith("OUT")
    assert errors == []


def test_a_connected_league_has_no_waivers(phone):
    connect, _ = phone
    assert "waivers" not in connect.leaves()
    connect.view_waivers_stale()                      # a stale #waivers
    assert connect.waivers_view_count() == 0 and connect.row_count() == 4


def test_the_switch_lists_it_and_offers_to_add_another(phone):
    connect, _ = phone
    connect.open_switch()
    assert any("Taco Corp" in i for i in connect.switch_teams())
    connect.tap_add_a_league()
    assert connect.sheet_is_visible()
    assert connect.league_field_is_visible()
    assert "Taco Corp" in connect.listed_leagues()


@pytest.mark.journey
def test_the_bookmark_hash_is_wiped_on_arrival(browser, page_file):
    """A journey: the bookmark brings the cookies in the address, and arriving is a fresh page load."""
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    try:
        connect = ConnectPage(page)
        connect.arrive_from_bookmark("%7B%22l%22%3A%22%22%2C%22s%22%3A%22x%22%2C%22w%22%3A%22y%22%7D")
        assert connect.hash() == ""
        assert connect.sheet_is_visible()
        assert connect.private_open_count() == 1        # cookies in hand, league link still needed
        assert connect.espn_s2() == "x"
    finally:
        ctx.close()
