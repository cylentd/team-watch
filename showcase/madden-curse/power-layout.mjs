import { RISER, PLATE_FACE, TROPHY, POSE_FORWARD } from "./constants-power.mjs";
export { RISER, PLATE_FACE, TROPHY, POSE_FORWARD };
/* Chapter 5's riser (docs/madden-film-chapter5.md, "Cinematic revision", David 2026-11-05): where every slot, plate,
   stamp, the summit, the trophy and Blip stand, on a desktop and a phone. Pure numbers, so the camera
   (power-camera.mjs) and the tests frame the same places the meshes stand (power-riser.mjs). Units are the room's:
   Chapter 1's card is 0.5 wide. */

export const TIER = Object.freeze({upper: 6, places: 12});   // power-data.mjs: places 1-6 are the back tier

// A plate's face, world units from the plate's centre (power-riser.mjs): the badge at 47% of the width (rule 23), the
// name and the record big, the actual W-L small under them. Each plane's aspect matches its canvas (power-textures.mjs:
// 4:1 lines, an 8:1 small line), so no type stretches.

// The trophy on the summit: its height in world units, how far above it starts its fall (above frame), the turn it
// unwinds as it lowers, and the radius the camera frames. `ball`: the ball's centre in the model's own units
// (scene.mjs FILM_INTRO.glint: the opening's glint sits 3.55 above the stage), `model` the model's height there.

// The shuffle's arc: a plate that gains places flies `ahead` toward the camera, one that loses them `behind`, each
// more by `per` place moved, and every mover lifts `lift`; so two flights never share a depth (rule: no crossing).
export const ARC = Object.freeze({launch: .2, return: .8, clear: .2, lane: .1});
// power-pose.mjs POSE.forward: the feature plate slides this far out of its slot (kept here so layout imports no pose).

const add = (origin, x, y, z) => [origin[0] + x, origin[1] + y, origin[2] + z];
const device = mobile => (mobile ? 'phone' : 'desk');

/* The slot for place `place` (1..12): {place, tier, x, y (the lip's top), z (the plate's centre plane), step}. */
export function slot(place, mobile) {
  const back = place <= TIER.upper, index = (place - 1) % TIER.upper;
  if (!mobile) {
    const tier = RISER.desk[back ? 'back' : 'front'], x = (index - (TIER.upper - 1) / 2) * RISER.desk.pitch;
    const [wx, wy, wz] = add(RISER.position, x, tier.top + RISER.lip.height, tier.z + RISER.desk.depth / 2 - RISER.lip.depth / 2);
    return {place, tier: back ? 'back' : 'front', x: wx, y: wy, z: wz, step: back ? 1 : 0};
  }
  const phone = RISER.phone, row = Math.floor(index / phone.columns), column = index % phone.columns, rows = TIER.upper / phone.columns;
  const step = (back ? 2 * rows - 1 : rows - 1) - row;   // 0 is the front, lowest step; places 1-3 stand on the top one
  const [wx, wy, wz] = add(RISER.position, (column - (phone.columns - 1) / 2) * phone.pitch, stepTop(step) + RISER.lip.height, stepZ(step));
  return {place, tier: back ? 'back' : 'front', x: wx, y: wy, z: wz, step};
}
const ROWS = TIER.upper / RISER.phone.columns;
const stepTop = step => RISER.phone.base + step * RISER.phone.rise + (step >= ROWS ? RISER.phone.gap : 0);
const stepZ = step => (2 * ROWS - 1 - step) * RISER.phone.step + (step >= ROWS ? 0 : RISER.phone.gap) + RISER.phone.step / 2 - RISER.lip.depth / 2;
export const slots = mobile => Array.from({length: TIER.places}, (_, index) => slot(index + 1, mobile));

/* A plate's centre for its pose (power-pose.mjs plates[]): on its standings slot until the shuffle, then flying an
   arc to its power slot; seated on its lip, lifted by its piston, dropping from above, slid forward out of the slot. */
