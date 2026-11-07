import { DRAFT_BUILD_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { SUSPENSE } from "./constants-draft-motion.mjs";
export { SUSPENSE };
import { inOutCubic, seg } from './draft-motion.mjs';
import { at, ats, beatTiming, span } from './timing.mjs';

/* The finale's build (ch17, coordinator for David: "at 36-38 s the music builds but nothing happens on screen").
   From the injury card's fade, on each onset of the build, a group of the other eleven columns dims, nearest
   Romo's first, and Romo's column brightens a step and pulses faster; on the reveal his column goes full with a
   flash. The build runs in the injury's tail and on into the finale; its clock is seconds into the injury beat,
   so the finale's seconds are `INJURY_LENGTH` later.
   2026-11-05 (David: "I count the reveal as the lit up column"; "the buildup happened a tick too early"): the
   reveal is the finale's own `reveal` event, its first frame, on the 40.077 bar line, the loudest kick of the
   passage. ~~The avatar's landing, film 40.571~~. The avatar now rises out of the lit column and lands on the
   40.544 onset. */
const INJURY_LENGTH = beatTiming('injury').duration;
export const BUILD = Object.freeze({
  cameraFrom: span('injury', 'fade')[1],
  // The build's steps, injury seconds: two onsets in its tail (film 38.048, 38.931), then the finale's bar line.
  steps: Object.freeze([...ats('injury', 'build'), ...ats('finale', 'build').map(time => time + INJURY_LENGTH)]),
  hit: at('finale', 'reveal') + INJURY_LENGTH,   // Romo's column lit, the 40.077 bar line
  land: span('finale', 'rise')[1] + INJURY_LENGTH,   // his avatar lands, onset 40.544; a phone moves in from here
  ease: TUNING.columnEase,          // seconds a column takes to change light: 3 frames, so the step reads as on the onset
  dim: TUNING.dimFraction,           // a dimmed column's share of the light it had (draft.mjs LIGHT.focus)
  peak: TUNING.peakFraction,         // Romo's column after the last step, below the finale's full column (FINALE.cardBase)
  depth: TUNING.pulseDepth,         // how deep Romo's pulse runs, a share of his light
  speeds: Object.freeze([TUNING.slowPulseFrequency, TUNING.mediumPulseFrequency, TUNING.fastPulseFrequency, TUNING.finalPulseFrequency]),
  flash: TUNING.flashIntensity,         // extra light on his column at the hit, gone over `flashFade` seconds
  flashFade: TUNING.flashFade,
});

/* The build's clock for a beat and its seconds, injury seconds, or null where no build runs. */
export function buildClock(beatId, seconds) {
  if (beatId === 'injury') return seconds;
  if (beatId === 'finale') return seconds + INJURY_LENGTH;
  return null;
}

/* Which step dims each of the other columns: nearest Romo's first, the left one of a tie first, in groups as
   even as the steps allow. Returns a Map column -> step index. */
export function dimOrder(columns, winner) {
  const others = columns.filter(column => column !== winner)
    .sort((a, b) => Math.abs(a - winner) - Math.abs(b - winner) || a - b);
  const steps = BUILD.steps.length;
  return new Map(others.map((column, rank) => [column, Math.floor(rank * steps / others.length)]));
}

const eased = (clock, from) => inOutCubic(seg(clock, from, from + BUILD.ease));

/* How many steps have landed by `clock`, eased: 0 before the first, steps.length after the last. */
const climbed = clock => BUILD.steps.reduce((sum, step) => sum + eased(clock, step), 0);

/* Romo's pulse phase at `clock`, continuous across the speed changes so the pulse never jumps. */
function phase(clock) {
  let total = 0;
  BUILD.steps.forEach((step, index) => {
    const end = BUILD.steps[index + 1] ?? Infinity;
    total += BUILD.speeds[index] * Math.max(0, Math.min(clock, end) - step);
  });
  return total;
}

/* A dimmed column's light share at `clock`, of `base`: `base` until its step, then BUILD.dim of it. */
export const otherLight = (clock, step, base) => base * (1 - (1 - BUILD.dim) * eased(clock, BUILD.steps[step]));

/* Romo's column before the hit, at `clock`: from `base`, a step brighter on each onset, pulsing faster each time. */
export function winnerLight(clock, base) {
  const level = base + (BUILD.peak - base) * climbed(clock) / BUILD.steps.length;
  const pulsing = Math.min(1, climbed(clock));
  return level * (1 + BUILD.depth * pulsing * Math.sin(phase(clock)) ** 2);
}

/* The flash on Romo's column from the hit: BUILD.flash at the hit, gone over BUILD.flashFade. */
export const flash = clock => clock < BUILD.hit ? 0 : BUILD.flash * (1 - seg(clock, BUILD.hit, BUILD.hit + BUILD.flashFade));

/* `kick`: on each step every card lifts by this share of its light and falls back over `kickFade` s, so a step
   reads on its onset (2026-11-05: a step only changed the pulse's speed, which nobody sees as a beat). */

/* The lift from the latest step at `clock`: SUSPENSE.kick on the step, gone over SUSPENSE.kickFade. */
const kick = clock => SUSPENSE.kick * Math.max(0, ...BUILD.steps.map(step =>
  clock >= step ? 1 - seg(clock, step, step + SUSPENSE.kickFade) : 0));

export function buildCardLight(clock, column, winner, base, winningLight) {
  if (clock < BUILD.hit) return base * (SUSPENSE.floor + SUSPENSE.depth * (1 + Math.sin(phase(clock))) / 2 + kick(clock));
  return column === winner ? winningLight + flash(clock) : base * BUILD.dim;
}

export function buildRailLight(clock, row) {
  if (clock < BUILD.steps[0] || clock >= BUILD.hit) return null;
  const chase = Math.max(0, Math.sin(phase(clock) - row * SUSPENSE.railPhase)) ** SUSPENSE.railPower;
  return SUSPENSE.floor + SUSPENSE.railPeak * chase;
}
