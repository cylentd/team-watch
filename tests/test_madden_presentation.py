import json
import subprocess

from test_draft_receipts import ROOT, run


SCENE_RESULT_SCRIPT = ('''
import {registerHooks} from 'node:module';
const base = BASE;
registerHooks({resolve(specifier, context, next) {
  return next(specifier === 'three' ? base + '/vendor/three.module.js' : specifier, context);
}});
globalThis.document = {createElement() {return {width: 0, height: 0,
  getContext() {return {createRadialGradient() {return {addColorStop() {}};}, fillRect() {}};}};}};
const THREE = await import('three');
const {makeRig} = await import(base + '/stage-lights.mjs');
const {finale} = await import(base + '/draft-curse.mjs');
const scene = new THREE.Scene(), rig = makeRig(scene);
rig.update(8, new THREE.Vector3(-.92, .13, .65));
const spots = [];
scene.traverse(object => {if (object.isSpotLight) spots.push(object);});
const board = {headers: new Map([[1, {disc: new THREE.Group(), home: 1, column: 0}]]),
  glow: {material: {opacity: 0}}};
const pulse = [1.4, 1.8].map(seconds => {finale(seconds, board, 1); return board.glow.material.opacity;});
console.log(JSON.stringify(EXPRESSION));
''')


def test_week_markers_explain_the_week_and_outcome():
    markers = run("data.weekMarkers(['smash', 'solid', 'bust', 'out'])")['ok']
    assert [marker['week'] for marker in markers] == ['W1', 'W2', 'W3', 'W4']
    assert [marker['label'] for marker in markers] == ['Boom', 'Solid', 'Bust', 'Out']
    assert [marker['flame'] for marker in markers] == [True, False, False, False]


def scene_result(expression):
    script = SCENE_RESULT_SCRIPT.replace('BASE', json.dumps(ROOT.as_uri())).replace('EXPRESSION', expression)
    result = subprocess.run(['node', '--input-type=module', '-e', script],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_every_visible_lamp_has_a_working_spotlight():
    assert scene_result('spots.length') == 11


def test_the_rig_actually_lights_blip_instead_of_only_the_trophy():
    assert scene_result('spots.some(spot => spot.target.position.distanceTo(new THREE.Vector3(-.92, .6, .65)) < .4)')


def test_romo_column_has_a_visible_pulse_during_the_reading_hold():
    first, second = scene_result('pulse')
    assert abs(first - second) > .25
