"""design/waiver.py: the Waivers sub-tab's block, against the fixture packet."""
import json
import re

import contract


def _waiver(built):
    m = re.search(r"^const LIVE_WAIVER = (.*);$", built.fragment, re.M)
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_block_carries_both_leagues_and_the_clear_time(built):
    w = _waiver(built)
    assert w["clears"] == "2026-09-23T00:00" and w["week"] == 2
    assert set(w["leagues"]) == {"espn", "yahoo"}
    assert w["leagues"]["yahoo"]["team"] == "Chat Take the Wheel \U0001F47E"
    assert w["leagues"]["espn"]["budget_left"] == 1000


def test_rows_keep_the_packet_numbers_and_gain_a_slug(built):
    espn = _waiver(built)["leagues"]["espn"]
    fant, lock, claiborne = espn["wire"]
    assert fant["slug"] == "noah-fant" and fant["role_pts"] == 6.6 and fant["edge"] == 2.4
    assert fant["starts"] == {"replaces": "George Kittle", "slot": "TE", "their_pts": 9.0, "margin": -2.4}
    assert lock["promoted"] == {"from": 2, "to": 1}
    assert claiborne["vacated"] == {"name": "Jordan Mason", "injury": "Thumb"} and claiborne["starts"] is None
    assert espn["adds"][0]["upgrade"]["margin"] == 1.8


def test_a_row_missing_a_field_fails_the_contract():
    row = {k: None for k in contract.WAIVER_ROW}
    del row["edge"]
    obj = {"date": "", "week": 2, "clears": "", "leagues": {"espn": {
        "team": "x", "type": "faab", "budget_left": 1, "lineup_unknown": False,
        "wire": [row], "adds": [], "stash": [], "drops": []}}}
    assert contract.problems("LIVE_WAIVER", obj) == ["LIVE_WAIVER.leagues['espn'].wire[0].edge"]
