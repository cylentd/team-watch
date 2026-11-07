import { DRAFT_PROPS_DETAIL as TUNING } from './constants-draft-surfaces.mjs';
import { PROPS } from "./constants-draft-surfaces.mjs";
export { PROPS };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { PLACARD, TEAM_NAME, placard, stamp, teamName, weekTile } from './draft-textures.mjs';
import { weekMarkers } from './draft-data.mjs';
import { weekFire } from './draft-weekfire.mjs';

/* The small physical things the beats move: week lights, stamps, the waiver floor, the injury's cut. */


const basic = (options = {}) => new THREE.MeshBasicMaterial({toneMapped: false, transparent: true, ...options});

export function weekLights(count) {
  const group = new THREE.Group(), geometry = new THREE.PlaneGeometry(PROPS.light, PROPS.lightHeight);
  const textures = new Map();
  const lights = Array.from({length: count}, (_, index) => {
    const mesh = new THREE.Mesh(geometry, basic({color: PALETTE.white, opacity: 0}));
    const column = index % PROPS.lightsPerRow, row = Math.floor(index / PROPS.lightsPerRow);
    mesh.position.x = (column - (PROPS.lightsPerRow - 1) / 2) * (PROPS.light + PROPS.lightGap);
    mesh.position.y = -row * (PROPS.lightHeight + PROPS.lightGap);
    group.add(mesh);
    return mesh;
  });
  group.position.set(0, -CARD_HEIGHT / 2 - PROPS.lightsBelow - PROPS.lightHeight / 2 + PROPS.lightGap, BOARD.depth / 2 + TUNING.lightZ);
  const fires = new Map();   // a smash light's live flame, made the first time it shows (draft-weekfire.mjs)
  /* Light `index` in `tier`, `on` 0..1, with a pop as it ignites; a smash light burns from its pop on. */
  group.userData.set = (index, tier, on, seconds = 0) => {
    const mesh = lights[index];
    const key = index + ':' + tier;
    if (!textures.has(key)) textures.set(key, weekTile({...weekMarkers(Array.from({length: count}, () => tier))[index], live: tier === 'smash'}));
    mesh.material.map = textures.get(key);
    mesh.material.opacity = lightOpacity(on);
    mesh.visible = on > 0;
    mesh.scale.setScalar(1 + Math.max(0, Math.sin(Math.min(1, on) * Math.PI)) * TUNING.lightPopScale);
    if (tier !== 'smash') { fires.get(index)?.group.removeFromParent(); fires.delete(index); return; }
    if (!fires.has(index)) { const fire = weekFire(PROPS.light, PROPS.lightHeight, index * TUNING.fireSeedStep); mesh.add(fire.group); fires.set(index, fire); }
    fires.get(index).update(seconds, on);
  };
  return group;
}

/* A week light is not there until its moment (rule 17, David rev 8: Golden's boxes showed from the start):
   nothing at 0, then it pops in at a third of its strength and fills as it ignites. ~~Unlit boxes at 0.2
   from the beat's first frame~~ (revision 7). */
export const lightOpacity = on => on > 0 ? Math.min(1, TUNING.lightOpacityBase + on) : 0;

export function stampMesh(text, color, ink) {
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(PROPS.stampWidth, PROPS.stampWidth / 2), basic({map: stamp(text, color, ink), depthWrite: false}));
  mesh.position.z = BOARD.depth / 2 + TUNING.slicedFaceZ;
  return mesh;
}

/* The cut: one straight line through the middle of the card, a little off level, like a blade. */
export const CARD_CUT = Object.freeze({slope: .12, depth: .004});

/* The card's face as two textured halves meeting on the cut: [top, bottom]. */
export function cutHalves(map) {
  const half = BOARD.card / 2, edge = CARD_HEIGHT / 2, cut = x => CARD_CUT.slope * x;
  const shapes = [[[-half, cut(-half)], [half, cut(half)], [half, edge], [-half, edge]],
    [[-half, -edge], [half, -edge], [half, cut(half)], [-half, cut(-half)]]];
  return shapes.map(corners => {
    const positions = [], uvs = [];
    [0, 1, 2, 0, 2, TUNING.quadLastCorner].forEach(index => {
      const [x, y] = corners[index];
      positions.push(x, y, BOARD.depth / 2 + CARD_CUT.depth);
      uvs.push((x + half) / BOARD.card, (y + edge) / CARD_HEIGHT);
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, TUNING.positionComponents));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    const piece = new THREE.Mesh(geometry, basic({map, side: THREE.DoubleSide}));
    piece.visible = false;
    return piece;
  });
}

/* The waiver floor: one pad per place the cursed card visits, a lit disc in `color` (the team's, or the
   wire's grey-blue), with one word under it. The wire's pad has no avatar or name: WAIVER says it once
   (rev 15; ~~a FREE AGENT icon and name beside it~~). */
export function station(kind, text, color, avatar = null, owner = null) {
  const group = new THREE.Group();
  const top = new THREE.Color(color).lerp(new THREE.Color(PALETTE.slab), 1 - PROPS.padTop);
  const pad = new THREE.Mesh(new THREE.CylinderGeometry(PROPS.pad, PROPS.pad, PROPS.padHeight, TUNING.padSegments),
    [basic({color: PALETTE.unlit, transparent: false}), basic({color: top, transparent: false}), basic({color: PALETTE.unlit, transparent: false})]);
  pad.position.y = PROPS.padHeight / 2;
  group.add(pad);
  // A big word on the floor in front of the pad, tilted up toward the camera.
  const words = new THREE.Mesh(new THREE.PlaneGeometry(PROPS.labelWidth, PROPS.labelWidth * PLACARD.height / PLACARD.width),
    basic({map: placard(text, kind === 'lineup' ? css(PALETTE.broadcast) : css(PALETTE.white)), depthWrite: false}));
  words.rotation.x = PROPS.labelTilt; words.position.set(0, PROPS.labelLift, PROPS.pad + PROPS.labelAhead);
  group.add(words);
  // Beside the pad, where the card never covers them: the team's avatar, and its name under it.
  if (avatar) {
    const face = new THREE.Mesh(new THREE.CircleGeometry(PROPS.avatar, TUNING.avatarSegments), avatar);
    face.position.set(PROPS.avatarSide, PROPS.avatarHeight, 0);
    group.add(face);
  }
  if (owner) {
    const name = new THREE.Mesh(new THREE.PlaneGeometry(PROPS.nameWidth, PROPS.nameWidth * TEAM_NAME.height / TEAM_NAME.width),
      basic({map: teamName(owner), depthWrite: false}));
    name.position.set(PROPS.avatarSide, PROPS.nameHeight, 0);
    group.add(name);
  }
  return group;
}
