"""The profile's journeys: the tests that leave the roster for another view, read the hash, or press Back.
They need the full page (the mounted roster has no Usage CSS and its history is not the page's), so each
is marked `journey`; the page is shared by viewport, as test_left_hurt.py shares its pages.

The profile itself is read through pages/profile.py, as in test_profile.py."""
import pytest

from conftest import SharedPages
from pages.profile import ProfilePage
from test_render import drive, go
from test_render import open_page as open_any_page

REQ = "The profile modal"
ST_BROWN = "Amon-Ra St. Brown"

def reset(page, snap):
    """Put a shared page back to what a fresh load plus a click on Roster would be: no profile or layer
    open, the first team in view, localStorage as loaded, scrolled to the top."""
    profile = ProfilePage(page)
    for _ in range(5):
        if not profile.anything_open():
            break
        profile.press_escape()
        profile.settle()
    profile.settle()
    profile.restore(snap)
    drive(page, go("roster"))


@pytest.fixture(scope="module")
def shared_pages(browser, page_file):
    """One loaded page per viewport for the module."""
    pages = SharedPages()

    def opener(size):
        ctx, page, errors = open_any_page(browser, page_file, size)
        drive(page, go("roster"))
        snap = ProfilePage(page).snapshot()
        assert errors == []         # whatever the load raised fails here, not lost to a later clear
        return ctx, page, errors, snap
    yield lambda size: pages.get(size, lambda: opener(size))
    pages.close()


@pytest.fixture
def shared(shared_pages):
    """shared((w, h)) -> (ProfilePage, errors): the viewport's page, reset, with its error list emptied. The
    list is asserted empty again when the test ends, so a test that forgets still fails on a page error."""
    used = []

    def open_shared(size):
        ctx, page, errors, snap = shared_pages(size)
        reset(page, snap)
        left, errors[:] = list(errors), []   # what the reset (its Escapes included) or the last test left
        assert left == []
        used.append(errors)
        return ProfilePage(page), errors
    yield open_shared
    for errors in used:
        assert errors == []


@pytest.mark.render
@pytest.mark.journey
@pytest.mark.req(REQ, ac="the profile reaches his row in the Usage grid in one tap; a player the grid lacks gets no link")
def test_the_profile_reaches_his_row_in_the_usage_grid_in_one_tap(shared):
    """Plan U3 (2026-10-05): a link under the strip opens Usage on his row (nav.js navGoRow), once the profile
    has closed behind it. A player the grid has no row for gets no link."""
    profile, errors = shared((390, 844))
    profile.roster.show_team("espn")
    profile.open_from_roster("Chase Brown")
    link = profile.grid_link()
    assert link["text"] == "His row in Usage"
    assert link["height"] >= 44
    profile.follow_grid_link()
    profile.wait_surface("usage")
    profile.wait_closed()
    assert profile.usage_hits("chase-brown") == 1
    assert profile.grid_link_markup({"n": "Nobody Known", "slug": "nobody-known"}) == ""
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
@pytest.mark.req(REQ, ac="an owner pill opens that team's roster as a look, not a pick, and Back returns to the view he came from")
def test_an_owner_pill_opens_that_teams_roster(shared):
    """A team's pill is a way to that team's roster (2026-09-28, for looking up a trade). It is a
    look, not a pick: the reader's own team is still theirs afterwards, and Back returns to the
    view they came from. A free agent's pill goes nowhere."""
    profile, errors = shared((1400, 900))
    drive(profile.page, go("usage"))                          # somewhere that is not a roster
    profile.open_player({"n": "Chase Brown", "pos": "RB", "team": "CIN", "slug": "chase-brown"})
    espn = [o for o in profile.owners() if o["button"] and o["league"] == "ESPN"]   # the ESPN team, not the one in view
    assert len(espn) == 1
    key = espn[0]["key"]
    assert key.startswith("espn") and profile.view() == "yahoo"
    profile.follow_owner("ESPN")
    profile.wait_hash("#roster")
    assert not profile.is_open()
    assert profile.view() == key
    assert profile.my_team() == "yahoo"                       # the reader's pick is untouched
    profile.back()
    profile.wait_hash("#usage")
    profile.open_player({"n": ST_BROWN, "pos": "WR", "team": "DET", "slug": "amonra-st-brown"})
    assert len([o for o in profile.owners() if o["free"] and not o["button"]]) == 2   # free agent in ESPN and AYO: not a button
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
@pytest.mark.req(REQ, ac="the sphere opens the stat sheet over the profile; Escape and Back close the sheet alone and keep the pane")
def test_the_sphere_opens_the_sheet_over_the_profile(shared):
    """The radar is a sphere in the head (orb.js) and a tap opens the flat sheet over the profile.
    Escape and Back close the sheet alone and put the reader back in the profile, on the pane they
    left; the sphere's caption is the rank the sheet opens on."""
    profile, errors = shared((1400, 900))
    profile.open_from_roster(ST_BROWN)
    rank = profile.rank_mark("WR", "wopr", "amonra-st-brown")
    assert profile.orb_text() == f"{rank} TARGET SHARE"
    assert profile.radars() == 0                              # not drawn until asked for
    profile.tab("usage")
    profile.open_sheet()
    assert profile.layer_radars() == 1
    assert profile.sheet_stat() == "Target share"
    profile.press_escape()
    assert profile.layers() == 0
    assert profile.is_open()
    assert profile.selected_tab() == "usage"
    assert profile.orb_focused()
    profile.open_sheet()
    profile.back()
    assert profile.layers() == 0
    assert profile.is_open()
    profile.roster.show_team("espn")
    profile.back()                                            # the profile's own entry
    profile.open_from_roster("George Kittle")                 # no sheet row: no sphere
    assert profile.orb_count() == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
@pytest.mark.req(REQ, ac="Compare picks from the profile and draws one radar; Back closes the whole layer and leaves the profile open")
def test_compare_picks_from_the_profile_and_draws_one_radar(shared):
    """Compare (2026-09-30): the head's button opens the picker over the profile with the reader's
    own team first; two ticks and Compare draw three chips, one shape each on one radar, and the
    rows; Back closes the whole layer and leaves the profile open."""
    profile, errors = shared((360, 800))
    profile.open_from_roster(ST_BROWN)
    profile.compare_open()
    assert profile.compare_layers() == 1
    assert profile.compare_rows() >= 2
    assert profile.compare_go_disabled()
    profile.compare_pick(0)
    profile.compare_pick(1)
    assert profile.compare_picked() == 2
    profile.compare_go()
    assert profile.compare_cards() == 3
    assert profile.compare_strips() == 4
    # One shape per player on the profile's graph, or no graph at all for a mixed-position set.
    assert (profile.compare_shapes(), profile.compare_graphs()) in ((3, 1), (0, 0))
    # It opens on the profile's own player, as his profile does.
    assert profile.compare_focus() == "0"
    assert profile.compare_focus_in_sheet()
    profile.back()
    profile.wait_compare_closed()
    profile.settle()
    assert profile.compare_layers() == 0
    assert profile.is_open()
    assert errors == []
