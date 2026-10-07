"""The team switch on a phone (2026-09-25; the header bar's, #hdrswitch, since 2026-10-05): the menu used to open clipped under the title, so a tap
meant for ESPN landed on the Sheet / Cards chips below it. A click in Playwright retries until the
target is hit, so the test asks what is actually on top at the point a finger would tap.

Each test mounts the Roster (tests/component.py) and reads the header's switch through
pages/teamswitch.py. The Waivers case of the width test opens that leaf on the same mount: the header
is chrome, so the leaf's own CSS does not change where its menu sits."""
import pytest

from component import mount as base_mount  # noqa: F401  (the fixture, `mount` below)
from pages.roster import RosterPage
from pages.teamswitch import TeamSwitchPage
from pages.warm import warm

pytestmark = pytest.mark.render


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the module's two phone contexts opened once (pages/warm.py)."""
    return warm(base_mount, ("roster", (390, 844)), ("roster", (360, 740)))


@pytest.mark.parametrize("mode", ["sheet", "cards"])
def test_every_league_in_the_menu_is_on_top_where_a_finger_taps(mount, mode):
    page, errors = mount("roster", size=(390, 844))
    RosterPage(page).mode(mode)
    switch = TeamSwitchPage(page)
    switch.toggle()
    assert switch.covered_taps() == []
    other = switch.other_league_team()
    switch.choose(other)
    assert switch.viewed_team() == other
    assert errors == []


def test_the_menu_lists_followed_teams_and_a_league_on_request(mount):
    """2026-09-26: the menu is the reader's own teams. Since 2026-09-29 every other team waits
    behind its league's row (storyboard option A), and a star follows one, the menu staying open."""
    page, errors = mount("roster", size=(390, 844))
    switch = TeamSwitchPage(page)
    switch.toggle()
    assert switch.team_keys() == ["yahoo", "espn", "ayo"], "unset, the list is David's teams (three since 2026-09-29)"
    lg = switch.first_mate_league()
    assert lg, "the fixture has leaguemates"
    mates = switch.mates_by_name(lg)
    switch.open_league(lg)
    assert switch.team_keys() == [lg, *mates], "David's team first, then by name"
    switch.follow(mates[0])
    assert switch.menu_is_visible(), "a star keeps the menu open"
    switch.back()
    assert switch.team_keys() == ["yahoo", "espn", "ayo", mates[0]], "Back shows the first screen, the new follow in it"
    assert switch.focused_league() == lg, "focus returns to the league's row"
    switch.follow("yahoo")
    assert "yahoo" not in switch.team_keys(), "unfollowed, it leaves Following"
    assert switch.followed_keys() == ["espn", "ayo", mates[0]]
    assert errors == []


def test_the_footer_is_gone_and_its_credits_are_one_tap_into_about(mount):
    """2026-10-04: the footer stood 161px under every view. Its credits, the archetype icons' CC BY
    attribution among them, moved to the team switch's About screen, which a phone can reach."""
    page, errors = mount("roster", size=(360, 740))
    switch = TeamSwitchPage(page)
    assert switch.footer_count() == 0
    switch.toggle()
    switch.open_about()
    assert switch.credits_are_visible() and "CC BY 3.0" in switch.credits_text()
    assert switch.focused() == "teamswitch-back", "focus moves to Back"
    switch.back()
    assert switch.credits_count() == 0
    assert switch.focused() == "teamswitch-about", "focus returns to About"
    # closed and opened again, the menu starts on its first screen, not on About
    switch.open_about()
    switch.toggle()
    switch.toggle()
    assert switch.about_count() == 1
    assert errors == []


@pytest.mark.parametrize("leaf", ["roster", "waivers"])
def test_the_menu_stays_on_a_phone_screen_whatever_the_names_length(mount, leaf):
    """2026-10-05: hung from the name's right end, a long name's menu ran 20px off the left edge (and a
    short one's off the right, 2026-09-29). On a phone it runs gutter to gutter."""
    page, errors = mount(leaf, size=(360, 740))
    switch = TeamSwitchPage(page)
    switch.toggle()
    left, right = switch.edges()
    assert 0 <= left and right <= 360, (left, right)
    assert errors == []


def test_a_whole_league_fits_the_menu_on_a_phone(mount):
    """Option A's point: a league's twelve on screen without scrolling the menu, at 360 x 740."""
    page, errors = mount("roster", size=(360, 740))
    switch = TeamSwitchPage(page)
    switch.toggle()
    assert switch.league_row_count(), "the fixture has leaguemates"
    switch.open_league()
    over = switch.overflow()
    assert over <= 1, f"the league's list scrolls {over}px inside the menu"
    assert switch.focused() == "teamswitch-back", "focus moves to Back"
    assert errors == []


def test_the_menu_opens_on_the_league_of_an_unfollowed_team(mount):
    page, errors = mount("roster", size=(390, 844))
    switch = TeamSwitchPage(page)
    mate = switch.first_mate()
    assert mate, "the fixture has leaguemates"
    # Viewed, not picked: a pick follows the team by default (data/mates.js followLoad).
    switch.view_without_picking(mate)
    switch.toggle()
    assert switch.back_is_visible()
    assert switch.is_selected(mate) == "true"
    assert errors == []
