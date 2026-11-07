import { BOARD_STAGE } from "./constants-draft-surfaces.mjs";
import { SYNC } from "./constants-music.mjs";
import { HOP } from "./constants-opening.mjs";

export const BACKDROP = Object.freeze({
  wall: {width: 34, height: 12, z: -2.2, y: 3},
  glow: {width: 7.5, height: 4.2, y: 1.9, z: -2.1, level: .55},            // one wash behind each station
  fins: {count: 13, from: -9, to: 9, z: -1.6, width: BOARD_STAGE.finWidth, depth: BOARD_STAGE.finDepth,
    tall: 4.2, taper: .12},                                                  // tallest at the centre, shorter outward
  recess: BOARD_STAGE.rimHeight,
});
export const CAMERA = Object.freeze({
  line: 4,             // the desk's subject plane (lineups-layout.mjs DESK.line)
  pitch: .12,          // rise per unit of distance (about 7 degrees down), so the slot's mouth and the desk top read
  whipFrom: -3,        // the whip in starts this far left of the socket framing, and runs right (rule 20)
  push: {desk: .06, phone: .04}, drift: .03,
});
export const STATION = Object.freeze({gibbs: -2.2, lamarley: 2.2});
export const LINEUPS_CAMERA_G = STATION.gibbs;
export const LINEUPS_CAMERA_L = STATION.lamarley;
export const FRAMES = Object.freeze({
  desk: {socket: [LINEUPS_CAMERA_G + .15, 1.1, 2.15], ledge: [LINEUPS_CAMERA_G - .6, 1.1, 2.15], down: [LINEUPS_CAMERA_L - .4, 1.34, 2.65], up: [LINEUPS_CAMERA_L - .35, 1.38, 2.65]},
  phone: {socket: [LINEUPS_CAMERA_G + .35, 1.24, 2], ledge: [LINEUPS_CAMERA_G - 1.2, 1.08, 2.6], down: [LINEUPS_CAMERA_L - .3, 1.02, 1.65], up: [LINEUPS_CAMERA_L - .3, 1.82, 1.58]},
});
export const EDITION = Object.freeze({season: 2026, league: 75203, through: 8, defenseTeam: 5, tightendTeam: 11,
  defenseWeeks: [1, 2, 3, 4, 5, 6, 7, 8], tightendWeeks: [5, 7, 8], shownDefense: [4, 5], shownTightends: [5, 8]});
export const DIM = Object.freeze({
  slot: {width: .64, depth: .14, rim: .02}, plinth: {width: 1.36, depth: .4}, shelf: {depth: .2, post: .025},
  lip: {height: .025, depth: .03}, ring: 1.12,   // the badge's silver ring, a share of its radius
});
export const KEY = Object.freeze({intensity: 90, angle: .62, penumbra: .85, decay: 2, offset: [-1.8, 4.6, 8.4], aim: [.4, .9, 4],
  rim: 2.4, rimFrom: [1.5, 4.5, -1.5], fill: .5, fillFrom: [3, 2, 10]});
export const PLATE = Object.freeze({width: 256, bevel: 12, keyline: 20, bevelLine: 6, keyLine: 3, brush: 3,
  bevelAlpha: '8c', keyAlpha: '59', brushAlpha: '0a', stops: [0, .42, 1]});
export const FRAME = 1 / SYNC.fps;
export const HEADLINE = Object.freeze({enter: 10 * FRAME, leave: 4 * FRAME,
  slam: .12,          // the title's extra scale at its first frame
  titleOut: .177,     // each title is gone at 67.9 and 75.9, this long before its beat's punchline bar
  outcomeOut: .077,   // storyboard: the outcome leaves at 70.0, this long before the whip's bar line
  payoffOut: .127});
