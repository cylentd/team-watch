"""Build's Mine only follows the teams the reader follows (2026-10-06, David: "mine" is the players on the teams the
reader follows, never his).

Bets read a flag the build wrote from David's rosters, so a leaguemate who tapped Mine only saw David's players, and
unfollowing a team in the switch changed nothing. The chip, the lime ring on a player and the "My players" preset now
read the switch's Following list (data/mates.js `mineSlugs`). A reader who follows no team has no players of their
own, so the chip and the preset are not drawn (a disabled chip would need a reason beside it; the Roster and Waivers
leaves already ask a reader with no team to pick one, and Ranks tags nobody). Whose lines are listed is test_js_bets_mine.py's
(Node); this proves the screen draws it and the switch's stars redraw it.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.parlay_build import BuildPage
from pages.teamswitch import TeamSwitchPage

SECTION = "Parlay and DFS"
# A first visit: nothing picked, nothing followed (the suite's seed picks and follows David's teams).
FRESH_READER = 'try { localStorage.removeItem("tw-team"); localStorage.removeItem("tw-follow"); } catch (e) {}\n'
DAVIDS = ["yahoo", "espn", "ayo"]


def open_build(mount, init=()):
    page, errors = mount("build", size=(390, 844), init=init)
    build = BuildPage(page)
    build.show_build("dk")
    build.build_with_settings_panel()
    return build, errors


@pytest.mark.render
@pytest.mark.req(SECTION, ac="unfollowing a team takes its players off Mine only at once")
def test_mine_only_lists_the_players_of_the_teams_still_followed_as_each_star_is_tapped(mount):
    build, errors = open_build(mount)
    switch, listable = TeamSwitchPage(build.page), build.listable_slugs()
    assert build.mine_only_chips() == 1, "the seed follows three teams"
    build.tap_mine_only()
    assert build.mine_only_pressed() == "true"
    followed = list(DAVIDS)
    assert build.listed_slugs() == build.held_by(followed) & listable != set(), "the fixture lists players on the teams"
    assert build.lit_players() == (build.player_blocks(),) * 2, "every player drawn is on a followed team"
    switch.open_menu()
    got, want, menu_open = [], [], []
    for gone in list(followed):
        switch.follow(gone)
        followed.remove(gone)
        got.append(build.listed_slugs())
        want.append(build.held_by(followed) & listable)
        menu_open.append(switch.menu_is_visible())
    # the last unfollow leaves no team, which the two asserts after these cover
    assert got[:-1] == want[:-1], "after each unfollow, Mine only lists the players of the teams still followed"
    assert menu_open == [True] * len(DAVIDS), "a star keeps the menu open"
    assert build.mine_only_chips() == 0, "no followed team, no players of mine, no chip"
    assert build.listed_slugs() != set() and build.lit_players()[0] == 0, "and the filter left on hides nothing"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(SECTION, ac="a reader's pick marks that team's players, not David's")
def test_a_leaguemate_who_picks_their_team_sees_their_own_players_under_mine_only(mount):
    """A pick follows the team by default (data/mates.js followLoad). David's teams hold lines on the list; the
    leaguemate's roster holds one player (planted: the fixture's leaguemates hold none of the lines')."""
    build, errors = open_build(mount, init=(FRESH_READER,))
    mate = build.page.evaluate("MATES.length ? MATES[0].key : null")
    theirs = sorted(build.listable_slugs())[0]
    assert mate and build.held_by(DAVIDS) & build.listable_slugs(), "the fixture has a leaguemate and David's players on the list"
    build.page.evaluate("([k, s]) => TEAMS[k].roster.push({n: s, slug: s})", [mate, theirs])
    build.page.evaluate("k => pickTeam(k)", mate)
    assert build.mine_only_chips() == 1
    build.tap_mine_only()
    assert build.listed_slugs() == {theirs}, "David's players, on the list too, are not theirs"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(SECTION, ac="a reader with no followed team has no Mine only chip and no My players preset")
def test_a_first_visit_has_no_mine_only_chip_and_no_my_players_preset(mount):
    build, errors = open_build(mount, init=(FRESH_READER,))
    assert build.held_by(DAVIDS) & build.listable_slugs(), "David's teams hold players on the list"
    assert build.mine_only_chips() == 0
    assert build.lit_players()[0] == 0, "none of the lines wears the lime ring"
    assert build.slip_presets() == ["blank"], "Clear stays; My players needs a team"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(SECTION, ac="a reader who follows a team has the My players preset")
def test_a_reader_who_follows_a_team_has_the_my_players_preset(mount):
    build, errors = open_build(mount)
    assert build.slip_presets() == ["mine", "blank"]
    assert errors == []
