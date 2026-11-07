import SHEET from './timing.json' with { type: 'json' };

/* The film's timing sheet (timing.json): every beat's length, headline hold, camera move and the seconds of
   its sub-events, so a cut is re-timed by editing one number and reloading, with no code edit. The modules
   read their times from here; this checks the sheet's shape where it enters and fails loudly naming the
   beat, so a bad edit breaks the film's load, not a frame halfway through it. */
const NEEDS = ['id', 'duration', 'hold', 'events'];

export function checkTiming(sheet) {
  if (!Array.isArray(sheet?.beats) || !sheet.beats.length) throw new Error('timing.json: no beats list');
  sheet.beats.forEach((beat, index) => {
    const name = beat?.id ?? `beat ${index + 1}`;
    const missing = NEEDS.filter(key => beat?.[key] === undefined);
    if (missing.length) throw new Error(`timing.json: ${name} has no ${missing.join(', ')}`);
    if (!Array.isArray(beat.events)) throw new Error(`timing.json: ${name} events is not a list`);
    if (beat.chapter !== undefined && !Number.isInteger(beat.chapter)) throw new Error(`timing.json: ${name} chapter is not a whole number`);
    beat.events.forEach(event => {
      if (typeof event.name !== 'string' || (typeof event.at !== 'number' && !(typeof event.from === 'number' && typeof event.to === 'number')))
        throw new Error(`timing.json: ${name} has an event with no name, or no at / from and to`);
    });
  });
  const words = sheet.opening?.titleWords;
  if (!Array.isArray(words) || !words.length || words.some((at, index) => typeof at !== 'number' || (index && at <= words[index - 1])))
    throw new Error('timing.json: opening.titleWords is not a rising list of film seconds');
  if (typeof sheet.opening.duration !== 'number' || sheet.opening.duration <= words[words.length - 1])
    throw new Error('timing.json: opening.duration is not a number of seconds after the last title word');
  const handover = sheet.opening.handover;
  if (!handover || ['from', 'flare', 'fade'].some(key => typeof handover[key] !== 'number')
      || handover.from <= words[words.length - 1] || handover.from >= sheet.opening.duration)
    throw new Error('timing.json: opening.handover needs from (between the last title word and the board), flare and fade');
  return sheet;
}

export const TIMING = Object.freeze(checkTiming(SHEET));
/* The film second each title word lands (film-title-drop.mjs), in the copy's word order. */
export const TITLE_WORDS = Object.freeze([...TIMING.opening.titleWords]);
const BEATS = Object.fromEntries(TIMING.beats.map(beat => [beat.id, beat]));

/* One beat's entry. */
export function beatTiming(id) {
  if (!BEATS[id]) throw new Error(`timing.json: no beat ${id}`);
  return BEATS[id];
}

function find(id, name) {
  const event = beatTiming(id).events.find(entry => entry.name === name);
  if (!event) throw new Error(`timing.json: ${id} has no ${name} event`);
  return event;
}

/* An event's moment: its `at`, or the end of its span (when it lands). */
export const at = (id, name) => { const event = find(id, name); return event.at ?? event.to; };
/* An event's span, [from, to]. */
export const span = (id, name) => { const event = find(id, name); return Object.freeze([event.from, event.to]); };
/* Every moment of a repeated event, in order (the curse's stops). */
export const ats = (id, name) => Object.freeze(beatTiming(id).events.filter(event => event.name === name).map(event => event.at ?? event.to));
/* A beat's own number outside its events (the curse's `move`, `minHold`). */
export function param(id, name) {
  const value = beatTiming(id)[name];
  if (value === undefined) throw new Error(`timing.json: ${id} has no ${name}`);
  return value;
}
/* Every impact the sheet marks with `hit`, in beat seconds. */
export const sheetHits = () => TIMING.beats.flatMap(beat => beat.events.filter(event => event.hit)
  .map(event => ({beat: beat.id, name: event.label ?? event.name, at: event.at ?? event.to})));
