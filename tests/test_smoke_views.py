"""Smoke check, one mount per view (2026-10-07).

All the app's JS shares one script scope and the nav calls into other views, so a change to a shared
file can break a view the diff never touched. A land that skips the full e2e and golden run on a
shared-file diff leans on this: every surface in `component.SURFACES` is mounted once and must draw
and raise nothing. The test reads the dict, so a new surface is covered without an edit here.
"""
import pytest

from component import SURFACES, mount  # noqa: F401  (mount is the fixture)

PHONE = (360, 740)

# A view that throws while drawing never fills #view, and the mount then waits out its whole load timeout for a
# draw that cannot come. On a page error this adds a child to #view, so the wait resolves at once and the
# mount's own error check fails the test with the real page error (tests/component.py is frozen: no edit there).
ON_ERROR = """(() => {
  const mark = () => {
    const view = document.getElementById('view');
    if (view) view.appendChild(document.createElement('i'));
    else document.addEventListener('DOMContentLoaded', mark, { once: true });
  };
  window.addEventListener('error', mark);
  window.addEventListener('unhandledrejection', mark);
})();"""


@pytest.fixture
def one_context_at_a_time(mount, request):
    """`mount` keeps a context per surface for the module, and 20 surfaces pass conftest's bound on open
    contexts. Each test needs its surface once, so its context is closed when the test ends."""
    yield
    surface = request.node.callspec.params["surface"]
    for key in [k for k in mount.pages.items if k[0] == surface]:
        mount.pages.items.pop(key)[0].close()


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_a_view_draws_and_raises_nothing_with_the_fixture_data(mount, one_context_at_a_time, surface):
    # Oracle: with the fixture build's data a view draws at least one element under #view, and the
    # page raised no error while loading or drawing it.
    page, errors = mount(surface, size=PHONE, init=(ON_ERROR,))
    drawn = page.evaluate("document.querySelectorAll('#view *').length")
    assert drawn > 0, f"{surface} drew nothing under #view"
    assert errors == [], f"{surface} raised: {errors[:3]}"
