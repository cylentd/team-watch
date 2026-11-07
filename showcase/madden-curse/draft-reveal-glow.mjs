import { REVEAL_GLOW } from "./constants-draft-motion.mjs";
export { REVEAL_GLOW };
import * as THREE from 'three';
import { ESTABLISH } from './draft-establish.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { PALETTE } from './constants.mjs';
import { makeBacklight } from './draft-backdrop.mjs';
import { makeBoardStage } from './draft-stage.mjs';

/* The full-board reveal's one blue backlight wave (rule 46). It sits behind the cards, so only the gaps between
   them and the board's rim show it. 2026-11-05 (David: the standing board read "pretty cheap"): ~~strength .85,
   band .14, gaps at a fifth of the rim~~ was a sliver hidden behind the cards; now a wide, bright sweep whose
   gaps carry `inside` of the rim's light, so the whole board reads backlit as it passes. */

export function revealGlowAt(seconds) {
  const progress = (seconds - ESTABLISH.stand[1]) / REVEAL_GLOW.duration;
  if (progress < 0 || progress >= 1) return null;
  return {across: progress * REVEAL_GLOW.travel - REVEAL_GLOW.lead,
    strength: Math.sin(Math.PI * progress) * REVEAL_GLOW.strength};
}

export function makeRevealGlow(cards) {
  const homes = [...cards.values()].map(card => card.home);
  const left = Math.min(...homes.map(home => home.x)), right = Math.max(...homes.map(home => home.x));
  const bottom = Math.min(...homes.map(home => home.y)), top = Math.max(...homes.map(home => home.y));
  const material = new THREE.ShaderMaterial({uniforms: {across: {value: 0}, strength: {value: 0},
    tint: {value: new THREE.Color(PALETTE.broadcast)}, band: {value: REVEAL_GLOW.band},
    edge: {value: REVEAL_GLOW.edge}, softness: {value: REVEAL_GLOW.softness}, inside: {value: REVEAL_GLOW.inside}},
    vertexShader: `varying vec2 glowUV;
      void main() {glowUV = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);}`,
    fragmentShader: `varying vec2 glowUV; uniform vec3 tint; uniform float across, strength, band, edge, softness, inside;
      void main() {
        float rim = max(abs(glowUV.x - 0.5), abs(glowUV.y - 0.5)) * 2.0;
        float halo = exp(-pow((rim - edge) / softness, 2.0));
        float wave = exp(-pow((glowUV.x - across) / band, 2.0));
        float fall = 1.0 - smoothstep(edge, 1.0, rim);   // to nothing at the plane's edge, so it has no hard side
        gl_FragColor = vec4(tint, wave * (inside * fall + (1.0 - inside) * halo) * strength);
        #include <colorspace_fragment>
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false});
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(right - left + BOARD.card + REVEAL_GLOW.padding,
    top - bottom + CARD_HEIGHT + REVEAL_GLOW.padding), material);
  mesh.position.set((left + right) / 2, (top + bottom) / 2, REVEAL_GLOW.depth);
  // The wave passes over a lit wall (draft-backdrop.mjs); both ride the board's pivot as one group.
  const wall = makeBacklight(cards), stage = makeBoardStage(cards), group = new THREE.Group();
  group.add(stage.group, wall.mesh, mesh);
  return {mesh: group, update(seconds, active) {
    stage.update(seconds, active);
    wall.update(seconds, active);
    const state = active ? revealGlowAt(seconds) : null;
    mesh.visible = Boolean(state);
    if (!state) return;
    material.uniforms.across.value = state.across;
    material.uniforms.strength.value = state.strength;
  }};
}
