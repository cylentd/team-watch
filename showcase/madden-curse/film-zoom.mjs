import { FILM_ZOOM_DETAIL as TUNING } from './constants-title.mjs';
import * as THREE from 'three';
import { OPENING } from './constants.mjs';
import { TIMING } from './timing.mjs';
import { clamp } from './timeline.mjs';

/* The opening's hand-over (David, chapter 17): from the fanfare's last hit the camera pushes fast and straight
   into the trophy's ball, easing in, while the title and tagline slide out of frame. The chrome's reflection
   fills the screen and the frame goes near white on the guitar's entry, where the board starts; the white
   then fades, so the board's fly-by starts from inside the flare. Zero roll, one straight dolly. The times
   and the flare live in timing.json `opening.handover`. ~~A light sweeping down into the board~~ (rule 18,
   revision 9). */
export const HANDOVER = Object.freeze({...TIMING.opening.handover,
  ease: TUNING.easeExponent,          // the push's ease-in power: slow off the hold, fastest into the chrome
  stop: TUNING.stopDistance,        // world units from the ball's centre where the push ends, just off its chrome
  rise: 2,          // the flare's ease-in power: it whites out late, as the chrome fills the frame
  slide: TUNING.titleSlide,        // frame heights the title drops out of frame by the board's first frame
});

/* 0..1 through the push: 0 until the fanfare's last hit, 1 on the board's first frame. */
export const zoomAmount = time => clamp((time - HANDOVER.from) / (OPENING.duration - HANDOVER.from)) ** HANDOVER.ease;

/* The white over the frame, 0..1: rising into the board's first frame, then fading over `fade`. */
export function flareAt(time) {
  if (time < OPENING.duration) return HANDOVER.flare * clamp((time - OPENING.duration + HANDOVER.flashIn) / HANDOVER.flashIn) ** HANDOVER.rise;
  return HANDOVER.flare * clamp(1 - (time - OPENING.duration) / HANDOVER.fade);
}

const end = new THREE.Vector3(), look = new THREE.Vector3();
/* The camera `time` seconds into the film, pushing from `start` (where the hold left it) along the straight line
   into `ball`, its aim turning from `aim` onto the ball. Up stays world up, so the camera never rolls. */
export function handoverCamera(time, start, aim, ball) {
  const amount = zoomAmount(time);
  end.copy(start).sub(ball).setLength(HANDOVER.stop).add(ball);
  look.copy(aim).lerp(ball, clamp(amount * HANDOVER.ease));
  return {position: start.clone().lerp(end, amount), target: look.clone(), amount};
}
