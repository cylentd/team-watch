"""Whose players are "mine" (data/mates.js rosterSlugs, 2026-10-06), in Node.

Ranks marks the reader's own players. It used to mark every roster on the page that was not a leaguemate's,
which is David's three teams for every reader whatever they picked or unfollowed. The marked set is now the
rosters of the teams the reader follows, so this is the one function that says it: teams in, slugs out.
"""
import pytest

TEAMS = {
    "yahoo": {"roster": [{"slug": "a"}, {"slug": "b"}]},
    "espn": {"roster": [{"slug": "b"}, {"slug": "c"}, {"n": "No Slug"}]},
    "espn-run-it-back": {"roster": [{"slug": "d"}], "mate": True},
    "empty": {},
}


@pytest.fixture(scope="module")
def mates(node_js):
    return node_js("data/mates.js", globals={"TEAMS": TEAMS})


def slugs(mates, keys):
    return sorted(mates("(ks) => [...rosterSlugs(TEAMS, ks)]", keys))


def test_no_team_followed_marks_no_one(mates):
    assert slugs(mates, []) == []


def test_one_team_marks_its_roster(mates):
    assert slugs(mates, ["yahoo"]) == ["a", "b"]


def test_a_player_on_two_followed_teams_counts_once_and_a_row_without_a_slug_is_skipped(mates):
    assert slugs(mates, ["yahoo", "espn"]) == ["a", "b", "c"]


def test_a_leaguemates_team_marks_its_players_when_the_reader_follows_it(mates):
    assert slugs(mates, ["espn-run-it-back"]) == ["d"]


def test_a_key_the_page_no_longer_has_and_a_team_with_no_roster_mark_no_one(mates):
    assert slugs(mates, ["gone", "empty"]) == []
