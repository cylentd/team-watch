import { TIMELINE_DETAIL as TUNING } from './constants-playback.mjs';
import { OPENING, SHOW } from './constants.mjs';

export const clamp = value => Math.min(1, Math.max(0, value));
export const smooth = value => { const amount = clamp(value); return amount * amount * (TUNING.smoothstepCoefficient - 2 * amount); };
export const mix = (start, end, amount) => start + (end - start) * amount;

export function showMoment(seconds, reduced = false) {
  const elapsed = reduced ? SHOW.duration : Math.max(0, Math.min(SHOW.duration, seconds));
  const opening = openingMoment(elapsed);
  const inTeams = elapsed >= SHOW.teamsAt && elapsed < SHOW.castAt;
  const teamIndex = inTeams ? Math.floor((elapsed - SHOW.teamsAt) / SHOW.teamDuration) : -1;
  return {
    ...opening, elapsed, complete: elapsed === SHOW.duration,
    chapter: elapsed < SHOW.coldAt ? opening.chapter : elapsed < SHOW.teamsAt ? 'cold'
      : inTeams ? 'team' : elapsed < SHOW.finaleAt ? 'cast' : 'final',
    teamIndex, teamProgress: inTeams ? ((elapsed - SHOW.teamsAt) % SHOW.teamDuration) / SHOW.teamDuration : 0,
    hero: opening.logo * (1 - smooth((elapsed - SHOW.coldAt) / SHOW.titleDuration)),
    ensemble: smooth((elapsed - SHOW.castAt) / SHOW.castDuration),
    finalTitle: smooth((elapsed - SHOW.finaleAt) / SHOW.titleDuration),
  };
}

export function openingMoment(seconds, reduced = false) {
  const time = reduced ? OPENING.duration : Math.max(0, Math.min(OPENING.duration, seconds));
  return {
    time, complete: time === OPENING.duration,
    chapter: time < OPENING.blipAt ? 'trophy' : time < OPENING.logoAt - OPENING.logoDuration ? 'blip' : 'logo',
    pullback: smooth(time / OPENING.logoAt),
    blip: smooth((time - OPENING.blipAt) / OPENING.revealDuration),
    // The title forms in the beat before its hit and is whole on it (constants.mjs OPENING).
    logo: smooth((time - OPENING.logoAt + OPENING.logoDuration) / OPENING.logoDuration),
    sweep: Math.sin(Math.PI * clamp(time / OPENING.duration)),
  };
}
