"""A connected league in the rendered page. The page is opened from disk, where connectLoad()
asks nothing (PAGE_SERVED is false), so the test hands it a card in api/league.py's shape the way
the GET would. The endpoint itself is covered by test_league.py."""

import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

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
def phone(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate("card => { connectAdd(card); VIEW = card.key; SURFACE = 'roster'; paintSubnav(); render(); }", CARD)
    yield page, errors
    ctx.close()


def test_a_connected_league_draws_its_roster_in_groups(phone):
    page, errors = phone
    assert page.locator(".ts-team").inner_text().strip() == "Taco Corp"
    assert page.locator(".row").count() == 4
    groups = [h.inner_text().strip().upper() for h in page.locator(".rule h2").all()]
    assert groups[:2] == ["STARTERS", "BENCH"] and groups[2].startswith("OUT")
    assert errors == []


def test_a_connected_league_has_no_waivers(phone):
    page, _ = phone
    assert page.locator("[data-leaf='waivers']").count() == 0
    page.evaluate("SURFACE = 'waivers'; render()")          # a stale #waivers
    assert page.locator(".wv").count() == 0 and page.locator(".row").count() == 4


def test_the_switch_lists_it_and_offers_to_add_another(phone):
    page, _ = phone
    page.click("[data-tsbtn]")
    items = [b.inner_text() for b in page.locator(".ts-item").all()]
    assert any("Taco Corp" in i for i in items)
    page.click("[data-tsadd]")
    assert page.locator("#connect").is_visible()
    assert page.locator("#cn-league").is_visible()
    assert "Taco Corp" in page.locator(".cn-list").inner_text()


def test_the_bookmark_hash_is_wiped_on_arrival(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.goto(page.url.split("#")[0] + "#connect=" + "%7B%22l%22%3A%22%22%2C%22s%22%3A%22x%22%2C%22w%22%3A%22y%22%7D")
    page.reload()
    assert page.evaluate("location.hash") == ""
    assert page.locator("#connect").is_visible()
    assert page.locator(".cn-private[open]").count() == 1        # cookies in hand, league link still needed
    assert page.locator("#cn-s2").input_value() == "x"
    ctx.close()
