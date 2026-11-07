import { LINEUPS_DESK_DETAIL as TUNING } from './constants-lineups.mjs';
import { DIM, KEY } from "./constants-lineups.mjs";
export { KEY };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { placard, stamp, teamName } from './draft-textures.mjs';
import { CARD, DESK, SHELF, SHIELD, places } from './lineups-layout.mjs';
import { printed } from './lineups-faces.mjs';
import { LINEUPS_COPY } from './lineups-copy.mjs';

/* Chapter 4's fixed set (docs/madden-film-chapter4.md, "Set and props"): one long slab with two stations, a polished
   silver lip over the broadcast-blue recess strip, Gibbs's socket and ledge, Lamarley's START socket and bench rack,
   the nameplates, the role signs, and the lights. ~~The chute and its flap~~ (2026-11-05, "Score slams, shield
   ejects"). `place(mobile)` stands every piece where lineups-layout.mjs says; `light(x)` keeps the key on the station
   the camera looks at, so every surface falls from lit to shadow across the frame (craft Part 2: no flat light). */

// Three-point light, Chapter 1's way (draft.mjs key, draft-board.mjs wall light): a soft spot key high front-left
// that falls off across the desk, a cool rim from behind that edges the plates, and a low fill.

const metal = (color, metalness = TUNING.defaultMetalness, roughness = TUNING.defaultRoughness) => new THREE.MeshStandardMaterial({color, metalness, roughness});
const glow = color => new THREE.MeshBasicMaterial({color, toneMapped: false});
const box = (width, height, depth, material) => new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);

/* A socket's mouth: a dark slot and a rim band that flares on each landing (its material is returned). */
function socket(width, color) {
  const group = new THREE.Group(), rim = glow(color), dark = glow(PALETTE.unlit);
  const slot = box(width, TUNING.slotHeight, DIM.slot.depth, dark); slot.position.y = TUNING.slotY;
  const bands = [[width + DIM.slot.rim * 2, DIM.slot.rim, 0, DIM.slot.depth / 2], [width + DIM.slot.rim * 2, DIM.slot.rim, 0, -DIM.slot.depth / 2],
    [DIM.slot.rim, DIM.slot.depth, width / 2, 0], [DIM.slot.rim, DIM.slot.depth, -width / 2, 0]].map(([w, d, x, z]) => {
    const band = box(w, TUNING.socketBandHeight, d, rim); band.position.set(x, TUNING.socketBandY, z); return band;
  });
  group.add(slot, ...bands);
  return {group, rim, base: color};
}

function lights(group) {
  const key = new THREE.SpotLight(PALETTE.white, KEY.intensity, 0, KEY.angle, KEY.penumbra, KEY.decay);
  const rim = new THREE.DirectionalLight(PALETTE.paper, KEY.rim), fill = new THREE.DirectionalLight(PALETTE.silver, KEY.fill);
  rim.position.set(...KEY.rimFrom); fill.position.set(...KEY.fillFrom);
  [rim, fill].forEach(light => light.target.position.set(0, DESK.height, DESK.line));
  group.add(key, key.target, rim, rim.target, fill, fill.target);
  return x => {
    key.position.set(x + KEY.offset[0], KEY.offset[1], KEY.offset[2]); key.target.position.set(x + KEY.aim[0], KEY.aim[1], KEY.aim[2]);
    rim.position.x = x + KEY.rimFrom[0]; rim.target.position.x = x;
  };
}

