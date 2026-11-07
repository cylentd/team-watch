import RECEIPTS from './power-receipts.json' with { type: 'json' };
import { checkPower, powerValues } from './power-data.mjs';

/* Chapter 5's checked receipts, read once at import like timing.json, so the pose, the camera and the set agree on
   the feature's place without a fetch. A receipt that fails its check leaves CAST null: the set's `ready` rejects
   and the room falls back, the way a failed badge does (app.mjs). */
function read() {
  try {
    const values = powerValues(checkPower(RECEIPTS));
    return Object.freeze({values, feature: values.feature.power, leaders: values.four.length,
      standings: Object.freeze(values.order.map(team => team.standing))});   // each power place's standing, for the shuffle
  } catch (error) {
    return Object.freeze({error});
  }
}
export const CAST = read();
// The place the camera frames for the feature when the receipts failed: the room shows the fallback anyway.
export const FALLBACK_FEATURE = 1;
