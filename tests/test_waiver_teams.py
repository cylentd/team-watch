"""Every other team's own Waivers (ledger #22, ff-jarvis `model.season.waiver_teams`): the build cuts
data/waiver_teams.json into LIVE_WAIVER_TEAMS (design/waiver.py `live_waiver_teams`, read through
design/sources.py), and a reader who picks another team in the League group sees that team's cards.

The fixture holds one team, AYO's Don Wick, key `ayo-don-wick` (design/mates.py's `<league>-<slug>`):
a must-claim, a watch and a speculative card, no FAAB, and WR as the team's need. It is not the first
leaguemate on purpose: tests/test_mates_page.py (frozen) holds the first one to the league's rail alone.
The Node half of the behaviour is tests/test_js_waiver_teams.py.
"""
import json
import re

import pytest

import contract
import sources
import waiver
from build import slugify
from component import mount  # noqa: F401  (the fixture)
from conftest import FIXTURES
from pages.mates import MatesPage
from wording import words

DATA = FIXTURES / "data"
KEY = "ayo-don-wick"
pytestmark = pytest.mark.req("Waivers")


def teams_block(built):
    m = re.search(r"^const LIVE_WAIVER_TEAMS = (.*);$", built.fragment, re.M)
    assert m, "LIVE_WAIVER_TEAMS is not injected"
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_each_team_is_keyed_like_mates_and_is_a_live_waiver_block():
    got = waiver.live_waiver_teams(DATA, slugify)
    assert got["date"] == "2026-09-22"
    assert list(got["teams"]) == [KEY]
    team = got["teams"][KEY]
    assert contract.problems("LIVE_WAIVER", team) == []
    assert contract.problems("LIVE_WAIVER_TEAMS", got) == []
    assert [r["tier"] for r in team["players"]] == ["must", "watch", "spec"]
    assert team["players"][0]["leagues"]["ayo"]["verdict"]["over"] == "Rival Starter"
    assert team["leagues_meta"]["ayo"]["faab_left"] is None, "a budget is its manager's alone"
    assert team["leagues_meta"]["ayo"]["needs"] == ["WR"]


def test_a_card_keeps_the_team_judged_tier_per_league():
    team = waiver.live_waiver_teams(DATA, slugify)["teams"][KEY]
    assert [(r["n"], r["leagues"]["ayo"]["tier"]) for r in team["players"]] == [
        ("Emanuel Wilson", "must"), ("Parker Washington", "watch"), ("Juwan Johnson", "spec")]


def test_no_file_or_a_broken_one_means_no_block(tmp_path):
    assert waiver.live_waiver_teams(tmp_path, slugify) is None
    (tmp_path / "waiver_teams.json").write_text("{not json", encoding="utf-8")
    assert waiver.live_waiver_teams(tmp_path, slugify) is None
    (tmp_path / "waiver_teams.json").write_text(json.dumps({"date": "2026-09-22", "teams": {}}), encoding="utf-8")
    assert waiver.live_waiver_teams(tmp_path, slugify) is None


def test_the_file_is_read_through_sources():
    assert sources.load_waiver_teams(DATA)["kind"] == "waiver_teams"
    assert sources.load_waiver_teams(DATA / "nowhere") is None


def test_the_headshots_of_every_teams_cards_are_wanted():
    got = waiver.live_waiver_teams(DATA, slugify)
    assert waiver.slugs(None, got) == ["emanuel-wilson", "juwan-johnson", "parker-washington"]


def test_the_build_injects_the_block_and_it_meets_the_contract(built):
    block = teams_block(built)
    assert list(block["teams"]) == [KEY]
    assert contract.problems("LIVE_WAIVER_TEAMS", block) == []


def test_a_block_missing_a_field_the_page_reads_is_a_contract_problem():
    got = waiver.live_waiver_teams(DATA, slugify)
    del got["teams"][KEY]["leagues_meta"]
    assert contract.problems("LIVE_WAIVER_TEAMS", got) == [f"LIVE_WAIVER_TEAMS.teams['{KEY}'].leagues_meta"]


@pytest.mark.render
def test_picking_another_team_shows_that_teams_own_cards_and_the_leagues_rail(mount, built):
    """A visitor (no owner token) picks Don Wick: his three cards, his must-claim count and his tab
    count, no FAAB. The rail is the league's wire with David's status rows out."""
    page, errors = mount("waivers", size=(390, 844))
    mate = MatesPage(page)
    mate.waivers.view_as_visitor()
    page.evaluate("LIVE_WIRE.leagues.ayo = LIVE_WIRE.leagues.yahoo")   # a league with a wire to keep
    events = [e["kind"] for e in teams_block_events(built)]
    kept = events.count("path") + events.count("drop") + min(events.count("adds"), 3)
    mate.show_waivers_of(KEY)
    assert mate.waivers.claim_card_count() == 3
    assert mate.mate_rail_count() == 0, "the soon note is for a team with no cards"
    hero = mate.waivers.hero_text()
    assert words("waiver.hero.mustOne") in hero and "FAAB" not in hero
    assert mate.waivers.subnav_count_badges() == 1
    assert mate.status_row_count() == 0
    assert mate.waivers.claim_row_count() == kept, "the rail is the league's, not the team's"
    assert errors == []


@pytest.mark.render
def test_a_team_with_no_block_keeps_todays_view(mount, built):
    """The first leaguemate has no block in the fixture: the league's rail and the soon note, no cards."""
    page, errors = mount("waivers", size=(390, 844))
    mate = MatesPage(page)
    first = json.loads(re.search(r"^const LIVE_MATES = (.*);$", built.fragment, re.M).group(1))["teams"][0]["key"]
    mate.waivers.view_as_visitor()
    mate.show_waivers_of(first)
    assert mate.waivers.claim_card_count() == 0 and mate.mate_rail_count() == 0
    assert mate.waivers.subnav_count_badges() == 0
    assert errors == []


def teams_block_events(built):
    wire = json.loads(re.search(r"^const LIVE_WIRE = (.*);$", built.fragment, re.M).group(1))
    return wire["leagues"]["yahoo"]["events"]
