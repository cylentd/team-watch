from test_madden_stage_polish import stage_result


BEAMS_FIRE_NEAR_THE_CAMERA_PATH_AND_CLEAR_AFTER_PASS_SCRIPT = ("""
const module = await import(base + '/draft-path-light.mjs');
if (!module.makePathBeams) return null;
const {passLook} = await import(base + '/draft-establish.mjs');
const point = passLook(2, false);
const cards = new Map([0, 1].map(index => [index, {pick: {pos: 'QB'},
  home: new THREE.Vector3(point.x + index * 8, point.along, 0)}]));
const lights = module.makePathBeams(cards);
lights.update(2, false);
const sampled = lights.group.children.map(mesh => ({opacity: mesh.material.opacity,
  height: mesh.geometry.parameters.height, z: mesh.position.z}));
lights.update(6, false);
return {sampled, ended: lights.group.visible};
""")

TITLE_WAVE_SPREADS_TOWARD_FOREGROUND_NOT_OVER_TROPHY_SCRIPT = ("""
globalThis.document = {createElement: () => ({width: 0, height: 0, getContext: () => ({
 createRadialGradient: () => ({addColorStop() {}}), fillRect() {}})})};
const {makeImpact} = await import(base + '/film-impact.mjs');
const effect = makeImpact(new THREE.Group());
effect.ring.updateMatrix();
const attribute = effect.ring.geometry.attributes.position;
const points = Array.from({length: attribute.count}, (_, index) =>
 new THREE.Vector3().fromBufferAttribute(attribute, index).applyMatrix4(effect.ring.matrix));
return {up: Math.max(...points.map(point => point.y)), forward: Math.max(...points.map(point => point.z))};
""")

WARMUP_UPLOADS_TEXTURES_DRAWS_OFFSCREEN_AND_RESTORES_TARGET_SCRIPT = ("""
const module = await import(base + '/scene-warmup.mjs').catch(() => null);
if (!module) return null;
const events = [], scene = new THREE.Scene(), texture = new THREE.Texture();
scene.add(new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial({map: texture})));
const renderer = {getRenderTarget: () => 'screen', setRenderTarget: target => events.push(target === 'screen' ? 'restore' : 'offscreen'),
 initTexture: value => events.push(value === texture ? 'texture' : 'wrong'), getContext: () => ({finish: () => events.push('finish')})};
await module.warmPlayback(renderer, scene, moment => events.push(moment), ['board', 'title']);
return events;
""")


def test_beams_fire_near_the_camera_path_and_clear_after_pass():
    result = stage_result(BEAMS_FIRE_NEAR_THE_CAMERA_PATH_AND_CLEAR_AFTER_PASS_SCRIPT)
    assert result is not None
    assert result["sampled"][0]["opacity"] > .3
    assert result["sampled"][1]["opacity"] == 0
    assert result["sampled"][0]["height"] > 1
    assert result["sampled"][0]["z"] > 0
    assert result["ended"] is False


def test_title_wave_spreads_toward_foreground_not_over_trophy():
    result = stage_result(TITLE_WAVE_SPREADS_TOWARD_FOREGROUND_NOT_OVER_TROPHY_SCRIPT)
    assert result["up"] < .001
    assert result["forward"] > .9


def test_warmup_uploads_textures_draws_offscreen_and_restores_target():
    result = stage_result(WARMUP_UPLOADS_TEXTURES_DRAWS_OFFSCREEN_AND_RESTORES_TARGET_SCRIPT)
    assert result == ['texture', 'offscreen', 'board', 'title', 'finish', 'restore']
