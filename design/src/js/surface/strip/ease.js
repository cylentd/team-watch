/* ------------------------------------------------------------------
   STRIP EASING — the small maths the strip's motion is built on.

   Every one-shot motion in the strip is a PURE FUNCTION of how far through the play we are, never
   a wall-clock CSS animation. The difference only shows when someone scrubs: a CSS animation is
   already snapped to its end state if you pause early and stuck mid-swing if you jump in late,
   because it has been running against the clock rather than against the slider. Looping motion
   (a stride, a breath) is the opposite case and stays in CSS, where it costs nothing.
------------------------------------------------------------------ */

const stLerp = (a, b, f) => a + (b - a) * f;
const stClamp = (v, lo, hi) => Math.max(lo, Math.min(v, hi));

/* in-out cubic: a play starts and ends at rest, which is what a snap and a tackle look like */
const stEase = u => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
/* out-cubic, for the beat AFTER a play: a tackle carrying on, a ball settling, a return */
const stOut = u => 1 - Math.pow(1 - u, 3);

/* stEase is monotonic, so its inverse by bisection: which u puts the eased play at fraction f.
   This is what lets Play resume from wherever the scrubber was left without the figure jumping --
   it re-enters the same timing curve rather than restarting it. 24 halvings is well under a pixel. */
function stEaseInv(f){
  let lo = 0, hi = 1;
  for (let k = 0; k < 24; k++){
    const mid = (lo + hi) / 2;
    if (stEase(mid) < f) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
}

/* piecewise-linear through named stops: stStep(.4, [[0,12],[.3,45],[.55,-70],[1,-78]]) */
function stStep(u, stops){
  u = stClamp(u, 0, 1);
  for (let k = 1; k < stops.length; k++){
    if (u <= stops[k][0]){
      const [t0, a] = stops[k - 1], [t1, b] = stops[k];
      return stLerp(a, b, (u - t0) / (t1 - t0));
    }
  }
  return stops[stops.length - 1][1];
}

/* The placekick swing: plant, wind the kicking leg back, drive it through, hold the follow-through.
   u is KICK progress 0-1, not play progress. Signs are figure.css's: the figure faces right, so a
   negative hip swings the leg forward and a positive one back, a positive knee bends it heel-up, a
   positive torso leans forward, and a positive arm goes back. Getting this backwards draws a man
   kicking behind himself, which is exactly what the first version did. */
const stKickAngles = u => ({
  hip: stStep(u, [[0, 12], [.3, 45], [.55, -70], [1, -78]]),
  knee: stStep(u, [[0, 20], [.3, 95], [.55, 10], [1, 0]]),
  torso: stStep(u, [[0, -6], [.3, -12], [.55, 8], [1, 8]]),
  armFar: stStep(u, [[0, 20], [.3, 35], [.55, -45], [1, -45]]),
  armNear: stStep(u, [[0, -15], [.3, -25], [.55, 40], [1, 40]]),
});

const ST_REDUCED = matchMedia("(prefers-reduced-motion:reduce)").matches;
