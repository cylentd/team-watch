import { DRAFT_PATH_LIGHT_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { HEADER_LIGHT } from "./constants-draft-motion.mjs";
export { HEADER_LIGHT };
import * as THREE from 'three';
import { mix } from './timeline.mjs';
import { ESTABLISH, passLook, standing } from './draft-establish.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { PALETTE } from './constants.mjs';
import { beamPulse, beamTrail, beamTrigger, beamAccent } from './draft-path-pulse.mjs';
export { makePathBeams } from './draft-path-beams.mjs';

/* A card face's light in the pass (2026-11-05, David: the lights "all seem to light up and diffuse"): unlit cards
   sit dark at `base`, a faint `ambient` pool of `radius` follows the camera so the frame is never dead, and a card
   flares to `peak` on its own border's pulse (draft-path-beams.mjs), so the lit card is the one that pops.
   ~~base .4, peak 1.4 over a radius 1.7 pool: half a dozen cards lit at once, the wash~~ (accepted 2026-11-04). */
export const PATH_LIGHT = Object.freeze({base: .3, peak: 1.5, trail: .85, ambient: .1, radius: 1.1, ahead: .35});

export function pathLight(x, along, seconds, mobile) {
  const point = passLook(seconds, mobile);
  const distance = (x - point.x) ** 2 + (along - point.along - PATH_LIGHT.ahead) ** 2;
  const pool = Math.exp(-distance / (PATH_LIGHT.radius ** 2));
  const age = seconds - beamTrigger({x, y: along}, mobile), pulse = beamPulse(age);
  const lit = mix(PATH_LIGHT.base + PATH_LIGHT.ambient * pool, PATH_LIGHT.trail, beamTrail(age));
  return mix(mix(lit, PATH_LIGHT.peak * beamAccent({x, y: along}, mobile), pulse), 1, standing(seconds));
}

export function makeHeaderLights(headers) {
  const geometry = new THREE.RingGeometry(BOARD.avatar, BOARD.avatar * (1 + HEADER_LIGHT.rim), HEADER_LIGHT.segments);
  const material = new THREE.MeshBasicMaterial({color: PALETTE.blue, transparent: true, opacity: 0,
    side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false});
  const rings = [...headers.values()].map(({disc}) => {
    const ring = new THREE.Mesh(geometry, material);
    ring.position.z = HEADER_LIGHT.lift;
    ring.visible = false;
    disc.add(ring);
    return ring;
  });
  return {update(seconds, active = true) {
    const rise = active ? standing(seconds) : 0;
    const settle = Math.max(0, Math.min(1, (seconds - ESTABLISH.stand[1]) / HEADER_LIGHT.settle));
    const brightness = active ? mix(mix(HEADER_LIGHT.base, HEADER_LIGHT.peak, rise), 1, settle) : 1;
    material.opacity = rise * mix(HEADER_LIGHT.opacity, HEADER_LIGHT.rest, settle);
    headers.forEach(({disc}) => disc.material.color.setRGB(brightness, brightness, brightness));
    rings.forEach(ring => { ring.visible = active && rise > 0; });
  }};
}

export const PATH_GLOW = Object.freeze({resolution: 64, spread: 1.65, softness: .24, opacity: .95, behind: .002});

function haloTexture() {
  const size = PATH_GLOW.resolution, data = new Uint8Array(size * size * TUNING.rgbaChannels);
  for (let row = 0; row < size; row++) {
    for (let column = 0; column < size; column++) {
      const horizontal = Math.abs((column + TUNING.pixelCenter) / size * 2 - 1);
      const vertical = Math.abs((row + TUNING.pixelCenter) / size * 2 - 1);
      const edge = Math.max(horizontal, vertical);
      const alpha = Math.exp(-(((edge - 1 / PATH_GLOW.spread) / PATH_GLOW.softness) ** 2));
      const offset = (row * size + column) * TUNING.rgbaChannels;
      data.set([TUNING.fullChannel, TUNING.fullChannel, TUNING.fullChannel, Math.round(alpha * TUNING.fullChannel)], offset);
    }
  }
  const texture = new THREE.DataTexture(data, size, size);
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

export function makePathGlows(cards) {
  const group = new THREE.Group(), map = haloTexture();
  const geometry = new THREE.PlaneGeometry(BOARD.card * PATH_GLOW.spread, CARD_HEIGHT * PATH_GLOW.spread);
  const items = [...cards.values()].map(card => {
    const material = new THREE.MeshBasicMaterial({map, color: PALETTE[card.pick.pos] ?? PALETTE.silver,
      transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false});
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.copy(card.home); mesh.position.z = -BOARD.depth / 2 - PATH_GLOW.behind;
    group.add(mesh);
    return {card, mesh};
  });
  return {group, update(seconds, mobile, active = true) {
    group.visible = active && standing(seconds) < 1;
    if (!group.visible) return;
    items.forEach(({card, mesh}) => {
      const brightness = pathLight(card.home.x, card.home.y, seconds, mobile);
      const pool = (brightness - PATH_LIGHT.base) / (PATH_LIGHT.peak - PATH_LIGHT.base);
      mesh.material.opacity = PATH_GLOW.opacity * pool * (1 - standing(seconds));
    });
  }};
}
