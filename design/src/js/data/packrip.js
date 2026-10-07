/* The pack's rip screen (2026-10-07, David): the numbers behind two of its fixes, kept apart from the
   drawing (surface/teams/packshow.js, pack.js) so each is tested in Node.

   The torn flap lifts and tips with the tear a little, and the rest with the finger pulling up, so the
   tear feels held; a finger pushing down lifts nothing more. The foil flakes start on the strip, not at the
   top of the leaned pack's box, which stands above it. */

/* {lift, tilt}: px the flap rises and degrees it tips, for how far along the tear is (0..1) and how far the
   finger has moved up (dy < 0) or down since it touched. The tear alone gives at most 6px and 6deg, a full pull
   (PK_PULL_MAX px up) adds 24px and 14deg. */
const PK_PULL_MAX = 36;
function pkFlapPose(tear, dy){
  const pull = Math.min(Math.max(-dy, 0), PK_PULL_MAX) / PK_PULL_MAX;
  return {lift: Math.min(tear, .6) * 10 + pull * 24, tilt: Math.min(tear, .5) * 12 + pull * 14};
}

/* {x, y}: where flakes start for a strip's box ({left, top, width, height}) and the finger's x (null: the
   middle). The strip's middle height, and the finger's x held to the strip's ends. */
function pkFlakeOrigin(strip, x){
  const mid = strip.left + strip.width / 2;
  const at = typeof x === "number" ? Math.min(strip.left + strip.width, Math.max(strip.left, x)) : mid;
  return {x: at, y: strip.top + strip.height / 2};
}
