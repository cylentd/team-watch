import { FILM_IMPACTS_DETAIL as TUNING } from './constants-playback.mjs';
import { OPENING } from './constants.mjs';
import { filmPlan, sceneChanges } from './film.mjs';
import { ONSETS, SYNC, BEAT, BAR, bar, filmTime } from './music-onsets.mjs';
import { HOP } from './blip-hop.mjs';
import { HOP_START } from './scene.mjs';
import { TITLE_WORDS, sheetHits } from './timing.mjs';

/* Every impact in the film, in film seconds (rule 16): Blip's landings, the title and every scene change from
   the constants, then each beat's stamp, landing, cut and flip from the timing sheet's `hit` events, the same
   numbers the animation runs on. */
export function filmImpacts() {
  const beats = Object.fromEntries(filmPlan().beats.map(beat => [beat.id, beat]));
  const at = (id, motion) => beats[id].start + motion * beats[id].pace;
  const hopLength = OPENING.revealDuration / OPENING.hops;
  return [
    {name: 'Trophy nudge', at: OPENING.nudgeAt},
    ...Array.from({length: OPENING.hops}, (_, index) => ({name: `Blip lands ${index + 1}`,
      at: HOP_START + hopLength * (index + 1 - HOP.land)})),
    ...TITLE_WORDS.map((at, index) => ({name: `Title word ${index + 1} lands`, at})),
    ...sceneChanges().map(change => ({name: `Cut to ${change.to}`, at: change.at})),
    ...sheetHits().map(hit => ({name: hit.name, at: at(hit.beat, hit.at)})),
  ];
}

/* The nearest onset, downbeat or documented Saints entrance beat, in film seconds and export frames. */
export function nearestHit(time) {
  const onsets = ONSETS.map(filmTime);
  const downbeats = Array.from({length: Math.ceil(filmPlan().duration / 2) + TUNING.downbeatPadding}, (_, index) => bar(index - 2));
  const entrance = filmPlan().beats.find(beat => beat.id === 'lineup-defense');
  const entranceBeat = entrance ? bar(0) + Math.round((entrance.start + BAR / 2 - bar(0)) / BEAT) * BEAT : null;
  const hits = [...onsets.map(at => ({at, kind: 'onset'})), ...downbeats.map(at => ({at, kind: 'downbeat'})),
    ...(entranceBeat === null ? [] : [{at: entranceBeat, kind: 'beat'}])];
  const best = hits.reduce((near, hit) => Math.abs(hit.at - time) < Math.abs(near.at - time) ? hit : near);
  return {...best, frames: +((time - best.at) * SYNC.fps).toFixed(2)};
}
