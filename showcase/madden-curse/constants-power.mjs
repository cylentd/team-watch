import * as THREE from "three";
import { SYNC } from "./constants-music.mjs";
import { GLINT } from "./constants-title.mjs";

export const POWER_CAMERA_DEG = THREE.MathUtils.degToRad;
export const POWER_RIG = Object.freeze({
  // Pitch down per shot, radians: shallow for the plates' faces, steeper where a tier sits behind another.
  pitch: {desk: {wide: POWER_CAMERA_DEG(12), feature: POWER_CAMERA_DEG(8), four: POWER_CAMERA_DEG(12), close: POWER_CAMERA_DEG(16), hero: POWER_CAMERA_DEG(8)},
    phone: {wide: POWER_CAMERA_DEG(18), feature: POWER_CAMERA_DEG(10), four: POWER_CAMERA_DEG(18), close: POWER_CAMERA_DEG(18), hero: POWER_CAMERA_DEG(10)}},
  // NDC windows: the desktop's headline sits at the upper left and the controls along the foot (rule 25), so
  // subjects stay below it and above -0.7; the phone's headline sits above the subject (rule 26), so its riser
  // takes the frame from the controls to under the headline: two-thirds of the height, its names at 2% (rule 23).
  window: {desk: {wide: [-.84, .84, -.66, .4], feature: [-.55, .86, -.64, .42], four: [-.72, .72, -.62, .5], close: [-.86, .86, -.7, .36], hero: [-.86, .86, -.7, .46]},
    phone: {wide: [-.94, .94, -.8, .56], feature: [-.96, .96, -.62, .46], four: [-.88, .88, -.7, .5], close: [-.94, .94, -.8, .5], hero: [-.94, .94, -.7, .46]}},
  // Seconds each move takes, ending on its hit. The push leaves half a second after the shuffle lands; the pull is
  // the sheet's (timing.json `pull`) unless that would move the camera more than half a unit a frame (rule 20).
  push: 1.5, pull: 1.1, settle: .45, early: .6,
  drift: .03,                                    // each beat pushes in 3% of its distance as it drifts
  hero: {radius: .3, height: .6}, endDistance: .08,
  blip: .5,                                      // Blip stands about this tall on the riser, world units
  aspect: {desk: 16 / 9, phone: 390 / 844},      // a caller with no size: the review sizes
  // The film seconds whose plates the wide frames: the standings landed, the shuffle's widest arcs, the power order.
  shuffle: [0, .35, .5, .65, 1],
});
export const EDITION = Object.freeze({season: 2026, league: 75203, through: 8, teams: 12,
  comparisons: 88,        // 11 opponents a week over 8 weeks
  games: 8});
export const DRESS = Object.freeze({
  // The wings' reach: the riser's half-width and its height with the trophy, as Chapter 1's card homes (makeBoardStage
  // reads the cards' extent): x is the outer column's centre, y the lowest and highest card centre.
  wings: {desk: {x: 2.9, low: .33, high: 2.7}, phone: {x: 1.45, low: .33, high: 3.95}},
  wall: {level: .45, wave: .5, size: [1.7, 1.5]},     // the back wall's light, and how much the wave adds to it
  pool: {level: .16, size: [9, 5], z: 1.6},          // the floor's key pool, world units, centred this far ahead of the riser
  haze: {z: 1.4},
  rim: {intensity: 2.4, position: [0, 4.5, -4]},
  // The stadium lights: where they hang (above frame, behind the riser), where they point before the trophy (the
  // riser's two ends), their cone, opacity and the spotlight that rides with them.
  beams: {desk: [[-2.4, 7.5, -1.5], [2.4, 7.5, -1.5]], phone: [[-1.3, 8.5, -1.2], [1.3, 8.5, -1.2]], radius: .45,
    opacity: .09, swing: 1.2, spot: {intensity: 9, angle: .3, penumbra: .7}},
});
export const FRAME = 1 / SYNC.fps;
export const HEADLINE = Object.freeze({enter: 10 * FRAME, leave: 4 * FRAME,
  closeOut: .177,   // storyboard: a headline leaves 0.177 s before the next move lands ("apart" 89.9, "close" 95.9)
  glint: .45});
