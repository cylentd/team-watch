import { POWER_RISER_DETAIL as TUNING } from './constants-power.mjs';
import { FACE } from "./constants-power.mjs";
export { FACE };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { teamName } from './draft-textures.mjs';
import { actualLine, badge, numeral, plateFace, record } from './power-textures.mjs';
import { PLATE_FACE, RISER, plateCentre, slot, slots, stairs, summit } from './power-layout.mjs';
import { POWER_COPY } from './power-copy.mjs';

/* Chapter 5's riser (docs/madden-film-chapter5.md, "Cinematic revision", props): a pedestal and a slot lip with its
   place numeral under each of the twelve places, a tier strip along each lip's front edge, a piston, the summit
   where the trophy lands and Blip's stair. Each plate is built like Chapter 1's cards (draft-board.mjs): a printed
   face on a metal-edged slab, its badge, name, record and actual W-L as faces of their own, so each pops on its own
   frame and the all-play record can pop in over the W-L on the shuffle's landing. The meshes only: power-set.mjs
   poses them from power-pose.mjs. */

const FRONT = 4;   // BoxGeometry's material slot for +z

const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, name) => values[name]);
const basic = options => new THREE.MeshBasicMaterial({toneMapped: false, ...options});
const lit = (color, metalness = TUNING.defaultMetalness, roughness = TUNING.defaultRoughness) => new THREE.MeshStandardMaterial({color, metalness, roughness});
const unit = new THREE.BoxGeometry(1, 1, 1);

function plateMeshes(team, image, place, face) {
  const root = new THREE.Group(), {width, height, depth} = RISER.plate, z = depth / 2 + PLATE_FACE.lift;
  // Chapter 1's card side: brushed metal that catches the rim light (draft-board.mjs `side`).
  const sides = Array.from({length: TUNING.boxFaceCount}, () => lit(PALETTE.slabEdge, TUNING.sideMetalness, TUNING.sideRoughness));
  sides[FRONT] = basic({map: face});
  const panel = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), sides);
  root.add(panel);
  const plane = (spec, map) => {
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(spec.width ?? spec.size, spec.height ?? spec.size), basic({map, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1}));
    mesh.position.set(0, spec.y, z); root.add(mesh); return mesh;
  };
  const faces = {badge: plane(PLATE_FACE.badge, badge(image)), name: plane(PLATE_FACE.name, teamName(team.name)),
    record: plane(PLATE_FACE.record, record(team.record)), allPlay: plane(PLATE_FACE.record, record(team.allPlay)),
    actual: plane(PLATE_FACE.actual, actualLine(fill(POWER_COPY.actual, {place: team.standing})))};
  const piston = new THREE.Mesh(new THREE.CylinderGeometry(RISER.piston, RISER.piston, 1, TUNING.pistonSegments), lit(PALETTE.silver));
  return {place, root, panel, faces, piston};
}

/* A dark block standing on the floor with a lit strip along its front top edge: a pedestal, the summit, a stair. */
function block(group) {
  const body = new THREE.Mesh(unit, lit(PALETTE.slab)), strip = new THREE.Mesh(unit, basic({color: PALETTE.broadcast}));
  group.add(body, strip);
  return {body, strip, stand([x, top, z], width, depth) {
    body.scale.set(width, Math.max(TUNING.scaleFloor, top), depth); body.position.set(x, top / 2, z);
    strip.scale.set(width, FACE.strip, FACE.strip); strip.position.set(x, top, z + depth / 2);
  }};
}

