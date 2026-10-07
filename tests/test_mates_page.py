"""A leaguemate picks their own team (leaguemates phase 1, 2026-09-25): every team in David's two
leagues is in the team switch under its league's name, a pick is remembered in the browser, and a
leaguemate's team has no Waivers (ff-jarvis builds David's only until phase 3).

Component tests: the Roster and Waivers mounted (tests/component.py); every locator is in tests/pages/mates.py.
The leaguemates and the league's wire come from the build's own blocks, never from the page under test."""
import json
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.mates import MatesPage


def block(built, name):
    """A `const NAME = <json>;` block the build injected, parsed."""
    return json.loads(re.search(rf"const {name} = (.*?);\n", built.fragment).group(1))


@pytest.mark.render
def test_a_leaguemate_picks_their_team_and_it_sticks(mount, built):
    """My teams asks first (2026-09-27): with no pick in this browser, every My teams view is the
    picker, all 24 teams by league and no "none", never David's roster."""
    mates = [m["key"] for m in block(built, "LIVE_MATES")["teams"]]
    assert mates, "the fixture's roster files hold no other team"
    page, errors = mount("roster", size=(390, 844))
    mate = MatesPage(page)
    mine = 3        # David's team per league: three since AYO, 2026-09-29
    mate.forget_pick_and_show_roster()
    assert mate.picker_team_count() == len(mates) + mine, "Roster asks first"
    assert mate.rows.count() == 0, "no roster until a pick"
    # Waivers and Recap do not ask (2026-10-05, the League merge): the wire and the league's week are the league's.
    mate.forget_owner_and_show_waivers()
    assert mate.picker_count() == 0 and mate.chip.team_name() == "Pick your team"
    mate.show("recap")
    assert mate.picker_count() == 0 and mate.chip.chip_switch_count() == 1
    mate.show("roster")
    assert mate.league_list_count() == mine, "one list per league"
    mate.pick(mates[0])
    assert mate.viewed_team() == mates[0]
    assert mate.stored_pick() == mates[0]
    assert mate.picker_count() == 0, "asked only until a pick"
    assert "Waivers" in mate.subnav_text(), "their league's rail (phase 2)"
    assert mate.waivers.subnav_count_badges() == 0, "but no claim count: that list is David's"
    mate.show("roster")
    assert mate.rows.count() > 0, "the leaguemate's roster draws"
    mate.reload()
    assert mate.viewed_team() == mates[0], "the pick opens next time"
    assert errors == []


@pytest.mark.render
def test_a_leaguemates_waivers_is_their_leagues_rail_without_davids_advice(mount, built):
    """Phase 2 (2026-09-26): a leaguemate's Waivers tab shows the league's Breaking rail, keyed by
    league, with no status rows (David's players), no verdicts, no cards, no must-claim count."""
    teams = block(built, "LIVE_MATES")["teams"]
    assert teams, "the fixture's roster files hold no other team"
    key, league = teams[0]["key"], teams[0]["league"]
    # the rail keeps path and drop events, at most three adds (data/wire.js), and none about David's own players
    events = [e["kind"] for e in block(built, "LIVE_WIRE")["leagues"][league]["events"]]
    kept = events.count("path") + events.count("drop") + min(events.count("adds"), 3)
    page, errors = mount("waivers", size=(390, 844))
    mate = MatesPage(page)
    mate.show_waivers_of(key)
    assert "Waivers" in mate.subnav_text()
    assert mate.waivers.claim_card_count() == 0 and mate.mate_rail_count() == 1
    assert mate.status_row_count() == 0
    assert mate.waivers.claim_row_count() == kept, "every league-wide row stays"
    text = mate.view_text()
    assert "must-claim" not in text.lower() and "FAAB" not in text
    assert errors == []


# Live followed a leaguemate's ESPN board until 2026-09-28; it now shows every matchup in both
# leagues to everyone (tests/test_gameday.py), so there is nothing per-team left to follow.


def test_owner_names_never_reach_the_page(page_file):
    """Team names only (David, 2026-09-25): LIVE_MATES carries a team's name and roster, nothing
    about who owns it."""
    text = page_file.read_text(encoding="utf-8")
    m = re.search(r"const LIVE_MATES = (.*?);\n", text)
    assert m and m.group(1) != "null", "no LIVE_MATES block in the fixture page"
    for team in json.loads(m.group(1))["teams"]:
        assert set(team) == {"key", "league", "name", "roster"}
