import { RECEIPT_ENTRANCE_DETAIL as TUNING } from './constants-playback.mjs';
import { RECEIPT_ENTER } from "./constants-playback.mjs";
export { RECEIPT_ENTER };
import { clamp } from './timeline.mjs';

const easeOut = amount => 1 - (1 - clamp(amount)) ** TUNING.cubicExponent;

export function receiptEntrance(beat, age) {
  const timing = RECEIPT_ENTER[beat === 'board' ? 'board' : 'feature'];
  return {rule: easeOut(age / timing.rule), headline: easeOut((age - timing.headAt) / timing.head),
    subline: easeOut((age - timing.subAt) / timing.sub)};
}
