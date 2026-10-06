"""design/STYLE.md, checked in the browser (audit 2026-09-25): at 360px no view scrolls anything
sideways inside a page that scrolls down, and nothing on the page moves on its own. Leaders' stat
tabs are the one sideways row: six stats need ~470px, and the row fades at its edge instead."""

import pytest

from test_render import open_page  # noqa: F401

VIEWS = ["roster", "waivers", "board", "movers", "usage", "news", "parlay", "build", "dfs", "weather", "teams"]
SIDEWAYS = """[...document.querySelectorAll('#view *')].filter(e =>
  /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4
  && !e.matches('.bd-tabs:not(.bets-tabsrow .bd-tabs), .reel-track')).map(e => String(e.className).slice(0, 40))"""
# .reel-track is the Roster's clip rail, the STYLE.md exception for a one-row thumbnail rail (Roster clips, 2026-10-05).
# A view is drawn once render() returns; "settled" is a painted frame with no finite animation still running.
# Settled: no finite animation still running. A plain predicate, polled every frame: wait_for_function
# returns at once on a returned Promise (an object is truthy) and never re-checks it.
SETTLED = """() => document.getAnimations().every(a =>
  !a.effect || a.effect.getTiming().iterations === Infinity || a.playState !== 'running')"""


def settle(page):
    page.wait_for_function(SETTLED)


@pytest.mark.parametrize("leaf", VIEWS)
def test_nothing_scrolls_sideways_on_a_phone(browser, page_file, leaf):
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    page.evaluate(f"navGo('{leaf}'); render()")
    settle(page)
    assert page.evaluate(SIDEWAYS) == []
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert errors == []
    ctx.close()


def test_nothing_moves_on_its_own(browser, page_file):
    """The logo and the chrome hold still; an infinite loop is left only where the motion is the
    content (the drive strip, the trading cards, a game in progress)."""
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    for leaf in ("board", "news", "parlay"):
        page.evaluate(f"navGo('{leaf}'); render()")
        settle(page)
        loops = page.evaluate("""document.getAnimations().filter(a => a.playState === 'running'
          && a.effect && a.effect.getTiming().iterations === Infinity).map(a => a.animationName)""")
        assert loops == [], (leaf, loops)
    assert errors == []
    ctx.close()
