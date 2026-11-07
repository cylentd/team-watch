import { DRAFT_BURN_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { BURN } from "./constants-draft-motion.mjs";
export { BURN };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { PROPS } from './draft-props.mjs';
import { FLAME_NOISE, FLAME_VERTEX, flameColours, spark } from './draft-flame.mjs';
import { seg } from './draft-motion.mjs';

/* The curse is passed, not piled up (David, revision 10): when Godwin's card lands on a team's pad, the
   owner's avatar ignites in place, a `flash` s flash and then its ring burns (rev 17, David; ~~a ball of fire
   ran from the card to the avatar~~, rev 10). When he leaves, that fire goes out in `out` seconds and the avatar is clean again: the curse
   leaves with him (revision 14 storyboard). One avatar burns at a time. The run starts on the landing, a
   drum onset (constants.mjs TRAIL.landings). ~~A charred avatar, a wisp of smoke and a fading pad~~
   (revisions 10-13). */


const FIRE = `
  uniform float time; uniform float amount; uniform float seed; uniform float radius;
  uniform vec3 hot; uniform vec3 deep; uniform vec3 core;
  varying vec2 vUv;
  ${FLAME_NOISE}
  void main() {
    vec2 q = (vUv - 0.5) * 2.0;
    float d = length(q);
    float n = fbm(vec2(q.x * 3.0 + seed, q.y * 2.4 - time * ${BURN.speed.toFixed(2)}));
    float angle = atan(q.y, q.x) + (n - 0.5) * 0.9;   // the noise bends each tongue as it climbs
    float up = 0.15 + 0.85 * pow(0.5 + 0.5 * sin(angle), 1.5);   // fire climbs: long tongues on top, a lick below
    float tongue = pow(0.5 + 0.5 * sin(angle * 7.0 + n * 6.0 - time * 2.0), 1.2);   // separate tongues, not a halo
    float outer = radius + (0.04 + 0.55 * tongue * n) * up;
    float body = smoothstep(radius - 0.08, radius - 0.02, d) * (1.0 - smoothstep(outer - 0.1, outer, d));
    float rim = exp(-pow((d - radius) / 0.03, 2.0));
    float flame = min(1.0, (body * (0.3 + 0.7 * n) * tongue + rim * 0.6) * amount * ${BURN.gain.toFixed(2)});
    vec3 colour = mix(deep, hot, smoothstep(0.1, 0.8, flame)) + core * pow(flame, 4.0) * 0.12;
    gl_FragColor = vec4(colour, flame);
  }`;

const fire = (size, radius, seed) => new THREE.Mesh(new THREE.PlaneGeometry(size, size),
  new THREE.ShaderMaterial({vertexShader: FLAME_VERTEX, fragmentShader: FIRE,
    uniforms: {time: {value: 0}, amount: {value: 0}, seed: {value: seed}, radius: {value: radius}, ...flameColours()},
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));

function points(count, size) {
  const geometry = new THREE.BufferGeometry(), positions = new Float32Array(count * TUNING.positionComponents);
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, TUNING.positionComponents));
  const mesh = new THREE.Points(geometry, new THREE.PointsMaterial({color: PALETTE.hexRim, size, map: spark(),
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  return {mesh, positions, geometry};
}

/* Each owner's visits from the trail: the card's landing on that team's pad and the moment it leaves, `move`
   before the next landing. The waiver wire is nobody's: its visits are left out. */
export function ownerVisits(steps, landings, move) {
  const visits = new Map();
  steps.forEach((step, index) => {
    if (step.station === 'pit') return;
    const next = index + 1;
    const leave = next < steps.length ? landings[next] - move : Infinity;
    visits.set(step.station, [...(visits.get(step.station) ?? []), {arrive: landings[index], leave}]);
  });
  return visits;
}

/* An owner's fire at `seconds`: the flash 1..0 over its first BURN.flash s and the ring's burn 0..1; 0 again once he is left. */
export function ownerState(seconds, visits) {
  const visit = visits.findLast(entry => seconds >= entry.arrive);
  if (!visit) return {flash: 0, burn: 0};
  const out = Number.isFinite(visit.leave) ? seg(seconds, visit.leave, visit.leave + BURN.out) : 0;   // the last stop never leaves
  const since = seconds - visit.arrive;
  const flash = since < BURN.flash && out < 1 ? 1 - since / BURN.flash : 0;
  const burn = seg(seconds, visit.arrive + BURN.flash, visit.arrive + BURN.flash + BURN.catch) * (1 - out);
  return {flash, burn};
}

/* The fire for one team's stop, in the station's own frame: the card stands at x 0, the avatar beside it. */
export function makeBurn() {
  const group = new THREE.Group(), radius = 1 / BURN.scale;
  const ring = fire(PROPS.avatar * 2 * BURN.scale, radius, TUNING.ringPhase);
  ring.position.set(PROPS.avatarSide, PROPS.avatarHeight, TUNING.ringZ);
  const flash = new THREE.Sprite(new THREE.SpriteMaterial({color: PALETTE.hexRim, map: spark(), transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  flash.scale.setScalar(PROPS.avatar * 2 * BURN.flashSize);
  flash.position.set(PROPS.avatarSide, PROPS.avatarHeight, TUNING.flashZ);
  const embers = points(BURN.embers, BURN.emberSize);
  group.add(ring, flash, embers.mesh);

  function update(seconds, visits) {
    const state = ownerState(seconds, visits);
    ring.material.uniforms.time.value = seconds;
    ring.material.uniforms.amount.value = state.burn;
    ring.visible = state.burn > 0;
    flash.material.opacity = state.flash;
    flash.visible = state.flash > 0;
    const burn = state.burn;
    // The burning avatar's embers rise from its ring.
    for (let index = 0; index < BURN.embers; index++) {
      const angle = index / BURN.embers * Math.PI * 2, rise = (seconds * BURN.emberSpeed + index * TUNING.emberSeedStep) % 1;
      embers.positions.set([PROPS.avatarSide + Math.cos(angle) * PROPS.avatar, PROPS.avatarHeight + Math.sin(angle) * PROPS.avatar + rise * BURN.emberRise, TUNING.emberZ], index * TUNING.positionComponents);
    }
    embers.mesh.material.opacity = burn;
    embers.mesh.visible = burn > 0;
    embers.geometry.attributes.position.needsUpdate = true;
  }
  return {group, update};
}
