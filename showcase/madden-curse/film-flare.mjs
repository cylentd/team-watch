import { FILM_FLARE_DETAIL as TUNING } from './constants-title.mjs';
import { FLARE, FLOOR_HAZE } from "./constants-title.mjs";
export { FLARE, FLOOR_HAZE };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { HAZE_NOISE, HAZE_VERTEX } from './stage-haze.mjs';

/* The title's hit (David, revision 13): a white lens flare bursts from the trophy's ball, a long
   anamorphic streak across the frame and a soft bloom, in `in` seconds and gone `decay` seconds later,
   and the beams flare with it (stage-lights.mjs `boost`). Over the title's hold a thin white haze fades in
   on the floor, drifting slowly and never higher than the trophy's base, so the beams read through it.
   White only, never dark or purple (rule 24: an NFL broadcast, not Halloween). */

/* How bright the flare is `age` seconds after the title's hit: up fast in `in`, then down over `decay`. */
export function flareAmount(age) {
  if (age < 0) return 0;
  if (age < FLARE.in) return 1 - (1 - age / FLARE.in) ** TUNING.entranceExponent;
  return Math.max(0, 1 - (age - FLARE.in) / FLARE.decay) ** 2;
}

function streakTexture() {
  const size = FLARE.texture, canvas = document.createElement('canvas');
  canvas.width = size; canvas.height = size / TUNING.streakAspect;
  const context = canvas.getContext('2d'), white = css(PALETTE.white);
  const across = context.createLinearGradient(0, 0, size, 0);
  across.addColorStop(0, 'transparent'); across.addColorStop(TUNING.gradientCenter, white); across.addColorStop(1, 'transparent');
  context.fillStyle = across; context.fillRect(0, 0, size, canvas.height);
  // Thin top and bottom: fade the band toward its edges so it reads as a line of light, not a bar.
  context.globalCompositeOperation = 'destination-in';
  const down = context.createLinearGradient(0, 0, 0, canvas.height);
  down.addColorStop(0, 'transparent'); down.addColorStop(TUNING.gradientCenter, white); down.addColorStop(1, 'transparent');
  context.fillStyle = down; context.fillRect(0, 0, size, canvas.height);
  return new THREE.CanvasTexture(canvas);
}

function bloomTexture() {
  const size = FLARE.texture, half = size / 2, canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const context = canvas.getContext('2d'), glow = context.createRadialGradient(half, half, 0, half, half, half);
  glow.addColorStop(0, css(PALETTE.white)); glow.addColorStop(1, 'transparent');
  context.fillStyle = glow; context.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

const sprite = map => {
  const mesh = new THREE.Sprite(new THREE.SpriteMaterial({map, color: PALETTE.white, transparent: true, depthTest: false,
    depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  mesh.renderOrder = TUNING.renderOrder; mesh.visible = false;
  return mesh;
};

const HAZE_FRAGMENT = `
  uniform float time; uniform float seed; uniform float opacity; uniform vec3 colour;
  varying vec2 vUv;
  ${HAZE_NOISE}
  void main() {
    vec2 flow = vec2(vUv.x * 5.0 + time * ${FLOOR_HAZE.drift.toFixed(2)} + seed, vUv.y * 4.0 - time * 0.02);
    float wisps = noise(flow) * 0.6 + noise(flow * 2.1 + vec2(seed, time * 0.03)) * 0.4;
    vec2 centre = vUv - 0.5;
    float pool = 1.0 - smoothstep(0.2, 0.5, length(centre * vec2(1.0, 1.3)));
    gl_FragColor = vec4(colour, pool * smoothstep(0.25, 0.85, wisps) * opacity);
  }`;

/* The flare's two sprites and the floor haze. `pose(age, ball, hold, time)`: age after the hit, the ball's
   world position, the hold's progress 0..1 and the film second for the haze's drift. */
export function makeFlare(scene) {
  const streak = sprite(streakTexture()), bloom = sprite(bloomTexture());
  const haze = new THREE.Group(), geometry = new THREE.PlaneGeometry(...FLOOR_HAZE.size);
  FLOOR_HAZE.layers.forEach((height, index) => {
    const mesh = new THREE.Mesh(geometry, new THREE.ShaderMaterial({vertexShader: HAZE_VERTEX, fragmentShader: HAZE_FRAGMENT,
      uniforms: {time: {value: 0}, seed: {value: index * TUNING.hazeSeedStep}, opacity: {value: 0}, colour: {value: new THREE.Color(PALETTE.white)}},
      transparent: true, depthWrite: false, toneMapped: false, side: THREE.DoubleSide}));
    mesh.rotation.x = -Math.PI / 2; mesh.position.y = height;
    haze.add(mesh);
  });
  haze.visible = false;
  scene.add(streak, bloom, haze);
  return {streak, bloom, haze, hide() { streak.visible = bloom.visible = haze.visible = false; },
    pose(age, ball, hold, time) {
      const amount = flareAmount(age);
      [streak, bloom].forEach(mesh => { mesh.visible = amount > 0; mesh.position.copy(ball); mesh.material.opacity = amount; });
      streak.scale.set(FLARE.streak.width * (TUNING.streakBaseScale + TUNING.streakGrowthScale * amount), FLARE.streak.height, 1);
      bloom.scale.setScalar(FLARE.bloom * (TUNING.bloomBaseScale + TUNING.bloomGrowthScale * amount));
      const there = Math.min(1, Math.max(0, (age + FLOOR_HAZE.before) / FLOOR_HAZE.before)) / 2 + hold / 2;
      const pushed = 1 + FLOOR_HAZE.push * (1 - (1 - Math.min(1, Math.max(0, age / FLOOR_HAZE.pushFor))) ** TUNING.hazePushExponent);
      haze.visible = there > 0; haze.scale.set(pushed, 1, pushed);
      haze.children.forEach(mesh => {
        mesh.material.uniforms.time.value = time;
        mesh.material.uniforms.opacity.value = FLOOR_HAZE.opacity * there;
      });
      return amount;
    }};
}
