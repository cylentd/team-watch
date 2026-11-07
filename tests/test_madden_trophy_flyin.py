"""Approved trophy fly-in: physical approach, then a locked closing tag."""
import pytest

from test_madden_chapter5 import camera, inside
from pages.madden_trophy_flyin import TrophyFlyinFilm


FINALE_APPROACHES_TROPHY_THEN_HOLDS_BEHIND_THE_CLOSING_TAG_SCRIPT = ("""
const samples = [90.077, 90.827, 91.577, 92.077, 97.9].map(time => {
  const shot = view(filmMoment(time), ctx);
  frame(camera, filmMoment(time), ctx);
  return {position: shot.position.toArray(), target: shot.target.toArray(), fov: camera.fov,
    distance: shot.position.distanceTo(new THREE.Vector3(...trophyCorners(MOBILE)[0]))};
});
return samples;""")

FINALE_FRAMES_THE_WHOLE_TROPHY_AND_PERCHED_BLIP_SCRIPT = ("""
const origin = perch(MOBILE), blip = [-.3, .3].flatMap(x => [0, .6].flatMap(y => [-.3, .3].map(z =>
  [origin[0] + x, origin[1] + y, origin[2] + z])));
return [91.4, 91.5, 91.577].map(time => ({whole: box(time, [...trophyCorners(MOBILE), ...blip]),
  trophy: box(time, trophyCorners(MOBILE))}));""")

FINALE_REWINDS_DETERMINISTICALLY_AND_REDUCED_MOTION_USES_ACTUAL_CLOCK_SCRIPT = ("""
const rig = await import(base + '/power-camera.mjs');
if (!rig.REDUCED) return {wired: false};
const take = seconds => rig.shot('power-close', seconds, ctx).position.toArray();
const first = take(6.75); take(13.8); const again = take(6.75);
rig.REDUCED.clock = 86.5; const early = take(14);
rig.REDUCED.clock = 93; const late = take(14);
rig.REDUCED.clock = 86.5; const back = take(14);
rig.REDUCED.clock = null;
return {wired: true, first, again, early, late, back};""")


@pytest.mark.parametrize('mobile', [False, True])
def test_finale_approaches_trophy_then_holds_behind_the_closing_tag(mobile):
    result = camera(mobile, FINALE_APPROACHES_TROPHY_THEN_HOLDS_BEHIND_THE_CLOSING_TAG_SCRIPT)
    assert result[0]['distance'] > result[1]['distance'] > result[2]['distance']
    assert result[2]['distance'] < result[0]['distance'] * .65
    assert result[3] == result[4]
    assert len({sample['fov'] for sample in result}) == 1


@pytest.mark.parametrize('mobile', [False, True])
def test_finale_frames_the_whole_trophy_and_perched_blip(mobile):
    result = camera(mobile, FINALE_FRAMES_THE_WHOLE_TROPHY_AND_PERCHED_BLIP_SCRIPT)
    assert all(inside(sample['whole'], .04) for sample in result), result
    assert all(sample['trophy']['height'] >= .4 for sample in result), result


@pytest.mark.parametrize('mobile', [False, True])
def test_finale_rewinds_deterministically_and_reduced_motion_uses_actual_clock(mobile):
    result = camera(mobile, FINALE_REWINDS_DETERMINISTICALLY_AND_REDUCED_MOTION_USES_ACTUAL_CLOCK_SCRIPT)
    assert result['wired']
    assert result['first'] == result['again']
    assert result['early'] == result['back']
    assert result['early'] != result['late']


@pytest.mark.journey
def test_reduced_motion_application_updates_and_rewinds_the_finale_clock(browser):
    film = TrophyFlyinFilm(browser, 390, 844, reduced=True)
    with film:
        film.load()
        rows = []
        for time in [86.5, 93, 86.5]:
            film.seek(time)
            rows.append(film.ending_camera())
        assert [row["clock"] for row in rows] == pytest.approx([86.5, 93, 86.5])
        assert rows[0]["position"] == rows[2]["position"] != rows[1]["position"]
        assert film.errors == []
