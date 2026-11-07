import { FRAME } from "./constants-power.mjs";
export { FRAME };
import { filmPlan } from './film.mjs';
import { at, span } from './timing.mjs';

/* Chapter 5's hits in film seconds, read from the timing sheet (timing.json `power-board`, `power-close`), so the
   pose, the camera and the headlines share one clock (rule 4: timing is a sheet). A span is [from, to]. */
const start = id => filmPlan().beats.find(beat => beat.id === id).start;
const BOARD = start('power-board'), CLOSE = start('power-close');
const board = name => BOARD + at('power-board', name), close = name => CLOSE + at('power-close', name);
const spanOf = (beat, offset, name) => Object.freeze(span(beat, name).map(value => offset + value));

export const TIMES = Object.freeze({
  board: BOARD, close: CLOSE, end: filmPlan().duration,
  standings: board('standings'), shuffle: spanOf('power-board', BOARD, 'shuffle'), feature: board('feature'), verdict: board('verdict'),
  four: close('four'), pull: spanOf('power-close', CLOSE, 'pull'), trophy: spanOf('power-close', CLOSE, 'trophy'),
  hops: spanOf('power-close', CLOSE, 'hops'), flyin: spanOf('power-close', CLOSE, 'flyin'), dive: spanOf('power-close', CLOSE, 'dive'), wave: close('wave'), identIn: close('identIn'), last: close('last'),
});
