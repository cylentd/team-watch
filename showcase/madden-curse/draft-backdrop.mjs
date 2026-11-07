import { DRAFT_BACKDROP_DETAIL as TUNING } from './constants-draft-surfaces.mjs';
import { BACKLIGHT } from "./constants-draft-surfaces.mjs";
export { BACKLIGHT };
import * as THREE from 'three';
import { standing } from './draft-establish.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { PALETTE } from './constants.mjs';
import { beatTiming } from './timing.mjs';
import { seg } from './draft-motion.mjs';

/* The wall behind the standing board (2026-11-05, David: the board "graphic ... is pretty cheap looking"). The
   board stood in a flat black void, every card lit alike; now the wall behind it is lit by the broadcast blue,
   brightest just behind the board and falling off to the room, the way a stage wall is lit behind a set.
   It lies behind the cards, rises with the stand-up and lowers over the beat's last `out` seconds, so it never
   lights the fly-by's table and leaves the steal's close-up dark. */

/* The light's alpha, a rounded rectangle the board's shape that falls off softly to nothing at the plane's edge. */
export function backdropTexture() {
  const size = BACKLIGHT.resolution, data = new Uint8Array(size * size * TUNING.rgbaChannels);
  for (let row = 0; row < size; row++) {
    for (let column = 0; column < size; column++) {
      const x = Math.max(0, Math.abs((column + TUNING.pixelCenter) / size * 2 - 1) - BACKLIGHT.inner);
      const y = Math.max(0, Math.abs((row + TUNING.pixelCenter) / size * 2 - 1) - BACKLIGHT.inner);
      const alpha = Math.exp(-((Math.hypot(x, y) / BACKLIGHT.soft) ** 2)) * (1 - Math.max(x, y) / (1 - BACKLIGHT.inner));
      data.set([TUNING.fullChannel, TUNING.fullChannel, TUNING.fullChannel, Math.round(Math.max(0, alpha) * TUNING.fullChannel)], (row * size + column) * TUNING.rgbaChannels);
    }
  }
  const texture = new THREE.DataTexture(data, size, size);
  texture.magFilter = texture.minFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

/* How lit the wall is `seconds` into the board beat, 0 to 1. */
export function backlightAt(seconds) {
  const end = beatTiming('board').duration;
  return standing(seconds) * (1 - seg(seconds, end - BACKLIGHT.out, end));
}

export function makeBacklight(cards) {
  const homes = [...cards.values()].map(card => card.home);
  const left = Math.min(...homes.map(home => home.x)), right = Math.max(...homes.map(home => home.x));
  const bottom = Math.min(...homes.map(home => home.y)), top = Math.max(...homes.map(home => home.y)) + BOARD.header;
  const material = new THREE.MeshBasicMaterial({map: backdropTexture(), color: PALETTE.broadcast, transparent: true,
    opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false});
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry((right - left + BOARD.card) * BACKLIGHT.size,
    (top - bottom + CARD_HEIGHT) * BACKLIGHT.size), material);
  mesh.position.set((left + right) / 2, (top + bottom) / 2, BACKLIGHT.depth);
  return {mesh, update(seconds, active) {
    const level = active ? backlightAt(seconds) : 0;
    mesh.visible = level > 0;
    material.opacity = BACKLIGHT.level * level;
  }};
}
