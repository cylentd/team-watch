import { WAIVERS_MOTION } from "./constants-waivers.mjs";
export { WAIVERS_MOTION };
import { outCubic, seg } from './draft-motion.mjs';
import { beatTiming, span } from './timing.mjs';

/* Chapter 3's motion, chapter seconds -> 0..1 amounts, every time from timing.json's two chapter-3 beats. Pure, so
   a seek or a still draws the same frame. The title rises after the whip; #3 and #2 land on their bar lines; on a
   phone the pair steps down to make room; #1 lands on the phrase seam, the other two dim, his weeks fill left to
   right, and the reading hold pushes in slowly (rule 15: no frozen frame). The rank sweep now starts one second
   earlier during #1's drift, without moving the subsequent scene or music cues (2026-11-06). */

const CARDS = Object.freeze(['third', 'second', 'first']);
const first = beatTiming('waiver-claim'), second = beatTiming('waiver-starts');
const ease = (seconds, beat, name) => outCubic(seg(seconds, ...span(beat, name)));

export function waiversPose(seconds, reduced = false, count = WAIVERS_MOTION.weeks) {
  const later = seconds >= first.duration;
  // Reduced motion shows each beat's story as one still: the pair before #1 comes, then the whole hold.
  const one = reduced ? (later ? first.duration : span('waiver-claim', 'room')[0]) : Math.min(seconds, first.duration);
  const two = !later ? null : reduced ? second.duration : seconds - first.duration;
  const weekTime = reduced ? two ?? -Infinity : seconds - first.duration;
  const [from, to] = span('waiver-starts', 'weeks'), step = (to - from) / (count + WAIVERS_MOTION.overlap - 1);
  const landed = name => span('waiver-claim', name)[1];
  return {
    head: ease(one, 'waiver-claim', 'headline'),
    sub: ease(one, 'waiver-claim', 'sub'),
    cards: CARDS.map(name => ease(one, 'waiver-claim', name)),
    // Each card's rim light, bright on its landing and gone within `glow` seconds; never in a still.
    glow: CARDS.map(name => reduced || seconds < landed(name) ? 0 : 1 - seg(seconds, landed(name), landed(name) + WAIVERS_MOTION.glow)),
    room: ease(one, 'waiver-claim', 'room'),
    // The stage continues drifting as the ranks appear (2026-11-06; rule 15).
    drift: reduced ? 0 : seg(one, ...span('waiver-claim', 'drift')),
    dim: two === null ? 0 : ease(two, 'waiver-starts', 'dim'),
    weeks: Array.from({length: count}, (_, index) =>
      outCubic(seg(weekTime, from + index * step, from + (index + WAIVERS_MOTION.overlap) * step))),
    push: two === null || reduced ? 0 : seg(two, ...span('waiver-starts', 'push')),
  };
}