/* Build the riser for `order` (power-data.mjs powerValues order) with each team's decoded badge `images[id]`. */
export function makeRiser(order, images) {
  const group = new THREE.Group(), face = plateFace();
  const blocks = order.map((_, index) => {
    const pedestal = block(group), lip = new THREE.Mesh(unit, lit(PALETTE.slabEdge));
    const number = new THREE.Mesh(new THREE.PlaneGeometry(FACE.numeral, FACE.numeral), basic({map: numeral(index + 1), transparent: true}));
    group.add(lip, number);
    return {pedestal, lip, number};
  });
  const crown = block(group), steps = [block(group), block(group)];
  const plates = order.map((team, index) => {
    const plate = plateMeshes(team, images[team.id], index + 1, face);
    group.add(plate.root, plate.piston);
    return plate;
  });
  let placedFor = null;
  /* Stand every block for a desktop or a phone: the layouts differ (power-layout.mjs). */
  function place(mobile) {
    if (placedFor === mobile) return;
    placedFor = mobile;
    slots(mobile).forEach((at, index) => {
      const {pedestal, lip, number} = blocks[index], base = at.y - RISER.lip.height;
      pedestal.stand([at.x, base, at.z], RISER.lip.width, RISER.lip.depth);
      lip.scale.set(RISER.lip.width, RISER.lip.height, RISER.lip.depth);
      lip.position.set(at.x, at.y - RISER.lip.height / 2, at.z);
      number.position.set(at.x, at.y - RISER.lip.height / 2, at.z + RISER.lip.depth / 2 + PLATE_FACE.lift);
      pedestal.strip.position.y = at.y;   // the strip runs along the lip's top edge, not the pedestal's
    });
    const top = summit(mobile), path = stairs(mobile);
    crown.stand([top.x, top.top, top.z], top.width, top.depth);
    steps.forEach((stair, index) => stair.stand(path[index + 1], RISER.stair.width, RISER.stair.depth));
  }
  /* One plate's pose (power-pose.mjs plates[]), its light times the scene's `dim`; `covered` hides its actual line
     while the "4-4 actual" stamp lies over it (power-props.mjs). */
  function posePlate(plate, pose, mobile, dim, covered) {
    const at = slot(plate.place, mobile), centre = plateCentre(plate.place, pose, mobile), {height} = RISER.plate;
    plate.root.visible = pose.visible;
    plate.root.position.set(...centre);
    plate.root.scale.set(1, pose.squash, 1);
    const light = pose.light * dim, swapped = pose.swap > 0;
    plate.panel.material.forEach((material, index) => (index === FRONT ? material.color.setScalar(light) : material.color.set(PALETTE.slabEdge).multiplyScalar(light)));
    const sizes = {badge: pose.pops[0], name: pose.pops[1], record: swapped ? 0 : pose.pops[2],
      allPlay: swapped ? pose.swap : 0, actual: swapped && !covered ? pose.swap : 0};
    Object.entries(plate.faces).forEach(([name, mesh]) => {
      mesh.scale.setScalar(Math.max(TUNING.scaleFloor, sizes[name]));
      mesh.visible = pose.visible && sizes[name] > 0;
      mesh.material.color.setScalar(light);
    });
    // The piston runs from the lip's top to the plate's foot while the plate is seated or lifted in its own slot.
    const foot = centre[1] - height / 2 * pose.squash, reach = foot - at.y, home = (pose.shuffle ?? 1) >= 1 || pose.standing === plate.place;
    plate.piston.visible = pose.visible && pose.drop === 0 && home && reach > TUNING.visibleThreshold;
    plate.piston.scale.set(1, Math.max(TUNING.scaleFloor, reach), 1);
    plate.piston.position.set(at.x, at.y + reach / 2, at.z);
  }
  /* Pose the riser: the plates, the strips' light (with the close's wave, 0..1 across or null) and the dim. */
  function pose(state, mobile, feature) {
    place(mobile);
    const covered = state.stamps.actual > TUNING.coveredThreshold;
    state.plates.forEach((entry, index) => posePlate(plates[index], entry, mobile, state.dim, covered && entry.place === feature));
    const all = [...blocks.map(entry => entry.pedestal), crown, ...steps], columns = mobile ? RISER.phone.columns : TIER_ROW;
    all.forEach((entry, index) => {
      entry.body.material.color.set(PALETTE.slab).multiplyScalar(state.dim);
      const across = index < blocks.length ? index % columns / (columns - 1) : 1;
      const wave = state.wave === null ? 0 : Math.max(0, 1 - Math.abs(state.wave * TUNING.waveTravelScale - TUNING.waveLead - across) * TUNING.waveSharpness);
      entry.strip.material.color.set(PALETTE.broadcast).multiplyScalar(FACE.stripGlow * Math.min(TUNING.stripGlowCap, state.strips + wave) * state.dim);
      entry.strip.visible = state.strips > 0;
    });
    blocks.forEach(({lip, number}) => { lip.material.color.set(PALETTE.slabEdge).multiplyScalar(state.dim); number.material.color.setScalar(state.dim); });
  }
  return {group, plates, pose, dispose() {
    group.traverse(object => { object.geometry?.dispose(); [object.material].flat().forEach(material => { material?.map?.dispose(); material?.dispose(); }); });
  }};
}
const TIER_ROW = 6;   // the desktop's places per tier, left to right (power-layout.mjs TIER.upper)
