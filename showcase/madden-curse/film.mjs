import { FILM, TRANSITION } from './constants.mjs';
import { openingMoment, smooth } from './timeline.mjs';
import { at } from './timing.mjs';

/* The midseason film: the trophy opening, Chapter 1 on the draft board, then Chapter 2's trades card, and on to Chapter 5's power rankings (ends at 98.077). Pure, so Node tests it and every frame
   is a function of the clock (seek, pause and the MP4 export all draw the same picture). */
let plan;
export function filmPlan() {
  if (plan) return plan;
  let start = FILM.chapterAt;
  const beats = FILM.beats.map(beat => { const placed = {...beat, start}; start += beat.duration; return placed; });
  plan = {chapterAt: FILM.chapterAt, duration: start, beats};
  return plan;
}

/* A moment's `chapter` by the beat's film chapter (timing.json `chapter`): the draft board, then the trades card
   (docs/madden-film-chapter2.md), which has no lower third and no 3D board of its own. */
export const CHAPTERS = Object.freeze({1: 'draft', 2: 'trades', 3: 'waivers', 4: 'lineups', 5: 'power'});
/* Whether two beats share a scene the board's camera can blend between (draft-camera.mjs). */
export const sameChapter = (first, second) => Boolean(first && second) && first.chapter === second.chapter;

/* The film second a beat's stat lands: its motion second, slowed by the beat's pace. */
export const statAt = beat => beat.stat === null ? null : beat.start + beat.stat * beat.pace;

/* The beats the camera travels into on the same board, with no wipe and no whip: the board stands and the camera
   moves on to Golden's card, then card to card (ch17, coordinator for David; draft-camera.mjs travel).
   ~~A whip and a light sweep into every beat~~ (rule 18, rev 9). `power-board` is the crane from Chapter 4's bench
   rack onto Chapter 5's riser, the one travel across chapters (docs/madden-film-chapter5.md, 2026-11-05). */
export const TRAVEL = Object.freeze(['steal', 'traded', 'sleeper', 'waiver-starts', 'lineup-tightends', 'power-board', 'power-close']);

/* Every scene change in the film (rule 18): the opening's hand-over to the board, then each beat's start.
   The opening's is a zoom into the trophy's ball that whites out into the board (film-zoom.mjs; ~~a light
   sweeping down into the board~~, ch17); a change of scene (to the curse's floor, back to the
   board, the finale's pull-back) sweeps across with a camera whip; a beat on the same board is a `travel`. */
export function sceneChanges() {
  const {chapterAt, beats} = filmPlan();
  return [{at: chapterAt, kind: 'zoom', to: beats[0].id, window: TRANSITION.intro},
    ...beats.slice(1).map(beat => ({at: beat.start, kind: TRAVEL.includes(beat.id) ? 'travel' : 'across', to: beat.id,
      window: TRANSITION.window}))];
}

/* The wipe under way at `elapsed`, 0..1 across its window (.5 on the bar line), or null; a travel has none. */
export function transitionAt(elapsed) {
  const change = sceneChanges().find(({at, window, kind}) => kind !== 'travel' && Math.abs(elapsed - at) < window / 2);
  return change ? {...change, amount: (elapsed - change.at + change.window / 2) / change.window} : null;
}

export function filmMoment(seconds, reduced = false) {
  const {chapterAt, duration, beats} = filmPlan();
  const elapsed = Math.max(0, Math.min(duration, seconds));
  const opening = openingMoment(elapsed, reduced);
  // The title leaves as the light sweeps down over it, gone on the bar line, where the board's headline lands.
  const half = FILM.handoff / 2;
  const base = {...opening, elapsed, complete: elapsed === duration, beat: null, beatIndex: -1,
    beatProgress: 0, headline: null, headlineAge: 0, statAge: 0, transition: reduced ? null : transitionAt(elapsed),
    hero: opening.logo * (1 - smooth((elapsed - chapterAt + half) / half))};
  if (elapsed < chapterAt) return base;
  const index = Math.max(0, beats.findLastIndex(beat => elapsed >= beat.start));
  const beat = beats[index], stat = statAt(beat);
  const progress = reduced ? 1 : Math.min(1, (elapsed - beat.start) / beat.duration);
  const reveal = beat.id === 'board' ? at('board', 'stand') * beat.pace : 0;
  const headlineAge = elapsed - beat.start - reveal;
  return {...base, chapter: CHAPTERS[beat.chapter], beat: beat.id, beatIndex: index, beatProgress: progress,
    headline: reduced || headlineAge >= 0 ? beat.id : null, headlineAge: reduced ? duration : headlineAge,
    statAge: reduced ? duration : stat === null ? 0 : elapsed - stat};
}
