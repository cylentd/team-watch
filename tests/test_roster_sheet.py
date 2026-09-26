"""The roster as a lineup sheet (2026-09-25): full-size rows on a phone in the cards' frame (it was
squeezed to one screen, and David found it read small), the bench beside the starters on a
desktop. Runs on the ESPN fixture, the one with a bench."""
import re

import pytest

from test_render import browser, drive, go, open_page  # noqa: F401  (browser is a fixture)


def espn_roster(browser, page_file, viewport):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    return ctx, page, errors


@pytest.mark.render
def test_a_phone_row_is_full_size(browser, page_file):
    ctx, page, errors = espn_roster(browser, page_file, (360, 660))
    heads = page.eval_on_selector_all(".row .head img, .row .head .fallback", "els => els.map(e => e.getBoundingClientRect().width)")
    assert heads and min(heads) >= 40, heads
    slots = page.eval_on_selector_all(".row.start .slot", "els => els.map(e => e.textContent)")
    assert slots and not any(re.search(r"\d", s) for s in slots), slots   # RB1 prints RB, FLX2 prints FLX
    # The bench is one to a row, like the starters: every bench row as wide as a starter row.
    widths = page.eval_on_selector_all(".row", "els => [...new Set(els.map(e => Math.round(e.getBoundingClientRect().width)))]")
    assert len(widths) == 1, widths
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_desktop_puts_the_bench_beside_the_starters(browser, page_file):
    ctx, page, errors = espn_roster(browser, page_file, (1280, 900))
    tops = page.eval_on_selector_all(".sheet-col", "els => els.map(e => Math.round(e.getBoundingClientRect().top))")
    lefts = page.eval_on_selector_all(".sheet-col", "els => els.map(e => Math.round(e.getBoundingClientRect().left))")
    assert len(tops) == 2 and tops[0] == tops[1] and lefts[1] > lefts[0]
    assert errors == []
    ctx.close()
