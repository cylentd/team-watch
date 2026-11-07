import { LINEUPS_POSE_DETAIL as TUNING } from './constants-lineups.mjs';
import { POSE } from "./constants-lineups.mjs";
export { POSE };
import { arc, impact, inOutCubic, outBack, outCubic, seg } from './draft-motion.mjs';
import { hop } from "./blip-hop.mjs";
import { CLOCK } from "./lineups-clock.mjs";
import { places } from './lineups-layout.mjs';

/* Chapter 4's desk at chapter second `seconds` (0 is film 62.077; docs/madden-film-chapter4.md, beat tables). Pure:
   the same second gives the same pose, so a seek either way rebuilds it (rule 19: nothing shows before its bar).
   `reduced` gives each hit's end state on its bar line: no falls, ejects, travel, hops, shafts, flashes or shake.
   `cast` is lineups-data.mjs lineupValues. Positions are world [x, y, z] from lineups-layout.mjs.
   The gag is "Score slams, shield ejects" (David, 2026-11-05; ~~tokens drain into a chute, the flap opens~~): a shield
   lands, its W and score slam 4 frames apart, and a negative score flashes the slot red and kicks it onto the ledge. */

const outExpo = value => (value >= 1 ? 1 : 1 - 2 ** (TUNING.expoSlope * value));
const mix = (from, to, amount) => from + (to - from) * amount;
const lerp = (from, to, amount) => from.map((value, index) => mix(value, to[index], amount));
const latest = (list, seconds) => list.filter(time => seconds >= time).at(-1);
const age = (seconds, time) => (time === undefined || seconds < time ? -1 : seconds - time);
/* 0 before `at`; eased over `length` after; the end state from `at` when reduced. */
const step = (seconds, at, length, ease, reduced) => (seconds < at ? 0 : reduced || seconds >= at + length ? 1 : ease(seg(seconds, at, at + length)));
const flare = (seconds, at, reduced) => (reduced || at === undefined ? 0 : 1 - seg(seconds, at, at + POSE.shaftFor));
function shields(seconds, reduced, cast, place) {
  const changing = CLOCK.landings[1] - (reduced ? 0 : CLOCK.fall);
  return cast.defense.map((entry, index) => {
    const land = CLOCK.landings[index], visible = index === 0 ? seconds >= land - (reduced ? 0 : CLOCK.fall) && seconds < changing : seconds >= changing;
    const drop = reduced || seconds >= land ? 0 : POSE.drop * (1 - outExpo(seg(seconds, land - CLOCK.fall, land)));
    const position = [place.socket[0], place.socket[1] + drop, place.socket[2]];
    const squash = reduced ? 1 : 1 - POSE.squash * Math.sin(Math.PI * seg(seconds, land, land + POSE.squashFor)) * (seconds >= land ? 1 : 0);
    return {name: entry.name, visible, position, squash, ledge: false};
  });
}

const slam = (seconds, at, reduced) => ({visible: seconds >= at, scale: reduced ? 1 : 1 + POSE.slam * (1 - outCubic(seg(seconds, at, at + POSE.slamFor)))});
const shieldStamps = (seconds, reduced, cast) => CLOCK.landings.map((land, index) => {
  const win = slam(seconds, CLOCK.wins[index], reduced);
  return {week: slam(seconds, land, reduced), score: slam(seconds, land + POSE.scoreAfter, reduced),
    win: {...win, visible: win.visible && cast.defense[index].won}};
});

function slot(seconds, cast) {
  const index = CLOCK.landings.findLastIndex(time => seconds >= time);
  return index < 0 || seconds >= CLOCK.track[0] ? null : cast.defense[index].name;
}

function cards(seconds, reduced, mobile, place) {
  const lands = CLOCK.players, [clearFrom] = CLOCK.switch, moveFrom = clearFrom + POSE.clear, swap = CLOCK.swap;
  const visible = seconds >= lands - (reduced ? 0 : CLOCK.fall);
  const drop = reduced || seconds >= lands ? 0 : POSE.drop * (1 - outExpo(seg(seconds, lands - CLOCK.fall, lands)));
  const moved = reduced ? (seconds >= swap ? 1 : 0) : inOutCubic(seg(seconds, moveFrom, swap));
  // The two paths bow apart across the line between the slots, so the faces pass side by side (180-degree rule).
  const along = [place.rack[0] - place.start[0], place.rack[1] - place.start[1]], length = Math.hypot(...along);
  const across = [-along[1] / length, along[0] / length], bow = POSE.bulge[mobile ? 'phone' : 'desk'] * arc(moved);
  const path = (from, to, side, front) => {
    const point = lerp(from, to, moved);
    return [point[0] + side * across[0] * bow, point[1] + side * across[1] * bow, point[2] + front * arc(moved)];
  };
  const squash = reduced ? 1 : 1 - POSE.squash * Math.sin(Math.PI * seg(seconds, lands, lands + POSE.squashFor)) * (seconds >= lands ? 1 : 0);
  const starter = path(place.start, place.rack, 1, -POSE.front / 2), bench = path(place.rack, place.start, -1, POSE.front);
  starter[1] += drop; bench[1] += drop;
  return [{visible, position: starter, squash}, {visible, position: bench, squash}];
}

/* A stamp pops in over 4 frames (outBack) at `at`, and clears in 4 frames from `until`. */
function stamp(seconds, at, until, scale, reduced) {
  const leaving = until === null ? 0 : seg(seconds, until, until + POSE.clear);   // null: it stays to the chapter's end
  const shown = seconds >= at && (until === null || seconds < until + (reduced ? 0 : POSE.clear));
  const grow = reduced ? 1 : outBack(seg(seconds, at, at + POSE.stampPop)) * (1 - leaving);
  return {visible: shown && grow > 0, scale: scale * Math.max(grow, 0)};
}