export const RISER = Object.freeze({
  // The riser stands on the footprint of Chapter 1's board wall (draft-board.mjs: twelve columns centred on x 0 at
  // z 0), a little in front of it, behind Chapter 4's desk and its bench rack. The wall hides while the riser shows.
  position: Object.freeze([0, 0, .6]),
  // A plate is portrait, 3:4 (the storyboard's "same face layout as the Chapter 1 cards", 128 x 168 is near 3:4).
  plate: Object.freeze({width: .6, height: .8, depth: .06}),
  // The slot block at each plate's foot carries its place numeral; the piston shows `rest` above it while seated.
  lip: Object.freeze({height: .16, depth: .3, width: .7}), rest: .02, piston: .035,
  // Desktop: two stepped tiers of six side by side; the back one is high enough that its numerals clear the front plates.
  desk: Object.freeze({pitch: .78, depth: .9, front: {top: .45, z: 1}, back: {top: 1.5, z: 0}}),
  // Phone: four steps of three, rise and depth chosen so a row clears the row in front of it from the phone camera's
  // ~18 degree pitch (rise x cos + depth x sin is at least plate + lip, x cos).
  phone: Object.freeze({pitch: .74, rise: .9, step: .55, gap: .22, base: .25, columns: 3}),
  // The summit: the riser's crown behind its top row, where the trophy lands (David, 2026-11-05: "The trophy
  // returns"). `x` is its centre, the trophy stands at x 0 and Blip perches at `perch`; `clear` is how far its top
  // stands above the top row's plates, so a seated plate never hides the trophy's foot.
  summit: Object.freeze({desk: {x: .35, width: 1.9, depth: .5, perch: .75}, phone: {x: .25, width: 1.5, depth: .45, perch: .6}, clear: .02, gap: .05}),
  // Blip's stair at the riser's right end: two blocks at the height of two steps, then the summit (three hops).
  stair: Object.freeze({width: .5, depth: .3, gap: .1, steps: {desk: [0, 1], phone: [1, 2]}, ahead: .55}),
  blip: .42,   // Blip's scale on the riser: about half a plate tall
});
export const PLATE_FACE = Object.freeze({
  badge: {size: .28, y: .215}, name: {width: .56, height: .20, y: 0}, record: {width: .56, height: .14, y: -.165},
  actual: {width: .44, height: .055, y: -.3}, lift: .012,
  // The feature's two stamps (power-props.mjs): "#3 power" over the plate's top edge, "4-4 actual" over its W-L.
  stamps: {width: .364, height: .182, power: {x: .13, y: .36}, actual: {x: 0, y: -.3}, ahead: .012},
});
export const POSE_FORWARD = .3;
export const POSE = Object.freeze({
  fall: .35, drop: 3.2, squash: .06, squashFor: 3 * FRAME,   // storyboard: 0.35 s outExpo from above frame, 6% squash
  pops: Object.freeze([0, 4 * FRAME, 8 * FRAME]), pop: 4 * FRAME,   // badge, name, record last, 3-5 frames apart
  swap: 6 * FRAME,                                                    // the all-play record pops in on the landing
  strip: {flash: 3 * FRAME, settle: .5, rest: .8},                    // tier strips light, then settle to 80%
  forward: POSE_FORWARD, slide: .3, soft: .4, softFor: .3, seat: .3, // Sausage's plate slides 0.3 out; the rest soften to 40%
  stamp: 5 * FRAME, stampLag: 4 * FRAME, shrink: .25,                // "#3 power", then "4-4 actual"; both go on the four
  lift: .25, notch: .08, liftFor: .35, dimSink: .1,                  // pistons: 0.25 plate heights, Jaxon a 0.08 notch higher
  clear: .3, climb: .5,                                              // Blip's hop clears a step by 0.3 plus half its rise
  dim: .4, dimFor: .5, wave: 1.5, shake: .025, thud: 1.6,            // the trophy's landing shakes 1.6 times a tier's
});
export const FACE = Object.freeze({
  numeral: .13, strip: .03,        // the numeral's square and the strip's thickness, world units
  stripGlow: 1.6,                  // the strip's colour at full light, over its token (a light, not paint)
});
export const TROPHY = Object.freeze({height: 1.25, radius: .32, fall: 4.5, spin: 1.4, ball: 3.55, model: 4.1});
export const POWER_SET = Object.freeze({
  // Each hit's dust and ring, in world units (film-impact.mjs scales by `unit`): the plates land hard, the shuffle
  // settles with a small one, the trophy lands hardest with sparks, Blip's landing puffs dust only (storyboard).
  tier: {unit: 1.4, hit: {ring: .8, sparks: .3, dust: 1, tone: 'ink', second: 0, carpet: false}},
  order: {unit: .9, hit: {ring: .4, sparks: 0, dust: .5, tone: 'ink', second: 0, carpet: false}},
  trophy: {unit: 1.2, hit: {ring: 1, sparks: 1, dust: 1, tone: 'lime', second: 0, carpet: false}},
  blip: {unit: .7, hit: {ring: 0, sparks: 0, dust: .7, tone: 'ink', second: 0, carpet: false}},
  glint: GLINT.trophy * TROPHY.height / TROPHY.model,   // the opening's glint, at the trophy's scale on the riser
  warm: .1,   // seconds after each hit the scene compiles a frame (scene.mjs warmAt)
});
export const SHEET = Object.freeze({badge: 128, ring: 6, numeral: 128, numeralSize: 104, border: 10,
  face: {size: 256, band: 7, print: .47, edge: 3},             // the rim band, where the print block starts, the inner edge
  line: {width: 512, height: 128, size: 112, margin: 24},       // the record: the display face filling its line
  small: {width: 512, height: 64, size: 52, margin: 16}});

