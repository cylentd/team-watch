"""The prop market as a card grid and the page's microinteractions (2026-09-25): two cards to a row
on a phone, an open chevron widens its card to the row, a new view's cards arrive once, and a tap
that only adds a leg pops that line without replaying the arrival of everything else."""
import re

import pytest

from test_render import SEED, browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render


def columns(page, sel):
    return len(page.evaluate(f"getComputedStyle(document.querySelector('{sel}')).gridTemplateColumns").split())


@pytest.mark.parametrize("book, grid", [("underdog", ".pgrid"), ("dk", ".lgrid")])
def test_the_market_is_two_cards_a_row_on_a_phone(browser, page_file, book, grid):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(f"SURFACE='parlay'; PARLAY_BOOK='{book}'; MKT_PAGE=1; render()")
    assert columns(page, grid) == 2
    card = page.locator(f"{grid} > *").first
    card.locator(".more").first.click()
    page.wait_for_timeout(50)
    opened = page.locator(f"{grid} > *:has(.legx)").first
    assert opened.bounding_box()["width"] > 300, "an open card spans the row"
    assert errors == []
    ctx.close()


def test_a_new_view_enters_once_and_a_tap_pops_only_its_line(browser, page_file):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="no-preference")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    page.goto(page_file.as_uri() + "#parlay")
    page.wait_for_function("document.getElementById('view').children.length > 0")
    assert page.evaluate("document.getElementById('view').classList.contains('enter')")
    page.locator(".pgrid .udline").first.click()
    assert not page.evaluate("document.getElementById('view').classList.contains('enter')")
    assert page.locator(".udline.just").count() == 1
    assert page.locator(".slip .sliphead .pill.bump").count() == 1
    assert errors == []
    ctx.close()


def test_reduced_motion_never_marks_an_entrance(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("SURFACE='parlay'; render()")
    assert not page.evaluate("document.getElementById('view').classList.contains('enter')")
    page.locator(".pgrid .udline").first.click()
    assert page.locator(".udline.just").count() == 0
    assert errors == []
    ctx.close()
