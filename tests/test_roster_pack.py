"""The roster's pack (2026-09-25): a new reader meets this week's pack waiting in the starters' place,
a stored Sheet wins over that default, and the pack opens, rips and deals once a week. Split out of
test_roster_cards.py (2026-10-06), which keeps the build side and the card itself; `on_cards` and `REQ`
come from there. The full-page helpers and the page's clock live in tests/pages/roster_motion.py and
roster_pack.py, for test_pack_stage.py and test_clip_sheet.py.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster import MOTION, NEW_READER, RosterPage
from test_roster_cards import REQ, on_cards


def on_motion(mount):
    """The same with motion on, as a reader without reduced motion sees it, on the virtual clock (a
    context of its own: `mount` loads with reduced motion on)."""
    page, errors = mount("roster", size=(390, 844), init=(MOTION,))
    roster = RosterPage(page)
    roster.allow_motion()
    roster.install_clock()
    roster.show_cards("espn")
    return roster, errors


@pytest.mark.render
@pytest.mark.req(REQ, ac="Cards is the default, so a new reader meets the pack, waiting in the starters' place on every followed team")
def test_a_new_reader_gets_cards_and_the_pack_waits_in_the_starters_place(mount):
    """2026-09-28: Cards is the default, so a new reader meets the pack. Since 2026-10-05 it waits where
    the starters go, on every followed team, and no stage ever opens by itself (it did once a week)."""
    page, errors = mount("roster", size=(390, 844), init=(NEW_READER,))
    roster = RosterPage(page)
    assert roster.has_packs(), "the fixture has a pack for both teams"
    assert roster.roster_mode() == "cards"
    assert roster.stored_mode() is None, "a default is not a choice"
    roster.install_clock()                                      # the wait for a stage that must not open runs on the page's clock
    for team in ("yahoo", "espn"):
        roster.show(team)
        roster.run_clock(450)
        assert roster.stages() == 0, f"{team}: nothing opens by itself"
        assert roster.sealed_gates() == 1, f"{team}: the pack waits, sealed"
    roster.open_stage()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a stored Sheet wins over the default and no stage opens by itself")
def test_a_stored_sheet_wins_over_the_default(mount):
    page, errors = mount("roster", size=(390, 844))
    roster = RosterPage(page)
    assert roster.roster_mode() == "sheet"
    roster.install_clock()                                      # the wait for a stage that must not open runs on the page's clock
    roster.redraw()
    roster.run_clock(450)
    assert roster.stages() == 0
    assert errors == []


# ---- the pack ----

@pytest.mark.render
@pytest.mark.req(REQ, ac="the pack opens once a week: an opened pack never waits again")
def test_the_pack_opens_once_a_week(mount):
    roster, errors = on_cards(mount, pack="stage")
    roster.rip()                                                # reduced motion: straight to the roster
    roster.wait_stage_gone()
    assert roster.slot_cards() == 0
    assert roster.gates() == 0 and roster.down_cards() == 0
    roster.install_clock()                                      # the wait for a stage that must not open runs on the page's clock
    roster.redraw()
    roster.run_clock(450)
    assert roster.stages() == 0 and roster.gates() == 0, "an opened pack never waits again"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="Rip again puts this week's pack back on the stage")
def test_rip_again_puts_this_weeks_pack_back_on_the_stage(mount):
    roster, errors = on_cards(mount, pack="gate")
    assert roster.rerips() == 0, "nothing to rip again before the pack is opened"
    roster.rip_gate()
    roster.rip()
    roster.wait_stage_gone()
    roster.rerip()
    assert roster.stage_seals() == 1
    assert roster.rerips() == 0, "the pack is on the stage, so the button steps aside"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="Rip grows the pack onto the stage and its cards fly home to their slots")
def test_rip_grows_the_pack_onto_the_stage_and_its_cards_fly_home_to_their_slots(mount):
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    # The stage's pack starts where the page's was, small, and grows to the middle (FLIP).
    start = roster.stage_pack_scale()
    assert start is not None and start < .9, start
    # Before the rip the page keeps the starters face down under an empty place.
    assert roster.gate_away() == 1
    roster.rip()
    # After it, the starters' slots are left empty, in place, until each card lands.
    empty, want = roster.empty_slots(), roster.pack_indexes()
    assert empty == want and len(want) == roster.starters_size()
    roster.until_a_card_is_dealt()
    roster.press_escape()                                       # after the rip, Escape skips to the roster
    roster.until_the_stage_is_gone(6000)
    assert roster.slot_cards() == 0 and roster.dealt_cards() == 0
    assert roster.rerips() == 1
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the first card comes out of the pack and the pile counts each card as it lands")
def test_the_first_card_comes_out_of_the_pack_and_the_pile_counts_it(mount):
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    roster.rip()
    roster.until_a_card_is_dealt()
    # The pack is still on the stage while its first card rises out of it, then it goes.
    assert roster.center_count() == 1
    roster.until_the_first_pack_is_gone(4000)
    # Nothing says the pack's size before the rip (2026-09-27); the pile counts each card as it lands.
    assert roster.pile_count() == 0
    roster.until_the_pile_counts(1, 8000)
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the tear starts under the finger and runs the way the finger goes")
def test_the_tear_starts_under_the_finger_and_runs_its_way(mount):
    roster, errors = on_cards(mount, pack="stage")
    assert roster.stages() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    box = roster.seal_box()
    y = box["y"] + 14
    roster.press_at(box["x"] + box["width"] * .6, y)
    roster.drag_to(box["x"] + box["width"] * .45, y)
    roster.drag_to(box["x"] + box["width"] * .3, y)
    got = roster.tear_vars()
    roster.release()
    assert abs(got[0] - .3) < .03 and abs(got[1] - .6) < .03 and got[2] == -1
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a grip near the end tears from the very edge")
def test_a_grip_near_the_end_tears_from_the_very_edge(mount):
    """2026-09-27: a finger never lands on the edge itself, and the tear left a stub of strip."""
    roster, errors = on_cards(mount, pack="stage")
    assert roster.stages() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    box = roster.seal_box()
    y = box["y"] + box["height"] * .07
    roster.press_at(box["x"] + box["width"] * .2, y)
    roster.drag_to(box["x"] + box["width"] * .4, y)
    ta = roster.tear_vars()[0]
    roster.release()
    assert ta == 0
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a stage card is its roster card scaled up whole")
def test_a_stage_card_is_its_roster_card_scaled_up_whole(mount):
    roster, errors = on_motion(mount)
    roster.open_stage_on_the_clock()
    roster.rip()
    roster.until_the_stage_card_is_labelled(8000)
    stage, on_page = roster.art_share("stage"), roster.art_share("roster")
    assert abs(stage - on_page) < .02, f"the photo is {stage:.2f} of a stage card, {on_page:.2f} of a roster card"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="only a drag along the strip rips; a tap, a drag across the body and a short drag do not")
def test_only_a_drag_along_the_strip_rips_and_a_short_one_springs_back(mount):
    roster, errors = on_cards(mount, pack="stage")
    assert roster.stages() > 0, "the fixture's schedule has a week ahead, so a pack on the stage"
    box = roster.seal_box()
    # A tap on the pack's body, and a tap on the strip, only nudge.
    roster.tap_at(box["x"] + box["width"] / 2, box["y"] + box["height"] * .7)
    roster.tap_at(box["x"] + 20, box["y"] + 14)
    assert roster.stage_seals() == 1, "a tap does not rip"
    # A drag across the body, below the strip, does not tear either.
    body = box["y"] + box["height"] * .6
    roster.drag_between(box["x"] + 10, body, box["x"] + box["width"] - 10, body)
    assert roster.stage_seals() == 1, "only the strip tears"
    roster.rip(.3)
    roster.wait_for_spring_back()
    assert roster.stage_seals() == 1, "a short drag does not rip"
    assert roster.tear_amount() in ("0", "0.000")
    roster.rip(.8)
    roster.wait_stage_gone()                                    # reduced motion: ripped, straight to the roster
    assert roster.gates() == 0
    assert errors == []
