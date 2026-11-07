import { DRAFT_CURSE_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { CURSE, INJURY, FINALE } from "./constants-draft-motion.mjs";
export { CURSE, INJURY, FINALE };
import * as THREE from 'three';
import { TRAIL } from './constants.mjs';
import { at } from "./timing.mjs";
import { CARD_HEIGHT } from './draft-board.mjs';
import { PROPS } from './draft-props.mjs';
import { lights, stampDrop } from './draft-beats.mjs';
import { arc, impact, inOutCubic, outBack, outCubic, seg } from './draft-motion.mjs';

/* Beats 5-7: the curse's tour of the waiver floor, the injury, and the board's verdict. */
// The card leaves the board at TRAIL.leave, drops onto WARREN-TY's pad and catches fire there (`ignite`,
// revision 14 storyboard; ~~burning from the first frame~~, rev 8), and lands on each stop at
// TRAIL.landings; a stop's pad and words pop up `reveal` before the card first reaches it, so nothing on
// the floor is drawn before its moment (rule 17). From the wire's second visit it leaps off the frame's
// right edge at TRAIL.leap, `leapHeight` high, to COOKed's pad. Only that last landing shakes the camera:
// the wide shot holds still through the first four (David's storyboard).
// Blip turns `watchAngle` radians over `watch` to follow the leap (BLIP below for the rest of him).

/* Scared Blip (David rev 17; ~~at the frame's right edge, shaking his head~~, rev 15): he stands between the first
   two pads, `behind` the hop line so the card passes in front of him. He trembles `tremble` (about 1-2 px in the
   wide shot) at two unrelated `rates` a second, and on each hop past him leans back `angle` radians over `back` s,
   then recovers over `recover` s. `halfWidth` is his widest reach at draft.mjs LIGHT.blip (blip.mjs arms at .29). */
export const BLIP = Object.freeze({behind: .55, tremble: .004, rates: [47, 61], back: .2, recover: .25, angle: .35, halfWidth: .1});

/* Blip's spot on the floor: half way between the pads at `from` and `to`, BLIP.behind back from them. */
export const blipHome = (from, to) => new THREE.Vector3((from.x + to.x) / 2, 0, Math.min(from.z, to.z) - BLIP.behind);

/* How far back Blip leans at `seconds`: up over BLIP.back from each hop's start, then back to 0 over BLIP.recover. */
const recoil = (seconds, hops) => BLIP.angle * Math.max(0, ...hops.map(time =>
  seconds < time + BLIP.back ? outCubic(seg(seconds, time, time + BLIP.back)) : 1 - inOutCubic(seg(seconds, time + BLIP.back, time + BLIP.back + BLIP.recover))));
/* The injury (rule 28): the card comes forward whole, so the portrait and name read, takes its IR
   stamp on the bar's third beat, then is cut cleanly in half on its fourth; the halves part along the
   cut and are gone by 2 s. Motion seconds; ~~IR at 1.43 s, cut at 1.95 s, faded by 3.25 s~~ (rev 7). */

/* The verdict: the winning column lit and pulsing, everything else dimmed (rule 28). The avatar lands
   on the fourth beat; the five returns pop in on eighth notes after it and the class total lands on the
   next bar line (`total`, receipt-details.mjs). */

/* How far a stop's pad, avatar and words have popped up: 0 until shortly before the card first lands there. */
export const stationReveal = (seconds, landing) => { const t = seg(seconds, landing - CURSE.reveal[0], landing - CURSE.reveal[1]); return t > 0 ? outBack(t) : 0; };
const standing = CARD_HEIGHT / 2 + PROPS.padHeight;

/* Each landing squashes the card and settles it back in `frames` s (3 frames of the 30 fps export), `x` wider and
   `y` shorter at the peak; it stays on top of the disc. David rev 17 reversed the sink. ~~Rev 16: the card sank
   a quarter of its height into the WARREN-TY and wire discs, a ring rippling out~~. */
export const LANDING = Object.freeze({frames: 3 / 30, x: .1, y: .16});

const spot = station => new THREE.Vector3(station.x, standing, station.z);

/* How squashed the card is by the landing at `time`: up and back down within LANDING.frames. */
const squashAt = (seconds, time) => { const t = seg(seconds, time, time + LANDING.frames); return t > 0 && t < 1 ? Math.sin(Math.PI * t) : 0; };

export function curse(seconds, item, stations, steps, blip, tile) {
  const {mesh, home, props, front} = item;
  front.map = item.drained ?? item.normal;
  const count = steps.length, landings = CURSE.landings.slice(0, count);
  const at = index => stations[steps[index].station];
  const flight = (from, to, amount, height = CURSE.hopHeight) => {
    const point = from.clone().lerp(to, amount);
    point.y += height * arc(amount);
    return point;
  };
  let position, light = 1, tumble = 0;
  const last = landings.findLastIndex(time => seconds >= time);
  if (seconds < CURSE.leave) position = home.clone().setZ(home.z + TUNING.cardLiftDepth * seg(seconds, TUNING.cardLiftStart, CURSE.leave));
  else if (last < 0) {
    const amount = inOutCubic(seg(seconds, CURSE.leave, landings[0]));
    position = flight(home.clone().setZ(home.z + TUNING.cardLiftDepth), spot(at(0)), amount); tumble = arc(amount);
  } else {
    const leaping = last + 1 === count - 1;
    const departs = last === count - 1 ? Infinity : leaping ? CURSE.leap : landings[last + 1] - CURSE.move;
    if (seconds < departs) position = spot(at(last));
    else {
      const amount = inOutCubic(seg(seconds, departs, landings[last + 1]));
      position = flight(spot(at(last)), spot(at(last + 1)), amount, leaping ? CURSE.leapHeight : CURSE.hopHeight);
      tumble = arc(amount);
    }
  }
  const shake = impact(seconds, CURSE.lastLanding) * CURSE.shake;
  props.flame.update(seconds, seg(seconds, ...CURSE.ignite) * (CURSE.flameBase + CURSE.flameFlare * impact(seconds, CURSE.flip[1])));
  mesh.position.copy(position);
  mesh.rotation.set(0, 0, TUNING.tumbleRoll * tumble);
  const squash = Math.max(...landings.map(time => squashAt(seconds, time)));
  mesh.scale.set(1 + LANDING.x * squash, 1 - LANDING.y * squash, 1);
  stampDrop(tile, seconds, CURSE.flip, props.stampZ);
  // Scared Blip between the first two pads (BLIP above): he flinches back from each hop past him and turns
  // to watch the card leap off to COOKed.
  const hops = landings.slice(1, -1).map(time => time - CURSE.move);
  Object.assign(blip, {visible: seconds >= CURSE.firstLanding && seconds < TRAIL.pan[1], squash: 1, lean: 0, scared: true,
    recoil: recoil(seconds, hops), look: CURSE.watchAngle * inOutCubic(seg(seconds, ...CURSE.watch))});
  const [fast, slow] = BLIP.rates;
  blip.position.copy(blip.home).add(new THREE.Vector3(Math.sin(seconds * fast), Math.sin(seconds * slow), 0).multiplyScalar(BLIP.tremble));
  return {light, shake};
}

/* Show or hide the card's own faces; its children (the IR stamp, the lights) keep their own state. */
const faces = (mesh, shown) => [mesh.material].flat().forEach(material => { material.visible = shown; });

export function injury(seconds, item, pieces = []) {
  const {mesh, home, props} = item;
  const forward = inOutCubic(seg(seconds, ...INJURY.forward));
  mesh.position.set(home.x, home.y, home.z + INJURY.forwardDepth * forward);
  lights(props.lights, item.pick.weeks, seconds, INJURY.lights, INJURY.lightStep, INJURY.lightOn);
  mesh.visible = true;
  const cut = seconds >= INJURY.cut;
  faces(mesh, !cut);
  props.lights.visible = !cut;
  const part = outCubic(seg(seconds, INJURY.cut, INJURY.cut + INJURY.part)), fade = 1 - seg(seconds, ...INJURY.fade);
  pieces.forEach((piece, index) => {
    const side = index === 0 ? 1 : -1;   // the top half lifts and slides left, the bottom drops and slides right
    piece.visible = cut && fade > 0;
    piece.position.copy(mesh.position);
    piece.position.x -= side * INJURY.partSlide * part;
    piece.position.y += side * INJURY.partGap * part;
    piece.rotation.set(0, 0, side * INJURY.partTurn * part);
    piece.material.opacity = fade;
  });
  if (props.status) props.status.material.opacity = cut ? fade : seg(seconds, ...INJURY.status);
  return {light: 1, shake: 0};
}

export function finale(seconds, board, team) {
  const header = board.headers.get(team), rise = outBack(seg(seconds, ...FINALE.rise));
  header.disc.position.y = header.home + FINALE.riseHeight * rise;
  header.disc.scale.setScalar(1 + FINALE.riseScale * rise);
  const wave = Math.sin(seconds * FINALE.pulseSpeed);
  board.glow.material.opacity = FINALE.glowPeak * seg(seconds, ...FINALE.glow) * (FINALE.pulseBase + FINALE.pulseDepth * wave);
}

/* The winning column's cards breathe with its light. */
export const columnPulse = seconds => FINALE.cardBase + FINALE.cardDepth * Math.sin(seconds * FINALE.pulseSpeed);

export const homeward = seconds => inOutCubic(seg(seconds, ...FINALE.home));
