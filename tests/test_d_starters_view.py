"""Defenders out, drawn (2026-10-06): a chip per short defense in Preview's box score, and a note under the rank in
the profile's Matchup pane. A displayed fact: nothing here moves a projection, a rank or an order, and no word of it
says start, sit, bet or fade. The data rules (which unit a position reads, the wording, the spellings) are Node's,
tests/test_js_dstarters.py; this file proves the screen draws them and the taps open.

The Preview fixture is week 2, five games in kickoff order: 0 PIT @ CLE (none missing), 1 JAX @ LA (LA has no earlier
game: null counts), 2 DET @ CAR (a lineman on IR and a corner Doubtful), 3 SF @ NYJ (one starter off the team, no
unit), 4 ATL @ NO (Elliss and Granderson, both front seven, Out). The profile fixture's next games are week 3 (Chase
Brown home to PIT, Amon-Ra St. Brown at KC), so those tests plant a block for week 3.
"""
import re

import pytest

from component import Mounter, mount  # noqa: F401  (the fixture)
from pages.dstarters import DefendersOut
from pages.roster import on_roster
from wording import words

REQ = "Defenders out"
SLOT = {"pos": "DT", "unit": "front7", "status": "Out", "snap_share": 0.1}
VERDICT = re.compile(r"\b(start|sit|bet|fade|lean|lock|smash|avoid|target|buy|sell)(s|ing)?\b", re.I)
EVIDENCE = "unproven until the forward test is scored in 2028"


def short(code, opp, players):
    """A defense record for the profile tests, counts taken from its players."""
    return {"team": code, "opp": opp, "n_starters": 11, "n_missing": len(players), "share": 0.2, "players": players,
            "front7_missing": sum(p["unit"] == "front7" for p in players),
            "secondary_missing": sum(p["unit"] == "secondary" for p in players)}


@pytest.fixture(scope="module")
def no_block(mount, built, tmp_path_factory):
    """Preview on a page whose feed carried no d_starters block: the const is null, as the build writes it. Built on
    `mount` so it stays a component test and uses the worker's one browser."""
    fragment = re.sub(r"^const LIVE_D_STARTERS = .*;$", "const LIVE_D_STARTERS = null;", built.fragment, flags=re.M)
    assert fragment != built.fragment, "the fixture build injects no LIVE_D_STARTERS to remove"
    m = Mounter(mount.browser, tmp_path_factory.getbasetemp() / "component-no-ds", fragment)
    yield m
    m.pages.close()


def preview_game(mount, i):
    page, errors = mount("preview")
    ds = DefendersOut(page, "preview")
    ds.open_game(i)
    return ds, errors


# ------------------------------------------------------------------ Preview

@pytest.mark.req(REQ, ac="a defense missing starters gets one chip that opens to the names, statuses and the unproven why")
def test_the_game_with_two_front_seven_starters_out_gets_a_chip_that_opens_to_the_names(mount):
    ds, errors = preview_game(mount, 4)
    assert ds.lines() == ["NO D: 2 front-seven starters out (Elliss, Granderson)"]
    assert ds.teams() == ["NO"] and ds.section_count() == 1
    assert not ds.is_open() and not ds.names_visible()
    ds.open()
    assert ds.is_open() and ds.names_visible()
    assert ds.names() == [("Kaden Elliss", "LB · Out · 11% of starter snaps"),
                          ("Carl Granderson", "DE · Out · 7% of starter snaps")]
    assert EVIDENCE in ds.why() and "2018 and 2020-2025" in ds.why()
    assert not VERDICT.search(ds.lines()[0] + ds.why())
    assert errors == []


@pytest.mark.req(REQ, ac="a defense missing a lineman and a corner says starters, and its statuses are spelled out")
def test_a_defense_missing_both_units_says_starters_and_spells_each_status(mount):
    ds, errors = preview_game(mount, 2)
    assert ds.lines() == ["CAR D: 2 starters out (Brown, Horn)"]
    ds.open()
    assert ds.names() == [("Derrick Brown", f"DT · {words('ds.status.ir')} · 10% of starter snaps"),
                          ("Jaycee Horn", "CB · Doubtful · 7% of starter snaps")]
    assert errors == []


