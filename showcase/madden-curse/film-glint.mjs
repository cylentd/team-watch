import { FILM_GLINT_DETAIL as TUNING } from './constants-title.mjs';
import { GLINT } from "./constants-title.mjs";
export { GLINT };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { filmPlan, statAt } from './film.mjs';

/* A glint on every metal hit (rule 19, David rev 8): a four-point star of light that flares on the frame a
   stamp, the 0.0 or the title lands and dies away in about a third of a second. It sits on the thing that
   was hit, so it never crosses the lower third (rule 34). */

function starTexture() {
  const size = GLINT.texture, half = size / 2, canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const context = canvas.getContext('2d'), white = css(PALETTE.white);
  const core = context.createRadialGradient(half, half, 0, half, half, half * TUNING.coreRadiusRatio);
  core.addColorStop(0, white); core.addColorStop(1, 'transparent');
  context.fillStyle = core; context.fillRect(0, 0, size, size);
  // Two thin rays crossing at the core, each fading to nothing at the tips.
  [[size, size * GLINT.ray], [size * GLINT.ray, size]].forEach(([width, height]) => {
    const ray = context.createRadialGradient(half, half, 0, half, half, half);
    ray.addColorStop(0, white); ray.addColorStop(1, 'transparent');
    context.fillStyle = ray; context.fillRect(half - width / 2, half - height / 2, width, height);
  });
  return new THREE.CanvasTexture(canvas);
}

/* How bright a glint is `age` seconds after its hit: a flare in `rise`, then an exponential fade. */
export const glintAmount = age => age < 0 ? 0 : age < GLINT.rise ? age / GLINT.rise : Math.exp(-(age - GLINT.rise) * GLINT.decay);

export function makeGlint(scene, size) {
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: starTexture(), color: PALETTE.white, transparent: true,
    depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  sprite.renderOrder = TUNING.renderOrder; sprite.visible = false;
  scene.add(sprite);
  const at = new THREE.Vector3();
  return {sprite, pose(age, object) {
    const amount = glintAmount(age);
    sprite.visible = amount > GLINT.gone && Boolean(object);
    if (!sprite.visible) return;
    object.getWorldPosition(at);
    sprite.position.copy(at);
    sprite.scale.setScalar(size * (TUNING.baseScale + amount));
    sprite.material.opacity = amount;
    sprite.material.rotation = age * GLINT.turn;
  }};
}

/* Chapter 1's glints: one on each featured card's stamp, light or flip, on its beat's stat frame. */
export function makeDraftGlints(scene) {
  const glint = makeGlint(scene, GLINT.card), beats = filmPlan().beats;
  return {hide() { glint.sprite.visible = false; }, update(moment, items, tile) {
    const beat = beats[moment.beatIndex], hit = beat && statAt(beat);
    const target = !beat ? null : beat.id === 'curse' ? tile : beat.id === 'injury' ? items.injury.props.status
      : beat.id === 'sleeper' ? items.sleeper.props.lights.children.at(-1) : items[beat.id]?.props.stamp;
    glint.pose(hit === null || !target ? -1 : moment.elapsed - hit, target);
  }};
}
