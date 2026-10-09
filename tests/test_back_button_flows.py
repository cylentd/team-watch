"""Back, second walk (2026-10-09, TODO "Back button assessment"; docs/back-button-walk.md): the drawer and Connect.

Same rule as tests/test_back_button.py: a view change is in the hash, so Back returns to the previous view; an
overlay is one URL-less history entry, so Back closes it before the view changes. Journeys on the full page at a
phone's size; the page's clock is a Saturday (SEED), so the default view is the Digest."""
import pytest

from pages.history_flows import HistoryFlows
from test_back_button import PHONE, REQ  # noqa: F401
from test_render import open_at
from test_render_connect import CARD

pytestmark = [pytest.mark.render, pytest.mark.journey]


@pytest.fixture
def start(browser, page_file):
    """start(hash) -> (HistoryFlows, errors): the full page at a phone's size on that hash; closed and checked for
    page errors when the test ends."""
    opened = []

    def open_(hash_=""):
        ctx, page, errors = open_at(browser, page_file, PHONE, hash_)
        opened.append((ctx, errors))
        return HistoryFlows(page), errors
    yield open_
    for ctx, errors in opened:
        ctx.close()
        assert errors == []


def dfs(start):
    """DFS (leaf `dfs`) one step after Matchup's first view, which is where "How this works" lives."""
    history, _ = start("#digest")
    history.tap_group("week")
    history.tap_pill("dfs")
    return history


@pytest.mark.req(REQ, ac="Back closes the drawer before the view changes")
def test_back_closes_the_how_this_works_drawer_and_stays_on_the_view(start):
    """The drawer is an overlay like the sheets, so Back closes it. It used to leave the drawer open over the
    view Back moved to."""
    history = dfs(start)
    history.open_explain()
    history.back()
    history.wait_drawer_closed()
    assert history.entry() == {"hash": "#dfs", "surface": "dfs", "layers": [], "entry_layer": None}
    history.back_to("live")


@pytest.mark.req(REQ, ac="closing the drawer from itself leaves no dead history entry")
def test_closing_the_drawer_with_its_x_takes_its_entry_back(start):
    """The x takes the drawer's entry back, so one Back from DFS leaves it, not a dead step first."""
    history = dfs(start)
    history.open_explain()
    history.close_drawer_with_x()
    history.page.wait_for_function("LAYERS.length === 0 && LAYER_SKIP.length === 0")
    history.back_to("live")
    assert not history.drawer_is_open()


@pytest.mark.req(REQ, ac="connecting a league writes the Roster it opens into the hash")
def test_connecting_a_league_opens_its_roster_as_a_step_back_can_return_from(start):
    """Connect closes its sheet and shows the new league's Roster. It used to set the view without the hash, so the
    address kept the old view (a reload landed there) and Back did not return to it."""
    history, _ = start("#ranks")
    history.connect_league(CARD)
    assert history.entry() == {"hash": "#roster", "surface": "roster", "layers": [], "entry_layer": None}
    history.back_to("ranks")
