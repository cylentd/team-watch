import { PALETTE } from "./constants.mjs";

export const FLARE = Object.freeze({
  in: .4, decay: .8,
  streak: {width: 7, height: .09},      // world units at the ball; the streak is ~75x as wide as it is tall
  bloom: 1.5, texture: 256,
  beamBoost: 1.2,                       // the beams' brightness rises by this share at the flare's peak
});
export const FLOOR_HAZE = Object.freeze({
  size: [16, 11], opacity: .2, drift: .05,
  layers: [.02, .055],                  // heights above the floor; the stage (environment.mjs STAGE) is 0.13 tall
  // Revision 14: the haze is half there as the title falls, and the title's hit pushes it out by `push` over `pushFor` s.
  before: 1, push: .35, pushFor: 1.2,
});
export const GLINT = Object.freeze({rise: .05, decay: 7, turn: 1.6, texture: 128, ray: .06,
  card: .55, trophy: 1.6, gone: .01});
export const IMPACT = Object.freeze({
  ring: {life: .7, from: .03, to: 1.2, width: .04, opacity: .9, tilt: .32},
  second: {delay: .07, life: 1, width: .025, opacity: .75},       // CURSE's larger ring, `hit.second` times the reach
  // count: 4x revision 15's 72. Heights in frame heights, times in seconds; `bounce` keeps this share of the
  // landing speed for the one bounce; `trail` seconds of path drawn behind each spark; `drag` slows the spread.
  sparks: {count: 288, phone: 110, life: [1.2, 1.7], up: [.4, 1.1], out: .7, gravity: 1.8, bounce: .35, drag: 1.1,
    trail: .07, size: .016, amber: .55, lift: .01},
  embers: {count: 56, phone: 28, life: 1.5, reach: [.75, 1.05], out: .45, size: .012, flicker: 9},
  chips: {count: 18, phone: 10, life: 1.4, size: [.007, .016], up: [.3, .8], out: .55, spin: 11},
  carpet: {count: 170, phone: 60, life: .8, speed: 2.5, depth: .05, size: .011, rise: .02},
  dust: {count: 6, life: 1, from: .06, to: .24, opacity: .35, rise: .05, spread: 1.1},
  order: 29,                        // under the letters, over the stage
});
export const TITLE_FONT = Object.freeze({family: '"Bricolage Grotesque", Archivo, sans-serif', weight: 800});
export const TITLE_PLACE = Object.freeze({
  desk: Object.freeze({left: .05, baseline: .86, width: .7, cap: .14, rows: [[0, 1, 2]]}),
  phone: Object.freeze({left: .051, baseline: .845, width: .897, cap: null, rows: [[0, 1], [2]]}),
  tag: .02,                         // the tagline's top under CURSE's baseline, where it sits under the title
});
export const TITLE_DROP = Object.freeze({
  font: TITLE_FONT,
  fall: .3,                         // seconds from above the frame to the bar
  frame: 1 / 30,                    // one frame of the 30 fps film
  squash: [1.07, .84],              // [width, height] on the hit frame
  tilt: .55,                        // radians the block is tipped back as it falls, flat by the hit
  // The camera's offsets on the three frames from the last word's hit, in world units: small, dying away.
  shake: Object.freeze([[.05, -.035], [-.035, .025], [.017, -.011]]),
  distance: 2,                      // world units in front of the camera, nearer than anything on the stage
  // Frame fractions, shared with the tagline's CSS (film-title-place.mjs).
  desk: TITLE_PLACE.desk,
  phone: TITLE_PLACE.phone,
  leading: .92,                     // a phone's rows apart, in font sizes
  depth: .5, layers: 16,            // the letters' thickness in font sizes, drawn as this many stacked faces
  texture: {line: 240, pad: 56},    // canvas pixels per font size and around each word (room for CURSE's glow)
  order: 30,                        // drawn after the stage, the haze and the beams
  look: Object.freeze({
    tracking: -.03,                 // font sizes between letters: tighter than the face sets itself
    bevel: .014,                    // font sizes: the lit top-left edge and the shaded bottom-right one
    glow: .12,                      // font sizes: CURSE's lime glow round its letters
    // ~~The logo's red slash before THE~~ (ch17, David: "it reads as out of place").
  }),
  // Each word's hit, in the copy's order (film-impact.mjs scales by these): the ring's reach, the share of
  // the sparks that fly, the dust puff's size, the beams' flash at its peak, the chips' material (`tone`), a
  // second ring's reach (0: none) and the floor-wide ember carpet. The last is the biggest.
  hits: Object.freeze([
    Object.freeze({ring: .7, sparks: .45, dust: .7, flash: .45, tone: 'ink', second: 0, carpet: false}),
    Object.freeze({ring: .85, sparks: .65, dust: .85, flash: .65, tone: 'ink', second: 0, carpet: false}),
    Object.freeze({ring: 1.3, sparks: 1, dust: 1.25, flash: 1, tone: 'lime', second: 2.3, carpet: true}),
  ]),
});
export const RIM = Object.freeze({rise: .08, settle: 1.1, rest: .3, intensity: 120, distance: 7, decay: 1.4,
  position: Object.freeze([1.5, 3.4, -1.3])});
