"""Whose cards Waivers draws (data/waiver.js, 2026-10-07; ledger #22): the team on screen's own block
from LIVE_WAIVER_TEAMS when a leaguemate has one, else David's packet, else nothing. Data to data, so
Node; what the screen draws from it is tests/test_waiver_teams.py.

The Node sandbox has no localStorage, so `isOwner()` is false (a visitor). The owner is the same sandbox
with a localStorage that holds his token (the way tests/test_js_waiver.py does it).
"""
import pytest

DAVID = {"players": [{"n": "David Pick", "tier": "must", "leagues": {"ayo": {"status": "fa", "tier": "must"}}}],
         "leagues_meta": {"ayo": {"label": "AYO"}}}
OWN = {"players": [{"n": "Own Must", "tier": "must", "leagues": {"ayo": {"status": "fa", "tier": "must"}}},
                   {"n": "Own Stash", "tier": "stash", "leagues": {"ayo": {"status": "fa", "tier": "stash"}}},
                   {"n": "Own Rostered", "tier": "watch", "leagues": {"ayo": {"status": "rostered", "tier": "watch"}}}],
       "leagues_meta": {"ayo": {"label": "AYO"}}}
TEAMS = {"ayo": {"key": "ayo"}, "ayo-don-wick": {"key": "ayo-don-wick", "mate": True, "league": "ayo"},
         "ayo-no-block": {"key": "ayo-no-block", "mate": True, "league": "ayo"},
         "link": {"key": "link", "connected": True}}


@pytest.fixture
def waiver(node_js):
    return node_js("data/owner.js", "data/waiver.js", globals={
        "LIVE_WAIVER": DAVID, "LIVE_WAIVER_TEAMS": {"date": "2026-09-22", "teams": {"ayo-don-wick": OWN}},
        "TEAMS": TEAMS, "VIEW": "ayo"})


def test_a_leaguemate_with_a_block_has_cards_of_its_own_for_any_reader(waiver):
    assert waiver("wvOwn(TEAMS['ayo-don-wick'])") is True
    assert waiver("waiverBlock(TEAMS['ayo-don-wick']) === LIVE_WAIVER_TEAMS.teams['ayo-don-wick']")


def test_a_leaguemate_without_a_block_has_none(waiver):
    assert waiver("wvOwn(TEAMS['ayo-no-block'])") is False
    assert waiver("waiverBlock(TEAMS['ayo-no-block'])") is None


def test_davids_cards_stay_his_browsers_alone(waiver):
    assert waiver("wvOwn(TEAMS.ayo)") is False, "a visitor"
    waiver("() => { globalThis.localStorage = {getItem: () => OWNER_HASH}; }")
    assert waiver("wvOwn(TEAMS.ayo)") is True
    assert waiver("waiverBlock(TEAMS.ayo) === LIVE_WAIVER")


def test_a_connected_league_has_no_cards(waiver):
    assert waiver("wvOwn(TEAMS.link)") is False
    assert waiver("waiverBlock(TEAMS.link)") is None


def test_a_teams_list_is_its_own_players_open_in_the_league_grouped_by_tier(waiver):
    blk = "waiverBlock(TEAMS['ayo-don-wick'])"
    assert waiver(f"waiverIn('ayo', {blk}).map(([r]) => r.n)") == ["Own Must", "Own Stash"], "rostered is not a card"
    assert waiver(f"waiverIn('ayo', {blk}).map(([, i]) => i)") == [0, 1], "the index the profile button carries"
    assert waiver(f"waiverMustIn('ayo', {blk})") == 1


def test_with_no_block_given_the_lists_are_davids(waiver):
    assert waiver("waiverIn('ayo').map(([r]) => r.n)") == ["David Pick"]
    assert waiver("waiverMustIn('ayo')") == 1
    assert waiver("waiverPlayers().length") == 1


def test_a_missing_teams_block_leaves_every_team_without_cards(node_js):
    bare = node_js("data/owner.js", "data/waiver.js", globals={"LIVE_WAIVER": DAVID, "TEAMS": TEAMS, "VIEW": "ayo"})
    assert bare("wvOwn(TEAMS['ayo-don-wick'])") is False
    assert bare("waiverBlock(TEAMS['ayo-don-wick'])") is None


def test_a_teams_meta_is_read_from_its_own_block_and_david_s_when_none_is_given(waiver):
    assert waiver("waiverMeta(waiverBlock(TEAMS['ayo-don-wick'])).ayo.label") == "AYO"
    assert waiver("waiverMeta().ayo.label") == "AYO"
