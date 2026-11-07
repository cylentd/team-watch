"""Chapter 1 fly-by and board polish (David, 2026-11-05).

Note 1: the fly-by lights read as a wash. Each card's border light must pop hard as the camera reaches it
and the shaft fades right after. November 6 experiment: borders and faces retain a softer lit trail.
Note 2: the standing board reads cheap: flat black void, a reveal wave hidden behind the cards.
"""
import pytest
from test_madden_stage_polish import stage_result

# One card under the look point at pass second 2, sampled every 10 ms through its light.
ONE_CARD = """
const {makePathBeams} = await import(base + '/draft-path-beams.mjs');
const {pathLight} = await import(base + '/draft-path-light.mjs');
const {passLook} = await import(base + '/draft-establish.mjs');
const MOBILE = MOBILE_FLAG;
const point = passLook(2, MOBILE);
const home = new THREE.Vector3(point.x, point.along, 0);
const beams = makePathBeams(new Map([[0, {pick: {pos: 'WR'}, home}]]));
const far = passLook(.2, MOBILE);
return Array.from({length: 300}, (_, step) => {
  const time = .5 + step / 100;
  beams.update(time, MOBILE);
  const mesh = beams.group.children[0];
  return {time, strength: mesh.visible ? mesh.material.uniforms.strength.value : 0,
    border: mesh.visible ? mesh.children[0].material.opacity : 0,
    face: pathLight(home.x, home.y, time, MOBILE), dark: pathLight(far.x + 6, far.along, time, MOBILE)};
});
"""


REVEAL_WAVE_IS_A_BRIGHT_WIDE_BACKLIGHT_NOT_A_HIDDEN_SLIVER_SCRIPT = ("""
const {revealGlowAt, REVEAL_GLOW} = await import(base + '/draft-reveal-glow.mjs');
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const peak = Math.max(...Array.from({length: 150}, (_, step) => revealGlowAt(ESTABLISH.stand[1] + step / 100)?.strength ?? 0));
return {peak, band: REVEAL_GLOW.band};
""")

WALL_BEHIND_THE_STANDING_BOARD_IS_LIT_BRIGHTEST_BEHIND_IT_AND_FALLS_OFF_TO_NOTHING_SCRIPT = ("""
const module = await import(base + '/draft-backdrop.mjs').catch(() => null);
if (!module) return null;
const {width, height, data} = module.backdropTexture().image;
const alpha = (u, v) => data[(Math.floor(v * (height - 1)) * width + Math.floor(u * (width - 1))) * 4 + 3];
return {centre: alpha(.5, .5), edge: alpha(.5, .78), corner: alpha(0, 0), side: alpha(.01, .5)};
""")

WALL_LIGHT_RISES_WITH_THE_STAND_AND_LOWERS_BEFORE_THE_STEAL_WITHOUT_A_JUMP_SCRIPT = ("""
const {backlightAt} = await import(base + '/draft-backdrop.mjs');
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const {beatTiming} = await import(base + '/timing.mjs');
const end = beatTiming('board').duration;
const samples = Array.from({length: Math.floor(end * 100) + 1}, (_, step) => backlightAt(step / 100));
return {pass: Math.max(...samples.slice(0, Math.floor(ESTABLISH.stand[0] * 100))), stood: backlightAt(ESTABLISH.stand[1] + 1),
  end: backlightAt(end), jump: Math.max(...samples.slice(1).map((value, index) => Math.abs(value - samples[index])))};
""")


def one_card(mobile):
    return stage_result(ONE_CARD.replace('MOBILE_FLAG', 'true' if mobile else 'false'))


def peak_of(samples, key):
    return max(samples, key=lambda sample: sample[key])


@pytest.mark.parametrize('mobile', [False, True])
def test_a_cards_shaft_pops_then_fades_leaving_a_soft_border_trail(mobile):
    samples = one_card(mobile)
    peak = peak_of(samples, 'strength')
    first = next(sample for sample in samples if sample['strength'] > 0)
    assert peak['time'] - first['time'] <= .08
    after = [sample for sample in samples if sample['time'] >= peak['time'] + .3]
    assert max(sample['strength'] for sample in after) < peak['strength'] * .05
    assert all(sample['border'] == pytest.approx(.45) for sample in after)


def test_the_desktop_shaft_and_border_hit_hard_at_their_peak():
    samples = one_card(False)
    assert peak_of(samples, 'strength')['strength'] >= .45
    assert peak_of(samples, 'border')['border'] == pytest.approx(1)


@pytest.mark.parametrize('mobile', [False, True])
def test_the_card_face_flares_with_its_border_then_stays_softly_lit(mobile):
    samples = one_card(mobile)
    face = peak_of(samples, 'face')
    dark = max(sample['dark'] for sample in samples)
    assert dark <= .34
    assert face['face'] >= dark * 3.5
    settled = [sample for sample in samples if sample['time'] >= face['time'] + .35 and sample['time'] < 4]
    assert all(sample['face'] == pytest.approx(.85) for sample in settled)


GRID = """
const {makePathBeams} = await import(base + '/draft-path-beams.mjs');
const {rowY, columnX} = await import(base + '/draft-board.mjs');
const cards = new Map(Array.from({length: 120}, (_, index) => [index,
  {pick: {pos: 'WR'}, home: new THREE.Vector3(columnX(index % 12), rowY(Math.floor(index / 12)), 0)}]));
const beams = makePathBeams(cards);
const strengths = [];
for (let step = 0; step <= 500; step++) {
  beams.update(step / 100, MOBILE_FLAG);
  strengths.push(beams.group.children.map(mesh => mesh.visible ? mesh.material.uniforms.strength.value : 0));
}
return strengths;
"""


@pytest.mark.parametrize('mobile', [False, True])
def test_mid_pass_only_a_few_cards_are_lit_at_once_so_the_lights_run_in_sequence(mobile):
    frames = stage_result(GRID.replace('MOBILE_FLAG', 'true' if mobile else 'false'))
    peak = max(max(frame) for frame in frames)
    lit = [sum(value > peak / 2 for value in frame) for frame in frames[100:450]]
    fired = {index for frame in frames for index, value in enumerate(frame) if value > peak / 2}
    assert max(lit) <= 3
    assert len(fired) >= 8


def test_the_reveal_wave_is_a_bright_wide_backlight_not_a_hidden_sliver():
    result = stage_result(REVEAL_WAVE_IS_A_BRIGHT_WIDE_BACKLIGHT_NOT_A_HIDDEN_SLIVER_SCRIPT)
    assert result['peak'] >= 1.4
    assert result['band'] >= .2


def test_the_wall_behind_the_standing_board_is_lit_brightest_behind_it_and_falls_off_to_nothing():
    result = stage_result(WALL_BEHIND_THE_STANDING_BOARD_IS_LIT_BRIGHTEST_BEHIND_IT_AND_FALLS_OFF_TO_NOTHING_SCRIPT)
    assert result is not None
    assert result['centre'] == 255
    assert result['side'] == 0 and result['corner'] == 0
    assert 0 < result['edge'] < result['centre']


def test_the_wall_light_rises_with_the_stand_and_lowers_before_the_steal_without_a_jump():
    result = stage_result(WALL_LIGHT_RISES_WITH_THE_STAND_AND_LOWERS_BEFORE_THE_STEAL_WITHOUT_A_JUMP_SCRIPT)
    assert result['pass'] == 0
    assert result['stood'] == pytest.approx(1)
    assert result['end'] == pytest.approx(0)
    assert result['jump'] < .1

