"""The pack's stage and its controls, fixes of 2026-09-25: "Rip again" sits over the cards and never
moves the Sheet / Cards switch, a drag on the pack turns it and it springs back, and a tap while the
cards are dealt hurries them. Since 2026-10-05 the pack waits in the starters' place on a followed team
(packgate.js) and the deal holds each hit with its label. The motion tests run on the page's virtual
clock (pages/roster_pack.VCLOCK), so no test waits for a real animation, and "how long it took" is the
page's own time. Every test mounts the roster (2026-10-06): reduced motion through `on_cards`, motion
through `on_motion`, a context of its own."""
import re

import pytest

from component import mount as base_mount  # noqa: F401  (the fixture, `mount` below)
from pages.roster import MOTION, RosterPage
from pages.roster_motion import on_motion
from pages.warm import warm
from test_roster_cards import PHONE, on_cards, signed_mount  # noqa: F401  (signed_mount is a fixture)


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the module's two contexts (reduced motion, motion on) opened once (pages/warm.py)."""
    return warm(base_mount, ("roster", PHONE), ("roster", (390, 844), (MOTION,)))


@pytest.mark.render
def test_rip_again_is_over_the_cards_and_the_switch_holds_still(mount):
    roster, errors = on_cards(mount, pack="stage")
    in_cards = roster.mode_chip_xs()
    roster.rip()
    roster.wait_stage_gone()
    # The page stays on the cards that just landed (2026-09-27: closing the stage threw it to the top):
    # the starters' grid is on screen once the stage has gone. (It asserted a scroll until 2026-10-05,
    # when the shorter header let the whole grid fit without one.)
    grid = roster.starters_grid_edges()
    assert 0 <= grid[0] < grid[1] <= roster.viewport_height(), grid
    assert roster.rule_rerips() == 1
    assert roster.mode_switch_rerips() == 0
    roster.scroll_to_top()
    assert roster.mode_chip_xs() == in_cards, "the rip moves neither Sheet nor Cards"
    roster.mode("sheet")
    assert roster.mode_chip_xs() == in_cards, "Sheet and Cards stay where they were"
    assert roster.rerips() == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("motion", [False, True])
def test_a_pack_with_no_metal_deals_its_starters_and_says_so(mount, motion):
    """2026-09-27: a week where nobody on the roster is a hit still gets its pack (2026-10-05: the
    starters, every one stock)."""
    roster, errors = on_motion(mount) if motion else on_cards(mount)
    roster.install_clock()                                      # a no-op on the motion page, which has it
    roster.plant_no_metal()
    assert roster.pack_has_a_hit() is False
    if motion:
        roster.rip_gate()
    else:
        roster.open_week_chip()
    roster.rip()
    roster.until_the_message_starts("No metal", 20000)
    roster.until_the_stage_is_gone(8000)
    assert roster.down_starters() == 0 and roster.slot_cards() == 0
    assert roster.rule_rerips() == 1, "it can be ripped again too"
    assert errors == []


@pytest.mark.render
def test_the_packs_side_seams_are_never_clipped(mount):
    """2026-09-27: a clip-path on the pack's turned edge slices dropped the spin to 16 fps on a
    throttled CPU (53 without). The side seams are shaped by border-radius instead."""
    roster, errors = on_cards(mount, pack="stage")
    clips = roster.wall_clips()
    assert len(clips) == 2 and set(clips) == {"none"}, clips
    assert errors == []


@pytest.mark.render
def test_a_drag_on_the_pack_turns_it_and_it_springs_back(mount):
    roster, errors = on_cards(mount, pack="stage")
    box = roster.seal_box()
    y = box["y"] + box["height"] * .6
    roster.press_at(box["x"] + box["width"] / 2, y)
    roster.drag_to(box["x"] + box["width"] * .9, y, steps=5)
    turned = roster.stage_pack_turn()
    roster.release()
    assert turned > 10, "the pack turns with the drag"
    assert roster.stage_pack_turn_style() == "", "and springs back"
    assert roster.stage_seals() == 1, "a drag on the body does not rip"
    assert errors == []


