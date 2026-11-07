import { DRAFT_ESTABLISH_DETAIL as TUNING } from './constants-draft-motion.mjs';
import * as THREE from 'three';
import { BOARD, CARD_HEIGHT, boardTop, columnX } from './draft-board.mjs';
import { inOutCubic, seg } from './draft-motion.mjs';
import { mix } from './timeline.mjs';
import { beatTiming, span } from './timing.mjs';

const PASS = beatTiming('board').camera;   // the dolly's length and ramps, from the timing sheet
// The most a board point may cross the frame in the pass, frame widths a second. Ch17 (the coordinator, for David):
// a low skim needs a faster cap than a high pass, and David's favourite pass (rev 13) ran ~0.9 and was fine because
// its path was straight; so 1.0 with the path held straight, level and eased. ~~.35, rev 16b: rev 15's .25 made
// the pass calm; .92 made him dizzy~~ (rev 16b, measured on the high pass).
const SKIM_CROSS = 1;
// Ch17 (David: "too far out ... like you're flying against the plane"): the camera skims the board's face, a drone
// over the table; a phone flies higher so more rounds show in its narrow frame (coordinator, ch17).
// ~~5.8 above the table on a desktop, 12.5 on a phone~~ (rev 16b); ~~1.5 cards on a phone~~ (ch17 first pass).
const ALTITUDE = {desk: 1.5, phone: 3};   // card heights above the card faces
// Ch17 (coordinator): the camera looks diagonally across the columns, not down one, so the cards pass at an angle
// and the rails and card edges show their depth. It travels the way it looks: one straight diagonal.
// Negative: up the board and to the left, so the pass ends near Golden's corner and the travel to the steal is short
// (ch17, David). ~~+27, ending on COOKed's column~~ (ch17 third pass).
const YAW = -27 * Math.PI / 180;
// How far the look point travels up the board, board units, measured under SKIM_CROSS by tests/test_madden_rev8.py
// (ch17): a desktop from round 7 to the team row; a phone as far as fits.
const REACH = {desk: 5.8, phone: 4.6};

/* The establishing shot (David, 2026-11-03: the board read too small to be a draft board). The board lies
   flat like a draft table and the camera skims it to the team avatars while the board stands up into the wall.
   Seconds are into the board beat. Every card is lit evenly throughout (draft.mjs LIGHT).
   Ch17: the rig rides the board. One straight dolly on a diagonal across it, from round 7 on the right to the team
   row near Gibbs' end, ALTITUDE above its face, YAW off its axis, a fixed 27 degree look down, no roll; it eases
   in, then eases out all the way to the stand-up onset, never still, while the board's tilt carries it to the wall.
   The rails stand proud of the faces (draft-board.mjs strips), the depth cue at this height; no blur.
   ~~A straight run up one column with a 0.55 s hold on the team row~~ (ch17 second pass); ~~a high pass over all
   ten rounds whose pitch followed the board~~ (rev 16-17). */
export const ESTABLISH = Object.freeze({
  hold: beatTiming('board').hold,
  table: TUNING.tableHeight,                 // the flat board's height above the floor
  move: PASS.duration, ramp: PASS.ramp, // seconds moving, and its ease in and out (cosine ramps on the speed; timing.json)
  fly: [0, span('board', 'stand')[0]], stand: span('board', 'stand'),   // the pass, then the stand-up onto its onset
  altitude: ALTITUDE,
  height: {desk: CARD_HEIGHT * ALTITUDE.desk, phone: CARD_HEIGHT * ALTITUDE.phone},   // above the card faces
  pitch: TUNING.pitchDegrees * Math.PI / TUNING.halfTurnDegrees,            // looking down at the board, fixed for the whole pass
  yaw: YAW,                             // off the board's axis, fixed for the whole pass
  // The lens through the pass, a share of the scene's (OPENING.cameraFov): a desktop's card fills about half the
  // frame's height at the centre and more below it; a phone keeps its own lens, or one card is wider than the frame.
  zoom: {desk: TUNING.desktopZoom, phone: 1},
  reach: REACH,
  from: {desk: boardTop() - BOARD.teamName.below / 2 - REACH.desk, phone: boardTop() - BOARD.teamName.below / 2 - REACH.phone},
  cross: SKIM_CROSS,               // frame widths a second, the most any point may cross (test_madden_rev8.py measures every point)
  turn: TUNING.turnSpeed,                  // radians a second the camera may turn in the pass: the board's tilt carries it (ch17)
  x: columnX(1),              // where the pass ends looking across: Golden's column, beside Gibbs at the left end (ch17, David)
  aim: BOARD.teamName.below / 2,   // where the pass ends looking: between the avatar row and the names
});

