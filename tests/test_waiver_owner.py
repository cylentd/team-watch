"""David's waiver advice shows only in his own browser (data/owner.js, 2026-09-27): everyone else's
Waivers is the league-wide Most added list, with no counts, no FAAB and no waiver rows in search."""
import pytest

from test_render import browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render


def _as_visitor(page, leaf="waivers"):
    page.evaluate(f"localStorage.setItem('tw-owner', ''); SURFACE = '{leaf}'; SEARCH_INDEX = null; render(); paintSubnav()")


def test_a_visitor_gets_most_added_and_none_of_davids_advice(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    _as_visitor(page)
    adds = page.evaluate("(dgD() || {adds: []}).adds.length")
    assert page.locator(".wv-hot li").count() == adds
    assert page.locator(".wvc").count() == 0 and page.locator(".wvr-row").count() == 0
    hero = page.locator(".wvhero").inner_text()
    assert "must-claim" not in hero.lower() and "FAAB" not in hero
    assert page.locator("#subnav .tabcount").count() == 0
    assert page.evaluate("searchSources().filter(([, src]) => src === 'market').length") == \
        page.evaluate("searchSources().length - searchSources().filter(([, s]) => s !== 'market').length")
    assert page.evaluate("waiverPlayers().every(w => !searchSources().some(([p]) => p === w))")
    assert errors == []
    ctx.close()


def test_a_visitors_roster_has_no_waiver_line(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    _as_visitor(page, "roster")
    assert page.evaluate("briefWire(TEAMS[VIEW])") == []
    assert errors == []
    ctx.close()


def test_a_wrong_owner_link_unlocks_nothing_and_leaves_the_address_bar(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("localStorage.setItem('tw-owner', '')")
    tab = ctx.new_page()   # a fresh load: a hash change alone does not rerun main.js
    tab.goto(page_file.as_uri() + "#owner-notthetoken")
    tab.wait_for_function("location.hash === '#waivers'", timeout=5000)
    assert tab.evaluate("isOwner()") is False
    assert errors == []
    ctx.close()
