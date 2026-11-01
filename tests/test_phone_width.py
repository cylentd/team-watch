"""S1: a reader on a 360px phone opens the page and every view draws with no sideways scroll.

Oracle, from the scenario: at 360 x 740 the document is no wider than the window, for every surface in
`component.SURFACES` (read from code, so a new view is covered without an edit), and nothing raised.
"""
import pytest

from component import SURFACES, mount  # noqa: F401  (mount is the fixture)
from pages.page_width import PageWidth
from test_smoke_views import one_context_at_a_time  # noqa: F401  (a fixture)

PHONE = (360, 740)


@pytest.mark.parametrize("surface", sorted(SURFACES))
def test_a_view_fits_a_360px_phone_with_no_sideways_scroll(mount, one_context_at_a_time, surface):
    page, errors = mount(surface, size=PHONE)
    view = PageWidth(page)
    scroll, client = view.widths()
    assert scroll <= client, f"{surface} scrolls sideways: {scroll} > {client}; widest: {view.widest_elements()}"
    assert errors == []
