"""Signed weeks (David, 2026-10-07): every week a player finished top 3 at his position is a signed week, a gold
bar on the Sheet row and the card back. design/signed.py `signed_weeks` lists them per page player, ranked the
way the autograph is (over every player ff-jarvis logged that week, every completed week). The bar model and
the drawing: test_js_pointsbars.py, test_roster_gold.py."""
import pytest

from signed import completed_weeks, signed_weeks

REQ = "Phone layout"
GAMES = [{"week": 1, "home": "A", "away": "B"}, {"week": 1, "home": "C", "away": "D"},
         {"week": 2, "home": "A", "away": "C"}, {"week": 2, "home": "B", "away": "D"},
         {"week": 3, "home": "A", "away": "D"}, {"week": 3, "home": "B", "away": "C"}]


def row(name, wk, pts, pos="RB", team="A"):
    return {"name": name, "pos": pos, "week": wk, "team": team, "pts": pts}


def full_week(wk, extra):
    """`extra` rows plus one filler per club, so the week counts as completed."""
    return extra + [row(f"Fill{wk}{t}", wk, 0.0, "K", t) for t in "ABCD"]


def slug(n):
    return n.lower().replace(" ", "-")


ROWS = (full_week(1, [row("R0", 1, 30), row("R1", 1, 20), row("R2", 1, 10), row("R3", 1, 5), row("Q0", 1, 9, "QB")])
        + full_week(2, [row("R3", 2, 30), row("R0", 2, 1), row("R1", 2, 2), row("R2", 2, 3)])
        + [row("R0", 3, 99)])                      # week 3: Thursday's game alone, not completed


@pytest.mark.req(REQ, ac="a signed week is any completed week he finished top three at his position")
def test_every_completed_week_he_finished_top_three_is_a_signed_week():
    got = signed_weeks({"rows": ROWS}, {"games": GAMES}, slug, {"r0", "r2", "r3", "q0"})
    assert got == {"r0": [1], "r2": [1, 2], "r3": [2], "q0": [1]}, "r3 was 4th in week 1, r0 4th in week 2; week 3 is not complete"


@pytest.mark.req(REQ, ac="a player in the top three in two weeks lists both, in order")
def test_a_player_signed_twice_lists_both_weeks_in_order():
    rows = ROWS + [row("R0", 2, 40)]
    got = signed_weeks({"rows": rows}, {"games": GAMES}, slug, {"r0"})
    assert got == {"r0": [1, 2]}


@pytest.mark.req(REQ, ac="the block the page gets keeps the autograph's wk and players and adds the weeks")
def test_the_page_block_adds_weeks_beside_the_autograph():
    from signed import with_weeks
    got = with_weeks({"rows": ROWS}, {"games": GAMES}, slug, {"r2"})
    assert got == {"wk": 2, "players": {"r2": {"rank": 2, "pts": 3}}, "weeks": {"r2": [1, 2]}}
    assert with_weeks({"rows": ROWS}, {"games": []}, slug, {"r2"}) is None


@pytest.mark.req(REQ, ac="completed weeks are the ones every club played in")
def test_completed_weeks_are_those_every_scheduled_club_logged():
    assert completed_weeks(ROWS, GAMES) == [1, 2]


@pytest.mark.req(REQ, ac="no game log or no completed week means no signed weeks")
def test_without_a_completed_week_there_are_no_signed_weeks():
    assert signed_weeks({"rows": ROWS}, {"games": []}, slug, {"r0"}) == {}
    assert signed_weeks(None, {"games": GAMES}, slug, {"r0"}) == {}