const flat = (x, along, height) => new THREE.Vector3(x, ESTABLISH.table + height, -along);
const lead = kind => ESTABLISH.height[kind] / Math.tan(ESTABLISH.pitch);
const HEADING = {x: Math.sin(YAW), along: Math.cos(YAW)};   // the way the camera looks and travels over the board

/* Distance travelled at full speed's worth of seconds after `seconds`: a cosine ease in, a constant middle
   and a cosine ease out, so the speed never jumps. */
function travelled(seconds) {
  const {move, ramp: [into, out]} = ESTABLISH, ease = (time, span) => time / 2 - span / (2 * Math.PI) * Math.sin(Math.PI * time / span);
  const time = Math.min(move, Math.max(0, seconds)), left = move - time, full = move - (into + out) / 2;
  if (time < into) return ease(time, into);
  if (left < out) return full - ease(left, out);
  return into / 2 + time - into;
}

/* How far the camera has handed over from the pass to the wall shot, 0 to 1 over the stand-up. */
export const standing = seconds => inOutCubic(seg(seconds, ...ESTABLISH.stand));

/* How far the board has tilted up, 0 flat to 1 the wall: one cosine ease from the pass's first frame to the
   stand-up onset, so it is rising all through the pass (David rev 17; ~~flat until the stand-up~~, rev 16b). */
export const tilt = seconds => (1 - Math.cos(Math.PI * seg(seconds, 0, ESTABLISH.stand[1]))) / 2;

/* The lens through the board beat, a share of the scene's: narrow for the pass, widening as the board stands. */
export const passZoom = (seconds, mobile) => mix(ESTABLISH.zoom[mobile ? 'phone' : 'desk'], 1, standing(seconds));

/* The board's pose, tilted `up` of the way to the wall: it pivots on its foot. */
const boardMatrix = up => new THREE.Matrix4().makeTranslation(0, ESTABLISH.table * (1 - up), 0)
  .multiply(new THREE.Matrix4().makeRotationX(-Math.PI / 2 * (1 - up)));
const FLAT = boardMatrix(0), UNFLAT = FLAT.clone().invert();

/* A point given as it sits over the flat board, carried with the board as it tilts at `seconds`; and back. */
export const riding = (point, seconds) => point.clone().applyMatrix4(UNFLAT).applyMatrix4(boardMatrix(tilt(seconds)));
export const flatten = (point, seconds) => point.clone().applyMatrix4(boardMatrix(tilt(seconds)).invert()).applyMatrix4(FLAT);

/* Lay the board's group at its tilt for `seconds` (Infinity: the wall). */
export function poseTable(group, seconds) {
  const up = tilt(seconds);
  group.rotation.x = -Math.PI / 2 * (1 - up);
  group.position.y = ESTABLISH.table * (1 - up);
}

/* Where on the flat board the pass looks at `seconds`, {x, along}: from `from` up to the avatar row's aim, on a
   diagonal ending on Golden's column. */
export function passLook(seconds, mobile) {
  const kind = mobile ? 'phone' : 'desk', end = boardTop() - ESTABLISH.aim, rise = end - ESTABLISH.from[kind];
  const left = rise * (1 - travelled(seconds) / travelled(ESTABLISH.move));
  return {x: ESTABLISH.x - left * HEADING.x / HEADING.along, along: end - left};
}

/* How far down the board the camera is at `seconds`: `lead` short of where it looks, along its heading. */
export const passAlong = (seconds, mobile) => passLook(seconds, mobile).along - lead(mobile ? 'phone' : 'desk') * HEADING.along;

/* The skim (ch17): the camera and what it looks at both ride the tilting board, so over the board the move is
   one straight dolly at one altitude, yaw and pitch, upright to the board (`up` is its normal); then it hands
   over to the wall shot. */
export function establishing(seconds, mobile, wall) {
  const kind = mobile ? 'phone' : 'desk', look = passLook(seconds, mobile), back = lead(kind);
  const height = ESTABLISH.height[kind] + BOARD.depth / 2;
  const at = flat(look.x - back * HEADING.x, look.along - back * HEADING.along, height);
  const position = riding(at, seconds), above = riding(at.clone().add(new THREE.Vector3(0, 1, 0)), seconds);
  const over = {position, target: riding(flat(look.x, look.along, BOARD.depth / 2), seconds), up: above.sub(position)};
  const amount = standing(seconds);
  return {position: over.position.clone().lerp(wall.position, amount), target: over.target.clone().lerp(wall.target, amount),
    up: over.up.lerp(new THREE.Vector3(0, 1, 0), amount).normalize()};
}