export const DESK = Object.freeze({
  width: 9, height: .8, back: 3.55, front: 4.2,   // in front of Chapter 5's riser (power-layout.mjs, z 0.6 to ~3)
  line: 4,          // the plane every shield and card stands in
  strip: .035,      // the broadcast-blue recess strip along the lip
});
export const BLIP = Object.freeze({scale: .28, phone: .16});
export const LAYOUTS = Object.freeze({
  desk: {socket: .35, ledge: -1.2, start: -.3, rack: {x: .62, z: -.4, y: 1.6}, week: {x: .23, width: .224, height: .112},
    blip: {gibbs: -.8, peek: -.45, lamarley: -.55, z: .25, scale: BLIP.scale},
    plate: {gibbs: [-1.9, -1.3], lamarley: [-1.25, -.65], y: .45, badge: .15, width: .62, height: .155}, def: .45},
  phone: {socket: .35, ledge: -1.2, start: -.3, rack: {z: 0}, week: {x: .17, width: .17, height: .08},
    blip: {gibbs: -.95, peek: -.27, lamarley: .17, z: .25, lamarleyZ: .12, scale: BLIP.phone},
    plate: {gibbs: [-.24, .08], lamarley: [-.24, .08], y: .4, lamarleyY: .6, badge: .085, width: .44, height: .11}, def: .64},
});
export const POSE = Object.freeze({
  drop: 1.6, squash: .08, squashFor: 3 * FRAME,       // shields fall from above frame, 8% squash on landing
  scoreAfter: 4 * FRAME, slam: .6, slamFor: 3 * FRAME, // W slams on the bar, the score 4 frames later, each from 160%
  ejectAfter: 1.5, eject: .35, pop: .4,
  flashFor: .3,                                        // the slot's red flash
  rim: .5, rimFor: .5, shaftFor: .5,                   // rim back to 50% and the shaft gone 0.5 s after the hit
  strip: .4, stripFor: .5,                             // the recess strip lights on 62.077, settles to 40%
  stampPop: 4 * FRAME, stampGap: 4 * FRAME, clear: 4 * FRAME, flip: 6 * FRAME,
  scores: Object.freeze({s5start: 1, s5bench: 1.2, s8start: 1, s8bench: 1.5}),   // the last largest (craft)
  rackLow: .4, rackIn: 3 * FRAME,                      // the rack at 40% until its card scores
  bulge: Object.freeze({desk: .35, phone: .28}), front: .2,   // the swap's arcs, far enough apart that faces never cross
  blipHops: 2, blipHopFor: .8, blipLift: HOP.lift,     // 66.4-67.2, two hops, lift in Blip's own scale
  lean: .25, leanFor: .15, look: -.6, turn: .4, nod: -.5, nodFor: 3 * FRAME, nodGap: 9 * FRAME,
  shake: .015,
});
export const LINEUPS_SET = Object.freeze({
  warm: .1,          // seconds after each hit the scene compiles a frame (scene.mjs warmAt), as power-set.mjs
  hitUnit: .5,       // film-impact.mjs unit: a desk prop's hit, half a card wide
  hitHalf: .3,       // the dust's half width at the socket, about a shield's
});

// Preserved lineups-camera.mjs configuration from the approved film cut.
export const LINEUPS_CAMERA_DETAIL = Object.freeze({
  halfTurnDegrees: 180,
});

// Preserved lineups-desk.mjs configuration from the approved film cut.
export const LINEUPS_DESK_DETAIL = Object.freeze({
  defaultMetalness: 0.6,
  defaultRoughness: 0.35,
  slotHeight: 0.01,
  slotY: 0.003,
  socketBandHeight: 0.012,
  socketBandY: 0.006,
  topMetalness: 0.7,
  topRoughness: 0.28,
  faceMetalness: 0.55,
  faceRoughness: 0.42,
  lipMetalness: 0.9,
  lipRoughness: 0.18,
  lipZ: 0.004,
  stripDepth: 0.01,
  stripZ: 0.006,
  defenseSocketPadding: 0.08,
  starterSocketPadding: 0.04,
  plinthHeight: 0.08,
  plinthMetalness: 0.7,
  plinthRoughness: 0.3,
  ledgeHeight: 0.02,
  ledgeDepth: 0.01,
  shelfPadding: 0.1,
  shelfMetalness: 0.7,
  shelfRoughness: 0.3,
  rackStripHeight: 0.012,
  rackStripDepth: 0.01,
  postMetalness: 0.9,
  postRoughness: 0.2,
  badgeRingMetalness: 0.9,
  badgeRingRoughness: 0.2,
  badgeSegments: 48,
  badgeRingZ: -0.001,
  ledgeY: 0.01,
  ledgeZ: 0.006,
  rackZ: 0.03,
  rackStripY: -0.004,
  rackStripZ: 0.006,
  postDepthDivisor: 4,
});

// Preserved lineups-faces.mjs configuration from the approved film cut.
export const LINEUPS_FACES_DETAIL = Object.freeze({
  defenseNameWeight: 900,
  playerNameWeight: 800,
  textureCenter: 0.5,
});

// Preserved lineups-layout.mjs configuration from the approved film cut.
export const LINEUPS_LAYOUT_DETAIL = Object.freeze({
  deskFaceZ: 0.003,
  phoneStartSignInset: 0.12,
  desktopStartSignInset: 0.1,
  startSignZ: 0.02,
  benchSignZ: 0.02,
  weekSignZ: 0.02,
});

// Preserved lineups-pose.mjs configuration from the approved film cut.
export const LINEUPS_POSE_DETAIL = Object.freeze({
  expoSlope: -10,
  weekFlipMidpoint: 0.5,
  ledgeFadeAmount: 0.5,
});

// Preserved lineups-props.mjs configuration from the approved film cut.
export const LINEUPS_PROPS_DETAIL = Object.freeze({
  sleeveTextureWidth: 4,
  sleeveTextureHeight: 64,
  sleeveSideY: 0.5,
  shieldPrintZ: 0.003,
  defenseNameAspect: 3.2,
  defenseSleevePadding: 0.08,
  sleeveHeight: 0.14,
  starterSleevePadding: 0.04,
});

// Preserved lineups-set.mjs configuration from the approved film cut.
export const LINEUPS_SET_DETAIL = Object.freeze({
  badgeImageOffset: 4,
  scaleFloor: 0.001,
});