@pytest.mark.render
def test_a_drag_on_the_waiting_pack_turns_it_and_a_tap_opens_it(mount):
    """2026-10-05: the pack in the starters' place turns with a sideways drag and springs back to the
    front; a press that never moved opens the stage."""
    roster, errors = on_cards(mount, pack="gate")
    box = roster.waiting_pack_box()
    y = box["y"] + box["height"] * .6
    roster.press_at(box["x"] + box["width"] * .3, y)
    roster.drag_to(box["x"] + box["width"] * .9, y, steps=5)
    turned = roster.waiting_pack_turn()
    roster.release()
    assert turned > 40, turned
    assert roster.waiting_pack_turn() == 0, "it springs back to the front (reduced motion: at once)"
    assert roster.stages() == 0, "a drag does not open it"
    roster.tap_at(box["x"] + box["width"] / 2, y)
    roster.wait_for_stage()
    assert errors == []


@pytest.mark.render
def test_a_tap_does_not_hurry_the_best_cards_reveal(mount):
    """2026-09-27: the last card is the payoff; a tap during it changes nothing."""
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    roster.rip()
    # The page's clock stops the moment the reveal begins (its first animation is still to run).
    roster.until_the_best_card_reveals(120000)
    roster.tap_at(20, 400)
    # The clock parks every animation (a pending pause); a rate read before it settles reads 1 even when
    # the tap's updatePlaybackRate(6) landed, so wait for each to be ready first.
    rates = roster.stage_animation_rates()
    assert rates and all(r == 1 for r in rates), rates
    assert errors == []


@pytest.mark.render
def test_taps_hurry_the_deal(mount):
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    roster.rip()
    roster.until_a_card_is_dealt()
    t0 = roster.clock_now()
    while roster.stages() and roster.clock_now() - t0 < 15000:
        roster.tap_at(20, 400)
        roster.run_clock(150)
    took = (roster.clock_now() - t0) / 1000                     # the page's seconds, not the host's
    n = roster.pack_size()
    # Untouched, a stock card takes ~0.6s, a hit ~2.3s and the best one ~5.5s more.
    assert took < 1.2 * n + 3, f"{n} cards took {took:.1f}s of page time with taps"
    assert roster.slot_cards() == 0
    assert errors == []


@pytest.mark.render
def test_the_deal_ends_with_every_starter_face_up_and_holds_each_hit_centred(mount):
    """2026-10-05: each card rises straight to the stage's centre; a metal holds there with its label
    (centred within 2px, it was 10px off in the storyboard), and the deal ends with every starter face up
    in its slot."""
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    roster.rip()
    roster.until_a_hit_is_labelled(30000)
    held = roster.held_card()
    assert abs(held[0] - held[1]) <= 2, held
    assert re.search(r"(Holo|Gold|Silver)#\d+ \w+ THIS WEEK", held[2]), held[2]
    roster.until_the_stage_is_gone(60000)
    assert roster.down_starters() == 0 and roster.slot_cards() == 0
    assert roster.starter_cards() == roster.starters_size()
    assert errors == []


@pytest.mark.render
def test_a_signed_card_holds_again_while_it_is_signed(signed_mount):
    """2026-10-05: the autograph is its own beat. The label names the finish and the week, the pen
    writes it with sparks, and nothing of it is left running when the stage has gone."""
    roster, errors = on_motion(signed_mount)                    # an empty LIVE_SIGNED for week 3
    pos = roster.sign_a_starter()
    roster.open_stage_on_the_clock()
    roster.rip()
    roster.until_a_hit_is_labelled(30000, "signed")
    assert roster.pack_msg() == f"Signed#2 {pos} IN WEEK 3 · 22.6 PTS"
    inking = roster.last_stage_card_inking()
    assert inking[0] is False and inking[1] == 1 and inking[2] == 1, inking
    roster.until_the_stage_is_gone(60000)
    assert roster.sparks() == 0, "every spark has gone"
    assert errors == []


