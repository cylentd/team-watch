"""The pack's rip screen, David's fixes of 2026-10-07 (design/DESIGN.md "Week's pack"):

- the mouth under the strip is cut to the torn stretch, wearing the strip's crimp, and paints only a thin lit
  edge: nothing sits behind the lifted flap (it was a black slab, then a silver one);
- the flap lifts and tips further as the finger pulls up, and settles flat when let go short of the tear;
- the foil flakes start on the strip where it is torn, not at the top of the leaned pack's box;
- the tier glow is a round pool 1.5x the pack's width that does not change as the pack turns;
- once ripped the foil's top is one straight lit edge, and the rainbow seam is gone;
- the hint under the cards gives way while a card is in the air.

Pure numbers (glow width, flap pose, flake origin) are proved in Node, tests/test_js_packrip.py. These prove
the screen draws them. The stage is the ESPN roster's, reduced motion through `on_cards` (the tear is the same
code), and the hint's flight on the virtual clock through `on_motion`.
"""
import pytest

from component import mount as base_mount  # noqa: F401  (the fixture, `mount` below)
from pages.pack_rip import PackRip
from pages.roster import MOTION
from pages.roster_motion import on_motion
from pages.warm import warm
from test_roster_cards import PHONE, on_cards

REQ = "Phone layout"       # DESIGN.md's Week's pack rows live under it, as test_roster_cards.py's do


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the module's two contexts (reduced motion, motion on) opened once (pages/warm.py)."""
    return warm(base_mount, ("roster", PHONE), ("roster", (390, 844), (MOTION,)))


@pytest.fixture
def stage(mount):
    """The stage of a roster whose pack waits, reduced motion: (PackRip, errors)."""
    roster, errors = on_cards(mount, pack="stage")
    return PackRip(roster.page), errors


@pytest.fixture(scope="module")
def flight(mount):
    """The stage with motion, ripped, at the moment a card is in the air, and the hint's fade done: set up once,
    the hint's look read by the tests (the clock stops there, so it stays that way)."""
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    roster.rip()
    rip = PackRip(roster.page)
    rip.until_a_card_flies(roster, 120000)
    rip.wait_for_hint_to_fade()
    return rip, errors


@pytest.mark.req(REQ, ac="the mouth is not drawn until the tear starts")
def test_the_mouth_is_hidden_before_the_tear_starts(stage):
    rip, errors = stage
    assert rip.mouth()["opacity"] == 0
    assert errors == []


@pytest.mark.req(REQ, ac="the mouth is cut to the torn stretch and wears the strip's crimp")
def test_the_mouth_shows_only_the_torn_stretch_in_the_strips_crimp(stage):
    rip, errors = stage
    rip.tear_to(.35, steps=3)
    ta, tb = rip.vars("--ta", "--tb")
    mouth = rip.mouth()
    rip.let_go()
    assert mouth["opacity"] == 1
    assert 0 <= ta < tb < 1, (ta, tb)
    assert mouth["left"] == pytest.approx(ta * 100, abs=.2), mouth
    assert mouth["right"] == pytest.approx((1 - tb) * 100, abs=.2), mouth
    assert mouth["crimped"], "the gaps between the strip's teeth show the stage, not the mouth"
    assert errors == []


@pytest.mark.req(REQ, ac="the flap follows the finger's pull and settles back when let go")
def test_the_flap_lifts_and_tips_further_as_the_finger_pulls_up(stage):
    rip, errors = stage
    rip.tear_to(.35, pull=-36, steps=3)
    pulled = rip.vars("--tl", "--tg")
    rip.let_go()
    # The tear alone lifts the flap at most 6px and 6deg (data/packrip.js); a full pull adds 24px and 14deg.
    assert pulled[0] > 20 and pulled[1] > 12, pulled
    assert rip.inline_vars("--tl", "--tg") == ["0.000", "0.000"], "let go short of the tear, it settles flat"
    assert errors == []


@pytest.mark.req(REQ, ac="flakes start on the strip where it is torn")
def test_the_flakes_start_inside_the_torn_edge(stage):
    rip, errors = stage
    rip.watch_flakes()
    rip.tear_to(.85, steps=4)
    rip.let_go()
    bursts = rip.flakes()
    assert len(bursts) >= 3, bursts
    outside = [b for b in bursts
               if not (b["edge"][0] <= b["x"] <= b["edge"][2] and b["edge"][1] <= b["y"] <= b["edge"][3])]
    assert outside == []
    assert errors == []


@pytest.mark.req(REQ, ac="the glow is a round pool of light that keeps its size when the pack turns")
def test_the_glow_is_a_round_pool_wider_than_the_pack_and_keeps_its_size_as_it_turns(stage):
    rip, errors = stage
    resting = rip.glow_pool()
    rip.spin_body(.4)
    turned = rip.glow_pool()
    rip.let_go()
    assert resting["round"] and resting["w"] == pytest.approx(resting["h"], abs=.5), resting
    assert resting["w"] / resting["pack"] == pytest.approx(1.5, abs=.1), resting
    assert (turned["w"], turned["h"]) == (resting["w"], resting["h"]), (resting, turned)
    assert errors == []


@pytest.mark.req(REQ, ac="after the rip the foil's top is one straight edge and the rainbow seam is gone")
def test_a_ripped_pack_has_a_straight_top_with_a_lit_edge_and_no_rainbow_line(stage):
    rip, errors = stage
    rip.tear_a_little()
    sealed = rip.foil_and_seam()
    rip.tear_the_stage()
    ripped = rip.foil_and_seam()
    assert sealed["seam"] > 0, sealed
    assert ripped["foil"] == "none", "no ragged polygon: the foil's own top edge is the straight line"
    assert ripped["edge"] != "none", "the opened edge is lit"
    assert ripped["seam"] == 0, ripped
    assert errors == []


@pytest.mark.req(REQ, ac="nothing is painted behind the torn stretch beyond a thin lit edge")
def test_the_mouth_paints_only_a_thin_lit_edge_so_the_stage_shows_behind_the_flap(stage):
    rip, errors = stage
    rip.tear_to(.35, steps=3)
    paint = rip.mouth_paint()
    rip.let_go()
    assert paint == {"layers": 1, "size": "100% 2px"}
    assert errors == []


@pytest.mark.req(REQ, ac="the rip hint steps aside once the finger is tearing")
def test_the_rip_hint_is_gone_once_the_finger_is_tearing(stage):
    rip, errors = stage
    assert rip.hint()["opacity"] == 1
    rip.tear_to(.35, steps=2)
    tearing = rip.hint()
    rip.let_go()
    assert tearing == {"opacity": 0, "animation": "none"}
    assert errors == []


@pytest.mark.req(REQ, ac="the hint gives way while a card flies to the pile")
def test_the_hint_is_gone_while_a_card_is_in_the_air(flight):
    rip, errors = flight
    assert rip.flying()
    assert rip.hint() == {"opacity": 0, "animation": "none"}
    assert errors == []
