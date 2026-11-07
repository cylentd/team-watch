import { span, at } from "./timing.mjs";
import { TRAIL } from "./constants.mjs";
import { CARD_HEIGHT, BOARD } from "./constants-draft-surfaces.mjs";

export const SIXTEENTH = .125;
export const STEAL = Object.freeze({rise: span('steal', 'rise'), blipIn: span('steal', 'blipIn'), stamp: span('steal', 'stamp'),
  blipOut: span('steal', 'blipOut'), lights: at('steal', 'lights'), lightStep: SIXTEENTH, lightOn: .1, riseDepth: .75, riseHeight: .12, bob: .015, shake: .03});
export const TRADED = Object.freeze({lift: span('traded', 'lift'), travel: span('traded', 'travel'), stamp: span('traded', 'stamp'),
  dim: span('traded', 'dim'), liftDepth: .45, arcDepth: 1.1, spin: .35, squash: .14, shake: .045, dimmed: .5,
  badge: [-1.4, .04, .6], land: [-.7, 0, .6], view: [-1.05, -.06, .6], badgeIn: span('traded', 'badge'), tagFade: span('traded', 'tagFade')});
export const WEEKS = 8;
export const SLEEPER = Object.freeze({rise: span('sleeper', 'rise'), lights: at('sleeper', 'lastLight') - WEEKS * SIXTEENTH, lightStep: SIXTEENTH,
  lightOn: SIXTEENTH, riseDepth: .75, riseHeight: .12});
export const SUSPENSE = Object.freeze({floor: .35, depth: .65, railPhase: .7, railPower: 8, railPeak: 1.8,
  kick: .6, kickFade: .25});
export const BURN = Object.freeze({
  flash: .2, catch: .12, out: .3,       // the flash on the landing, the ring flaring up after it, the fire dying
  scale: 2.4,                           // the ring's plane, in avatar diameters, so tongues have room above it
  flashSize: 1.6,                       // the flash's glow, in avatar diameters
  embers: 18, emberRise: .45, emberSpeed: .6, emberSize: .045,
  speed: 1.9, gain: 1.1,
});
export const MOBILE_FRAME = Object.freeze({widthFill: .86, heightFill: .48, lift: .13,
  reference: {width: 390, height: 844},
  // beamDensity: the phone's shaft density over the desktop's; ~~2.7~~ while the desktop's was half today's .55
  // (2026-11-05), so the phone's peak shaft alpha, ~0.8, stays translucent over the portrait (rule 46).
  // lightFocus: how far toward the camera, a share of its ground lead, a phone card fires. ~~.2~~ with the
  // 0.8 s light; the 0.33 s light (2026-11-05) fires each card ~0.2 s later, as it reaches the lower frame.
  pull: .7, reveal: .65, passLift: -.04, lightFocus: .27, beamHeight: 1.8, beamDensity: 1.5});
export const CURSE = Object.freeze({leave: TRAIL.leave, landings: TRAIL.landings, move: TRAIL.move,
  firstLanding: TRAIL.landings[0], lastLanding: TRAIL.landings.at(-1), leap: TRAIL.leap,
  hopHeight: .45, leapHeight: 1.1, flip: span('curse', 'flip'), shake: .04,
  ignite: [TRAIL.landings[0], TRAIL.landings[0] + .12], flameBase: .8, flameFlare: .45, reveal: [.45, .1],
  watch: [TRAIL.leap - .1, TRAIL.leap + .35], watchAngle: .9});
