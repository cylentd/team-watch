"""David's sustained fly-by lighting and visible first DEF entrance, 2026-11-06."""
import pytest

from test_madden_flyby_polish import one_card, peak_of
from test_madden_stage_polish import stage_result
from test_madden_chapter4 import POSE
from test_madden_chapter2 import node


ALL_TWELVE_AVATARS_IGNITE_TOGETHER_THEN_RESET_ON_REVERSE_SEEK_AND_OTHER_BEATS_SCRIPT = ("""
const module = await import(base + '/draft-path-light.mjs');
const headers = new Map(Array.from({length:12}, (_, index) => [index, {disc: new THREE.Mesh(new THREE.CircleGeometry(.17), new THREE.MeshBasicMaterial({color:0xffffff}))}]));
const lights = module.makeHeaderLights?.(headers);
const at = (seconds, active=true) => {lights?.update(seconds, active); return [...headers.values()].map(({disc}) => ({brightness:disc.material.color.r, rim:disc.children.some(child=>child.visible && child.material.opacity>0)}));};
return {before:at(4.9), arriving:at(5.3), peak:at(5.5), hold:at(7), other:at(2,false), reverse:at(4.9)};
""")


@pytest.mark.parametrize('mobile', [False, True])
def test_ignited_cards_keep_a_soft_border_and_face_after_the_shaft_has_faded(mobile):
    samples = one_card(mobile)
    peak = peak_of(samples, 'strength')
    held = [sample for sample in samples if peak['time'] + .5 <= sample['time'] <= peak['time'] + .8]
    assert held
    assert all(.3 <= sample['border'] <= .6 for sample in held)
    assert all(.7 <= sample['face'] <= 1.1 for sample in held)
    assert all(sample['strength'] < .01 for sample in held)


def test_all_twelve_avatars_ignite_together_then_reset_on_reverse_seek_and_other_beats():
    result = stage_result(ALL_TWELVE_AVATARS_IGNITE_TOGETHER_THEN_RESET_ON_REVERSE_SEEK_AND_OTHER_BEATS_SCRIPT)
    assert all(row['brightness'] <= .35 and not row['rim'] for row in result['before'])
    assert all(.35 < row['brightness'] < 1.3 and row['rim'] for row in result['arriving'])
    assert len(result['peak']) == 12 and all(row['brightness'] >= 1.2 and row['rim'] for row in result['peak'])
    assert all(row['brightness'] == pytest.approx(1) and row['rim'] for row in result['hold'])
    assert all(row['brightness'] == pytest.approx(1) and not row['rim'] for row in result['other'])
    assert result['reverse'] == result['before']


@pytest.mark.parametrize('mobile', [False, True])
@pytest.mark.parametrize('seconds', [.7, .8, .95, 1])
def test_saints_drops_after_the_wipe_on_the_same_curve_as_raiders(mobile, seconds):
    result = node(POSE + "const at=s=>lineupsPose(s,false,cast," + str(mobile).lower() + "); return {empty:[0,.4,.55,.649].map(s=>at(s).shields.map(card=>card.visible)), falls:[at(" + str(seconds) + ").shields[0],at(" + str(seconds + 3) + ").shields[1]], reverse:at(.55).shields};")
    assert result['empty'] == [[False, False]] * 4
    saints, raiders = result['falls']
    assert saints['visible'] and raiders['visible']
    assert saints['position'] == pytest.approx(raiders['position'])
    assert saints['squash'] == pytest.approx(raiders['squash'])
    assert not any(card['visible'] for card in result['reverse'])


def test_saints_lands_on_the_half_bar_not_an_invented_audio_onset():
    result = node("const {filmImpacts,nearestHit}=await import(base+'/film-impacts.mjs'); const hit=filmImpacts().find(hit=>hit.name==='Saints deduction'); return {...hit,reference:nearestHit(hit.at)};")
    assert result['at'] == pytest.approx(59.077)
    assert result['reference']['kind'] == 'beat'
    assert abs(result['reference']['frames']) <= 2
