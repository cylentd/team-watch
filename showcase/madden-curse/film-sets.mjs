import { TRANSITION } from './constants.mjs';
import { CHAPTERS, filmPlan } from './film.mjs';

/* The 3D sets the later chapters draw in the room after Chapter 1's board (docs/madden-film-chapter4.md and
   docs/madden-film-chapter5.md, "Cinematic revision", David 2026-11-05). The contract, for a set's author:

   registerSet(chapter, factory, camera)
     chapter  the CHAPTERS name of its beats: 'lineups' (Chapter 4) or 'power' (Chapter 5).
     factory  (scene, context) => {update(moment, ctx), hide(), dispose(), ready: Promise, warmAt: [film seconds]}.
              Built once by makeDraft (draft.mjs) after the board; context is {draft, teams, board, table, ground}.
              update returns {shake} or nothing; ctx is {camera, mobile, blip, size}. A set may hide context.table
              (the board's wall); Chapter 1's pose shows it again. dispose frees its geometry, materials, textures.
     camera   {shot(id, seconds, ctx) => {position, target, up?}, lift: {desk: {[id]: share}, phone: {[id]: share}}},
              pure, like draft-camera.mjs `shot` and `RIG.lift`; the camera calls it for the set's beats.
   A set's local clock is `moment.elapsed - beat.start` (activeSets below hands it over as `seconds`). It may be
   negative: an object that lands on a beat's first frame falls during the incoming whip or travel. So a set is
   updated whenever its chapter is current OR the film is within half a transition window of one of its beats'
   edges (a whip's `moment.transition.to` is one of its beats, or a travel crosses into or out of it), and is
   hidden every other frame. shot(id, seconds) sees the same negative seconds while the camera whips in from a
   chapter with no set. Every pose is a pure function of film time, so seeking either way rebuilds it. */
const REGISTRY = new Map();

export function registerSet(chapter, factory, camera = {}) {
  if (!Object.values(CHAPTERS).includes(chapter) || chapter === CHAPTERS[1]) throw new Error(`film-sets: no later chapter ${chapter}`);
  REGISTRY.set(chapter, Object.freeze({chapter, factory, shot: camera.shot, lift: camera.lift ?? {}}));
}
export const setFor = chapter => REGISTRY.get(chapter);
/* The chapters the room draws in 3D: the board, then every registered set. */
export const drawnChapters = () => [CHAPTERS[1], ...REGISTRY.keys()];
/* A beat's chapter name, or undefined. */
export const chapterOf = id => { const beat = filmPlan().beats.find(entry => entry.id === id); return beat && CHAPTERS[beat.chapter]; };
/* A beat's set, when its chapter has one. */
export const setOfBeat = id => setFor(chapterOf(id));

/* Every registered set this moment shows, the current chapter's first: {chapter, beat, seconds} with the set's own
   beat and its local clock (the contract above). */
export function activeSets(moment) {
  const beats = filmPlan().beats, time = moment.elapsed, half = TRANSITION.window / 2, current = moment.chapter;
  const shown = [...REGISTRY.keys()].filter(chapter => {
    if (chapter === current) return true;
    const own = beats.filter(beat => CHAPTERS[beat.chapter] === chapter);
    return own.some(beat => Math.abs(time - beat.start) < half || Math.abs(time - beat.start - beat.duration) < half);
  }).sort((first, second) => (second === current) - (first === current));
  return shown.map(chapter => {
    const own = beats.filter(beat => CHAPTERS[beat.chapter] === chapter);
    const beat = own.findLast(entry => time >= entry.start) ?? own[0];
    return {chapter, beat: beat.id, seconds: time - beat.start};
  });
}

/* Whether the room draws its 3D path for this moment: the board, or a set that shows (activeSets). */
export const roomDraws = moment => moment.chapter === CHAPTERS[1] || activeSets(moment).length > 0;

/* Build every registered set into `scene` (makeDraft); `update` poses the ones that show and hides the rest,
   returning the current set's result (or {}), or null when no set shows. */
export function buildSets(scene, context) {
  const built = [...REGISTRY.values()].map(entry => ({chapter: entry.chapter, set: entry.factory(scene, context)}));
  return {
    ready: Promise.all(built.map(({set}) => set.ready)),
    warmAt: built.flatMap(({set}) => set.warmAt ?? []),
    update(moment, ctx) {
      const shown = activeSets(moment).map(entry => entry.chapter);
      let result = null;
      built.forEach(({chapter, set}) => {
        if (!shown.includes(chapter)) return set.hide();
        const own = set.update(moment, ctx) ?? {};
        if (chapter === shown[0]) result = own;
      });
      return result;
    },
    hide: () => built.forEach(({set}) => set.hide()),
    dispose: () => built.forEach(({set}) => set.dispose()),
  };
}