export const RIG = Object.freeze({
  wide: {desk: 18.5, phone: 21.5},   // ten rounds stand 8.4 tall; 18.5 fits them above the desktop lower third (15 in rev 6)
  // Rule 25: the scene takes the full width with its subject centred over a lower-third bar whose rule
  // line sits `ruleLine` down the frame (film.css --broadcast-rule-top), and nothing in the scene comes
  // within `gap` of that line (rule 26, David rev 8: Achane's weeks touched it). Only the finale slides
  // right, by a quarter of the width, so Romo's list and the board share the frame half and half.
  ruleLine: {desk: .76, phone: .66}, gap: .04, deskShift: {finale: .25},
  // `lift` slides the frame's content up by this share of its height, so the subject sits centred in
  // the space above the bar. Measured from the rev 8 stills; `all` is every beat not named.
  lift: {desk: {all: .17, board: .12, finale: 0}, phone: {all: .25, board: MOBILE_FRAME.lift, steal: .22, curse: .16, injury: .26, finale: .02}},
  boardStageBack: 2.3,
  finale: {desk: 14.8, phone: 11.6, phoneShift: .28},
  close: {desk: [3.7, 3.3], phone: [3.3, 2.95]}, track: {desk: 5, phone: 5.2},
  // Golden's card and its two rows of week lights fit on a phone between the WR40 -> WR7 line and the
  // controls' scrim only from further back (rule 22, 2026-11-04 rev 6 stills).
  closePhone: {steal: [4.5, 4.3], injury: [3.7, 3.4]},   // injury: from 2.95 Achane's weeks sat 3.2% off the rule (rev 8)
  // Rev 15: the close frames Aura's badge and the card beside it, 1.3 wide and 1 tall (draft-beats.mjs TRADED).
  trackClose: {desk: 2.6, phone: 3.9}, trackSettle: span('traded', 'push'), phoneLift: .05, trackTravel: span('traded', 'track'),
  // [height, back, aim]: the camera follows the card from pad to pad and frames one whole stop, the
  // avatar and its name beside the card, centred on `stopCentre` (draft-props.mjs PROPS: the middle of
  // avatarSide - nameWidth / 2 and the card's right edge). Rule 22: nothing cut off, at 1080p and 390px.
  floor: {desk: [1.3, 2.6, .35], phone: [1.9, 3.9, .35]}, stopCentre: -.41, cutToFloor: [CURSE.leave - .1, CURSE.firstLanding],
  // Revision 14 (David's storyboard): one fixed wide shot [height, back, aim] of WARREN-TY's pad and the
  // waiver wire through the first four stops, no moves; it spans `extent` past the outer stations: the left
  // owner's name (avatarSide - nameWidth / 2) and room past the wire (Blip stood there until rev 17). Over
  // TRAIL.pan a whip right to COOKed's stop, ending `revealPull` further back than the close framing above
  // (`floor`), then a push of TRAIL.push s onto it, then a slow push of `holdPush` to the beat's end.
  // ~~A widen to COOKed's landing and one push in; per-stop pans to the charred owner~~ (revisions 10-13).
  trailWide: {desk: [1.3, 4.9, .75], phone: [2.1, 9.6, 1.05]}, extent: {desk: [-1.07, 1.75], phone: [-1.07, 1]}, revealPull: .9, holdPush: .06,
  // Rule 19 (David rev 9: everything looked tilted): every shot drifts at most `yaw` radians (3 degrees) across
  // its beat, through square-on, and pushes in by `push` of its distance, so no frame is still; the subject
  // stays upright, with no roll. ~~Orbits of up to 0.2 rad and a 0.05 rad roll on the whip~~ (revision 8).
  orbit: {yaw: [-.026, .026], push: .08},
  // The opening hands over by tilting down (scene.mjs FILM_INTRO.exit); the board's first frames arrive
  // from above, the camera `rise` higher and looking `look` higher, and settle onto the pass.
  dropIn: {rise: 1.4, look: 3},
});
export const INJURY = Object.freeze({forward: span('injury', 'forward'), lights: at('injury', 'lights'), lightStep: .05, lightOn: .1,   // rev 16: all eight lit by the IR stamp at 0.5 s
  forwardDepth: .9, status: span('injury', 'status'),
  cut: at('injury', 'cut'), part: .4, fade: span('injury', 'fade'), partGap: .06, partSlide: .05, partTurn: .05});
