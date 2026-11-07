import { BLIP_HOP_DETAIL as TUNING } from './constants-opening.mjs';
import { HOP } from "./constants-opening.mjs";
export { HOP };
/* Blip never glides (David, 2026-11-03: "the sliding looks awkward"). A move across the floor is a
   run of hops: each one crouches (anticipation), lifts, lands with a squash and settles. The middle
   hops are longer than the first and last, so the speed eases in and out. Pure, so Node tests it. */

const lengths = steps => {
  const weights = Array.from({length: steps}, (_, index) => TUNING.weightBaseline + Math.sin(Math.PI * (index + TUNING.weightSampleCenter) / steps));
  const total = weights.reduce((sum, weight) => sum + weight, 0);
  return weights.map(weight => weight / total);
};

/* Where a `steps`-hop move is at `progress` (0..1): `travel` 0..1 along the path, `lift` above the
   floor, `squash` for his height (1 is his rest height). */
export function hop(progress, steps) {
  const clamped = Math.min(1, Math.max(0, progress));
  if (clamped >= 1) return {travel: 1, lift: 0, squash: 1};
  const index = Math.min(steps - 1, Math.floor(clamped * steps)), phase = clamped * steps - index;
  const share = lengths(steps), done = share.slice(0, index).reduce((sum, value) => sum + value, 0);
  const air = 1 - HOP.crouch - HOP.land;
  const flight = Math.min(1, Math.max(0, (phase - HOP.crouch) / air));
  const eased = flight * flight * (TUNING.smoothstepCoefficient - 2 * flight);
  let squash = 1 + HOP.stretch * Math.sin(Math.PI * flight);
  if (phase < HOP.crouch) squash = 1 - HOP.squash * Math.sin(Math.PI * phase / HOP.crouch);
  else if (phase > 1 - HOP.land) squash = 1 - HOP.squash * Math.sin(Math.PI * (phase - (1 - HOP.land)) / HOP.land);
  return {travel: done + share[index] * eased, lift: HOP.lift * Math.sin(Math.PI * flight), squash};
}
