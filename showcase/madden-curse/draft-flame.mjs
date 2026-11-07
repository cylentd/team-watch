import { DRAFT_FLAME_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { FLAME } from "./constants-draft-motion.mjs";
export { FLAME };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';

/* The curse: Godwin's card burns in purple flame (David, 2026-11-03: "a real animated flame, not a
   static mark"). A noise flame drawn on two planes plus embers that rise and fade. Revision 10 (David:
   the card hid the fire): the front plane is wider and taller than the card and burns round it, up both
   sides and over its lower edge, with a hole over the portrait and name so they still read; the back
   plane keeps the glow behind. The colours are the curse's own tokens (--hex-*), as League > Trades. */

export const FLAME_VERTEX = `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
/* Value noise and its five-octave sum, shared with the owners' burning avatars (draft-burn.mjs). */
export const FLAME_NOISE = `
  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
  }
  float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; } return v; }`;
const FRAGMENT = `
  uniform float time; uniform float amount; uniform float seed; uniform float edgeWidth; uniform float gain;
  uniform vec4 hole; uniform float holeSoft; uniform vec3 hot; uniform vec3 deep; uniform vec3 core;
  varying vec2 vUv;
  ${FLAME_NOISE}
  void main() {
    vec2 p = vec2(vUv.x * 3.2 + seed, vUv.y * 2.4 - time * ${FLAME.speed.toFixed(2)});
    float n = fbm(p + fbm(p * 1.7) * 0.6);
    float tongues = 0.32 + 0.48 * pow(0.5 + 0.5 * sin(vUv.x * 23.0 + n * 5.0), 1.4);
    float edge = smoothstep(0.0, edgeWidth, vUv.x) * (1.0 - smoothstep(1.0 - edgeWidth, 1.0, vUv.x));
    float baseFade = smoothstep(0.0, 0.12, vUv.y);
    float silhouette = 1.0 - smoothstep(tongues - 0.15, tongues + 0.08, vUv.y);
    float inside = smoothstep(hole.x, hole.x + holeSoft, vUv.x) * (1.0 - smoothstep(hole.z - holeSoft, hole.z, vUv.x))
      * smoothstep(hole.y, hole.y + holeSoft, vUv.y) * (1.0 - smoothstep(hole.w - holeSoft, hole.w, vUv.y));
    float flame = min(1.0, silhouette * edge * baseFade * (0.45 + 0.55 * n) * amount * gain) * (1.0 - inside);
    float flicker = 0.85 + 0.15 * sin(time * ${FLAME.flicker.toFixed(1)} + n * 6.0);
    vec3 colour = mix(deep, hot, smoothstep(0.1, 0.8, flame)) + core * pow(flame, 4.0) * 0.12;
    gl_FragColor = vec4(colour * flicker, flame);
  }`;

/* The flame's colours as shader uniforms: the curse's hex tokens. */
export const flameColours = () => ({hot: {value: new THREE.Color(PALETTE.hexRim)}, deep: {value: new THREE.Color(PALETTE.hex1)},
  core: {value: new THREE.Color(PALETTE.white)}});
const NO_HOLE = [2, 2, 2, 2, .01];

function plane([width, height], seed, edgeWidth, gain = 1, [left, bottom, right, top, soft] = NO_HOLE) {
  const material = new THREE.ShaderMaterial({vertexShader: FLAME_VERTEX, fragmentShader: FRAGMENT,
    uniforms: {time: {value: 0}, amount: {value: 0}, seed: {value: seed}, edgeWidth: {value: edgeWidth}, gain: {value: gain},
      hole: {value: new THREE.Vector4(left, bottom, right, top)}, holeSoft: {value: soft}, ...flameColours()},
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false});
  return new THREE.Mesh(new THREE.PlaneGeometry(BOARD.card * width, CARD_HEIGHT * height), material);
}

/* A round, soft ember, so the points never read as square pixels. */
export function spark() {
  const element = document.createElement('canvas');
  element.width = element.height = TUNING.sparkSize;
  const context = element.getContext('2d'), gradient = context.createRadialGradient(TUNING.sparkCenter, TUNING.sparkCenter, 0, TUNING.sparkCenter, TUNING.sparkCenter, TUNING.sparkRadius);
  gradient.addColorStop(0, 'rgba(255,255,255,1)'); gradient.addColorStop(1, 'rgba(255,255,255,0)');
  context.fillStyle = gradient; context.fillRect(0, 0, TUNING.sparkSize, TUNING.sparkSize);
  return new THREE.CanvasTexture(element);
}

/* Where the front plane's centre sits on the card, so its foot is `frontBelow` under the card's. */
export const frontCentre = () => -CARD_HEIGHT / 2 - CARD_HEIGHT * FLAME.frontBelow + CARD_HEIGHT * FLAME.front[1] / 2;

export function makeFlame() {
  const group = new THREE.Group();
  const back = plane(FLAME.back, 0, FLAME.edge.back), front = plane(FLAME.front, TUNING.frontPhase, FLAME.edge.front, FLAME.frontGain, FLAME.hole);
  back.position.set(0, CARD_HEIGHT * (FLAME.back[1] - 1) / 2, -BOARD.depth);
  front.position.set(0, frontCentre(), BOARD.depth / 2 + TUNING.frontZ);
  front.renderOrder = 2;   // over the card's face and its stamps
  const seeds = Array.from({length: FLAME.embers}, (_, index) => [(index * TUNING.horizontalSeedStep) % 1, (index * TUNING.verticalSeedStep) % 1]);
  const positions = new Float32Array(FLAME.embers * TUNING.positionComponents), geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, TUNING.positionComponents));
  const embers = new THREE.Points(geometry, new THREE.PointsMaterial({color: PALETTE.hexRim, size: FLAME.emberSize, map: spark(),
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  group.add(back, front, embers);

  /* Burn at `amount` (0 out, 1 full) for this second of the beat. */
  function update(seconds, amount) {
    group.visible = amount > 0;
    [back, front].forEach(mesh => { mesh.material.uniforms.time.value = seconds; mesh.material.uniforms.amount.value = amount; });
    seeds.forEach(([across, phase], index) => {
      const rise = (seconds * FLAME.emberSpeed + phase) % 1;
      positions[index * TUNING.positionComponents] = (across < TUNING.sideThreshold ? -1 : 1) * BOARD.card * (TUNING.emberEdge + phase * TUNING.emberSpread) + Math.sin(seconds * TUNING.emberSwayFrequency + index) * FLAME.emberSway * rise;
      positions[index * TUNING.positionComponents + 1] = -CARD_HEIGHT / 2 + rise * CARD_HEIGHT * FLAME.emberRise * TUNING.emberRiseScale;
      positions[index * TUNING.positionComponents + 2] = BOARD.depth / 2 + TUNING.emberZ;
    });
    geometry.attributes.position.needsUpdate = true;
    embers.material.opacity = amount;
  }
  return {group, update};
}