export function makeDesk(cast, names) {
  const group = new THREE.Group(), labels = [];
  const label = mesh => { labels.push(mesh); return mesh; };
  const top = metal(PALETTE.slab, TUNING.topMetalness, TUNING.topRoughness), face = metal(PALETTE.slabEdge, TUNING.faceMetalness, TUNING.faceRoughness);
  const slab = new THREE.Mesh(new THREE.BoxGeometry(DESK.width, DESK.height, DESK.front - DESK.back), [face, face, top, face, face, face]);
  slab.position.set(0, DESK.height / 2, (DESK.front + DESK.back) / 2);
  const lip = box(DESK.width, DIM.lip.height, DIM.lip.depth, metal(PALETTE.silver, TUNING.lipMetalness, TUNING.lipRoughness));
  lip.position.set(0, DESK.height - DIM.lip.height / 2, DESK.front - DIM.lip.depth / 2 + TUNING.lipZ);
  const strip = glow(PALETTE.broadcast);
  const recess = box(DESK.width, DESK.strip, TUNING.stripDepth, strip); recess.position.set(0, DESK.height - DIM.lip.height - DESK.strip / 2, DESK.front + TUNING.stripZ);
  group.add(slab, lip, recess);
  const gibbs = socket(SHIELD.width + TUNING.defenseSocketPadding, PALETTE.DEF), start = socket(CARD.width + TUNING.starterSocketPadding, PALETTE.TE);
  gibbs.group.visible = false;
  const plinth = box(DIM.plinth.width, TUNING.plinthHeight, DIM.plinth.depth, metal(PALETTE.slabEdge, TUNING.plinthMetalness, TUNING.plinthRoughness));
  const ledgeLight = glow(PALETTE.broadcast), under = box(DIM.plinth.width, TUNING.ledgeHeight, TUNING.ledgeDepth, ledgeLight);
  group.add(gibbs.group, start.group, plinth, under);
  // The bench rack: a shelf under the rack's card on two silver posts, and its light along the shelf's front.
  const rack = new THREE.Group(), shelf = box(CARD.width + TUNING.shelfPadding, SHELF.height, DIM.shelf.depth, metal(PALETTE.slabEdge, TUNING.shelfMetalness, TUNING.shelfRoughness));
  const rackLight = glow(PALETTE.TE), rackStrip = box(CARD.width + TUNING.shelfPadding, TUNING.rackStripHeight, TUNING.rackStripDepth, rackLight);
  const posts = [-1, 1].map(side => { const post = box(DIM.shelf.post, 1, DIM.shelf.post, metal(PALETTE.silver, TUNING.postMetalness, TUNING.postRoughness)); post.userData.side = side; return post; });
  rack.add(shelf, rackStrip, ...posts);
  group.add(rack);
  // Words: the role signs, DEF, the nameplates (rule 23: the manager's badge and name together). Each is a unit
  // plane scaled per layout, so the readout (lineups-readout.mjs) measures what the frame shows.
  const sign = (text, color) => label(printed(placard(text, css(color)), 1, 1, text, 'sign'));
  const startSign = sign(LINEUPS_COPY.starter, PALETTE.white), benchSign = sign(LINEUPS_COPY.bench, PALETTE.white);
  const defSign = sign(LINEUPS_COPY.socket, PALETTE.DEF);
  const ringMaterial = metal(PALETTE.silver, TUNING.badgeRingMetalness, TUNING.badgeRingRoughness);
  const plate = (text, key) => {
    const badge = new THREE.Mesh(new THREE.CircleGeometry(1, TUNING.badgeSegments), new THREE.MeshBasicMaterial({color: PALETTE.white, toneMapped: false}));
    const ring = new THREE.Mesh(new THREE.CircleGeometry(DIM.ring, TUNING.badgeSegments), ringMaterial); ring.position.z = TUNING.badgeRingZ; badge.add(ring);
    return {name: label(printed(teamName(text), 1, 1, text.toUpperCase(), 'plate')), badge, key};
  };
  const plates = [plate(names.gibbs, 'gibbs'), plate(names.lamarley, 'lamarley')];
  // The week stamp beside START: W5 flips once to W8 (lineups-pose.mjs stamps.week); one face per week.
  const weeks = cast.tightends.map(entry => label(printed(stamp(entry.week, PALETTE.broadcast), 1, 1, entry.week, 'stamp')));
  group.add(startSign, benchSign, defSign, ...weeks, ...plates.flatMap(entry => [entry.name, entry.badge]));
  const aim = lights(group);

  function place(mobile) {
    const at = places(mobile), set = (mesh, [x, y, z], size) => { mesh.position.set(x, y, z); if (size) mesh.scale.set(size.width, size.height, 1); };
    gibbs.group.position.set(at.socket[0], DESK.height, at.socket[2]);
    start.group.position.set(at.start[0], DESK.height, at.start[2]);
    set(plinth, at.plinth); under.position.set(at.plinth[0], DESK.height + TUNING.ledgeY, at.plinth[2] + DIM.plinth.depth / 2 + TUNING.ledgeZ);
    rack.position.set(at.rack[0], at.shelf, at.rack[2] - TUNING.rackZ);
    rackStrip.position.set(0, TUNING.rackStripY, DIM.shelf.depth / 2 + TUNING.rackStripZ);
    const drop = at.shelf - DESK.height;
    posts.forEach(post => { post.scale.y = drop; post.position.set(post.userData.side * CARD.width / 2, -drop / 2, -DIM.shelf.depth / TUNING.postDepthDivisor); });
    set(startSign, at.startSign, at.sign); set(benchSign, at.benchSign, at.sign); set(defSign, at.defSign, at.sign);
    weeks.forEach(mesh => set(mesh, at.week, at.weekSize));
    defSign.visible = false; plinth.visible = false; under.visible = false;
    plates.forEach(({name, badge, key}) => {
      name.visible = key !== 'gibbs'; badge.visible = key !== 'gibbs';
      const [badgeX, nameX] = at.plates[key], y = key === 'lamarley' ? at.plates.lamarleyY : at.plates.y;
      badge.position.set(badgeX, y, at.front); badge.scale.setScalar(at.plates.badge);
      set(name, [nameX, y, at.front], at.plates);
    });
  }
  return {group, labels, place, aim, strip, ledgeLight, rackLight, rims: {gibbs: gibbs.rim, start: start.rim}, weeks,
    badges: plates.map(entry => entry.badge)};
}
