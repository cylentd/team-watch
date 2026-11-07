import { POWER_CAMERA_DETAIL as TUNING } from './constants-power.mjs';
import { POWER_RIG } from "./constants-power.mjs";
export { POWER_RIG };

import { OPENING } from './constants.mjs';
import { seg } from './draft-motion.mjs';
import { drift } from './draft-camera.mjs';
import { TIMES } from './power-clock.mjs';
import { CAST, FALLBACK_FEATURE } from './power-cast.mjs';
import { powerPose } from './power-pose.mjs';
import { TIER, perch, plateCorners, stairs, stampCorners, trophyCorners } from './power-layout.mjs';
import { fitShot } from './power-frame.mjs';

/* Chapter 5's camera (docs/madden-film-chapter5.md, "Cinematic revision", camera column of both beat tables): a wide
   of the whole riser held over the standings and the shuffle, one push onto the feature plate, the top four, then
   the pull back to the riser and the summit where the trophy lands. Every shot is square-on with a slow drift
   (rule 19: 3 degrees at most, no roll), and frames its subjects whole inside a window that clears the headline and
   the controls (rules 22, 25, 26). Pure: shot(id, seconds) for the power beats, the contract in film-sets.mjs. */

const all = Array.from({length: TIER.places}, (_, index) => index + 1);
const cast = () => ({feature: CAST.feature ?? FALLBACK_FEATURE, leaders: CAST.leaders ?? TUNING.fallbackLeaderCount, standings: CAST.standings});
const posed = (time, mobile) => powerPose(time, false, cast(), mobile).plates;
const corners = (time, places, mobile) => { const plates = posed(time, mobile); return places.flatMap(place => plateCorners(place, plates[place - 1], mobile)); };
const up = (point, rise) => [point[0], point[1] + rise, point[2]];

function subjects(name, mobile) {
  const feature = cast().feature, [from, to] = TIMES.shuffle;
  if (name === 'wide') return POWER_RIG.shuffle.flatMap(share => corners(from + share * (to - from), all, mobile));
  if (name === 'feature') { const time = TIMES.verdict - TUNING.featurePreVerdictOffset, plate = posed(time, mobile)[feature - 1];
    return [...plateCorners(feature, plate, mobile), ...stampCorners(feature, plate, mobile)]; }
  if (name === 'four') return corners(TIMES.four + 1, all.slice(0, cast().leaders), mobile);
  if (name === 'hero') {
    const origin = perch(mobile), {radius, height} = POWER_RIG.hero;
    const blip = [-radius, radius].flatMap(x => [0, height].flatMap(y => [-radius, radius].map(z =>
      [origin[0] + x, origin[1] + y, origin[2] + z])));
    return [...trophyCorners(mobile), ...blip];
  }
  const path = stairs(mobile);
  return [...corners(TIMES.trophy[1], all, mobile), ...trophyCorners(mobile), ...path, ...path.map(point => up(point, POWER_RIG.blip))];
}

const CACHE = new Map();
function framed(name, ctx) {
  const device = ctx.mobile ? 'phone' : 'desk', aspect = ctx.size ? ctx.size.width / ctx.size.height : POWER_RIG.aspect[device];
  const key = `${name}:${device}:${aspect.toFixed(3)}`;
  if (!CACHE.has(key)) {
    const [left, right, bottom, top] = POWER_RIG.window[device][name], fov = ctx.mobile ? OPENING.phoneFov : OPENING.cameraFov;
    CACHE.set(key, fitShot(subjects(name, ctx.mobile), POWER_RIG.pitch[device][name], {left, right, bottom, top}, fov, aspect));
  }
  const view = CACHE.get(key);
  return {position: view.position.clone(), target: view.target.clone()};
}
const blend = (a, b, amount) => ({...a, position: a.position.clone().lerp(b.position, amount), target: a.target.clone().lerp(b.target, amount)});
// A sine ease in and out: its peak speed is half a cubic's, so the long moves stay smooth.
const inOutSine = value => (1 - Math.cos(Math.PI * value)) / 2;
const move = (time, end, length) => inOutSine(seg(time, end - length, end));

/* The view `seconds` into a power beat (film-sets.mjs contract). Negative seconds hold the beat's first frame. */
export const REDUCED = {clock: null};

export function shot(id, seconds, ctx) {
  if (REDUCED.clock !== null) {
    const time = REDUCED.clock;
    const name = time < TIMES.close ? (time < TIMES.feature ? 'wide' : 'feature')
      : time < TIMES.pull[1] ? 'four' : time < TIMES.flyin[1] ? 'close' : 'hero';
    return framed(name, ctx);
  }
  const board = id === 'power-board', start = board ? TIMES.board : TIMES.close, end = board ? TIMES.close : TIMES.end;
  const time = start + Math.max(0, seconds);
  let view;
  if (board) {
    view = blend(framed('wide', ctx), framed('feature', ctx), move(time, TIMES.feature, POWER_RIG.push));
  } else {
    // The travel from the feature arrives on the four half done; the four finish arriving over `settle` (rule 20).
    const arrive = POWER_RIG.early + (1 - POWER_RIG.early) * inOutSine(seg(time, TIMES.close, TIMES.close + POWER_RIG.settle));
    view = blend(framed('feature', ctx), framed('four', ctx), arrive);
    view = blend(view, framed('close', ctx), move(time, TIMES.pull[1], Math.max(POWER_RIG.pull, TIMES.pull[1] - TIMES.pull[0])));
  }
  const driftTime = board ? time : Math.min(time, TIMES.flyin[0]);
  view = drift(view, (driftTime - start) / (end - start), ctx.mobile, POWER_RIG.drift);
  if (board) return view;
  view = blend(view, framed('hero', ctx), move(time, TIMES.flyin[1], TIMES.flyin[1] - TIMES.flyin[0]));
  const finish = {target: view.target, position: view.target.clone().add(view.position.clone().sub(view.target).multiplyScalar(POWER_RIG.endDistance))};
  return blend(view, finish, move(time, TIMES.dive[1], TIMES.dive[1] - TIMES.dive[0]));
}

// The frame's lift (draft-camera.mjs RIG.lift): none, since each shot places its subjects in its own window.
export const lift = Object.freeze({desk: {'power-board': 0, 'power-close': 0}, phone: {'power-board': 0, 'power-close': 0}});
