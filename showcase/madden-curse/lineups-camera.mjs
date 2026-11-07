import { LINEUPS_CAMERA_DETAIL as TUNING } from './constants-lineups.mjs';
import { CAMERA, FRAMES } from "./constants-lineups.mjs";
export { CAMERA };
import * as THREE from 'three';
import { OPENING, TRANSITION } from './constants.mjs';
import { expoInOut, inOutCubic, seg } from "./draft-motion.mjs";
import { CLOCK } from './lineups-clock.mjs';

/* Chapter 4's camera (docs/madden-film-chapter4.md, beat tables and composition table): pure, like draft-camera.mjs
   `shot`. Each framing is the point it looks at and the height of the frame there (`h`, world units at the subject's
   plane); the camera stands square on to the desk and looks down a little onto its top, so the yaw and roll are zero
   and every face stays upright and square (rule 19). One move per shot, eased; the holds drift 3% (never still). */

/* Framings [x, y, h], measured from the stills (2026-11-05, ch4 corrective). Every frame keeps its station's words
   whole between the title band (top 20% desktop, 16% phone) and the bottom margin (4% desktop; 12.5% phone, above
   the review controls with rule 28's 4% gap). Desktop 36 degree lens, phone 44 (constants.mjs OPENING).
   Desktop: the shield is 47% of the frame in the right half, the nameplate and DEF on the desk face below; the ledge
   pair at left with the socket at right; Lamarley's medium holds START low left, the rack high right and the
   nameplate whole. Phone: the shield is 47% and centred over DEF and the nameplate; the ledge pair whole at 32% (the
   ensemble case, rule 51); START's card is 41% over its nameplate (down), and the crane up puts the rack card at 41%
   under the title with START's placard, week and name band at the bottom edge. */

const mixFrame = (from, to, amount) => from.map((value, index) => value + (to[index] - value) * amount);
const scaled = ([x, y, h], share) => [x, y, h * share];
const held = (seconds, from, to) => Math.sin(Math.PI / 2 * seg(seconds, from, to));   // eases in, ends still moving

/* Gibbs: the whip in, one slow push through three landings, the track left to the ledge, a held drift. */
function defense(seconds, frames, push) {
  const pushFrom = TRANSITION.window / 2;
  if (seconds < pushFrom) {
    const whip = expoInOut(seg(seconds, -pushFrom, pushFrom));
    return mixFrame([frames.socket[0] + CAMERA.whipFrom, frames.socket[1], frames.socket[2]], frames.socket, whip);
  }
  return scaled(frames.socket, 1 - push * inOutCubic(seg(seconds, pushFrom, CLOCK.second)));
}

/* Lamarley, on the second beat's clock: the medium, a crane up to the rack, down with the swap, up for 18.40, then a
   held drift up and back toward Chapter 5's riser behind the rack. */
function tightends(seconds, frames) {
  const [[upFrom, upTo], [againFrom, againTo]] = CLOCK.cranes.map(([from, to]) => [from - CLOCK.second, to - CLOCK.second]);
  const [downFrom, downTo] = CLOCK.switch.map(value => value - CLOCK.second);
  const end = CLOCK.end - CLOCK.second;
  const height = inOutCubic(seg(seconds, upFrom, upTo)) - inOutCubic(seg(seconds, downFrom, downTo)) + inOutCubic(seg(seconds, againFrom, againTo));
  // Each hold pushes in 3%, and the next crane eases it back out, so the drift never piles up across the beat.
  const pushes = [[0, upFrom], [upTo, downFrom], [downTo, againFrom]].map(([from, to], index) =>
    held(seconds, from, to) * (1 - inOutCubic(seg(seconds, to, [upTo, downTo, againTo][index]))));
  const drift = 1 - CAMERA.drift * Math.max(...pushes), last = held(seconds, againTo, end);
  const [x, y, h] = mixFrame(frames.down, frames.up, height);
  return [x, y + CAMERA.drift * h * last, h * drift * (1 + CAMERA.drift * last)];
}

/* Reduced motion (storyboard): each shot's settled framing, cut on its bar, no whip, crane or drift. draft-camera.mjs
   hands a reduced beat its last second, so the set (lineups-set.mjs update, which runs before the camera frames)
   tells the camera the film's own chapter second each frame; null while motion plays. The settled framing is the
   motion shot's own frame at the end of the hold the clock is in, or of the next hold during a move, so a reduced
   still matches the motion still beside it (2026-11-05: ~~the move's first settled second~~, which at 77.5 framed the
   rack without the pull-back that keeps START's stamp in a phone's frame). */
export const REDUCED = {clock: null};
const HOLD_ENDS = Object.freeze({
  'lineup-defense': () => [CLOCK.track[0], CLOCK.second - TRANSITION.window / 2],
  'lineup-tightends': () => [...CLOCK.cranes.map(([from]) => from), CLOCK.switch[0], CLOCK.end - TRANSITION.window / 2]
    .map(value => value - CLOCK.second).sort((first, second) => first - second),
});
function settled(clock) {
  const id = clock < CLOCK.second ? 'lineup-defense' : 'lineup-tightends', local = id === 'lineup-defense' ? clock : clock - CLOCK.second;
  const ends = HOLD_ENDS[id]();
  return [id, ends.find(end => end >= local) ?? ends.at(-1)];
}

/* The camera for beat `id`, `seconds` into it: {position, target}. */
export function shot(id, seconds, ctx) {
  const device = ctx.mobile ? 'phone' : 'desk', frames = FRAMES[device];
  if (REDUCED.clock !== null) [id, seconds] = settled(REDUCED.clock);
  const [x, y, h] = id === 'lineup-defense' ? defense(seconds, frames, CAMERA.push[device]) : tightends(seconds, frames);
  const fov = (ctx.mobile ? OPENING.phoneFov : OPENING.cameraFov) * Math.PI / TUNING.halfTurnDegrees;
  const distance = h / 2 / Math.tan(fov / 2);
  return {target: new THREE.Vector3(x, y, CAMERA.line), position: new THREE.Vector3(x, y + distance * CAMERA.pitch, CAMERA.line + distance)};
}

/* How far each frame's content slides up (draft-camera.mjs frame): none, the framings above are already placed. */
export const LIFT = Object.freeze({desk: {'lineup-defense': 0, 'lineup-tightends': 0}, phone: {'lineup-defense': 0, 'lineup-tightends': 0}});
