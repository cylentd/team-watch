"""David's phone listening notes, November 5: visible arrivals, not only light clocks."""
import pytest
from test_madden_stage_polish import stage_result
from test_madden_rev8 import CAMERA


COOKED_ARRIVES_ON_THE_LISTENER_MARK_AND_ZERO_FOLLOWS_ON_THE_NEXT_HIT_SCRIPT = ("""
const {CURSE} = await import(base + '/draft-curse.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const start = filmPlan().beats.find(beat => beat.id === 'curse').start;
return {landing: start + CURSE.lastLanding, stamp: start + CURSE.flip[1],
  fourth: start + CURSE.landings[3], leap: start + CURSE.leap};
""")

PHONE_IS_ON_THE_COLUMN_ON_THE_MUSIC_REVEAL_NOT_A_SECOND_AFTER_IT_SCRIPT = ("""
const {BUILD} = await import(base + '/draft-build.mjs');
const {mobileBuildAt} = await import(base + '/draft-mobile-framing.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const start = filmPlan().beats.find(beat => beat.id === 'injury').start;
return {build: start + BUILD.steps[0], hit: start + BUILD.hit,
  arrival: mobileBuildAt(40.077 - start).reveal, before: mobileBuildAt(39.3 - start).reveal};
""")

PHONE_REVEAL_FRAME_HAS_REACHED_ITS_COLUMN_COMPOSITION_ON_THE_HIT_SCRIPT = ("""
const {frame, RIG} = await import(base + '/draft-camera.mjs');
ctx.size = {width: 390, height: 844};
const camera = new THREE.PerspectiveCamera(44, 390 / 844, .1, 100);
frame(camera, filmMoment(40.077), ctx);
return {offset: camera.view.offsetX / ctx.size.width,
  back: camera.position.z, expectedBack: RIG.finale.phone};
""")

FLYBY_STRONGEST_FLASHES_PEAK_ON_MUSIC_HITS_WITHOUT_MOVING_THE_CAMERA_SCRIPT = ("""
const cues = await import(base + '/draft-path-pulse.mjs').catch(() => null);
if (!cues) return null;
const {ONSETS, filmTime} = await import(base + '/music-onsets.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const {columnX, rowY} = await import(base + '/draft-board.mjs');
const start = filmPlan().beats[0].start;
const mobile = MOBILE;
return Array.from({length: 120}, (_, index) => {
  const home = {x: columnX(index % 12), y: rowY(Math.floor(index / 12))};
  return {strength: cues.beamAccent(home, mobile),
    peak: start + cues.beamTrigger(home, mobile) + cues.PATH_BEAM.rise};
}).filter(card => card.strength > 1).map(card => ({...card,
  error: Math.min(...ONSETS.map(onset => Math.abs(filmTime(onset) - card.peak)))}));
""")


def test_cooked_arrives_on_the_listener_mark_and_zero_follows_on_the_next_hit():
    result = stage_result(COOKED_ARRIVES_ON_THE_LISTENER_MARK_AND_ZERO_FOLLOWS_ON_THE_NEXT_HIT_SCRIPT)
    assert result['landing'] == pytest.approx(33.3)
    assert result['stamp'] == pytest.approx(33.581, abs=2 / 30)
    assert result['leap'] - result['fourth'] >= .4


def test_phone_is_on_the_column_on_the_music_reveal_not_a_second_after_it():
    result = stage_result(PHONE_IS_ON_THE_COLUMN_ON_THE_MUSIC_REVEAL_NOT_A_SECOND_AFTER_IT_SCRIPT)
    assert result['build'] == pytest.approx(37.587, abs=2 / 30)
    assert result['hit'] == pytest.approx(40.077)
    assert result['arrival'] == pytest.approx(1)
    assert result['before'] == pytest.approx(0)


def test_phone_reveal_frame_has_reached_its_column_composition_on_the_hit():
    result = stage_result(CAMERA.replace('MOBILE', 'true') + PHONE_REVEAL_FRAME_HAS_REACHED_ITS_COLUMN_COMPOSITION_ON_THE_HIT_SCRIPT)
    assert result['offset'] == pytest.approx(-.28)
    assert result['back'] == pytest.approx(result['expectedBack'], abs=.02)


@pytest.mark.parametrize('mobile', [False, True])
def test_flyby_strongest_flashes_peak_on_music_hits_without_moving_the_camera(mobile):
    result = stage_result(FLYBY_STRONGEST_FLASHES_PEAK_ON_MUSIC_HITS_WITHOUT_MOVING_THE_CAMERA_SCRIPT.replace('MOBILE', 'true' if mobile else 'false'))
    assert result is not None and len(result) >= 3
    assert all(card['error'] <= 1 / 30 for card in result)
    assert len({round(card['peak'], 3) for card in result}) == len(result)