export const FINALE = Object.freeze({home: span('finale', 'home'), glow: span('finale', 'glow'), glowPeak: 1,
  rise: span('finale', 'rise'), riseHeight: .45, riseScale: .6, rows: at('finale', 'rows'), rowStep: .25,
  total: at('finale', 'total'), next: at('finale', 'next'),   // the next-best line on the onset after the total (asset 42.957 s)
  pulseBase: .6, pulseDepth: .4, pulseSpeed: 4, cardBase: .82, cardDepth: .18});
export const FLAME = Object.freeze({
  back: [1.65, 1.35],
  // [width, height] of the card; the plane's foot sits `frontBelow` card heights under the card's.
  front: [1.4, 1.15], frontBelow: .08, frontGain: 1.25,
  // The clear window over the portrait and name, in the front plane's uv: [left, bottom, right, top, soft].
  // The card spans x .143-.857 of the plane; its lower 18% and a 5% strip up each side burn.
  hole: [.19, .23, .81, 1.1, .05],
  edge: {back: .16, front: .03},
  speed: 1.7, flicker: 17, embers: 40, emberRise: 1.1, emberSpeed: .45, emberSize: .06, emberSway: .12,
});
export const HEADER_LIGHT = Object.freeze({base: .3, peak: 1.3, settle: .35,
  rim: .18, segments: 48, opacity: .7, rest: .3, lift: .004});
export const PATH_BEAM = Object.freeze({height: CARD_HEIGHT * 3.2,
  flare: 1.15, corridor: BOARD.card * 1.1, trail: .45,
  rise: .05, hold: .06, fade: .22, lead: .08, opacity: 1, density: .55, samples: 100, resolution: 64, accent: 1.3, maxShift: .18,
  frame: .03,     // the lit border band's width, a share of the card's width (~12 px of a desktop's ~400 px card in the pass)
  lift: .002});
export const REVEAL_GLOW = Object.freeze({duration: 1.5, padding: .6, depth: -.1, strength: 1.6,
  band: .22, edge: .94, softness: .12, travel: 1.4, lead: .2, inside: .5});
export const BADGE = Object.freeze({
  avatar: .3, rim: .03,            // the avatar's radius, and the white ring round it
  nameWidth: .8, nameBelow: .46,   // the name's width, and its centre under the avatar's
  // The tag's line on the card face (draft-textures.mjs card: 150 of 168 px down, 14 px type), as shares of the card.
  cover: {width: .92, height: .13, y: .5 - 150 / 168, behind: .003},
});
export const LIGHT = Object.freeze({focus: .16, focusIn: .3,
  strip: .35, exposure: 1.1, exposureIn: .5, blip: .28, fog: .012, stampY: -.255, ground: [60, 40],
  status: {x: .13, y: .25, scale: .5}, key: {intensity: 70, position: [0, 7, 7], target: [0, 0, 1.9]}});

// Preserved draft-beats.mjs configuration from the approved film cut.
export const DRAFT_BEATS_DETAIL = Object.freeze({
  stampLiftRatio: 0.2,
  stealBobFrequency: 6,
  stealHitDepth: 0.06,
  stealPitch: -0.08,
  stealHitRoll: 0.05,
  blipApproachX: 1.2,
  blipAtCardX: 0.05,
  blipDepartX: 0.5,
  blipApproachY: 0.75,
  blipJumpHeight: 0.6,
  blipRideDrop: 0.3,
  blipExitHop: 0.25,
  blipApproachZ: 0.12,
  blipExitZ: 0.08,
  blipHitSquash: 0.25,
  blipExitSquash: 0.3,
  blipLookThreshold: 0.5,
  blipExitLook: -0.7,
  badgeScaleFloor: 0.001,
  tradedPitch: -0.2,
  tradedYaw: 0.45,
  tradedThudStretch: 0.08,
  tradedHitShake: 0.5,
  sleeperBobHeight: 0.015,
  sleeperBobFrequency: 6,
  sleeperPitch: -0.08,
});

