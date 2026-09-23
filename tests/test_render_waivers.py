"""Waivers v2 in Chromium: the league filter, the two weekday modes, the rail's order, the flip,
and the once-only motion. Same pinned inputs as test_render.py: fixture page, Date.now pinned
(SEED is a Saturday, so wire-watch mode unless a test pins a Tuesday)."""
import re

import pytest

from test_render import SEED, TUESDAY

pytestmark = pytest.mark.render


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def open_waivers(browser, page_file):
    """open_waivers(view=, init=, reduced=, width=) -> page on #waivers for that league."""
    ctxs = []

    def go(view="espn", init="", reduced=True, width=390):
        ctx = browser.new_context(viewport={"width": width, "height": 844},
                                  reduced_motion="reduce" if reduced else "no-preference")
        ctxs.append(ctx)
        page = ctx.new_page()
        page.set_default_timeout(5000)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.route(re.compile(r"^https?://"), lambda route: route.abort())
        page.add_init_script(SEED)
        if init:
            page.add_init_script(init)
        page.goto(page_file.as_uri() + "#waivers")
        page.wait_for_function("document.querySelector('#view .wv')")
        if view != "yahoo":
            page.locator("[data-tsbtn]").click()
            page.locator(f".ts-item[data-k='{view}']").click()
        page.errors = errors
        return page

    yield go
    for c in ctxs:
        c.close()


def _cards(page):
    return page.evaluate("""[...document.querySelectorAll('.wv-cards .wvc')].map(c =>
        [c.querySelector('h3').textContent, c.querySelector('.wvc-stamp').textContent])""")


def test_the_league_filter_follows_the_team_switch(open_waivers):
    """Parker Washington is rostered in Yahoo, so he is an ESPN card only; Emanuel Wilson is
    Must claim in ESPN and Worth a claim in Yahoo (the packet's per-league tier)."""
    page = open_waivers("espn")
    espn = dict(_cards(page))
    assert espn["Emanuel Wilson"] == "Must claim" and "Parker Washington" in espn
    assert page.locator(".wvr-row").count() == 5
    assert "2 must-claims" in page.locator(".wvhero").inner_text()
    # Switch in place, the way a reader does.
    page.locator("[data-tsbtn]").click()
    page.locator(".ts-item[data-k='yahoo']").click()
    yahoo = dict(_cards(page))
    assert yahoo["Emanuel Wilson"] == "Worth a claim" and "Parker Washington" not in yahoo
    assert page.locator(".wvr-row").count() == 4
    assert "0 must-claims" in page.locator(".wvhero").inner_text()
    # The other league shrinks to one line on the back.
    other = page.locator(".wvc-other").first.inner_text()
    assert other.startswith("ESPN: on waivers")
    # And the tab's count is this league's, stash left out.
    live = sum(1 for tier in yahoo.values() if tier != "Stash")
    assert page.locator("#subnav [data-leaf='waivers'] .tabcount").inner_text() == str(live)
    assert page.errors == []


def test_an_unknown_status_is_said_never_fa(open_waivers):
    """Jerome Ford's Yahoo status is "unknown": a Yahoo card that says so, and an ESPN back line
    that says so; the Yahoo path event reads the same way."""
    page = open_waivers("yahoo")
    ford = page.locator(".wvc:has(h3:text-is('Jerome Ford'))")
    assert ford.locator(".wvc-front .wvc-st").inner_text().endswith("Availability unknown")
    assert "(availability unknown)" in page.locator(".wvr-row.k-path").inner_text()
    espn = open_waivers("espn")
    assert "Yahoo: availability unknown" in espn.locator(".wvc:has(h3:text-is('Jerome Ford')) .wvc-other").text_content()


def test_the_lane_tag_names_why_he_is_listed(open_waivers):
    page = open_waivers("espn")
    tag = page.locator(".wvc:has(h3:text-is('Jerome Ford')) .wvc-lane")
    assert tag.text_content() == "Beats a starter" and "healthy starters" in tag.get_attribute("title")
    out = page.locator(".wvc:has(h3:text-is('Tank Dell')) .wvc-lane")
    assert out.text_content() == "Out now"
    # The lane is ESPN's reason; in Yahoo, where his screen did not list him, there is no tag.
    yahoo = open_waivers("yahoo")
    assert yahoo.locator(".wvc:has(h3:text-is('Jerome Ford')) .wvc-lane").count() == 0


def test_a_drop_that_would_start_says_so(open_waivers):
    page = open_waivers("yahoo")
    text = page.locator(".wvr-row.k-drop:has-text('R. Stevenson')").inner_text()
    assert "starts over C. Brown at FLEX, +1.4/wk" in text and "Waivers" in text


