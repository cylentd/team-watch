import json
import subprocess
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse'


TROPHY_POSE_IS_STATIC_UNLESS_THE_VIEWER_ROTATES_IT_SCRIPT = ('''
const {poseTrophy} = await import(base + '/trophy.mjs');
const trophy = new THREE.Group();
return [0, 1, 4, 7.9].map(seconds => {
  trophy.rotation.set(seconds, seconds, seconds);
  poseTrophy(trophy, 0);
  return trophy.rotation.toArray().slice(0, 3);
});
''')

TEAM_NAMES_CLEAR_BOTH_THE_RAIL_AND_AVATAR_SCRIPT = ('''
const {BOARD, CARD_HEIGHT, boardTop, rowY} = await import(base + '/draft-board.mjs');
const name = boardTop() - BOARD.teamName.below;
const rail = rowY(0) + CARD_HEIGHT / 2 + (BOARD.pitchY - CARD_HEIGHT) / 2 + BOARD.stripHeight / 2;
return {railGap: name - BOARD.teamName.height / 2 - rail,
  avatarGap: boardTop() - BOARD.avatar - name - BOARD.teamName.height / 2};
''')

HAZE_IS_LOW_AND_TIME_DRIVEN_WITHOUT_HARD_SHEET_EDGES_SCRIPT = ('''
const {makeHaze} = await import(base + '/stage-haze.mjs');
const haze = makeHaze();
haze.update(2, new THREE.Vector3(3, 2, 7));
const first = haze.group.children.map(mesh => mesh.material.uniforms.time.value);
haze.update(3, new THREE.Vector3(3, 2, 7));
return {first, next: haze.group.children.map(mesh => mesh.material.uniforms.time.value),
  low: haze.group.children.every(mesh => mesh.position.y + mesh.geometry.parameters.height / 2 < 1),
  transparent: haze.group.children.every(mesh => mesh.material.transparent && !mesh.material.depthWrite),
  feathered: haze.group.children.every(mesh => mesh.material.fragmentShader.includes('smoothstep'))};
''')

TROPHY_POSE_IS_STATIC_UNLESS_THE_VIEWER_ROTATES_IT_SCRIPT_2 = ('''
const {poseTrophy} = await import(base + '/trophy.mjs');
const trophy = new THREE.Group(); poseTrophy(trophy, .3);
return trophy.rotation.y;
''')

FLOOR_BOUNDARY_IS_BEYOND_THE_OPENING_CAMERA_FAR_CLIP_SCRIPT = ('''
const {STAGE} = await import(base + '/environment.mjs');
return STAGE.floor / 2;
''')

STAGE_RESULT_SCRIPT = ('''
import {registerHooks} from 'node:module';
const base = BASE;
registerHooks({resolve(specifier, context, next) {
  const path = specifier === 'three' ? base + '/vendor/three.module.js'
    : specifier.startsWith('three/addons/') ? base + '/vendor/' + specifier.slice('three/addons/'.length) : specifier;
  return next(path, context);
}});
const THREE = await import('three');
console.log(JSON.stringify(await (async () => {EXPRESSION})()));
''')


def stage_result(expression):
    script = STAGE_RESULT_SCRIPT.replace('BASE', json.dumps(SOURCE.as_uri())).replace('EXPRESSION', expression)
    result = subprocess.run(['node', '--input-type=module', '-e', script],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_trophy_pose_is_static_unless_the_viewer_rotates_it():
    poses = stage_result(TROPHY_POSE_IS_STATIC_UNLESS_THE_VIEWER_ROTATES_IT_SCRIPT)
    assert poses == [[0, -.45, 0]] * 4
    assert stage_result(TROPHY_POSE_IS_STATIC_UNLESS_THE_VIEWER_ROTATES_IT_SCRIPT_2) == pytest.approx(-.15)


def test_floor_boundary_is_beyond_the_opening_camera_far_clip():
    assert stage_result(FLOOR_BOUNDARY_IS_BEYOND_THE_OPENING_CAMERA_FAR_CLIP_SCRIPT) > 80


def test_team_names_clear_both_the_rail_and_avatar():
    bounds = stage_result(TEAM_NAMES_CLEAR_BOTH_THE_RAIL_AND_AVATAR_SCRIPT)
    assert bounds['railGap'] >= .1
    assert bounds['avatarGap'] >= .02


def test_haze_is_low_and_time_driven_without_hard_sheet_edges():
    result = stage_result(HAZE_IS_LOW_AND_TIME_DRIVEN_WITHOUT_HARD_SHEET_EDGES_SCRIPT)
    assert result['first'] and all(value == 2 for value in result['first'])
    assert all(value == 3 for value in result['next'])
    assert result['low'] and result['transparent'] and result['feathered']