export const PAINT = {
  ink: [[0, PALETTE.white], [.46, PALETTE.ink], [.53, PALETTE.inkShade], [1, PALETTE.ink]],
  lime: [[0, PALETTE.brandLime], [.48, PALETTE.brandLime], [.53, PALETTE.limeShade], [1, PALETTE.brandLime]],
};

// Preserved film-flare.mjs configuration from the approved film cut.
export const FILM_FLARE_DETAIL = Object.freeze({
  entranceExponent: 3,
  streakAspect: 8,
  gradientCenter: 0.5,
  renderOrder: 11,
  hazeSeedStep: 3.1,
  streakBaseScale: 0.6,
  streakGrowthScale: 0.4,
  bloomBaseScale: 0.5,
  bloomGrowthScale: 0.5,
  hazePushExponent: 3,
});

// Preserved film-glint.mjs configuration from the approved film cut.
export const FILM_GLINT_DETAIL = Object.freeze({
  coreRadiusRatio: 0.45,
  renderOrder: 10,
  baseScale: 0.5,
});

// Preserved film-impact.mjs configuration from the approved film cut.
export const FILM_IMPACT_DETAIL = Object.freeze({
  cubicExponent: 3,
  randomIndexMultiplier: 127.1,
  randomSaltMultiplier: 311.7,
  randomOutputMultiplier: 43758.5453,
  ringFadeExponent: 1.5,
  glowFadeExponent: 1.2,
  positionComponents: 3,
  colorComponents: 3,
  ringSegments: 96,
  sparkAcrossSalt: 5,
  randomCenter: 0.5,
  sparkUpSalt: 3,
  sparkDepthSalt: 4,
  sparkColorSalt: 6,
  lineComponents: 6,
  emberAngleSalt: 7,
  emberReachSalt: 8,
  emberFlickerBase: 0.65,
  emberFlickerAmplitude: 0.35,
  emberFlickerPhase: 2.4,
  emberColorSalt: 9,
  emberWhiteMix: 0.4,
  chipOpacityGain: 3,
  chipAcrossSalt: 11,
  chipSpreadSalt: 12,
  chipUpSalt: 13,
  chipDepthSalt: 14,
  chipSizeSalt: 15,
  chipSpinXSalt: 16,
  chipSpinYSalt: 17,
  chipSpinZSalt: 18,
  carpetAcrossSalt: 21,
  carpetFadeExponent: 1.5,
  carpetColorSalt: 22,
  carpetWhiteMix: 0.5,
  carpetRiseSalt: 23,
  carpetDepthSalt: 24,
});

// Preserved film-title-drop.mjs configuration from the approved film cut.
export const FILM_TITLE_DROP_DETAIL = Object.freeze({
  frameEpsilon: 0.000001,
  edgeHighlightRatio: 0.6,
  textureAnisotropy: 8,
  projectionDepth: 0.5,
});

// Preserved film-zoom.mjs configuration from the approved film cut.
export const FILM_ZOOM_DETAIL = Object.freeze({
  easeExponent: 3,
  stopDistance: 0.45,
  titleSlide: 0.7,
});
