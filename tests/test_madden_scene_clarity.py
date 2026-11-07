import pytest
from playwright.sync_api import expect

from pages.madden_scene_clarity import SceneClarityFilm
from test_madden_stage_polish import stage_result


ACHANE_SPLIT_KEEPS_ITS_CLOSEUP_UNTIL_THE_HALVES_FADE_SCRIPT = ("""
const {shot} = await import(base + '/draft-camera.mjs');
const ctx = {mobile:MOBILE, size:{width:MOBILE ? 390 : 1440, height:MOBILE ? 844 : 900}, finaleX:0,
  featured:{injury:{home:new THREE.Vector3(3,4,0)}}};
return [1.4,1.65,1.8,2.0,3.0,4.0].map(seconds => {
  const view=shot('injury',seconds,ctx);
  return view.position.distanceTo(view.target);
});
""")


@pytest.mark.parametrize('mobile', [False, True])
def test_achane_split_keeps_its_closeup_until_the_halves_fade(mobile):
    samples = stage_result(ACHANE_SPLIT_KEEPS_ITS_CLOSEUP_UNTIL_THE_HALVES_FADE_SCRIPT.replace('MOBILE', str(mobile).lower()))
    assert all(distance <= samples[0] * 1.1 for distance in samples[1:4]), samples
    assert samples[4] > samples[0] * 2, samples
    assert samples[5] > samples[0] * 2, samples


@pytest.fixture(scope='module', params=[(390, 844), (768, 690), (1440, 900)])
def scene_clarity(browser, request):
    film = SceneClarityFilm(browser, *request.param)
    with film:
        film.load()
        yield film


@pytest.mark.parametrize('seconds, headline', [(71.2, 'Lamarley: the tight-end switch.'), (69.4, 'Lamarley: the tight-end switch.'), (71.2, 'Lamarley: the tight-end switch.'), (73.5, 'Again.')])
def test_te_action_has_one_caption_not_a_second_start_bench_list(scene_clarity, seconds, headline):
    scene_clarity.seek(seconds)
    expect(scene_clarity.headline()).to_be_visible()
    expect(scene_clarity.headline()).to_have_text(headline)
    expect(scene_clarity.detail()).to_have_count(0)
    box = scene_clarity.headline_box()
    assert box['x'] >= 0 and box['x'] + box['width'] <= scene_clarity.width
    assert box['y'] >= 0 and box['y'] + box['height'] <= scene_clarity.height
    assert not scene_clarity.errors
