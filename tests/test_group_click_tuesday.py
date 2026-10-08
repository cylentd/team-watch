"""A group click opens the group's first view on a Tuesday too (2026-10-07, David).

On a Tuesday the League row leads with Waivers (claims day; navLeavesFor's waiverDay). A group click used to
open the row's first leaf, so League opened Waivers on a Tuesday. The group's first view is its normal first
view, Roster for League, on every day. The Tuesday rule still sets the row's order and the no-hash landing
(navDefaultLeaf); test_group_default_leaf.py proves the rest of the group-click rules on the Saturday SEED.
The clock is pinned to a Tuesday (TUESDAY, test_render.py) after SEED, so the Tuesday order is in play."""
import pytest

from component import mount  # noqa: F401
from test_render import TUESDAY

pytestmark = pytest.mark.render

SIZES = {"phone bottom bar": (360, 740), "desktop bar": (1280, 800)}
GROUP_BUTTON = "#nav .navitem[data-s='{}']"


def leaf(page):
    return page.evaluate("SURFACE")


def tap_group(page, group):
    page.locator(GROUP_BUTTON.format(group)).click()
    page.wait_for_function("g => navGroupOf(SURFACE) === g", arg=group)


@pytest.fixture(params=sorted(SIZES))
def tuesday(request, mount):
    """The Digest on a Tuesday at the size under test: (page, errors), asserted free of page errors after the test."""
    page, errors = mount("digest", size=SIZES[request.param], init=(TUESDAY,))
    yield page
    assert errors == []


@pytest.mark.req("Navigation: one League group, Stats", ac="a group click opens the group's first view, Tuesday too")
def test_league_opens_roster_on_a_tuesday_not_waivers(tuesday):
    tuesday.evaluate("navGo('teams')")
    tap_group(tuesday, "week")
    tap_group(tuesday, "league")
    assert leaf(tuesday) == "roster"
