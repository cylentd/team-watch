"""Physical surroundings for the ensemble board, David: stage depth, November 5."""
from test_madden_stage_polish import stage_result
from test_madden_rev8 import CAMERA


STAGE = """
const {makeRevealGlow} = await import(base + '/draft-reveal-glow.mjs');
const {columnX, rowY} = await import(base + '/draft-board.mjs');
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const {beatTiming} = await import(base + '/timing.mjs');
const cards = new Map(Array.from({length: 120}, (_, index) => [index,
  {home: new THREE.Vector3(columnX(index % 12), rowY(Math.floor(index / 12)), 0)}]));
const reveal = makeRevealGlow(cards);
reveal.update(ESTABLISH.stand[1] + 1, true);
const stage = reveal.mesh.getObjectByName('draft-stage');
"""


BOARD_SURROUNDINGS_HAVE_TWO_SOLID_WINGS_AND_A_DECK_WITH_REAL_DEPTH_SCRIPT = ("""
if (!stage) return null;
const bounds = name => {
  const object = stage.getObjectByName(name);
  return object ? new THREE.Box3().setFromObject(object).getSize(new THREE.Vector3()).toArray() : null;
};
return {left: bounds('stage-left'), right: bounds('stage-right'), deck: bounds('stage-deck')};
""")

STAGE_CLEARS_THE_FLYBY_AND_OTHER_SCENES_AND_RESTORES_ON_REVERSE_SEEK_SCRIPT = ("""
if (!stage) return null;
return [[0, true], [ESTABLISH.stand[1] + 1, true],
  [beatTiming('board').duration, true], [ESTABLISH.stand[1] + 1, false],
  [ESTABLISH.stand[1] + 1, true]].map(([time, active]) => {
    reveal.update(time, active);
    return stage.visible;
  });
""")

DESKTOP_STAGE_LEAVES_ROUND_TEN_ABOVE_THE_CAPTION_CLEARANCE_SCRIPT = ("""
const {frame} = await import(base + '/draft-camera.mjs');
const {rowY, CARD_HEIGHT} = await import(base + '/draft-board.mjs');
ctx.size = {width: 1440, height: 900};
const camera = new THREE.PerspectiveCamera(36, 1440 / 900, .1, 100);
frame(camera, filmMoment(14), ctx);
camera.updateProjectionMatrix(); camera.updateMatrixWorld();
const foot = new THREE.Vector3(0, rowY(9) - CARD_HEIGHT / 2, 0).project(camera);
return (1 - foot.y) / 2;
""")


def test_board_surroundings_have_two_solid_wings_and_a_deck_with_real_depth():
    result = stage_result(STAGE + BOARD_SURROUNDINGS_HAVE_TWO_SOLID_WINGS_AND_A_DECK_WITH_REAL_DEPTH_SCRIPT)
    assert result is not None
    assert result['left'][0] >= 2 and result['right'][0] >= 2
    assert result['left'][2] >= 1 and result['right'][2] >= 1
    assert result['deck'][0] >= 12 and result['deck'][2] >= 2


def test_stage_clears_the_flyby_and_other_scenes_and_restores_on_reverse_seek():
    result = stage_result(STAGE + STAGE_CLEARS_THE_FLYBY_AND_OTHER_SCENES_AND_RESTORES_ON_REVERSE_SEEK_SCRIPT)
    assert result == [False, True, False, False, True]


def test_desktop_stage_leaves_round_ten_above_the_caption_clearance():
    result = stage_result(CAMERA.replace('MOBILE', 'false') + DESKTOP_STAGE_LEAVES_ROUND_TEN_ABOVE_THE_CAPTION_CLEARANCE_SCRIPT)
    assert result <= .72
