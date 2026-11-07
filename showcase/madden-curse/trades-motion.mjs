import { TRADES_MOTION } from "./constants-trades.mjs";
export { TRADES_MOTION };
import { arc, inOutCubic, outCubic, seg } from './draft-motion.mjs';
import { span } from './timing.mjs';

/* Chapter 2's motion, beat seconds -> 0..1 amounts, every time from timing.json's trades beat. Pure, so a seek
   or a still draws the same frame. The rails draw out from Aura, the lights run to the winner's end in one eased
   move each, the leads bloom where they stop, the push eases to a stop on the record's hit, the headline enters
   with it, and through the reading hold a light drifts along each rail's bright half (rule 15: no frozen frame). */

const between = (seconds, name) => seg(seconds, ...span('trades', name));

export function tradesPose(seconds, count) {
  const [driftFrom] = span('trades', 'drift'), held = seconds - driftFrom;
  const drift = held < 0 ? null : Array.from({length: count}, (_, index) => {
    const phase = ((held / TRADES_MOTION.bar) + index / count) % 1;
    return {along: phase, glow: arc(phase) * TRADES_MOTION.driftGlow * seg(held, 0, TRADES_MOTION.driftIn)};
  });
  const stamp = outCubic(between(seconds, 'record'));
  const [, arrive] = span('trades', 'lights'), [leadsFrom] = span('trades', 'leads'), [recordFrom] = span('trades', 'record');
  return {
    // A phone's beams rise from Aura with their source (trades-view.mjs); the stem it trails is gone before the
    // headline enters (rule 36).
    rise: outCubic(between(seconds, 'rails')),
    stem: 1 - seg(seconds, leadsFrom, recordFrom),
    // Seconds since the one flare's hit (film-glint.mjs glintAmount): the lights reaching the leads.
    glint: seconds - arrive,
    rails: outCubic(between(seconds, 'rails')),
    travel: inOutCubic(between(seconds, 'lights')),
    leads: outCubic(between(seconds, 'leads')),
    push: outCubic(between(seconds, 'push')),
    stamp, stampScale: TRADES_MOTION.stampFrom + (1 - TRADES_MOTION.stampFrom) * stamp,
    headline: outCubic(between(seconds, 'headline')),
    breathe: held < 0 ? 1 : 1 + TRADES_MOTION.breathe * Math.sin(2 * Math.PI * held / TRADES_MOTION.bar),
    drift,
  };
}

/* The card's share revealed by the whip in (film.mjs transitionAt, amount .5 on the bar line), matching the light
   sweeping across (film.css .wipe, --wipe-at = amount x 140% - 20%), and how far its contents still have to slide. */
export function whipIn(transition) {
  if (!transition) return {reveal: 1, slide: 0};
  const reveal = Math.min(1, Math.max(0, transition.amount * TRADES_MOTION.sweepSpan - TRADES_MOTION.sweepLead));
  return {reveal, slide: (1 - inOutCubic(transition.amount)) * TRADES_MOTION.whipShift};
}
