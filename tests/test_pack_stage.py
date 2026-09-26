"""The pack's stage and its controls, fixes of 2026-09-25: "Rip again" sits over the cards and never
moves the Sheet / Cards switch, a drag on the pack turns it and it springs back, and a tap while the
cards are dealt hurries them."""
import time

import pytest

from test_roster_cards import cards_page, motion_page, rip
from test_render import browser  # noqa: F401  (browser is a fixture)


def chips(page):
    return page.evaluate("[...document.querySelectorAll('.rmode .chip')].map(b => Math.round(b.getBoundingClientRect().x))")


@pytest.mark.render
def test_rip_again_is_over_the_cards_and_the_switch_holds_still(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file)
    if page.locator(".pack").count() == 0:
        pytest.skip("the fixture's schedule has no week ahead, so no pack to open")
    page.click(".pack .pack-seal")
    rip(page)
    page.wait_for_selector(".pk-stage", state="detached")
    assert page.locator(".cards .rule [data-rerip]").count() == 1
    assert page.locator(".rmode [data-rerip]").count() == 0
    in_cards = chips(page)
    page.click("[data-rmode='sheet']")
    assert chips(page) == in_cards, "Sheet and Cards stay where they were"
    assert page.locator("[data-rerip]").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_drag_on_the_pack_turns_it_and_it_springs_back(browser, page_file):
    ctx, page, errors = cards_page(browser, page_file, keep_stage=True)
    if page.locator(".pk-stage").count() == 0:
        pytest.skip("the fixture's schedule has no week ahead, so no pack to open")
    box = page.locator(".pk-stage .pack-seal").bounding_box()
    y = box["y"] + box["height"] * .6
    page.mouse.move(box["x"] + box["width"] / 2, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .9, y, steps=5)
    turned = page.evaluate("parseFloat(document.querySelector('.pk-center').style.getPropertyValue('--pry'))")
    page.mouse.up()
    assert turned > 10, "the pack turns with the drag"
    assert page.evaluate("document.querySelector('.pk-center').style.getPropertyValue('--pry')") == "", "and springs back"
    assert page.locator(".pk-stage .pack-seal").count() == 1, "a drag on the body does not rip"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_taps_hurry_the_deal(browser, page_file):
    ctx, page, errors = motion_page(browser, page_file)
    try:
        page.wait_for_selector(".pk-stage", timeout=2000)
    except Exception:
        pytest.skip("the fixture's schedule has no week ahead, so no pack to open")
    rip(page)
    page.wait_for_selector(".pk-card")
    t0 = time.time()
    while page.locator(".pk-stage").count() and time.time() - t0 < 15:
        page.mouse.click(20, 400)
        page.wait_for_timeout(150)
    took = time.time() - t0
    n = page.evaluate("packCards(TEAMS.espn).length")
    # Untouched, a card takes ~2.4s and the best one ~5.5s more.
    assert took < 1.2 * n + 3, f"{n} cards took {took:.1f}s with taps"
    assert page.locator(".cards .tc.pk-slot").count() == 0
    assert errors == []
    ctx.close()
