import pytest
from component import mount
from test_madden_stage_polish import stage_result
from test_madden_headline_entrance import headline_page, seek


LOWER_THIRD_MASKS_LEAVE_ROOM_FOR_DESCENDERS_SCRIPT = (r"""elements => elements.filter(element => !element.hidden).map(element => {
      const style = getComputedStyle(element), values = style.clipPath.match(/-?[\d.]+px/g).map(Number.parseFloat);
      return {bottom: values[2] ?? values[0], font: Number.parseFloat(style.fontSize)};
    })""")

LIGHT_SHAFT_ORIGIN_FOLLOWS_THE_WHOLE_CARD_BORDER_SCRIPT = ("""
const {makePathBeams} = await import(base + '/draft-path-light.mjs');
const {BOARD, CARD_HEIGHT} = await import(base + '/draft-board.mjs');
const lights = makePathBeams(new Map([[1, {pick: {pos:'WR'}, home:new THREE.Vector3(0,0,0)}]]));
const beam = lights.group.children[0], positions = beam.geometry.attributes.position;
const foot = Array.from({length:positions.count}, (_, index) => new THREE.Vector3().fromBufferAttribute(positions,index))
 .filter(point => Math.abs(point.z) < .0001);
return {count:foot.length, x:[...new Set(foot.map(point=>point.x))], y:[...new Set(foot.map(point=>point.y))],
 width:BOARD.card, height:CARD_HEIGHT, origin:beam.position.y};
""")

FULL_BOARD_WAVE_IS_ONE_PASS_THEN_SETTLES_SCRIPT = ("""
const module = await import(base + '/draft-reveal-glow.mjs').catch(() => null);
if (!module) return null;
return [4, 5.5, 6, 6.5, 8].map(time => module.revealGlowAt(time));
""")

BUILDUP_DOES_NOT_REVEAL_THE_WINNING_COLUMN_BEFORE_THE_HIT_SCRIPT = ("""
const module = await import(base + '/draft-build.mjs');
if (!module.buildCardLight) return null;
const sample = clock => Array.from({length:12}, (_, column) => module.buildCardLight(clock,column,4,.16,1));
return {before:sample(module.BUILD.hit-.01), hit:sample(module.BUILD.hit)};
""")


@pytest.mark.parametrize('time', [13.7, 18, 22, 26, 32, 38, 43])
def test_lower_third_masks_leave_room_for_descenders(headline_page, time):
    seek(headline_page, time)
    masks = headline_page.locator('[data-receipt-head], [data-receipt-sub]').evaluate_all(LOWER_THIRD_MASKS_LEAVE_ROOM_FOR_DESCENDERS_SCRIPT)
    assert masks
    assert all(mask['bottom'] <= -mask['font'] * .15 for mask in masks)
    assert not headline_page.locator('[data-receipt-chapter]').is_visible()


def test_light_shaft_origin_follows_the_whole_card_border():
    result = stage_result(LIGHT_SHAFT_ORIGIN_FOLLOWS_THE_WHOLE_CARD_BORDER_SCRIPT)
    assert result['count'] >= 8
    assert sorted(result['x']) == pytest.approx([-result['width'] / 2, result['width'] / 2])
    assert sorted(result['y']) == pytest.approx([-result['height'] / 2, result['height'] / 2])
    assert result['origin'] == 0


def test_full_board_wave_is_one_pass_then_settles():
    result = stage_result(FULL_BOARD_WAVE_IS_ONE_PASS_THEN_SETTLES_SCRIPT)
    assert result is not None
    assert result[0] is None and result[-1] is None
    assert result[1]['across'] < result[2]['across'] < result[3]['across']


def test_buildup_does_not_reveal_the_winning_column_before_the_hit():
    result = stage_result(BUILDUP_DOES_NOT_REVEAL_THE_WINNING_COLUMN_BEFORE_THE_HIT_SCRIPT)
    assert result is not None
    assert len(set(result['before'])) == 1
    assert result['hit'][4] > max(value for index, value in enumerate(result['hit']) if index != 4) * 5
