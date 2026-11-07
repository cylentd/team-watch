import { OPENING } from './constants.mjs';
import { HANDOVER } from './film-zoom.mjs';
import { filmPlan } from './film.mjs';
import { at, span } from './timing.mjs';
import { outBack } from './draft-motion.mjs';

/* The TEAM WATCH tag is an ident, not a bug in the corner (ch17, David): it shows in the opening, in from the
   first frame and out with the zoom into the trophy. Every beat after it has no tag (David, 2026-11-05: it left
   Chapter 1's finale and returns on the last chapter's final seconds: Chapter 5's `ident` event, held to the end).
   ~~In again in the finale's last seconds, with the class total~~ (Chapter 1, 2026-11-04). Pure, so stills and
   exports draw the same. */
export const IDENT = Object.freeze({fade: .25});   // seconds the tag takes to come in

/* The beat whose `ident` span (timing.json) brings the tag back, then holds it to the film's end
   (David, 2026-11-05; docs/madden-film-chapter5.md). */
const CLOSE_BEAT = 'power-close';

const clamp =value => Math.min(1, Math.max(0, value));

/* The tag's opacity at film second `time`, 0..1. */
export function identAt(time) {
  const [from, to] = span(CLOSE_BEAT, 'ident');
  const start = filmPlan().beats.find(beat => beat.id === CLOSE_BEAT).start;
  if (time >= start + from) return clamp((time - start - from) / (to - from));
  if (time >= OPENING.duration) return 0;
  return clamp(time / IDENT.fade) * (1 - clamp((time - HANDOVER.from) / (OPENING.duration - HANDOVER.from)));
}

/* The ident lands on the song's last hit (power-close `last`, 97.59): the tag settles from 104% with an outBack
   over 0.3 s (docs/madden-film-chapter5.md, power-close beat table). */
export const IDENT_LAND = Object.freeze({from: 1.04, settle: .3});

/* The tag at film second `time`: its opacity (identAt) and its scale. */
export function identPose(time) {
  const lands = filmPlan().beats.find(beat => beat.id === CLOSE_BEAT).start + at(CLOSE_BEAT, 'last');
  const amount = (time - lands) / IDENT_LAND.settle;
  const scale = amount < 0 || amount >= 1 ? 1 : IDENT_LAND.from + (1 - IDENT_LAND.from) * outBack(amount);
  return {opacity: identAt(time), scale};
}

export function endcardPose(time, reduced = false) {
  const start = filmPlan().beats.find(beat => beat.id === CLOSE_BEAT).start;
  const absolute = value => Math.round((start + value) * OPENING.milliseconds) / OPENING.milliseconds;
  const [blackFrom, blackTo] = span(CLOSE_BEAT, 'blackout').map(absolute);
  const [logoFrom, logoTo] = span(CLOSE_BEAT, 'endLogo').map(absolute);
  const black = clamp((time - blackFrom) / (blackTo - blackFrom));
  const logo = clamp((time - logoFrom) / (logoTo - logoFrom));
  return {active: time >= blackFrom, black: reduced ? Number(time >= blackTo) : black * black,
    logo: reduced ? Number(time >= logoTo) : logo};
}

export function winkAt(time, reduced = false) {
  if (reduced) return 0;
  const start = filmPlan().beats.find(beat => beat.id === CLOSE_BEAT).start;
  const [from, to] = span(CLOSE_BEAT, 'wink');
  const progress = clamp((time - start - from) / (to - from));
  return progress <= 0 || progress >= 1 ? 0 : Math.sin(Math.PI * progress) ** 2;
}
