import { POWER_POSE_DETAIL as TUNING } from './constants-power.mjs';
import { POSE } from "./constants-power.mjs";
export { POSE };
import { impact, inOutCubic, outBack, outCubic, seg } from './draft-motion.mjs';
import { hop } from './blip-hop.mjs';
import { TIMES } from "./power-clock.mjs";
import { RISER, TIER, TROPHY, stairs } from "./power-layout.mjs";

/* Chapter 5's set at film second `time` (docs/madden-film-chapter5.md, "Cinematic revision", David 2026-11-05:
   "Standings shuffle into power order" and "The trophy returns"). Pure: the same second gives the same pose, so
   seeking either way rebuilds it (rule 19: nothing is visible before its moment). `reduced` gives each hit's end
   state on its bar line: no falls, flights, hops, dust or wave. `cast` is power-cast.mjs: the feature's place, the
   top four and each power place's standing. */

const outExpo = value => (value >= 1 ? 1 : 1 - 2 ** (TUNING.expoSlope * value));
const inCubic = value => value ** TUNING.cubicExponent;
const mix = (from, to, amount) => from + (to - from) * amount;
const lerp = (from, to, amount) => from.map((value, index) => mix(value, to[index], amount));

/* The hop share at which one hop touches down (blip-hop.mjs `hop`), found by bisection so a landing sits on its bar
   however HOP is tuned. */
function touchdown() {
  let low = 0, high = 1;
  for (let round = 0; round < TUNING.landingSearchIterations; round++) { const middle = (low + high) / 2; if (hop(middle, 1).travel >= 1) high = middle; else low = middle; }
  return high;
}
const ONE_HOP = touchdown(), HOPS = 3;

/* A step at `at`: 0 before, eased 0..1 over `length` after; reduced, the end state from `at`. */
const step = (time, at, length, ease, reduced) => (time < at ? 0 : reduced || time >= at + length ? 1 : ease(seg(time, at, at + length)));

function plates(time, reduced, cast) {
  const [from, to] = TIMES.shuffle, lands = TIMES.standings;
  const shuffle = reduced ? (time >= to ? 1 : 0) : time < from ? 0 : time >= to ? 1 : inOutCubic(seg(time, from, to));
  const swap = time < to ? 0 : reduced ? 1 : outBack(seg(time, to, to + POSE.swap));
  const four = step(time, TIMES.four, POSE.softFor, outCubic, reduced), back = step(time, TIMES.pull[0], POSE.softFor, outCubic, reduced);
  const seated = 1 - step(time, TIMES.pull[0], POSE.seat, inOutCubic, reduced);
  return Array.from({length: TIER.places}, (_, index) => {
    const place = index + 1, feature = place === cast.feature, leader = place <= cast.leaders, falling = !reduced && time < lands;
    const visible = time >= lands - (reduced ? 0 : POSE.fall);
    const drop = falling ? POSE.drop * (1 - outExpo(seg(time, lands - POSE.fall, lands))) : 0;
    const press = reduced ? 0 : Math.sin(Math.PI * seg(time, lands, lands + POSE.squashFor));
    const pops = POSE.pops.map(delay => (reduced ? (time >= lands ? 1 : 0) : outBack(seg(time, lands + delay, lands + delay + POSE.pop))));
    const out = step(time, TIMES.feature, POSE.slide, outCubic, reduced) - step(time, TIMES.verdict, POSE.seat, inOutCubic, reduced);
    const lifted = leader ? step(time, TIMES.four, POSE.liftFor, outBack, reduced) * seated * (POSE.lift + (place === 1 ? POSE.notch : 0)) : 0;
    // The feature softens the rest to 40%; on the four's hit the leaders come up and places 5-12 stay down and sink;
    // from the pull back every plate is seated and at full light again, for the trophy (storyboard, power-close).
    const soften = feature ? 0 : step(time, TIMES.feature, POSE.softFor, outCubic, reduced);
    const dimmed = leader ? soften * (1 - four) : Math.max(soften, four);
    return {place, standing: cast.standings?.[index] ?? place, visible, drop, squash: 1 - POSE.squash * press, pops, shuffle, swap,
      forward: feature ? POSE.forward * out : 0, lift: lifted * RISER.plate.height, sink: leader ? 0 : POSE.dimSink * four * (1 - back),
      light: mix(1, POSE.soft, dimmed * (1 - back))};
  });
}

function stamps(time, reduced) {
  const gone = 1 - step(time, TIMES.four, POSE.shrink, inCubic, reduced);
  return {power: step(time, TIMES.feature, POSE.stamp, outBack, reduced) * gone,
    actual: step(time, TIMES.feature + POSE.stampLag, POSE.stamp, outBack, reduced) * gone};
}

/* The trophy lowers from above frame onto the summit, accelerating into its landing on the bar, unwinding a turn. */
function trophy(time, reduced) {
  const [from, to] = TIMES.trophy;
  if (time < (reduced ? to : from)) return {visible: false, height: TROPHY.fall, spin: TROPHY.spin};
  const amount = reduced ? 1 : seg(time, from, to);
  return {visible: true, height: TROPHY.fall * (1 - amount * amount), spin: TROPHY.spin * (1 - outCubic(amount))};
}

/* Blip waits on the floor at the stair from the pull back, then hops up it: three hops, the last touching down
   beside the trophy on the hops' bar. */
function blip(time, reduced, mobile) {
  const path = stairs(mobile), [from, to] = TIMES.hops, still = {lift: 0, squash: 1};
  if (time < TIMES.pull[0]) return {visible: false, position: path[0], ...still};
  if (reduced || time < from) return {visible: true, position: reduced && time >= to ? path[HOPS] : path[0], ...still};
  const length = (to - from) / (HOPS - 1 + ONE_HOP), index = Math.min(HOPS - 1, Math.floor((time - from) / length));
  const run = hop((time - from - index * length) / length, 1), [a, b] = [path[index], path[index + 1]], rise = b[1] - a[1];
  const along = lerp(a, b, run.travel), arc = rise * (1 - (1 - run.travel) ** 2 - run.travel);
  const lift = arc + (POSE.clear + POSE.climb * Math.abs(rise)) * Math.sin(Math.PI * run.travel);
  return {visible: true, position: along, lift: Math.max(0, lift), squash: run.squash};
}

export function powerPose(time, reduced = false, cast = {feature: 0, leaders: 0}, mobile = false) {
  const lit = reduced ? (time >= TIMES.board ? POSE.strip.rest : 0)
    : time < TIMES.board ? 0 : mix(1, POSE.strip.rest, outCubic(seg(time, TIMES.board + POSE.strip.flash, TIMES.board + POSE.strip.flash + POSE.strip.settle)));
  const age = at => (reduced ? -1 : time - at);
  const wave = reduced || time < TIMES.wave || time >= TIMES.wave + POSE.wave ? null : seg(time, TIMES.wave, TIMES.wave + POSE.wave);
  const knock = at => (reduced ? 0 : impact(time, at));
  return {strips: lit, plates: plates(time, reduced, cast), stamps: stamps(time, reduced), trophy: trophy(time, reduced),
    blip: blip(time, reduced, mobile), wave, dim: mix(1, POSE.dim, step(time, TIMES.identIn, POSE.dimFor, inOutCubic, reduced)),
    impacts: {standings: age(TIMES.standings), order: age(TIMES.shuffle[1]), trophy: age(TIMES.trophy[1]), blip: age(TIMES.hops[1])},
    shake: POSE.shake * (knock(TIMES.standings) + POSE.thud * knock(TIMES.trophy[1]))};
}