@pytest.mark.render
def test_the_waiting_pack_keeps_the_starters_place_and_the_bench_shows(mount):
    """2026-10-05: on a followed team the pack stands over the starters' grid, which keeps its size with
    every card face down; Rip and Skip sit under the pack; the bench draws as always."""
    roster, errors = on_cards(mount, pack="gate")
    assert roster.down_starters() == roster.starters_size() > 0
    assert roster.bench_cards() > 0 and roster.down_bench_cards() == 0
    # The fixture's ESPN lineup is one row; a real one is three, taller than the pack. The place is the
    # grid, grown to hold the pack and its buttons when the grid is shorter (packgate.css .pk-zone).
    boxes = roster.zone_boxes()
    zone, grid, pk, rip_, skip = (boxes[k] for k in ("zone", "grid", "pack", "rip", "skip"))
    assert grid["y"] <= pk["y"] < grid["y"] + 60 and pk["y"] + pk["height"] < rip_["y"] < rip_["y"] + rip_["height"] <= zone["y"] + zone["height"]
    assert abs(pk["x"] + pk["width"] / 2 - (grid["x"] + grid["width"] / 2)) < 6, "centred over the grid"
    assert 120 <= pk["width"] <= 150 and abs(rip_["y"] - skip["y"]) < 1
    assert roster.waiting_open_week_chips() == 1, "the chip waits, hidden, for a Skip"
    assert roster.stages() == 0
    assert errors == []


@pytest.mark.render
def test_skip_turns_the_starters_face_up_and_leaves_the_chip_across_a_reload(mount):
    roster, errors = on_cards(mount, pack="gate")
    grid = roster.starters_grid_rect()
    roster.skip_pack()                                          # reduced motion: at once
    assert roster.gates() == 0 and roster.down_starters() == 0
    assert roster.starter_cards() == roster.starters_size()
    assert roster.starters_grid_rect() == grid, "the cards turn where they lay"
    wk = roster.sched_week()
    chip = roster.open_week_chip_state()
    assert chip["count"] == 1 and chip["text"] == f"Open week {wk}" and not chip["waits"]
    roster.reload()
    roster.show("espn")
    assert roster.gates() == 0 and roster.open_week_chips() == 1
    roster.open_week_chip()                                     # the chip opens the stage directly
    roster.wait_for_stage_seal()
    assert errors == []


@pytest.mark.render
def test_skip_with_motion_shrinks_the_pack_into_the_chip_and_turns_the_cards_in_a_wave(mount):
    roster, errors = on_motion(mount)
    roster.skip_pack()
    shrink = roster.waiting_pack_shrink()
    assert shrink is not None and shrink < .2, shrink
    roster.until_the_gate_is_gone(2000)
    assert roster.down_starters() == roster.starters_size(), "the cards turn after the pack has gone"
    roster.run_clock(230)
    first = roster.down_starters()
    assert 0 < roster.starters_size() - first < roster.starters_size(), "one after another, not at once"
    roster.until_the_cards_have_turned_up(3000)
    assert errors == []


@pytest.mark.render
def test_a_browsed_team_shows_its_roster_with_the_chip_and_sheet_never_waits(mount):
    page, errors = mount("roster", size=(360, 800))
    roster = RosterPage(page)
    roster.browse_espn_following_only_yahoo()
    assert roster.gates() == 0 and roster.down_cards() == 0
    assert roster.open_week_chips() == 1, "a team only browsed: its roster, and the chip"
    roster.show("yahoo")
    assert roster.gates() == 1, "a followed team waits"
    roster.mode("sheet")
    assert roster.gates() == 0 and roster.stages() == 0, "Sheet never waits"
    assert roster.start_rows() > 0
    assert errors == []


@pytest.mark.render
def test_the_waiting_pack_stands_still_under_reduced_motion(mount):
    """STYLE.md motion rule 1: a slow turn as a tap cue, never under reduced motion."""
    roster, errors = on_cards(mount, pack="gate")
    assert roster.idle_turns() == 0, "reduced motion: it stands still"
    assert errors == []


@pytest.mark.render
def test_the_waiting_pack_turns_by_itself_with_motion(mount):
    """STYLE.md motion rule 1: a slow turn as a tap cue, with motion on."""
    roster, errors = on_motion(mount)
    assert roster.idle_turns() == 1
    # The turn is the page's own frame loop on the wall clock: it rests 2 s first, then turns.
    roster.wait_for_the_waiting_pack_to_turn(6000)
    assert errors == []
