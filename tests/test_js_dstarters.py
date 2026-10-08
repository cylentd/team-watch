"""Defenders out (data/dstarters.js, 2026-10-06), in Node: which defenses are short, and the one line that says so.

LIVE_D_STARTERS is ff-jarvis's d_starters block cut by design/d_starters.py (test_d_starters.py). The page computes
no number: a count is the file's, a name the file's, a status the file's. What it decides is which unit a position
reads (a back the front seven, a WR or TE the secondary, a QB the whole defense), that a missing count is not a zero,
and the wording, which is a plain fact: it never says start, sit, bet, fade or lean.
The fixture is week 2: NO two front seven out, CAR a lineman (IR) and a corner (Doubtful), NYJ one starter off the team
with no unit, LA (the page's LAR) null counts, PIT and CLE none.
"""
import json
import pathlib
import re

import pytest

from d_starters import live_d_starters
from wording import words

FIX = live_d_starters(json.loads((pathlib.Path(__file__).parent / "fixtures" / "data" / "d_starters.json").read_text(encoding="utf-8")))
REQ = "Defenders out"
VERDICT = re.compile(r"\b(start|sit|bet|fade|lean|lock|smash|avoid|target|buy|sell)(s|ing)?\b", re.I)


@pytest.fixture(scope="module")
def ds(node_js):
    return node_js("data/dstarters.js")


@pytest.mark.req(REQ, ac="a game gets one chip per defense with a starter out, away first")
def test_a_game_gets_a_view_for_each_short_defense(ds):
    no = ds("dsGameViews", FIX, {"away": "ATL", "home": "NO"}, 2)
    assert [(v["team"], v["kind"], v["n"], [p["name"] for p in v["players"]]) for v in no] == [
        ("NO", "front7", 2, ["Kaden Elliss", "Carl Granderson"])]
    assert ds("dsGameViews", FIX, {"away": "PIT", "home": "CLE"}, 2) == []          # the game with none missing


@pytest.mark.req(REQ, ac="a defense missing starters from both units reads as starters, a missing unit never as zero")
def test_a_mixed_defense_reads_as_starters_and_a_null_count_as_nothing(ds):
    car = ds("dsGameViews", FIX, {"away": "DET", "home": "CAR"}, 2)
    assert [(v["team"], v["kind"], v["n"]) for v in car] == [("CAR", "any", 2)]
    nyj = ds("dsGameViews", FIX, {"away": "SF", "home": "NYJ"}, 2)
    assert [(v["team"], v["kind"], v["n"]) for v in nyj] == [("NYJ", "any", 1)]      # a starter with no unit
    assert ds("dsGameViews", FIX, {"away": "JAX", "home": "LA"}, 2) == []               # LA has no earlier game: null, not none


@pytest.mark.req(REQ, ac="either spelling of a team finds its defense")
def test_the_page_and_nflverse_spellings_find_the_same_defense(ds):
    assert ds("dsTeam", FIX, "LA")["team"] == "LAR" and ds("dsTeam", FIX, "LAR")["team"] == "LAR"
    assert ds("dsTeam", FIX, "XXX") is None


@pytest.mark.req(REQ, ac="a back reads the front seven, a WR or TE the secondary, a QB the whole defense")
def test_a_position_reads_its_own_unit(ds):
    no = lambda pos: ds("dsPlayerView", FIX, pos, 2, "NO")
    assert (no("RB")["kind"], no("RB")["n"]) == ("front7", 2)
    assert no("WR") is None and no("TE") is None                    # NO's secondary is whole
    assert (no("QB")["kind"], no("QB")["n"]) == ("front7", 2)       # all of them, and all of them are front seven
    car = lambda pos: ds("dsPlayerView", FIX, pos, 2, "CAR")
    assert [p["name"] for p in car("RB")["players"]] == ["Derrick Brown"]
    assert [p["name"] for p in car("WR")["players"]] == ["Jaycee Horn"] and car("TE")["kind"] == "secondary"
    assert (car("QB")["kind"], car("QB")["n"]) == ("any", 2)
    assert ds("dsPlayerView", FIX, "K", 2, "CAR") is None and ds("dsPlayerView", FIX, "DEF", 2, "CAR") is None


