"""design/STYLE.md, checked in the browser (audit 2026-09-25): at 360px no view scrolls anything
sideways inside a page that scrolls down, and nothing on the page moves on its own. Leaders' stat
tabs are the one sideways row: six stats need ~470px, and the row fades at its edge instead.

Component tests (2026-10-06): each view is mounted on its own page (tests/component.py), the page chrome
included, so a view's rule is read from the view and not from what another view left behind.
"""

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from conftest import SharedPages

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
LOOPS = """document.getAnimations().filter(a => a.playState === 'running'
  && a.effect && a.effect.getTiming().iterations === Infinity).map(a => a.animationName)"""


class PerSize(SharedPages):
    """One page per viewport, not per view: each test loads its own view into it, which clears storage
    and reloads, so a view's rule is still read from that view alone."""

    def get(self, key, opener):
        return super().get(key[1:], opener)


@pytest.fixture(scope="module")
def mounted(mount, built):
    """A Mounter of this module's own, on the module's folder, that keeps one page per size and not one
    per view (eleven views would keep more contexts than a module may)."""
    m = Mounter(mount.browser, mount.folder, built.fragment)
    m.pages = PerSize()
    yield m
    m.pages.close()


def settle(page):
    page.wait_for_function(SETTLED)


@pytest.mark.render
@pytest.mark.parametrize("leaf", VIEWS)
def test_nothing_scrolls_sideways_on_a_phone(mounted, leaf):
    page, errors = mounted(leaf, size=(360, 800))
    page.evaluate(f"navGo('{leaf}'); render()")
    settle(page)
    assert page.evaluate(SIDEWAYS) == []
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("leaf", ["board", "news", "parlay"])
def test_nothing_moves_on_its_own(mounted, leaf):
    """The logo and the chrome hold still; an infinite loop is left only where the motion is the
    content (the drive strip, the trading cards, a game in progress)."""
    page, errors = mounted(leaf, size=(1280, 900))
    page.evaluate(f"navGo('{leaf}'); render()")
    settle(page)
    assert page.evaluate(LOOPS) == []
    assert errors == []
