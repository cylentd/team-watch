"""The pack's rip screen (David, 2026-10-07): the logic its fixes share, in Node (data/packrip.js). The tier glow is a pool of light that does not follow the
pack's turn, so it has no number here (test_pack_rip.py reads it drawn). `pkFlapPose` is how far the torn
flap lifts and how far it tips: a little with the tear, and the rest with the finger pulling up, never when
it pushes down. `pkFlakeOrigin` is where the foil flakes start: on the strip, under the finger's x."""
import pytest


@pytest.fixture(scope="module")
def pk(node_js):
    return node_js("data/packrip.js")


def test_a_flap_with_no_tear_and_no_pull_does_not_lift(pk):
    assert pk("pkFlapPose", 0, 0) == {"lift": 0, "tilt": 0}


def test_the_tear_alone_lifts_the_flap_a_little(pk):
    pose = pk("pkFlapPose", .5, 0)
    assert pose == {"lift": pytest.approx(5.0), "tilt": pytest.approx(6.0)}


def test_the_tears_own_lift_stops_growing_past_its_cap(pk):
    assert pk("pkFlapPose", 1, 0) == {"lift": pytest.approx(6.0), "tilt": pytest.approx(6.0)}


def test_pulling_up_a_full_pull_lifts_the_flap_most(pk):
    pose = pk("pkFlapPose", .6, -36)
    assert pose == {"lift": pytest.approx(30.0), "tilt": pytest.approx(20.0)}


def test_pulling_up_further_than_a_full_pull_changes_nothing(pk):
    assert pk("pkFlapPose", .6, -300) == pk("pkFlapPose", .6, -36)


def test_half_a_pull_is_half_the_extra_lift(pk):
    base, half = pk("pkFlapPose", .6, 0), pk("pkFlapPose", .6, -18)
    assert half["lift"] - base["lift"] == pytest.approx(12.0)
    assert half["tilt"] - base["tilt"] == pytest.approx(7.0)


@pytest.mark.parametrize("dy", [1, 40, 500])
def test_pushing_down_never_lifts_more_than_the_tear_does(pk, dy):
    assert pk("pkFlapPose", .6, dy) == pk("pkFlapPose", .6, 0)


STRIP = {"left": 100, "top": 80, "width": 240, "height": 36}


def test_flakes_start_at_the_strips_middle_height(pk):
    assert pk("pkFlakeOrigin", STRIP, 200)["y"] == 98


def test_flakes_start_under_the_finger_when_it_is_on_the_strip(pk):
    assert pk("pkFlakeOrigin", STRIP, 200)["x"] == 200


@pytest.mark.parametrize("x, want", [(20, 100), (900, 340)])
def test_a_finger_off_the_strips_end_starts_them_at_that_end(pk, x, want):
    assert pk("pkFlakeOrigin", STRIP, x)["x"] == want


def test_with_no_finger_flakes_start_at_the_strips_middle(pk):
    assert pk("pkFlakeOrigin", STRIP, None) == {"x": 220, "y": 98}
