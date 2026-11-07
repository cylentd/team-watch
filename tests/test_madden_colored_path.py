import pytest
from test_madden_stage_polish import stage_result


CUT_FLASH_STARTS_ONLY_AT_THE_END_OF_THE_FOOTBALL_ZOOM_SCRIPT = ("""
const {flareAt} = await import(base + '/film-zoom.mjs');
const {OPENING} = await import(base + '/constants.mjs');
return [-.2, -.06, -.02, 0, .07, .15].map(offset => flareAt(OPENING.duration + offset));
""")

MOVING_HALOS_MATCH_CARD_COLORS_AND_CLEAR_FOR_THE_BOARD_HOLD_SCRIPT = ("""
const {makePathGlows} = await import(base + '/draft-path-light.mjs');
const {passLook, ESTABLISH} = await import(base + '/draft-establish.mjs');
const {PALETTE} = await import(base + '/constants.mjs');
const point = passLook(2, false);
const cards = new Map(['QB', 'RB', 'WR'].map((pos, index) => [index,
  {pick: {pos}, home: new THREE.Vector3(point.x + index * 4, point.along, 0)}]));
const lights = makePathGlows?.(cards);
if (!lights) return null;
lights.update(2, false);
const shown = lights.group.children.map(mesh => ({color: mesh.material.color.getHex(), opacity: mesh.material.opacity,
  behind: mesh.position.z < 0, width: mesh.geometry.parameters.width}));
lights.update(ESTABLISH.stand[1], false);
return {shown, colors: ['QB', 'RB', 'WR'].map(pos => PALETTE[pos]), held: lights.group.visible};
""")


def test_cut_flash_starts_only_at_the_end_of_the_football_zoom():
    result = stage_result(CUT_FLASH_STARTS_ONLY_AT_THE_END_OF_THE_FOOTBALL_ZOOM_SCRIPT)
    assert result[:2] == [0, 0]
    assert 0 < result[2] < result[3] <= .6
    assert 0 < result[4] < result[3]
    assert result[5] == 0


def test_moving_halos_match_card_colors_and_clear_for_the_board_hold():
    result = stage_result(MOVING_HALOS_MATCH_CARD_COLORS_AND_CLEAR_FOR_THE_BOARD_HOLD_SCRIPT)
    assert result is not None
    assert [light['color'] for light in result['shown']] == result['colors']
    assert result['shown'][0]['opacity'] > result['shown'][1]['opacity'] + .2
    assert all(light['behind'] and light['width'] > .5 for light in result['shown'])
    assert result['held'] is False
