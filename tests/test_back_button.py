"""Back lands where the reader came from (2026-10-08, TODO "Back button assessment"; docs/back-button-walk.md).

The rule: a view change is in the hash, so Back returns to the previous view; an overlay (profile, search,
Preview's dossier, Compare) is one URL-less history entry, so Back closes it before the view changes. Tabs
inside a view (navModes) and the team switch's pick are not entries: Back leaves the view.

Each test is a journey on the full page (hash and Back are the page's, a mount has no history of its own), so
it is marked `journey` and not counted by the full-load ratchet. The page's clock is a Saturday (SEED), so
the default view is the Digest, not Tuesday's Waivers."""
import pytest

from pages.history import HistoryPage
from test_render import open_at

pytestmark = [pytest.mark.render, pytest.mark.journey]
PHONE = (360, 800)
REQ = "Navigation: one League group, Stats"


@pytest.fixture
def start(browser, page_file):
    """start(hash) -> (HistoryPage, errors): the full page at a phone's size on that hash; closed and checked for
    page errors when the test ends."""
    opened = []

    def open_(hash_=""):
        ctx, page, errors = open_at(browser, page_file, PHONE, hash_)
        opened.append((ctx, errors))
        return HistoryPage(page), errors
    yield open_
    for ctx, errors in opened:
        ctx.close()
        assert errors == []


@pytest.mark.req(REQ, ac="Back after a view change lands on the view the page opened on")
def test_back_from_the_first_tap_returns_to_the_digest_the_page_opened_on(start):
    """A page opened with no hash shows the Digest and has no hash to return to; Back after the first tap must
    show the Digest again, not stay on the view the tap opened."""
    history, _ = start("")
    history.tap_group("league")
    assert history.entry()["hash"] == "#roster"
    history.back()
    history.page.wait_for_function("SURFACE === 'digest'")
    assert history.entry()["surface"] == "digest"


@pytest.mark.req(REQ, ac="a view change with an overlay open leaves no dead history entry")
@pytest.mark.parametrize("view,opens,away", [("preview", "open_dossier", "matchups"), ("matchups", "open_compare", "news")])
def test_leaving_a_view_with_its_layer_open_leaves_one_step_back_not_two(start, view, opens, away):
    """Preview's dossier (and Compare two) is a history entry. Tapping another view while it is up used to leave
    that entry behind the new one: Back came back to the view with nothing open, and a second Back did nothing."""
    history, _ = start("#digest")
    history.tap_pill(view)
    getattr(history, opens)()
    history.tap_pill(away)
    history.back_to(view)
    assert history.entry() == {"hash": f"#{view}", "surface": view, "layers": [], "entry_layer": None}
    history.back_to("digest")


@pytest.mark.req(REQ, ac="a link out of the profile leaves no dead history entry")
@pytest.mark.parametrize("follow,view", [("follow_grid_link", "usage"), ("follow_first_owner", "roster")])
def test_a_profile_link_opened_from_search_returns_to_the_view_the_reader_left(start, follow, view):
    """Search over Slips, a result's profile over the sheet, then the profile's link to a view. The sheet and the
    profile both close, and Back from the view lands on Slips, then Ranks: no step is spent on the sheet's entry."""
    history, _ = start("#ranks")
    history.tap_group("bets")
    history.open_search_result("a")
    getattr(history, follow)()
    history.page.wait_for_function("v => SURFACE === v && LAYERS.length === 0", arg=view)
    history.back_to("parlay")
    assert history.entry()["entry_layer"] is None
    history.back_to("ranks")


@pytest.mark.req(REQ, ac="a pick that moves the view to the nearest leaf is not a history entry")
def test_picking_a_league_without_the_view_replaces_it_instead_of_adding_a_step(start):
    """Records is the Yahoo league's. Picking the ESPN team lands on Recap; Back from there must return to the view
    before Records, not to a `#records` entry that shows Recap."""
    history, _ = start("#digest")
    history.tap_group("league")
    history.tap_pill("records")
    history.pick_team("espn")
    history.page.wait_for_function("SURFACE === 'recap'")
    assert history.entry()["hash"] == "#recap"
    history.back_to("roster")