function stamps(seconds, reduced, cast) {
  // Week 5 clears and W5 flips to W8 just before the crane down starts, so the held frame never shows a half stamp.
  const clear = CLOCK.switch[0] - POSE.flip, never = null, s = POSE.scores;
  const weeks = cast.tightends.map(entry => entry.week);
  const flipping = reduced ? (seconds >= clear ? 1 : 0) : seg(seconds, clear, clear + POSE.flip);
  return {
    week: {visible: seconds >= CLOCK.players, text: weeks[flipping < TUNING.weekFlipMidpoint ? 0 : 1], flip: reduced ? 1 : Math.abs(Math.cos(Math.PI * flipping))},
    s5start: {...stamp(seconds, CLOCK.players + POSE.stampGap, clear, s.s5start, reduced), card: 0, text: cast.tightends[0].starter.score},
    s5bench: {...stamp(seconds, CLOCK.bench5, clear, s.s5bench, reduced), card: 1, text: cast.tightends[0].bench.score},
    s8start: {...stamp(seconds, CLOCK.starter8, never, s.s8start, reduced), card: 1, text: cast.tightends[1].starter.score},
    s8bench: {...stamp(seconds, CLOCK.bench8, never, s.s8bench, reduced), card: 0, text: cast.tightends[1].bench.score},
  };
}

function blip(seconds, reduced, place) {
  const scale = place.blip.scale;
  if (seconds < CLOCK.second) {
    // After Chiefs' 0 nothing happens, so he hops over to the slot and leans in to look; on the track he turns to the ledge.
    const [from] = CLOCK.peek, [turnFrom, turnTo] = CLOCK.track;
    const moved = reduced ? {travel: seconds >= from ? 1 : 0, lift: 0, squash: 1} : hop(seg(seconds, from, from + POSE.blipHopFor), POSE.blipHops);
    const position = lerp(place.blip.gibbs, place.blip.peek, moved.travel);
    position[1] += moved.lift * POSE.blipLift * scale;
    const leaning = step(seconds, from + POSE.blipHopFor, POSE.leanFor, outCubic, reduced) - step(seconds, turnFrom, turnTo - turnFrom, outCubic, reduced);
    return {visible: true, position, scale, squash: moved.squash, lean: POSE.lean * leaning, look: POSE.look * step(seconds, turnFrom, turnTo - turnFrom, outCubic, reduced), nod: 0};
  }
  // At 18.40 he snaps his head up to the rack twice: up, back, then up and held (storyboard).
  const at = CLOCK.bench8, first = at + POSE.nodFor, again = at + POSE.nodGap;
  const nodding = reduced ? (seconds >= at ? 1 : 0) : seconds < at ? 0 : seconds < first ? seg(seconds, at, first)
    : seconds < again ? 1 - seg(seconds, first, first + POSE.nodFor) : seg(seconds, again, again + POSE.nodFor);
  return {visible: true, position: place.blip.lamarley, scale, squash: 1, lean: 0, look: POSE.turn, nod: POSE.nod * nodding};
}

/* The whole desk at chapter second `seconds`. */
export function lineupsPose(seconds, reduced, cast, mobile = false) {
  const place = places(mobile), lands = CLOCK.landings;
  const last = latest(lands, seconds), cardHit = latest([CLOCK.players, CLOCK.swap], seconds);
  const rackHit = latest([CLOCK.bench5, CLOCK.bench8], seconds);
  const rackFull = (seconds >= CLOCK.bench5 && seconds < CLOCK.swap) || seconds >= CLOCK.bench8;
  const rackLight = rackFull ? mix(POSE.rackLow, 1, step(seconds, rackHit, POSE.rackIn, outCubic, reduced)) : POSE.rackLow;
  const scored = lands.map(land => land + POSE.scoreAfter);
  const hits = [...lands, ...scored, CLOCK.players, CLOCK.bench5, CLOCK.swap, CLOCK.bench8];
  const red = 0;
  return {
    shields: shields(seconds, reduced, cast, place),
    shieldStamps: shieldStamps(seconds, reduced, cast),
    slot: slot(seconds, cast), flash: red,
    strip: reduced || seconds >= lands[0] + POSE.stripFor ? POSE.strip : mix(1, POSE.strip, seg(seconds, lands[0], lands[0] + POSE.stripFor)),
    ledge: reduced ? (seconds >= CLOCK.outcome ? 1 : 0) : seconds < CLOCK.outcome ? 0 : 1 - TUNING.ledgeFadeAmount * seg(seconds, CLOCK.outcome, CLOCK.outcome + POSE.rimFor),
    rims: {gibbs: POSE.rim + (1 - POSE.rim) * Math.max(flare(seconds, last, reduced), red), start: POSE.rim + (1 - POSE.rim) * flare(seconds, cardHit, reduced),
      rack: rackLight},
    shafts: {gibbs: flare(seconds, last, reduced), start: flare(seconds, cardHit, reduced), rack: flare(seconds, rackHit, reduced), flash: red},
    impacts: {gibbs: reduced ? -1 : age(seconds, last), start: reduced ? -1 : age(seconds, cardHit), rack: reduced ? -1 : age(seconds, rackHit)},
    cards: cards(seconds, reduced, mobile, place),
    stamps: stamps(seconds, reduced, cast),
    blip: blip(seconds, reduced, place),
    shake: reduced ? 0 : POSE.shake * Math.max(0, ...hits.map(time => impact(seconds, time))),
  };
}
