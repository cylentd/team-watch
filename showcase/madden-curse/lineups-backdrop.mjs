import { BACKDROP } from "./constants-lineups.mjs";
export { BACKDROP };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { BOARD_STAGE } from './draft-stage.mjs';
import { backdropTexture } from './draft-backdrop.mjs';

/* The set behind Chapter 4's desk (David 2026-11-05: the desk stood in a black void, half the frame dead). Chapter 1's
   stage, rebuilt here: a wall lit broadcast blue from behind the desk, brightest behind each station and falling off
   to the room (draft-backdrop.mjs), and a row of the stage wings' fins with their blue recess lights on top
   (draft-stage.mjs), all behind Chapter 5's riser (power-layout.mjs, z 0.6 to ~3) so the crane onto it sees them too.
   Flat-shaded like Chapter 1's stage; `update(level)` fades the whole set (1 lit, 0 gone). */

export function makeBackdrop(stations) {
  const group = new THREE.Group(), settings = BACKDROP;
  group.name = 'lineups-backdrop';
  const flat = (color, strength) => new THREE.MeshBasicMaterial({color: new THREE.Color(color).multiplyScalar(strength),
    transparent: true, toneMapped: false});
  const materials = {wall: flat(PALETTE.cardSurface, BOARD_STAGE.surface), metal: flat(PALETTE.slabEdge, BOARD_STAGE.edge),
    light: flat(PALETTE.broadcast, 1), room: flat(PALETTE.room, 1)};
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(settings.wall.width, settings.wall.height), materials.room);
  wall.position.set(0, settings.wall.y, settings.wall.z);
  group.add(wall);
  const glowMaterial = new THREE.MeshBasicMaterial({map: backdropTexture(), color: PALETTE.broadcast, transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, opacity: settings.glow.level});
  stations.forEach(x => {
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(settings.glow.width, settings.glow.height), glowMaterial);
    glow.position.set(x, settings.glow.y, settings.glow.z);
    group.add(glow);
  });
  const {fins} = settings, step = (fins.to - fins.from) / (fins.count - 1), half = (fins.count - 1) / 2;
  for (let index = 0; index < fins.count; index++) {
    const height = fins.tall * (1 - fins.taper * Math.abs(index - half) / half * 2);
    const fin = new THREE.Mesh(new THREE.BoxGeometry(fins.width, height, fins.depth),
      [materials.wall, materials.wall, materials.metal, materials.wall, materials.metal, materials.wall]);
    fin.position.set(fins.from + index * step, height / 2, fins.z);
    const light = new THREE.Mesh(new THREE.BoxGeometry(fins.width, settings.recess, settings.recess), materials.light);
    light.position.set(fin.position.x, height, fins.z + fins.depth / 2);
    group.add(fin, light);
  }
  const levels = new Map([...Object.values(materials), glowMaterial].map(material => [material, material.opacity]));
  return {group, update(level) {
    group.visible = level > 0;
    levels.forEach((full, material) => { material.opacity = full * level; });
  }};
}