// Preserved draft-build.mjs configuration from the approved film cut.
export const DRAFT_BUILD_DETAIL = Object.freeze({
  columnEase: 0.1,
  dimFraction: 0.4,
  peakFraction: 0.82,
  pulseDepth: 0.2,
  slowPulseFrequency: 1.5,
  mediumPulseFrequency: 3,
  fastPulseFrequency: 6,
  finalPulseFrequency: 12,
  flashIntensity: 0.9,
  flashFade: 0.4,
});

// Preserved draft-burn.mjs configuration from the approved film cut.
export const DRAFT_BURN_DETAIL = Object.freeze({
  positionComponents: 3,
  ringPhase: 2.3,
  ringZ: 0.012,
  flashZ: 0.03,
  emberSeedStep: 0.618,
  emberZ: 0.02,
});

// Preserved draft-camera.mjs configuration from the approved film cut.
export const DRAFT_CAMERA_DETAIL = Object.freeze({
  cardEyeX: 0.1,
  cardEyeY: 0.05,
  cardTargetDrop: 0.08,
  cardTargetZ: 0.35,
  wideEyeY: 0.4,
  wideLiftRatio: 0.5,
  finaleEyeY: 0.3,
  travelTargetZ: 0.4,
  travelEyeY: 0.1,
  horizontalShakeRatio: 0.5,
});

// Preserved draft-curse.mjs configuration from the approved film cut.
export const DRAFT_CURSE_DETAIL = Object.freeze({
  cardLiftDepth: 0.2,
  cardLiftStart: 0.1,
  tumbleRoll: 0.3,
});

// Preserved draft-establish.mjs configuration from the approved film cut.
export const DRAFT_ESTABLISH_DETAIL = Object.freeze({
  tableHeight: 0.55,
  pitchDegrees: 27,
  halfTurnDegrees: 180,
  desktopZoom: 0.6,
  turnSpeed: 0.45,
});

// Preserved draft-flame.mjs configuration from the approved film cut.
export const DRAFT_FLAME_DETAIL = Object.freeze({
  sparkSize: 32,
  sparkCenter: 16,
  sparkRadius: 16,
  frontPhase: 4.7,
  frontZ: 0.015,
  horizontalSeedStep: 0.618,
  verticalSeedStep: 0.382,
  positionComponents: 3,
  sideThreshold: 0.5,
  emberEdge: 0.48,
  emberSpread: 0.15,
  emberSwayFrequency: 3,
  emberRiseScale: 1.4,
  emberZ: 0.02,
});

// Preserved draft-motion.mjs configuration from the approved film cut.
export const DRAFT_MOTION_DETAIL = Object.freeze({
  cubicExponent: 3,
  midpoint: 0.5,
  cubicInScale: 4,
  expoSlope: 20,
  expoOffset: 10,
  negativeExpoSlope: -20,
});

// Preserved draft-path-beams.mjs configuration from the approved film cut.
export const DRAFT_PATH_BEAMS_DETAIL = Object.freeze({
  rgbaChannels: 4,
  fadeExponent: 3,
  fullChannel: 255,
  positionComponents: 3,
  scaleFloor: 0.001,
  growthExponent: 3,
});

// Preserved draft-path-light.mjs configuration from the approved film cut.
export const DRAFT_PATH_LIGHT_DETAIL = Object.freeze({
  rgbaChannels: 4,
  pixelCenter: 0.5,
  fullChannel: 255,
});

// Preserved draft-trade.mjs configuration from the approved film cut.
export const DRAFT_TRADE_DETAIL = Object.freeze({
  avatarSegments: 64,
  faceZ: 0.004,
});

// Preserved draft.mjs configuration from the approved film cut.
export const DRAFT_DETAIL = Object.freeze({
  stampZ: 0.006,
  scaleFloor: 0.001,
});
