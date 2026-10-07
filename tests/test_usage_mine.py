"""Whose players the Usage grid marks as the reader's own (data/usage.js usageMine, 2026-10-06).

David, 2026-10-06, on Ranks: "Unselecting your team doesn't remove them from the MINE designation." Usage had the
same bug: it marked every roster on the page, a leaguemate's included, so the mark and its Mine filter never
followed what the reader follows. The rule is Ranks': the players on the teams the switch lists as followed.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.teamswitch import TeamSwitchPage
from pages.usage import UsagePage

PHONE = (390, 844)
FOLLOWED = ["yahoo", "espn", "ayo"]     # the suite's seed follows David's three


@pytest.mark.render
@pytest.mark.req("Leaguemates", ac="a leaguemate's players are not the reader's unless the reader follows that team")
def test_a_leaguemates_player_is_not_mine_until_the_reader_follows_that_team(mount):
    page, errors = mount("usage", size=PHONE)
    usage = UsagePage(page)
    mate, theirs = usage.first_mate(), next(s for s in usage.shown_slugs() if s not in usage.held_by(FOLLOWED))
    assert mate, "the fixture has a leaguemate"
    usage.put_on_roster(mate, theirs)
    usage.redraw()
    assert theirs in usage.shown_slugs() and theirs not in usage.mine_slugs(), "on a team nobody here follows"
    usage.follow(mate)
    assert theirs in usage.mine_slugs(), "followed, he is the reader's"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Leaguemates", ac="unfollowing a team takes its players off the mark and the Mine filter at once")
def test_unfollowing_a_team_takes_its_players_off_mine_without_a_reload(mount):
    page, errors = mount("usage", size=PHONE)
    usage, switch = UsagePage(page), TeamSwitchPage(page)
    shown, followed = set(usage.shown_slugs()), list(FOLLOWED)
    assert usage.mine_slugs() == usage.held_by(followed) & shown != set(), "the fixture holds players the grid shows"
    switch.open_menu()
    wrong_mine = []
    for gone in list(followed):
        switch.follow(gone)
        followed.remove(gone)
        if usage.mine_slugs() != usage.held_by(followed) & shown:
            wrong_mine.append(gone)
    assert wrong_mine == [], "MINE did not match the teams still followed after unfollowing these"
    assert usage.mine_slugs() == set()
    switch.toggle()                     # the menu covers the settings chip
    usage.filter_to_mine()
    assert usage.shown_slugs() == [], "the Mine filter shows no one when nothing is followed"
    assert errors == []