def test_a_packet_without_per_league_tiers_falls_back(open_waivers):
    """Tyler Allgeier's record has no per-league tier: his card reads the top-level Stash."""
    page = open_waivers("espn")
    assert page.locator(".wvfold .wvc:has-text('Tyler Allgeier') .wvc-stamp").text_content() == "Stash"


@pytest.mark.parametrize("day,mode,shown", [("sat", "watch", 5), ("tue", "claim", 3)])
def test_the_mode_follows_the_weekday(open_waivers, day, mode, shown):
    page = open_waivers("espn", init=TUESDAY if day == "tue" else "")
    assert page.locator(f".wv.mode-{mode}").count() == 1
    assert page.locator(f".wvr.{mode} > .wvr-list > .wvr-row").count() == shown
    if mode == "claim":
        assert page.locator(".wvr-more summary").inner_text().strip().upper() == "SHOW ALL 5"
        assert page.locator(".wvhero-mode").inner_text().upper() == "CLAIM DAY"
    else:
        assert page.locator(".wvr-more").count() == 0
        assert page.locator(".wvhero-mode").inner_text().upper() == "WIRE WATCH"
    # The rail sits above the cards in both; on claim day it is three rows, not the whole wire.
    assert page.evaluate("document.querySelector('.wvr').compareDocumentPosition(document.querySelector('.wv-cards')) & 4")


def test_the_rail_orders_path_drop_status_adds(open_waivers):
    page = open_waivers("espn")
    kinds = page.evaluate("[...document.querySelectorAll('.wvr-row')].map(r => r.className.match(/k-(\\w+)/)[1])")
    assert kinds == ["path", "drop", "status", "adds", "adds"]
    first = page.locator(".wvr-row").first.inner_text()
    assert "D. Achane DNP (hamstring) → J. Wright is FA" in first


def test_a_path_says_what_the_claim_does_when_it_knows(open_waivers):
    """ESPN's path carries a verdict and says it the way a drop does; Yahoo's has none and stops
    at who is available."""
    page = open_waivers("espn")
    assert page.locator(".wvr-row.k-path .wvr-t").inner_text().startswith(
        "D. Achane DNP (hamstring) → J. Wright is FA · bench over C. Brown, +2.1/wk")
    yahoo = open_waivers("yahoo")
    assert "·" not in yahoo.locator(".wvr-row.k-path .wvr-t").inner_text()


def test_an_empty_rail_says_since_when(open_waivers):
    page = open_waivers("espn")
    page.evaluate("WIRE.leagues.espn.events = []; render();")
    assert page.locator(".wvr-none").inner_text() == "No wire moves since Tue"


def test_the_flip_toggles_aria_pressed_without_a_layout_shift(open_waivers):
    page = open_waivers("espn")
    btn = page.locator(".wvc-flip").first
    # Page coordinates, not viewport ones: the click scrolls the card into view.
    boxes = """[...document.querySelectorAll('.wvc')].slice(0, 2).map(c => {
      const r = c.getBoundingClientRect(); return [r.top + scrollY, r.height, r.width]; })"""
    before = page.evaluate(boxes)
    btn.click()
    assert btn.get_attribute("aria-pressed") == "true"
    assert page.evaluate("document.querySelector('.wvc .wvc-front').inert") is True
    assert page.evaluate("document.querySelector('.wvc .wvc-back').inert") is False
    assert page.evaluate(boxes) == before
    # The keyboard turns it back.
    btn.focus()
    page.keyboard.press("Enter")
    assert btn.get_attribute("aria-pressed") == "false"
    page.keyboard.press(" ")
    assert btn.get_attribute("aria-pressed") == "true"
    # The back's own button opens the profile, not another flip.
    page.locator(".wvc-profile").first.click()
    assert page.evaluate("document.getElementById('modal').classList.contains('on')")
    assert btn.get_attribute("aria-pressed") == "true"


def test_reduced_motion_renders_the_final_state(open_waivers):
    """Even a first open of the day (no stamp) deals nothing under reduced motion, and a forced
    deal class still lands every card and stamp where it rests."""
    page = open_waivers("espn")
    assert page.locator(".wv.deal").count() == 0
    page.evaluate("document.querySelector('.wv').classList.add('deal')")
    page.wait_for_timeout(50)
    assert page.evaluate("[...document.querySelectorAll('.wv-cards > .wvc-list .wvc')].every(c => getComputedStyle(c).opacity === '1')")
    assert page.evaluate("getComputedStyle(document.querySelector('.tier-must .wvc-stamp')).opacity") == "1"
    assert page.evaluate("getComputedStyle(document.querySelector('.wvc-in')).transitionDuration") != "0.55s"


