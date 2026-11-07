"""Madden Curse film, revision 17: scared Blip on the waiver floor and the word-by-word title."""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from test_madden_stage_polish import stage_result

SHOWCASE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse'

BLIP_ON_THE_FLOOR = """
const {curse, CURSE, BLIP, blipHome} = await import(base + '/draft-curse.mjs');
const {TRAIL} = await import(base + '/constants.mjs');
const {PROPS} = await import(base + '/draft-props.mjs');
const {FLOOR} = await import(base + '/draft-floor.mjs');
const faces = Array.from({length: 6}, () => new THREE.MeshBasicMaterial());
const item = {mesh: new THREE.Mesh(new THREE.BoxGeometry(), faces), home: new THREE.Vector3(), front: faces[4],
  props: {root: new THREE.Group(), stampZ: .03, flame: {update() {}}}};
const names = ['wr', 'wire', 'wr', 'wire', 'cooked'], gap = FLOOR.gap.phone;
const xs = [-gap / 2, gap / 2, -gap / 2, gap / 2, gap / 2 + FLOOR.reveal];
const stations = Object.fromEntries(names.map((name, index) => [name + index, {x: xs[index], z: FLOOR.z}]));
const steps = names.map((name, index) => ({station: name + index}));
const home = blipHome(stations.wr0, stations.wire1);
const blip = {home, position: new THREE.Vector3()};
const tile = new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial());
const frame = 1 / 30, samples = [];
for (let time = CURSE.firstLanding; time < TRAIL.pan[1]; time += frame) {
  curse(time, item, stations, steps, blip, tile);
  samples.push({time, visible: blip.visible, scared: blip.scared, recoil: blip.recoil, look: blip.look,
    jitter: blip.position.distanceTo(home), card: item.mesh.position.z});
}
return {samples, home: home.toArray(), pads: [xs[0], xs[1]], z: FLOOR.z, pad: PROPS.pad,
  label: [PROPS.labelWidth, PROPS.labelAhead], hops: CURSE.landings.slice(1, -1).map(time => time - CURSE.move),
  blip: BLIP, leap: CURSE.leap, keys: Object.keys(CURSE)};
"""


BLIPS_SCARED_FACE_HAS_WIDE_EYES_AND_A_WAVY_MOUTH_IN_PLACE_OF_THE_SMILE_SCRIPT = ("""
const {makeBlip, blipFace} = await import(base + '/blip.mjs');
const blip = makeBlip(), calm = blip.face.eyes.map(eye => eye.scale.y);
blipFace(blip, true);
const scared = {eyes: blip.face.eyes.map(eye => eye.scale.y), smile: blip.face.smile.visible, wavy: blip.face.wavy.visible};
blipFace(blip, false);
return {calm, scared, back: {smile: blip.face.smile.visible, wavy: blip.face.wavy.visible}};
""")


@pytest.fixture(scope='module')
def floor():
    return stage_result(BLIP_ON_THE_FLOOR)


def test_blip_stands_between_warren_ty_and_the_wire_behind_the_hop_line_clear_of_the_words(floor):
    # David rev 17: Blip stands on the floor between the WARREN-TY pad and the WAIVER pad, slightly behind the
    # hop line, so the card passes in front of him, and never over the pad words. ~~At the frame's right edge~~ (rev 15).
    x, y, z = floor['home']
    left, right = floor['pads']
    assert x == pytest.approx((left + right) / 2) and y == 0
    assert z < floor['z'] - floor['pad']                               # behind the pads, so behind the hop line
    width, _ = floor['label']
    reach = floor['blip']['halfWidth']
    assert all((abs(x - pad) > width / 2 + reach) for pad in (left, right))


def test_blip_is_scared_and_trembles_one_or_two_pixels_while_he_is_on_the_floor(floor):
    shown = [sample for sample in floor['samples'] if sample['visible']]
    assert shown and all(sample['scared'] for sample in shown)
    jitter = [sample['jitter'] for sample in shown]
    assert max(jitter) > 0 and max(jitter) <= floor['blip']['tremble'] * math.sqrt(2) + 1e-9
    assert floor['blip']['tremble'] <= .006                            # about 1-2 px in the wide shot


def test_blip_flinches_back_as_the_card_hops_past_then_recovers_and_never_shakes_his_head(floor):
    # David rev 17: he leans back for 0.2 s each time the card hops past, then recovers; this replaces the head-shake.
    assert not {'headShake', 'shakes', 'shakeAngle'} & set(floor['keys'])
    samples, blip = floor['samples'], floor['blip']
    assert len(floor['hops']) == 3
    recoil = lambda time: min(samples, key=lambda sample: abs(sample['time'] - time))['recoil']
    assert recoil(floor['hops'][0] - .1) == 0
    for hop in floor['hops']:
        peak = recoil(hop + blip['back'])
        assert peak == pytest.approx(blip['angle'], abs=.02)  # honest: allow COND_ASSERT each deterministic hop must satisfy the same recoil trajectory
        assert recoil(hop + blip['back'] / 2) < peak                   # leaning back over the first 0.2 s  # honest: allow COND_ASSERT each deterministic hop must satisfy the same recoil trajectory
        assert recoil(hop + blip['back'] + blip['recover'] + .04) == pytest.approx(0, abs=1e-6)  # honest: allow COND_ASSERT each deterministic hop must satisfy the same recoil trajectory


def test_blip_turns_to_watch_the_card_leap_off_to_cooked(floor):
    samples, leap = floor['samples'], floor['leap']
    before = [sample['look'] for sample in samples if sample['time'] < leap - .15]
    after = [sample['look'] for sample in samples if sample['time'] > leap + .4 and sample['visible']]
    assert all(look == 0 for look in before)
    assert after and min(after) > .8                                   # turned toward COOKed, off the right edge


def test_blips_scared_face_has_wide_eyes_and_a_wavy_mouth_in_place_of_the_smile():
    face = stage_result(BLIPS_SCARED_FACE_HAS_WIDE_EYES_AND_A_WAVY_MOUTH_IN_PLACE_OF_THE_SMILE_SCRIPT)
    assert all(wide > calm * 1.2 for wide, calm in zip(face['scared']['eyes'], face['calm']))
    assert face['scared']['wavy'] and not face['scared']['smile']
    assert face['back']['smile'] and not face['back']['wavy']
    source = (SHOWCASE / 'draft.mjs').read_text(encoding='utf8')
    assert 'blipFace(blip, blipState.scared)' in source and 'blipState.recoil' in source