export function plateCentre(place, plate, mobile) {
  const amount = plate.shuffle ?? 1, from = slot(plate.standing ?? place, mobile), to = slot(place, mobile);
  const moving = (plate.standing ?? place) !== place;
  const travel = Math.min(1, Math.max(0, (amount - ARC.launch) / (ARC.return - ARC.launch)));
  const lane = Math.max(...slots(mobile).map(entry => entry.z)) + ARC.clear + place * ARC.lane;
  const depth = amount < ARC.launch ? from.z + (lane - from.z) * amount / ARC.launch
    : amount > ARC.return ? lane + (to.z - lane) * (amount - ARC.return) / (1 - ARC.return) : lane;
  const mix = (a, b) => a + (b - a) * travel, {height} = RISER.plate;
  return [mix(from.x, to.x), mix(from.y, to.y) + RISER.rest + plate.lift - plate.sink + plate.drop + height / 2,
    (moving ? depth : to.z) + plate.forward];
}

const box = ([x, y, z], width, height, depth) =>
  [-1, 1].flatMap(sx => [-1, 1].flatMap(sy => [-1, 1].map(sz => [x + sx * width / 2, y + sy * height / 2, z + sz * depth / 2])));
const onPlate = (place, plate, mobile, x, y, z = 0) => { const [cx, cy, cz] = plateCentre(place, plate, mobile);
  return [cx + x, cy + y * (plate.squash ?? 1), cz + RISER.plate.depth / 2 + z]; };

/* The eight corners of a plate, of its name and of the feature's two stamps, for framing and the camera tests. */
export const plateCorners = (place, plate, mobile) => box(plateCentre(place, plate, mobile), RISER.plate.width, RISER.plate.height, RISER.plate.depth);
export const nameCorners = (place, plate, mobile) =>
  box(onPlate(place, plate, mobile, 0, PLATE_FACE.name.y), PLATE_FACE.name.width, PLATE_FACE.name.height, 0);
export const stampCentre = (place, plate, mobile, name) => { const {stamps} = PLATE_FACE, at = stamps[name];
  return onPlate(place, plate, mobile, at.x, at.y, stamps.ahead); };
export const stampCorners = (place, plate, mobile) => ['power', 'actual'].flatMap(name =>
  box(stampCentre(place, plate, mobile, name), PLATE_FACE.stamps.width, PLATE_FACE.stamps.height, 0));

/* The summit's block {x, top, z, width, depth}: behind the top row, its top a little above the row's plates. */
export function summit(mobile) {
  const own = RISER.summit[device(mobile)], top = slot(1, mobile);
  return {x: own.x, top: top.y + RISER.rest + RISER.plate.height + RISER.summit.clear, width: own.width, depth: own.depth,
    z: top.z - RISER.lip.depth / 2 - RISER.summit.gap - own.depth / 2};
}
/* Where the trophy's foot lands and Blip perches beside it, world units. */
export const trophySpot = mobile => { const top = summit(mobile); return [0, top.top, top.z]; };
export const perch = mobile => { const top = summit(mobile); return [RISER.summit[device(mobile)].perch, top.top, top.z]; };
export const trophyCorners = mobile => { const [x, y, z] = trophySpot(mobile);
  return box([x, y + TROPHY.height / 2, z], 2 * TROPHY.radius, TROPHY.height, 2 * TROPHY.radius); };

/* Blip's path up the riser: his start on the floor, the two stair tops, his perch. The stair stands at the riser's
   right end, beside the last column's lip. */
export function stairs(mobile) {
  const last = slot(TIER.upper, mobile), x = last.x + RISER.lip.width / 2 + RISER.stair.gap + RISER.stair.width / 2;
  const tops = RISER.stair.steps[device(mobile)].map(step => slots(mobile).find(entry => entry.step === step));
  const front = tops[0];
  return [[x, 0, front.z + RISER.stair.ahead], ...tops.map(entry => [x, entry.y, entry.z]), perch(mobile)];
}
