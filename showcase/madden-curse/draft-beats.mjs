import { DRAFT_BEATS_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { SIXTEENTH, STEAL, TRADED, SLEEPER } from "./constants-draft-motion.mjs";
export { SIXTEENTH, STEAL, TRADED, SLEEPER };
import { BOARD } from './draft-board.mjs';

import { mix } from './timeline.mjs';
import { arc, impact, inOutCubic, jolt, outBack, outCubic, seg } from './draft-motion.mjs';

/* Beats 2-4. Each pose sets one featured card (and its props) for `seconds` into its beat and returns
   the card face's light and the camera shake. Times are motion seconds into the beat (constants.mjs
   FILM); a stamp lands on its beat's `stat`, the frame the same number appears in the headline. */
   // Golden's sleeper weeks: the eighth light is whole on the sheet's lastLight
// Every beat time below comes from timing.json; only distances, angles and the note length live here.
// Golden rises out of the board and holds there, bobbing, the way Hubbard does (David, 2026-11-04).
// Revision 8: his weeks light first, one per sixteenth note (`lightStep` .125 s at 120 BPM), then the WR7
// stamp lands on the bar's fourth beat with Blip riding it; all of it done by 1.9 s (rule 10).


// Revision 15 (David: a card must never land in another team's column): the card lifts out of Gibbs'
// column, Aura's badge pops up off the board's left edge, and the card arcs out and lands beside it on the
// fourth beat; its "WR · 2.12" tag fades under a cover, then the WR111 stamp slams where it was. Offsets
// are from the card's home: `badge` and `land` sit `aside` in front of the board, left of column 1's edge,
// and the camera frames `view`, between them. ~~It flew into Aura's column and took a slot there~~ (rev 6-14).


/* Where the trade happens, from the card's home: Aura's badge, the card's landing, the camera's aim. */
export const tradePlaces = home => Object.fromEntries(['badge', 'land', 'view']
  .map(key => [key, home.clone().set(home.x + TRADED[key][0], home.y + TRADED[key][1], home.z + TRADED[key][2])]));
// The eighth light is whole on the fourth beat (`stat`), each one a sixteenth note after the last.

const STAMP_START = 1.35, STAMP_HEIGHT = .35, STAMP_SETTLE = .12;   // the slam's overshoot and how long it settles

export function lights(group, weeks, seconds, start, step, on) {
  weeks.forEach((tier, index) => group.userData.set(index, tier, seg(seconds, start + index * step, start + index * step + on), seconds));
}

/* A stamp is nothing until its slam frame (`to`), the frame its number appears in the headline; it
   then lands at full strength, oversized, and settles flat with a hit. `from` is when the card braces. */
export function stampDrop(mesh, seconds, [, to], resting) {
  const settle = outCubic(seg(seconds, to, to + STAMP_SETTLE));
  mesh.visible = seconds >= to;
  mesh.scale.setScalar(mix(STAMP_START, 1, settle));
  mesh.position.z = resting + STAMP_HEIGHT * (1 - settle) * TUNING.stampLiftRatio;
  mesh.material.opacity = seconds >= to ? 1 : 0;
  return impact(seconds, to);
}

export function steal(seconds, item, blip) {
  const {mesh, home, props} = item;
  const rise = outBack(seg(seconds, ...STEAL.rise));
  const hit = stampDrop(props.stamp, seconds, STEAL.stamp, props.stampZ);
  mesh.position.set(home.x, home.y + STEAL.riseHeight * rise + STEAL.bob * Math.sin(seconds * TUNING.stealBobFrequency) * rise,
    home.z + STEAL.riseDepth * rise - TUNING.stealHitDepth * hit);
  mesh.rotation.set(TUNING.stealPitch * rise, 0, jolt(seconds, STEAL.stamp[1]) * TUNING.stealHitRoll);
  lights(props.lights, item.pick.weeks, seconds, STEAL.lights, STEAL.lightStep, STEAL.lightOn);
  // Blip leaps onto the stamp, rides it down, then hops aside to watch the weeks light up.
  const into = outCubic(seg(seconds, ...STEAL.blipIn)), away = outCubic(seg(seconds, ...STEAL.blipOut));
  blip.visible = seconds >= STEAL.blipIn[0];
  const ride = seconds < STEAL.stamp[0] ? 0 : outCubic(seg(seconds, ...STEAL.stamp));
  blip.position.set(mesh.position.x + mix(mix(TUNING.blipApproachX, TUNING.blipAtCardX, into), TUNING.blipDepartX, away),
    mix(mesh.position.y + TUNING.blipApproachY + TUNING.blipJumpHeight * arc(into) - TUNING.blipRideDrop * ride, home.y - BOARD.pitchY / 2, away) + TUNING.blipExitHop * arc(away),
    mix(mesh.position.z + TUNING.blipApproachZ, BOARD.depth + TUNING.blipExitZ, away));
  // He lands from the leap with a squash, as on the stamp.
  blip.squash = 1 - TUNING.blipHitSquash * hit - TUNING.blipExitSquash * impact(seconds, STEAL.blipOut[1]);
  blip.look = away > TUNING.blipLookThreshold ? TUNING.blipExitLook : 0;
  return {light: 1, shake: hit * STEAL.shake};
}

export function traded(seconds, item, places) {
  const {mesh, home, props} = item, landing = places.land;
  const badge = outBack(seg(seconds, ...TRADED.badgeIn)), tag = seg(seconds, ...TRADED.tagFade);
  props.badge.visible = badge > 0; props.badge.scale.setScalar(Math.max(TUNING.badgeScaleFloor, badge));
  props.cover.visible = tag > 0; props.cover.material.opacity = tag;
  const lift = outCubic(seg(seconds, ...TRADED.lift)), travel = inOutCubic(seg(seconds, ...TRADED.travel));
  const thud = impact(seconds, TRADED.travel[1]);
  mesh.position.set(mix(home.x, landing.x, travel), mix(home.y, landing.y, travel),
    mix(home.z + TRADED.liftDepth * lift, landing.z, travel) + TRADED.arcDepth * arc(travel));
  mesh.rotation.set(TUNING.tradedPitch * arc(travel), TUNING.tradedYaw * arc(travel), -TRADED.spin * arc(travel));
  mesh.scale.set(1 + TUNING.tradedThudStretch * thud, 1 - TRADED.squash * thud, 1);
  const hit = stampDrop(props.stamp, seconds, TRADED.stamp, props.stampZ);
  return {light: mix(1, TRADED.dimmed, seg(seconds, ...TRADED.dim)), shake: (thud + hit * TUNING.tradedHitShake) * TRADED.shake};
}

export function sleeper(seconds, item) {
  const {mesh, home, props} = item;
  const rise = outBack(seg(seconds, ...SLEEPER.rise));
  mesh.position.set(home.x, home.y + SLEEPER.riseHeight * rise + TUNING.sleeperBobHeight * Math.sin(seconds * TUNING.sleeperBobFrequency) * rise, home.z + SLEEPER.riseDepth * rise);
  mesh.rotation.set(TUNING.sleeperPitch * rise, 0, 0);
  lights(props.lights, item.pick.weeks, seconds, SLEEPER.lights, SLEEPER.lightStep, SLEEPER.lightOn);
  return {light: 1, shake: 0};
}