@pytest.mark.req(REQ, ac="a note needs the block's own week, an opponent and counts")
def test_no_note_for_another_week_no_opponent_or_a_null_defense(ds):
    assert ds("dsPlayerView", FIX, "RB", 3, "NO") is None            # the block is week 2
    assert ds("dsPlayerView", FIX, "RB", 2, None) is None
    assert ds("dsPlayerView", FIX, "RB", 2, "LA") is None            # null counts
    assert ds("dsPlayerView", None, "RB", 2, "NO") is None
    assert ds("dsGameViews", None, {"away": "ATL", "home": "NO"}, 2) == []
    assert ds("dsGameViews", {}, {"away": "ATL", "home": "NO"}, 2) == []
    assert ds("dsGameViews", FIX, {"away": "ATL", "home": "NO"}, 1) == []        # an earlier week's game: this block is week 2


@pytest.mark.req(REQ, ac="the chip says how many, which unit, and names up to three")
@pytest.mark.parametrize("game,line", [
    ({"away": "ATL", "home": "NO"}, "NO D: 2 front-seven starters out (Elliss, Granderson)"),
    ({"away": "DET", "home": "CAR"}, "CAR D: 2 starters out (Brown, Horn)"),
    ({"away": "SF", "home": "NYJ"}, "NYJ D: 1 starter out (McDonald)"),
])
def test_the_chip_line(ds, game, line):
    (view,) = ds("dsGameViews", FIX, game, 2)
    assert ds("dsChipText", view) == line


@pytest.mark.req(REQ, ac="one missing starter in a unit is singular; past three names the rest are counted")
def test_singular_and_the_names_cap(ds):
    car = ds("dsPlayerView", FIX, "WR", 2, "CAR")
    assert ds("dsChipText", car) == "CAR D: 1 secondary starter out (Horn)"
    many = {"team": "XYZ", "kind": "front7", "n": 5, "players": [{"name": n} for n in
            ("A One", "B Two", "C Three", "D Four", "E Five")]}
    assert ds("dsChipText", many) == "XYZ D: 5 front-seven starters out (One, Two, Three +2)"
    three = {**many, "n": 3, "players": many["players"][:3]}
    assert ds("dsChipText", three) == "XYZ D: 3 front-seven starters out (One, Two, Three)"        # exactly three: no "+0"


@pytest.mark.req(REQ, ac="a status is a word the reader knows, and a status the page does not know is shown as it came")
def test_status_words(ds):
    assert [ds("dsStatusWord", s) for s in ("Out", "Doubtful", "IR", "PUP", "Sus", "Suspended", "Off team")] == [
        words("ds.status.out"), words("ds.status.doubtful"), words("ds.status.ir"), words("ds.status.pup"),
        words("ds.status.sus"), words("ds.status.suspended"), words("ds.status.offteam")]
    assert ds("dsStatusWord", "Mystery") == "Mystery"


@pytest.mark.req(REQ, ac="a surname drops a generational suffix")
def test_surnames(ds):
    assert ds("dsSurname", "Will McDonald IV") == "McDonald"
    assert ds("dsSurname", "Kaden Elliss") == "Elliss"
    assert ds("dsSurname", "Madonna") == "Madonna"


@pytest.mark.req(REQ, ac="the wording is a plain fact: no start, sit, bet, fade or lean, and it says unproven")
def test_the_copy_is_a_fact_and_says_unproven(ds):
    from jsunit import COPY
    ds_keys = {k: v for k, v in COPY.items() if k.startswith("ds.")}
    assert ds_keys, "the wording keys are missing from content.json"
    verdicts = {k: v for k, v in ds_keys.items() if VERDICT.search(v)}
    assert verdicts == {}, "wording that says start, sit, bet, fade or lean"
    why = ds("dsWhyText", FIX["rules"])
    assert why == FIX["rules"]["evidence"] and "unproven" in why and "2028" in why
    fallback = ds("dsWhyText", None)
    assert "unproven" in fallback.lower() and "2028" in fallback and "12.93" in fallback