@pytest.mark.req(REQ, ac="a starter with no unit counts as a starter out, and one who left the team says so")
def test_a_starter_with_no_unit_who_left_the_team_is_still_named(mount):
    ds, errors = preview_game(mount, 3)
    assert ds.lines() == ["NYJ D: 1 starter out (McDonald)"]
    ds.open()
    assert ds.names() == [("Will McDonald IV", f"EDGE · {words('ds.status.offteam')} · 8% of starter snaps")]
    assert errors == []


@pytest.mark.req(REQ, ac="a game with none missing, and one defense with no earlier game, draw no row")
@pytest.mark.parametrize("i", [0, 1])
def test_a_game_with_nobody_out_or_a_null_count_draws_no_row(mount, i):
    ds, errors = preview_game(mount, i)
    assert (ds.count(), ds.section_count()) == (0, 0)
    assert errors == []


@pytest.mark.req(REQ, ac="a feed with no d_starters block draws the dossier whole, with no chip")
def test_with_no_block_the_dossier_draws_without_a_chip(no_block):
    ds, errors = preview_game(no_block, 4)
    assert (ds.count(), ds.section_count()) == (0, 0)
    assert errors == []


@pytest.mark.req(REQ, ac="a game that has kicked off no longer shows its chip: it is for setting lineups")
def test_a_game_past_kickoff_shows_no_chip(mount):
    page, errors = mount("preview", init=("Date.now = () => Date.parse('2026-09-22T01:00:00Z');",))
    ds = DefendersOut(page, "preview")
    ds.open_game(4)
    assert ds.count() == 0
    assert errors == []


# ------------------------------------------------------------------ the profile

def matchup_note(mount, plant, name):
    """Plant a week 3 block, open `name` from the roster and read his Matchup pane's chip."""
    profile, errors = on_roster(mount)
    ds = DefendersOut(profile.page, "profile")
    ds.plant(week=3, teams=plant)
    profile.open_from_roster(name)
    profile.tab("matchup")
    return profile, ds, errors


FRONT = [dict(SLOT, name="Alex Front"), dict(SLOT, name="Ben Rusher", pos="DE")]
BACK = [dict(SLOT, name="Cal Corner", pos="CB", unit="secondary", status="Doubtful")]


@pytest.mark.req(REQ, ac="a back sees the front seven of the defense he faces, not its secondary")
def test_a_back_reads_the_front_seven_of_the_defense_he_faces(mount):
    profile, ds, errors = matchup_note(mount, {"PIT": short("PIT", "CIN", FRONT + BACK)}, "Chase Brown")
    assert ds.lines() == ["PIT D: 2 front-seven starters out (Front, Rusher)"]
    ds.open()
    assert [n for n, _ in ds.names()] == ["Alex Front", "Ben Rusher"] and EVIDENCE in ds.why()
    assert errors == []


@pytest.mark.req(REQ, ac="a receiver sees the secondary, and a defense short only in the other unit draws nothing")
def test_a_receiver_reads_the_secondary_and_the_other_unit_draws_nothing(mount):
    profile, ds, errors = matchup_note(mount, {"KC": short("KC", "DET", FRONT + BACK)}, "Amon-Ra St. Brown")
    assert ds.lines() == ["KC D: 1 secondary starter out (Corner)"]
    profile.close()
    ds.plant(teams={"KC": short("KC", "DET", FRONT)})
    profile.open_from_roster("Amon-Ra St. Brown")
    profile.tab("matchup")
    assert ds.count() == 0 and profile.rank() == "9th easiest of 32 for WRs"      # the rank sentence still draws
    assert errors == []


@pytest.mark.req(REQ, ac="a block for another week gives no note: it is not his next game")
def test_a_block_for_another_week_gives_no_note(mount):
    profile, errors = on_roster(mount)
    ds = DefendersOut(profile.page, "profile")
    ds.plant(week=2, teams={"PIT": short("PIT", "CIN", FRONT)})
    profile.open_from_roster("Chase Brown")
    profile.tab("matchup")
    assert ds.count() == 0
    assert errors == []


@pytest.mark.req(REQ, ac="no block at all leaves the Matchup pane as it was")
def test_with_no_block_the_matchup_pane_is_unchanged(no_block):
    profile, errors = on_roster(no_block)
    profile.open_from_roster("Chase Brown")
    profile.tab("matchup")
    assert DefendersOut(profile.page, "profile").count() == 0
    assert profile.selected_tab() == "matchup"
    assert errors == []
