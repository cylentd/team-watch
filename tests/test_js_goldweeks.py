"""Signed weeks in the bar model (David, 2026-10-07): every week a player finished top 3 at his position is a
gold bar, on the Sheet row and the card back. `pbSignedWeeks` (data/pointsbars.js) reads LIVE_SIGNED for one
player, `pbMarkSigned` flags the slots. Pure parts, in Node; the drawing is test_roster_gold.py."""
import pytest


@pytest.fixture(scope="module")
def pb(node_js):
    return node_js("data/pointsbars.js")


def model(pb, played, proj=12.0, week=5):
    return pb("pbModel", [{"wk": wk, "pts": pts} for wk, pts in played], proj, week)


def test_the_weeks_come_from_the_list_and_the_autograph_week(pb):
    signed = {"wk": 4, "players": {"a": {"rank": 1, "pts": 30}}, "weeks": {"a": [1, 2], "b": [3]}}
    assert pb("pbSignedWeeks", signed, "a") == [1, 2, 4], "the autograph's week joins the list, in order"
    assert pb("pbSignedWeeks", signed, "b") == [3]
    assert pb("pbSignedWeeks", signed, "c") == []


def test_a_block_without_the_list_still_gives_the_autograph_week(pb):
    signed = {"wk": 3, "players": {"a": {"rank": 2, "pts": 20}}}
    assert pb("pbSignedWeeks", signed, "a") == [3] and pb("pbSignedWeeks", signed, "b") == []


def test_no_block_or_no_slug_means_no_weeks(pb):
    assert pb("pbSignedWeeks", None, "a") == [] and pb("pbSignedWeeks", {"wk": 1, "players": {}}, None) == []


def test_only_played_weeks_in_the_list_are_marked(pb):
    m = pb("pbMarkSigned", model(pb, [(1, 10.0), (3, 20.0), (4, 5.0)]), [1, 2, 3])
    assert [(s["wk"], s.get("signed", False)) for s in m["slots"]] == [(1, True), (2, False), (3, True), (4, False)]
    assert not m["proj"].get("signed"), "the projection is never a signed week"


def test_marking_nothing_marks_nothing_and_passes_null_through(pb):
    m = pb("pbMarkSigned", model(pb, [(1, 10.0), (2, 20.0)]), [])
    assert [s.get("signed", False) for s in m["slots"]] == [False] * 4
    assert pb("pbMarkSigned", None, [1]) is None
