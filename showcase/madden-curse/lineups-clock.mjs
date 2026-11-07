import { FRAME } from "./constants-lineups.mjs";
export { FRAME };
import { filmPlan } from './film.mjs';
import { at, beatTiming, span } from './timing.mjs';

/* Chapter 4's moments in chapter seconds (0 is film 62.077, the first beat's bar line), read from the timing sheet
   (timing.json `lineup-defense`, `lineup-tightends`), so the pose, the camera and the headline share one clock
   (rule 4). `crane` appears twice in the sheet, so its spans are read by filter, not `span`. */
const beat = id => filmPlan().beats.find(entry => entry.id === id);
const DEFENSE = beat('lineup-defense'), TIGHTENDS = beat('lineup-tightends');
const SECOND = TIGHTENDS.start - DEFENSE.start;   // the second beat's bar line on the chapter clock
const defense = name => at('lineup-defense', name), tight = name => SECOND + at('lineup-tightends', name);
const tightSpan = name => span('lineup-tightends', name).map(value => SECOND + value);
const cranes = beatTiming('lineup-tightends').events.filter(event => event.name === 'crane')
  .map(event => Object.freeze([SECOND + event.from, SECOND + event.to]));

export const CLOCK = Object.freeze({
  start: DEFENSE.start, second: SECOND, end: SECOND + TIGHTENDS.duration,
  fall: at('lineup-defense', 'saints') - span('lineup-defense', 'saints')[0],   // 0.35 s, the shield's drop
  landings: Object.freeze(['saints', 'raiders'].map(defense)),
  wins: Object.freeze([defense('saintsWin'), defense('outcome')]),
  peek: span('lineup-defense', 'peek'), track: span('lineup-defense', 'track'), outcome: defense('outcome'),
  players: tight('players5'), bench5: tight('bench5'), switch: Object.freeze(tightSpan('switch')),
  swap: tight('swap'), starter8: tight('starter8'), bench8: tight('bench8'), cranes: Object.freeze(cranes),
});

/* The chapter clock at film second `time`. */
export const chapterSeconds = time => time - CLOCK.start;
