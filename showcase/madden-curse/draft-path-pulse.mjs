import { PATH_BEAM } from "./constants-draft-motion.mjs";
export { PATH_BEAM };
import { ESTABLISH, passLook } from './draft-establish.mjs';
import { columnX, rowY } from "./draft-board.mjs";
import { MOBILE_FRAME } from './draft-mobile-framing.mjs';
import { ONSETS, filmTime } from './music-onsets.mjs';
import { TIMING } from './timing.mjs';
import { CELL } from './draft-textures.mjs';

   // the band sits this far off the card face, so the two never z-fight

/* A card's light `age` seconds after it fires, 0 to 1: a near-instant attack, a short hold, a quadratic decay. */
export function beamPulse(age) {
  if (!(age >= 0)) return 0;
  if (age < PATH_BEAM.rise) return 1 - (1 - age / PATH_BEAM.rise) ** 2;
  const fade = (age - PATH_BEAM.rise - PATH_BEAM.hold) / PATH_BEAM.fade;
  return fade <= 0 ? 1 : fade >= 1 ? 0 : (1 - fade) ** 2;
}

export function beamTrail(age) {
  return age >= 0 ? 1 - (1 - Math.min(1, age / PATH_BEAM.rise)) ** 2 : 0;
}

function trigger(home, mobile) {
  let closest = Infinity, when = 0;
  for (let index = 0; index <= PATH_BEAM.samples; index++) {
    const time = ESTABLISH.move * index / PATH_BEAM.samples, point = passLook(time, mobile);
    const offset = mobile ? ESTABLISH.height.phone / Math.tan(ESTABLISH.pitch) * MOBILE_FRAME.lightFocus : 0;
    const distance = Math.hypot(home.x - point.x + offset * Math.sin(ESTABLISH.yaw),
      home.y - point.along + offset * Math.cos(ESTABLISH.yaw));
    if (distance < closest) { closest = distance; when = time; }
  }
  return closest <= PATH_BEAM.corridor ? when - PATH_BEAM.lead : Infinity;
}

const ACCENTS = new Map(), TRIGGERS = new Map();
const keyOf = home => home.x + '|' + home.y;

function accentTimes(mobile) {
  if (ACCENTS.has(mobile)) return ACCENTS.get(mobile);
  const cards = Array.from({length: CELL.columns * CELL.rows}, (_, index) => {
    const home = {x: columnX(index % CELL.columns), y: rowY(Math.floor(index / CELL.columns))};
    return {home, peak: trigger(home, mobile) + PATH_BEAM.rise};
  }).filter(card => Number.isFinite(card.peak));
  const selected = new Map();
  const cues = ONSETS.map(filmTime).map(time => time - TIMING.opening.duration)
    .filter(time => time > PATH_BEAM.maxShift && time < ESTABLISH.stand[0]);
  cues.forEach(cue => {
    const nearest = cards.filter(card => !selected.has(keyOf(card.home)))
      .sort((first, second) => Math.abs(first.peak - cue) - Math.abs(second.peak - cue))[0];
    if (nearest && Math.abs(nearest.peak - cue) <= PATH_BEAM.maxShift)
      selected.set(keyOf(nearest.home), cue - PATH_BEAM.rise);
  });
  ACCENTS.set(mobile, selected);
  return selected;
}

export function beamTrigger(home, mobile) {
  const key = keyOf(home) + '|' + mobile;
  if (!TRIGGERS.has(key)) TRIGGERS.set(key, accentTimes(mobile).get(keyOf(home)) ?? trigger(home, mobile));
  return TRIGGERS.get(key);
}

export const beamAccent = (home, mobile) => accentTimes(mobile).has(keyOf(home)) ? PATH_BEAM.accent : 1;
