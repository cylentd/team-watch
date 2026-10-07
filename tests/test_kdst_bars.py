"""A kicker's and a defense's card back and Sheet row draw the same points bars as a player (David, 2026-10-07):
one bar per played week from LIVE_KDST under the picked league's scoring, a bye an empty slot, then the hollow
projection bar from LIVE_DST. A kicker's weeks that another kicker kicked are faded. The pure parts are
test_js_kdst.py. Component layer: `mount`, `KdstBars` (tests/pages/roster_kdst.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster_kdst import KdstBars
from pages.roster_motion import show_cards

REQ = "Phone layout"
PHONE = (360, 660)
SCENE = {"games": [{"week": 5, "home": "TEN", "away": "CIN", "kickoff": "2026-10-11T17:00:00Z"}],
         "factors": {}, "form": {}, "weather": {}}


def row(wk, kickers=("T.Boot",), dst=6.0, k=9.0):
    return {"week": wk, "opp": "CIN", "home": True, "dst_espn": dst + 1.5, "dst_yahoo": dst, "k_yahoo": k, "k_ayo": k - 1,
            "kickers": list(kickers)}


FULL = {"teams": {"TEN": [row(1), row(2, dst=2.0, k=12.0), row(3), row(4)]}}
BYE = {"teams": {"TEN": [row(1), row(3), row(4)]}}
SWAP = {"teams": {"TEN": [row(1, ("A.Other",)), row(2), row(3), row(4, ("A.Other",))]}}


@pytest.fixture(scope="module")
def roster(mount):
    page, errors = mount("roster", size=PHONE)
    r = KdstBars(page)
    assert show_cards(r, "espn", "skip") == 1
    r.plant(SCENE)
    yield r
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a defense's back draws a bar per played week and the hollow projection last")
def test_a_defenses_back_draws_four_weeks_and_the_hollow_projection(roster):
    got = roster.back("DST", "TEN", "yahoo", FULL, proj=5.4)
    assert [b["proj"] for b in got["bars"]] == [False] * 4 + [True]
    assert got["pts"] == ["6", "2", "6", "6", "5"], "the Yahoo score per week, then the projection"
    assert got["facts"] == 0 and got["kick"] and got["whole"] and got["over"] <= 0, got


@pytest.mark.render
def test_espn_scores_a_defense_on_its_own_points(roster):
    assert roster.back("DST", "TEN", "espn", FULL)["pts"][:4] == ["8", "4", "8", "8"]


@pytest.mark.render
@pytest.mark.req(REQ, ac="a bye keeps its slot, empty, like a player's")
def test_a_bye_is_an_empty_slot(roster):
    got = roster.back("DST", "TEN", "yahoo", BYE)
    assert [b["gap"] for b in got["bars"]] == [False, True, False, False, False]


@pytest.mark.render
@pytest.mark.req(REQ, ac="a kicker's back reads the league's kicker scoring")
def test_a_kickers_back_follows_the_leagues_scoring(roster):
    madden = roster.back("K", "TEN", "yahoo", FULL, name="Tom Boot")
    ayo = roster.back("K", "TEN", "ayo", FULL, name="Tom Boot")
    assert (madden["pts"][:2], ayo["pts"][:2]) == (["9", "12"], ["8", "11"])
    assert len(madden["bars"]) == 5 and madden["bars"][-1]["proj"] and madden["over"] <= 0 and madden["whole"]


@pytest.mark.render
@pytest.mark.req(REQ, ac="a kicker's weeks another kicker kicked are faded")
def test_the_weeks_another_kicker_kicked_are_faded(roster):
    got = roster.back("K", "TEN", "yahoo", SWAP, name="Tom Boot")
    assert [b["faded"] for b in got["bars"]] == [True, False, False, True, False]


@pytest.mark.render
def test_espn_has_no_kicker_slot_so_its_back_keeps_the_facts(roster):
    got = roster.back("K", "TEN", "espn", FULL, name="Tom Boot")
    assert got["bars"] == [] and got["facts"] >= 2


@pytest.mark.render
def test_a_defense_with_no_file_row_keeps_the_facts(roster):
    got = roster.back("DST", "TEN", "yahoo", {"teams": {"ARI": [row(1)]}})
    assert got["bars"] == [] and got["facts"] >= 2


@pytest.mark.render
@pytest.mark.req(REQ, ac="a Sheet row draws the same strip")
def test_a_sheet_row_draws_the_strip_for_a_defense_and_a_kicker(roster):
    dst = roster.row("DST", "TEN", "yahoo", FULL)["bars"]
    k = roster.row("K", "TEN", "ayo", SWAP, name="Tom Boot")["bars"]
    assert [b["proj"] for b in dst] == [False] * 4 + [True]
    assert [b["faded"] for b in k] == [True, False, False, True, False]


@pytest.mark.render
@pytest.mark.req(REQ, ac="a K or D/ST row shows the same projection as its back")
def test_a_rows_number_is_the_backs_projection(roster):
    assert roster.row("DST", "TEN", "yahoo", FULL, proj=5.43)["num"] == "5.4"
    assert roster.row("K", "TEN", "ayo", FULL, name="Tom Boot", proj=7.86)["num"] == "7.9"


@pytest.mark.render
@pytest.mark.req(REQ, ac="ESPN has no K scoring, so a K row draws no bars from another league's")
def test_an_espn_kicker_row_draws_no_bars_and_no_number(roster):
    got = roster.row("K", "TEN", "espn", FULL, name="Tom Boot")
    assert got["bars"] == [] and got["num"] == "—"
