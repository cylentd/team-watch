import { DRAFT_CAMERA_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { RIG } from "./constants-draft-motion.mjs";
export { RIG };
import * as THREE from 'three';
import { OPENING, TRAIL, TRANSITION } from './constants.mjs';
import { boardCentre } from './draft-board.mjs';
import { expoInOut, inOutCubic, outCubic, seg } from './draft-motion.mjs';
import { TRAVEL, filmPlan, sameChapter } from './film.mjs';
import { ESTABLISH, establishing, passZoom, standing } from './draft-establish.mjs';

import { FLOOR } from './draft-floor.mjs';

import { BUILD, buildClock } from './draft-build.mjs';
import { MOBILE_FRAME, phoneOverview, mobileBuildAt } from './draft-mobile-framing.mjs';
import { ONSETS, filmTime } from './music-onsets.mjs';
import { activeSets, setOfBeat } from './film-sets.mjs';

/* One shot per beat, a whip pan between them. Distances are chosen so the hero card fills about half
   the frame's height on a desktop and half its width on a 390px phone, the board fits whole in the
   wide shots, and on a phone the target sits higher so the action clears the headline above it. */
// The close shots on a phone come in to 3.0: the card is then about 70% of a 390px frame's width,
// so its name and stamp read, and its week lights still clear the controls (David, 2026-11-03).

// A beat's motion clock runs `pace` times slower than the film's (constants.mjs FILM).
const DURATION = Object.fromEntries(filmPlan().beats.map(beat => [beat.id, beat.duration / beat.pace]));
const PACE = Object.fromEntries(filmPlan().beats.map(beat => [beat.id, beat.pace]));
// A later chapter's beat is a flat card with no board shot (film.mjs sameChapter): the camera holds the finale's end.
const LATER = new Set(filmPlan().beats.filter(beat => (beat.chapter ?? 1) > 1).map(beat => beat.id));
const LATER_BEATS = filmPlan().beats.filter(beat => LATER.has(beat.id));
const LATER_CLOCK = Object.fromEntries(LATER_BEATS.map(beat => [beat.id, beat.start - LATER_BEATS[0].start]));
const LATER_SPAN = LATER_BEATS.reduce((sum, beat) => sum + beat.duration, 0) || 1;
const UP = new THREE.Vector3(0, 1, 0);

function close(card, seconds, id, mobile) {
  const [from, to] = (mobile && RIG.closePhone[id]) || RIG.close[mobile ? 'phone' : 'desk'];
  const distance = from + (to - from) * Math.min(1, seconds / DURATION[id]);
  const lift = mobile ? RIG.phoneLift : 0;
  return {position: card.home.clone().add(new THREE.Vector3(TUNING.cardEyeX, TUNING.cardEyeY + lift, distance)),
    target: card.home.clone().add(new THREE.Vector3(0, lift - TUNING.cardTargetDrop, TUNING.cardTargetZ))};
}

function wide(mobile, extra = 0) {
  const centre = boardCentre();
  return {position: new THREE.Vector3(0, centre + TUNING.wideEyeY + extra * TUNING.wideLiftRatio, RIG.wide[mobile ? 'phone' : 'desk'] + extra),
    target: new THREE.Vector3(0, centre, 0)};
}

/* The finale: on a phone the winning column, whole; on a desktop the whole board in the right half. */
function winner(ctx) {
  const centre = boardCentre(), x = ctx.mobile ? ctx.finaleX : 0;
  return {position: new THREE.Vector3(x, centre + TUNING.finaleEyeY, RIG.finale[ctx.mobile ? 'phone' : 'desk']),
    target: new THREE.Vector3(x, centre, 0)};
}

const mix = (from, to, amount) => from + (to - from) * amount;
// The edition's own floor, two stations in the wide and COOKed's to the right (draft-floor.mjs), for a caller with no layout.
const edition = device => ({left: -FLOOR.gap[device] / 2, right: FLOOR.gap[device] / 2, reveal: FLOOR.gap[device] / 2 + FLOOR.reveal});

/* The trail's floor shot (revision 14): the fixed wide of the first four stops, then the whip right and the
   push onto COOKed's stop, then the hold's slow push. `ctx.trail`: the wide stations' outer x and the reveal's. */
function floor(ctx, seconds) {
  const device = ctx.mobile ? 'phone' : 'desk', {left, right, reveal} = ctx.trail ?? edition(device), z = ctx.floorZ;
  const [wideHeight, wideBack, wideAim] = RIG.trailWide[device], [height, back, aim] = RIG.floor[device];
  const pan = expoInOut(seg(seconds, ...TRAIL.pan)), push = outCubic(seg(seconds, TRAIL.pan[1], TRAIL.pan[1] + TRAIL.push));
  const hold = seg(seconds, TRAIL.pan[1] + TRAIL.push, DURATION.curse);
  const [before, after] = RIG.extent[device], x = mix((left + before + right + after) / 2, reveal + RIG.stopCentre, pan);
  const distance = mix(wideBack, back + RIG.revealPull, pan) - RIG.revealPull * push - back * RIG.holdPush * hold;
  return {position: new THREE.Vector3(x, mix(wideHeight, height, pan), z + distance), target: new THREE.Vector3(x, mix(wideAim, aim, pan), z)};
}

// A view's `up` is world up unless it says otherwise: the board's skim is upright to the board (draft-establish.mjs).
const upOf = view => view.up ?? UP;
const blend = (a, b, amount) => ({position: a.position.clone().lerp(b.position, amount), target: a.target.clone().lerp(b.target, amount),
  up: upOf(a).clone().lerp(upOf(b), amount).normalize()});

/* The slow orbit and push every shot carries (RIG.orbit), `amount` 0..1 through its beat. */
export function drift(view, amount, mobile, push = RIG.orbit.push, pushFrom = 0) {
  const [from, to] = RIG.orbit.yaw, t = Math.min(1, Math.max(0, amount));
  const pushing = Math.max(0, t - pushFrom) / (1 - pushFrom);   // the push starts at `pushFrom` of the orbit
  const arm = view.position.clone().sub(view.target).multiplyScalar(1 - push * pushing).applyAxisAngle(UP, from + (to - from) * t);
  return {position: view.target.clone().add(arm), target: view.target.clone(), up: upOf(view).clone().applyAxisAngle(UP, from + (to - from) * t)};
}

function framing(id, seconds, ctx) {
  const {featured, mobile} = ctx;
  if (id === 'board') return establishing(seconds, mobile, mobile ? phoneOverview(ctx.size) : wide(mobile, RIG.boardStageBack));
  if (id === 'traded') {
    const from = featured.traded.home, to = ctx.landing, amount = inOutCubic(seg(seconds, ...RIG.trackTravel));
    const target = from.clone().lerp(to, amount).add(new THREE.Vector3(0, mobile ? RIG.phoneLift : 0, TUNING.travelTargetZ));
    const device = mobile ? 'phone' : 'desk', settle = inOutCubic(seg(seconds, ...RIG.trackSettle));
    const distance = RIG.track[device] + (RIG.trackClose[device] - RIG.track[device]) * settle;
    return {position: target.clone().add(new THREE.Vector3(0, TUNING.travelEyeY, distance)), target};
  }
  if (id === 'curse') {
    // The camera establishes the player, then follows his transaction history across the floor.
    return blend(close(featured.curse, seconds, id, mobile), floor(ctx, seconds), inOutCubic(seg(seconds, ...RIG.cutToFloor)));
  }
  if (id === 'finale') {
    // The pull-back runs on from the injury's tail (pulled, below), from its last frame, orbit and all.
    return pulled(injuryShot(DURATION.injury, ctx), seconds + DURATION.injury, seconds / DURATION.finale, ctx);
  }
  return close(featured[id], seconds, id, mobile);
}

/* The finale's pull-back to the winner's wide, starting on the build's first step in the injury's tail (ch17,
   draft-build.mjs), so the camera moves with the music's build and arrives on the reveal.
   `clock` is injury seconds; `amount` the winner's drift. */
function pulled(base, clock, amount, ctx) {
  if (ctx.mobile) {
    const build = mobileBuildAt(clock);
    if (!build) return base;
    const overview = blend(base, phoneOverview(ctx.size), build.pull);
    return blend(overview, drift(winner(ctx), amount, true, 0), build.reveal);
  }
  const from = BUILD.cameraFrom, length = BUILD.hit - from;
  return blend(base, drift(winner(ctx), amount, ctx.mobile, 0), outCubic(seg(clock, from, from + length)));   // orbit only: a push would crop round ten
}
const injuryShot = (seconds, ctx) => drift(framing('injury', seconds, ctx), seconds / DURATION.injury, ctx.mobile);

const BOARD_ORBIT_FROM = .5;   // the board's orbit starts half way, square-on (below)

/* A beat's shot `seconds` into its motion, carrying the orbit. The board orbits only once it stands, from
   square-on (rev 15: the pass's 1.5 degree yaw slanted the rows like a roll), so half the orbit. */
export function shot(id, seconds, ctx) {
  const set = setOfBeat(id);   // a later chapter's own 3D set frames its beats (film-sets.mjs)
  if (set?.shot) return set.shot(id, seconds, ctx);
  if (LATER.has(id)) {   // the finale's end frame, pushing in slowly so the camera never stands still (rule 19)
    // One push across all later chapters' beats, by film time, so it is continuous from card to card.
    const end = framing('finale', DURATION.finale, ctx), pushed = 1 - RIG.orbit.push * Math.min(1, (LATER_CLOCK[id] + seconds * PACE[id]) / LATER_SPAN);
    return {...end, position: end.target.clone().add(end.position.clone().sub(end.target).multiplyScalar(pushed))};
  }
  const clock = seconds;   // the wall shot is fixed once the board stands; the orbit and push run on through the hold
  if (id === 'board') seconds = Math.min(seconds, ESTABLISH.stand[1]);
  if (id === 'finale') return framing(id, seconds, ctx);
  if (id === 'injury') return pulled(injuryShot(seconds, ctx), seconds, 0, ctx);
  const amount = id === 'board' ? mix(BOARD_ORBIT_FROM, 1, seg(clock, ESTABLISH.stand[ctx.mobile ? 1 : 0], DURATION.board)) : seconds / DURATION[id];
  if (id === 'curse') return framing(id, seconds, ctx);   // rev 14 storyboard: a fixed wide, no orbit; ~~the trail only widens~~ (rev 12)
  // The board pushes in only once it stands, so the pass is one straight line (rev 17).
  return drift(framing(id, seconds, ctx), amount, ctx.mobile, RIG.orbit.push, id === 'board' ? BOARD_ORBIT_FROM : 0);
}

/* A travel (ch17, coordinator for David: no wipe between beats on the same board, film.mjs TRAVEL): the camera
   moves in one eased move from the last beat's shot to the next's, arriving on the next beat's first onset. Out
   of the board it starts as the board stands, so the stand-up runs on into Golden's card; between cards it starts
   half a whip before the bar line. Returns {from, to, amount} beats and 0..1, or null outside a travel. */
const ARRIVE_AFTER = .1;   // seconds: an onset closer than this to the bar line is the bar's own, not the arrival
// Rule 20: a transition runs 0.7-1.0 s, so an onset later than this is not the travel's arrival. No onset falls
// from film 62.077 to 97.59 (Chapters 4 and 5), so there a travel arrives half a whip after the bar, centred on it.
const ARRIVE_WITHIN = 1;
const arrival = start => {
  const onset = ONSETS.map(filmTime).find(time => time > start + ARRIVE_AFTER) - start;
  return onset <= ARRIVE_WITHIN ? onset : TRANSITION.window / 2;
};
/* The travel under way at `moment`, or null. Only a TRAVEL beat is travelled into, so a travel crosses chapters
   only where film.mjs says (Chapter 4's bench rack to Chapter 5's riser). */
const secondsInto = (moment, beat) => setOfBeat(beat.id)
  ? Math.min(beat.duration, Math.max(0, moment.elapsed - beat.start)) : moment.beatProgress * beat.duration;

export function travelAt(moment) {
  const beats = filmPlan().beats, index = moment.beatIndex, beat = beats[index];
  if (!beat) return null;
  const seconds = secondsInto(moment, beat), previous = beats[index - 1], next = beats[index + 1];
  const timing = (from, to) => ({arrive: arrival(to.start),
    lead: from.id === 'board' ? from.duration - (ESTABLISH.stand[1] + ESTABLISH.hold) * PACE.board : TRANSITION.window / 2});
  if (previous && TRAVEL.includes(beat.id)) {
    const {lead, arrive} = timing(previous, beat);
    if (seconds < arrive) return {from: previous, to: beat, amount: inOutCubic(Math.max(0, (lead + seconds) / (lead + arrive)))};
  }
  if (next && TRAVEL.includes(next.id)) {
    const {lead, arrive} = timing(beat, next);
    if (beat.duration - seconds < lead) return {from: beat, to: next, amount: inOutCubic((seconds - beat.duration + lead) / (lead + arrive))};
  }
  return null;
}

/* The set beat the camera shows while the current beat has no shot of its own and a set whips in (film-sets.mjs). */
function entered(moment) {
  const beat = filmPlan().beats[moment.beatIndex];
  return beat && !setOfBeat(beat.id) ? activeSets(moment)[0] ?? null : null;
}

/* The camera's view for this moment: the beat's shot; on the same board a travel from the last beat's (above),
   and across a change of scene a whip across the bar line, half before it and half after (rule 18). */
export function view(moment, ctx) {
  const beats = filmPlan().beats, index = moment.beatIndex, beat = beats[index];
  const entering = entered(moment);   // a set whipping in under a chapter with none: its own shot, its clock negative
  if (entering) return {up: UP, ...shot(entering.beat, entering.seconds, ctx), roll: 0};
  const seconds = secondsInto(moment, beat), half = TRANSITION.window / 2, entry = TRANSITION.intro / 2;
  // The board's camera blends only toward a beat on the board: Chapter 2's card has no shot (film.mjs sameChapter).
  const previous = beats[index - 1], next = sameChapter(beat, beats[index + 1]) ? beats[index + 1] : undefined, travel = travelAt(moment);
  let current = shot(beat.id, seconds / PACE[beat.id], ctx);
  if (travel) {
    const from = travel.from === beat ? current : shot(travel.from.id, DURATION[travel.from.id], ctx);
    current = blend(from, travel.to === beat ? current : shot(travel.to.id, 0, ctx), travel.amount);
  } else if (!previous && seconds < entry) {
    const amount = expoInOut((seconds + entry) / TRANSITION.intro);
    const above = {up: current.up, position: current.position.clone().add(new THREE.Vector3(0, RIG.dropIn.rise, 0)),
      target: current.target.clone().add(new THREE.Vector3(0, RIG.dropIn.look, 0))};
    current = blend(above, current, amount);
  } else if (previous && beat.id !== 'finale' && seconds < half && !(setOfBeat(beat.id) && !setOfBeat(previous.id))) {
    current = blend(shot(previous.id, DURATION[previous.id], ctx), current, expoInOut((seconds + half) / TRANSITION.window));
  } else if (next && next.id !== 'finale' && !TRAVEL.includes(next.id) && beat.duration - seconds < half) {
    current = blend(current, shot(next.id, 0, ctx), expoInOut((seconds - beat.duration + half) / TRANSITION.window));
  }
  // No roll anywhere: the subject stays upright (rule 19, rev 9; ~~a 0.05 rad roll on the whip~~, rev 8).
  return {...current, roll: 0};
}

/* The lens for this moment, a share of the scene's: the board's pass is narrower (draft-establish.mjs
   passZoom), easing in over the first half of the opening's hand-over so the lens never jumps. */
function lens(moment, mobile) {
  const beat = filmPlan().beats[moment.beatIndex];
  if (beat.id !== 'board') return 1;
  const seconds = moment.beatProgress * beat.duration, zoom = passZoom(seconds / PACE.board, mobile);
  return mix(1, zoom, inOutCubic(seg(seconds, 0, TRANSITION.intro / 2)));
}

/* Place the camera for this moment, upright, with its lens; returns its distance to the subject. */
export function frame(camera, moment, ctx, shake = 0) {
  const beat = filmPlan().beats[moment.beatIndex], {position, target, up: upright} = view(moment, ctx);
  camera.fov = (ctx.mobile ? OPENING.phoneFov : OPENING.cameraFov) * lens(moment, ctx.mobile);
  const {width, height} = ctx.size;
  // A travel carries the frame's lift from one beat's to the next's with the camera, so nothing jumps.
  // A set's own lift wins for its beats (film-sets.mjs), else the beat's, else `all`.
  const device = ctx.mobile ? 'phone' : 'desk', lift = RIG.lift[device], travel = travelAt(moment);
  const liftOf = id => setOfBeat(id)?.lift[device]?.[id] ?? lift[id] ?? lift.all;
  let up = travel ? mix(liftOf(travel.from.id), liftOf(travel.to.id), travel.amount) : liftOf(entered(moment)?.beat ?? beat.id);
  if (ctx.mobile && beat.id === 'board' && !travel) up = mix(MOBILE_FRAME.passLift, lift.board, standing(moment.beatProgress * beat.duration / PACE.board));
  const build = ctx.mobile ? mobileBuildAt(buildClock(beat.id, moment.beatProgress * beat.duration / PACE[beat.id])) : null;
  if (build) up = mix(mix(lift.injury, MOBILE_FRAME.lift, build.pull), lift.finale, build.reveal);
  const slide = ctx.mobile ? (build?.reveal ?? 0) * RIG.finale.phoneShift : RIG.deskShift[beat.id] ?? 0;
  camera.setViewOffset(width, height, -width * slide, height * up, width, height);
  camera.position.copy(position);
  camera.position.x += shake * TUNING.horizontalShakeRatio; camera.position.y += shake;
  camera.up.copy(upright ?? UP);
  camera.lookAt(target);
  return camera.position.distanceTo(target);
}
