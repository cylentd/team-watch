
export const HAZE = Object.freeze({width: 30,   // wide enough to reach both edges of the frame (ch17)
  height: 1.1, opacity: .16,
  layers: [{x: -.8, y: .2, z: -1.6}, {x: .6, y: .25, z: -.4}, {x: -.2, y: .3, z: 1.2}]});
export const RIG = Object.freeze({
  heads: 11, pitch: 1.6, height: 3.9, arch: .12, depth: -7.5,
  housing: {radius: .19, rear: .15, length: .34, bezel: .025, yoke: .27, yokeTube: .018}, lens: .13, glow: 1.25, glowOpacity: .85, lensBoost: 2.2,
  movers: [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
  // Soft enough that the floor pool keeps its falloff instead of clipping white (review, 2026-11-03).
  spot: {intensity: 24, distance: 24, angle: .2, penumbra: .9, decay: 1.5},
  // A beam is drawn to its target and no further (`reach` past it), so it never runs on across the frame.
  // `floor`: the least a beam shows however it turns, so a beam aimed toward the lens never vanishes (David rev 9:
  // the left spots looked off).
  beam: {length: 10, radius: .7, opacity: .22, segments: 64, edge: 2.2, fall: 1.4, reach: 1.05, floor: .45},
  // The movers hang right of centre, so their beams reach the trophy and Blip from the right and never
  // cross the title, which sits left of them on a desktop.
  sweep: {speed: .9, phase: 1.7, width: 2.6, depth: 1.4, aim: .2},
  sway: {speed: 1.3, width: .22}, spread: .25,   // the converged beams fan this far apart across the trophy
  trophyAim: 1.7,                             // the height on the trophy the converged beams meet
  exit: {spread: 1.1, ahead: 5},              // where the beams land on the floor as the film hands over
  // A side truss down the stage's left (David, ch17: "the huge black area top-left"): lamps from the left edge
  // of the frame, their beams on the trophy. Beams only, no spot lights, so a phone holds frame rate.
  side: {x: -6.8, height: 4.4, depths: [-6, -3.8, -1.6, .6, 2.8], aim: 1.7, spread: .5, opacity: .7},
});
export const STANDS = Object.freeze({
  radius: 19, bottom: -.5, top: 12, segments: 96,
  tiers: 14, tierLine: .18,           // tier rows up the stand, and each row's lit rail as a share of the row
  texture: {width: 2048, height: 512},
  opacity: .85, lift: 2.2,            // the stand's faintness over the background, and how far its dark tiers are lifted
  bokeh: {count: 760, low: .8, high: 11.5, size: [.18, .55], opacity: .32, inset: .4},
});

// Preserved stage-lights.mjs configuration from the approved film cut.
export const STAGE_LIGHTS_DETAIL = Object.freeze({
  glowTextureSize: 64,
  glowTextureCenter: 32,
  glowTextureRadius: 32,
  glowCoreStop: 0.25,
  canSegments: 32,
  bezelRadialSegments: 10,
  bezelTubularSegments: 40,
  yokeRadialSegments: 8,
  yokeTubularSegments: 32,
  housingMetalness: 0.7,
  housingRoughness: 0.4,
  lensSegments: 24,
  lensZ: 0.002,
  sweepDepthFrequency: 0.7,
  blipFocusStride: 3,
  blipFocusLift: 0.47,
  aimBlend: 0.25,
});

// Preserved stage-stands.mjs configuration from the approved film cut.
export const STAGE_STANDS_DETAIL = Object.freeze({
  randomIndexMultiplier: 91.7,
  randomSaltMultiplier: 47.3,
  randomOutputMultiplier: 43758.5453,
  tierLineOpacity: 0.3,
  positionComponents: 3,
  colorComponents: 3,
  heightDistributionExponent: 1.4,
  glowBaseline: 0.35,
  glowRange: 0.65,
  glowSalt: 3,
});