// Preserved power-camera.mjs configuration from the approved film cut.
export const POWER_CAMERA_DETAIL = Object.freeze({
  fallbackLeaderCount: 4,
  featurePreVerdictOffset: 0.01,
});

// Preserved power-dress.mjs configuration from the approved film cut.
export const POWER_DRESS_DETAIL = Object.freeze({
  coneSegments: 32,
  coneApexOffset: -0.5,
  poolY: 0.004,
});

// Preserved power-frame.mjs configuration from the approved film cut.
export const POWER_FRAME_DETAIL = Object.freeze({
  midpoint: 0.5,
});

// Preserved power-pose.mjs configuration from the approved film cut.
export const POWER_POSE_DETAIL = Object.freeze({
  expoSlope: -10,
  cubicExponent: 3,
  landingSearchIterations: 40,
});

// Preserved power-props.mjs configuration from the approved film cut.
export const POWER_PROPS_DETAIL = Object.freeze({
  visibleThreshold: 0.001,
  scaleFloor: 0.001,
});

// Preserved power-riser.mjs configuration from the approved film cut.
export const POWER_RISER_DETAIL = Object.freeze({
  defaultMetalness: 0.35,
  defaultRoughness: 0.55,
  boxFaceCount: 6,
  sideMetalness: 0.6,
  sideRoughness: 0.35,
  pistonSegments: 16,
  scaleFloor: 0.001,
  visibleThreshold: 0.001,
  coveredThreshold: 0.001,
  waveTravelScale: 1.4,
  waveLead: 0.2,
  waveSharpness: 3,
  stripGlowCap: 1.6,
});

// Preserved power-set.mjs configuration from the approved film cut.
export const POWER_SET_DETAIL = Object.freeze({
  waveWidthScale: 3,
});

// Preserved power-textures.mjs configuration from the approved film cut.
export const POWER_TEXTURES_DETAIL = Object.freeze({
  displayWeight: 900,
  baselineDivisor: 4,
  labelWeight: 800,
});
