import { DRAFT_MOTION_DETAIL as TUNING } from './constants-draft-motion.mjs';
/* Easing for the draft room. Every curve is a pure function of a 0..1 amount, so a frame depends only
   on the clock. The overshoot and decay constants are tuned by eye against the beat screenshots. */
import { clamp, mix } from './timeline.mjs';

export const BACK_OVERSHOOT = 1.70158;            // Penner's standard ease-out-back
export const SETTLE_RATE = 9;                      // how fast a thud or a light flash dies away, per second
export const WOBBLE = 34;                          // a jolt's frequency, radians per second

export const seg = (value, start, end) => clamp((value - start) / (end - start));
export const outCubic = value => 1 - Math.pow(1 - clamp(value), TUNING.cubicExponent);
export const inOutCubic = value => { const v = clamp(value); return v < TUNING.midpoint ? TUNING.cubicInScale * v * v * v : 1 - Math.pow(-2 * v + 2, TUNING.cubicExponent) / 2; };
export const expoInOut = value => {
  const v = clamp(value);
  if (v === 0 || v === 1) return v;
  return v < TUNING.midpoint ? Math.pow(2, TUNING.expoSlope * v - TUNING.expoOffset) / 2 : (2 - Math.pow(2, TUNING.negativeExpoSlope * v + TUNING.expoOffset)) / 2;
};
export const outBack = value => {
  const v = clamp(value) - 1, c = BACK_OVERSHOOT;
  return 1 + (c + 1) * v * v * v + c * v * v;
};
export const arc = value => Math.sin(Math.PI * clamp(value));
/* A hit at `at` seconds: 0 before it, 1 at it, dying away after. */
export const impact = (seconds, at) => seconds < at ? 0 : Math.exp(-(seconds - at) * SETTLE_RATE);
export const jolt = (seconds, at) => impact(seconds, at) * Math.sin((seconds - at) * WOBBLE);
export const lerp3 = (out, from, to, amount) => out.set(mix(from.x, to.x, amount), mix(from.y, to.y, amount), mix(from.z, to.z, amount));