def test_the_deal_runs_once_per_day(open_waivers):
    page = open_waivers("yahoo", reduced=False)
    assert page.locator(".wv.deal").count() == 1
    page.evaluate("render()")
    assert page.locator(".wv.deal").count() == 0
    # A stamp for today (as the page writes it) means no deal on the next load.
    today = page.evaluate("wvToday()")
    again = open_waivers("yahoo", reduced=False, init=f'localStorage.setItem("tw.waiver.dealt", "{today}");')
    assert again.locator(".wv.deal").count() == 0


@pytest.mark.parametrize("width", [360, 390, 1400])
def test_no_rail_text_or_turn_label_sits_under_the_chat_button(open_waivers, width):
    """The chat button is fixed to the right edge, so every row scrolls past it. The rail's text
    and each card's "Evidence ›" must end left of it at any scroll position."""
    page = open_waivers("espn", width=width)
    over = page.evaluate("""(() => {
      const fab = document.getElementById('chatfab').getBoundingClientRect();
      const els = [...document.querySelectorAll('.wvr-t, .wvr-at, .wvr-k, .wv-cards > .wvc-list .wvc-front .wvc-turn')];
      return els.filter(e => e.getBoundingClientRect().right > fab.left).map(e => e.textContent.trim().slice(0, 30));
    })()""")
    assert over == []


@pytest.mark.parametrize("day", ["sat", "tue"])
def test_a_desktop_lays_the_must_claim_open_beside_a_rail_column(open_waivers, day):
    """At 1280px the Must claim shows both faces at once (no flip, nothing inert) and the rail is a
    sticky right-hand column holding every row, claim day included."""
    page = open_waivers("espn", width=1280, init=TUESDAY if day == "tue" else "")
    must = page.locator(".wvc.tier-must").first
    front, back = must.locator(".wvc-front"), must.locator(".wvc-back")
    assert front.is_visible() and back.is_visible()
    assert page.evaluate("""(() => { const c = document.querySelector('.wvc.tier-must');
      return [...c.querySelectorAll('.wvc-face')].map(f => [f.inert, f.getAttribute('aria-hidden')]); })()""") \
        == [[False, "false"], [False, "false"]]
    assert not must.locator(".wvc-flip").is_visible()
    f, b = front.bounding_box(), back.bounding_box()
    assert b["x"] >= f["x"] + f["width"] - 1 and abs(b["y"] - f["y"]) < 1 and abs(b["height"] - f["height"]) < 1
    # The profile button on the open back is reachable by keyboard.
    assert back.locator(".wvc-profile").is_enabled()
    rail, cards = page.locator(".wvr").bounding_box(), page.locator(".wv-cards").bounding_box()
    assert rail["x"] >= cards["x"] + cards["width"] and abs(rail["y"] - cards["y"]) < 40
    assert page.evaluate("getComputedStyle(document.querySelector('.wvr')).position") == "sticky"
    assert page.locator(".wvr-row:visible").count() == 5
    # Other tiers keep the flip, two to a row.
    worth = page.locator(".wvc.tier-worth .wvc-flip").first
    assert worth.is_visible()
    worth.click()
    assert worth.get_attribute("aria-pressed") == "true"
    assert page.errors == []


def test_a_phone_still_flips_the_must_claim(open_waivers):
    page = open_waivers("espn", width=390)
    must = page.locator(".wvc.tier-must").first
    assert must.locator(".wvc-flip").is_visible()
    assert page.evaluate("document.querySelector('.wvc.tier-must .wvc-back').inert") is True
    assert page.locator(".wvc.both").count() == 0


def test_section_counts_are_plain(open_waivers):
    page = open_waivers("espn")
    heads = page.evaluate("[...document.querySelectorAll('.wv .rule')].map(r => r.querySelector('h2').textContent + ' ' + r.querySelector('.count').textContent)")
    assert heads[:2] == ["Breaking · 5", "Must claim · 2"]


def test_new_rail_rows_flash_once(open_waivers):
    """Yahoo, because it is the page's default league: the first Waivers render takes the stamp,
    and a team switch after it is already a second render."""
    seen = 'localStorage.setItem("tw.wire.seen", String(Date.parse("2026-09-23T12:00:00-07:00")));'
    page = open_waivers("yahoo", init=seen)
    fresh = page.evaluate("[...document.querySelectorAll('.wvr-row.fresh .wvr-k')].map(k => k.textContent)")
    assert fresh == ["Status"]                   # 12:50; the drop (10:15) and the path are older
    page.evaluate("render()")
    assert page.locator(".wvr-row.fresh").count() == 0
