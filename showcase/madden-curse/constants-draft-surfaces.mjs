
export const BACKLIGHT = Object.freeze({
  resolution: 96,
  size: 2.2,       // the lit plane, a multiple of the board's extent
  inner: .36,      // how far out from the centre the light is flat, a share of the plane's half-size (the board's own edge is ~.45)
  soft: .3,        // how fast it falls off beyond that, the same units
  level: .32,      // its opacity at full, additive broadcast blue on the room
  out: .5,         // seconds it takes to lower at the board beat's end
  depth: -.3,      // behind the cards and the reveal wave, in front of the backdrop (BOARD.backdropZ)
});
export const BOARD = Object.freeze({
  card: .5, depth: .035, pitchX: .6, pitchY: .76, base: .75, header: .92, avatar: .17,
  backdrop: [60, 34], backdropZ: -.45, stripHeight: .03, stripDepth: .07, anisotropy: 8,
  teamName: {width: .58, height: .17, below: .3, depth: .01},
  // The winning column's light is wider than the column, so it fills the gaps on both sides of its cards.
  columnWidth: 1.35, columnDepth: -.02,
});
export const CELL = Object.freeze({width: 128, height: 168, columns: 12, rows: 10, picksPerRound: 12, atlasScale: 2});
export const CARD_HEIGHT = BOARD.card * CELL.height / CELL.width;
export const PROPS = Object.freeze({
  // A week light is 0.15 tall: at the close shots that is 8-9% of the frame's height, over the 4% of
  // rule 23, and its W1..W8 reads at a glance. Two rows of four sit under the card, as wide as it is,
  // so a 390px phone keeps all eight in frame.
  light: .12, lightHeight: .15, lightGap: .014, lightsBelow: .1, lightsPerRow: 4, stampWidth: .28,
  // Revision 15 (David: the white rings and words blended): a pad is a solid disc `padHeight` thick, its
  // top in the stop's colour at `padTop` of full strength, its side dark; the card stands on it, the
  // wire's too (~~a pit the card sank `pitDepth` into~~, rev 8-14).
  pad: .34, padHeight: .07, padTop: .75, pitDepth: 0,
  // A stop (rule 17): the card on its pad, the big word on the floor in front, and beside the pad the
  // team's avatar over its name. The avatar's 0.4 diameter is 10% or more of the frame at the trail's camera.
  // The word lies under the disc, `labelAhead` in front of its rim, never over it (rev 15; was .3).
  labelWidth: .7, labelTilt: -.85, labelLift: .07, labelAhead: .42,
  avatar: .2, avatarSide: -.72, avatarHeight: .5, nameWidth: .7, nameHeight: .2,
});
export const BOARD_STAGE = Object.freeze({
  wingWidth: 5.4, wingDepth: .28, wingAngle: .32, wingGap: .28,
  wingHeight: 1, finCount: 3, finWidth: .52, finDepth: .48, finTaper: .1,
  deckWidth: 22, deckHeight: .24, deckDepth: 3.6, deckFront: 1.2,
  rimHeight: .035, rimInset: .18, surface: .55, edge: .7, blue: .42,
  crownHeight: .22, crownDepth: .65, crownGap: .3,
});
export const WEEK_FIRE = Object.freeze({
  tile: [128, 160],      // the week tile's canvas (draft-textures.mjs WEEK_TILE)
  glow: 1.1,             // the glow's diameter, in light widths
  glowRest: .3, glowPulse: .25, flash: .9, flashGrow: .5,
  overshoot: 1.7,        // the ignite's back-ease: it swells past full size, then settles
  embers: 3, emberRise: .55, emberSpeed: .9, emberSize: .022, emberSway: .12,
});
export const FLAME_ICON = Object.freeze({
  pivot: [64, 140],      // the flame's base: it pulses and ignites from here
  centre: [66, 104],     // where its glow sits
  tip: [64, 58],         // where its embers leave
  fps: 12,               // a flicker frame lasts 1/12 s, 2.5 frames of the 30 fps film
  pulse: Object.freeze([0, .6, 1, .4]),   // each frame's share of the scale pulse, in step with its shape
  scale: .08,            // the pulse's peak: 1.0 to 1.08
  // Per frame, in tile pixels: [tip dx, right side dx, left side dx, notch dx, notch dy].
  frames: Object.freeze([[0, 0, 0, 0, 0], [3, -3, 2, 3, -4], [-2, 4, -3, -3, 3], [2, 1, -2, 4, -2]]),
});

// Preserved draft-backdrop.mjs configuration from the approved film cut.
export const DRAFT_BACKDROP_DETAIL = Object.freeze({
  rgbaChannels: 4,
  pixelCenter: 0.5,
  fullChannel: 255,
});

// Preserved draft-board.mjs configuration from the approved film cut.
export const DRAFT_BOARD_DETAIL = Object.freeze({
  avatarSegments: 48,
  sideMetalness: 0.6,
  sideRoughness: 0.35,
  boxFaceCount: 6,
  railMetalness: 0.8,
  railRoughness: 0.3,
  columnGlowPadding: 1.5,
  boardLightIntensity: 2.2,
  boardLightX: -4,
  boardLightY: 12,
  boardLightZ: 9,
});

// Preserved draft-props.mjs configuration from the approved film cut.
export const DRAFT_PROPS_DETAIL = Object.freeze({
  lightZ: 0.004,
  lightPopScale: 0.3,
  fireSeedStep: 0.37,
  lightOpacityBase: 0.35,
  slicedFaceZ: 0.006,
  quadLastCorner: 3,
  positionComponents: 3,
  padSegments: 48,
  avatarSegments: 64,
});

// Preserved draft-weekfire.mjs configuration from the approved film cut.
export const DRAFT_WEEKFIRE_DETAIL = Object.freeze({
  backOutExponent: 3,
  tileMidpoint: 0.5,
  iconZ: 0.003,
  iconRenderOrder: 4,
  glowZ: 0.002,
  glowRenderOrder: 3,
  positionComponents: 3,
  colorComponents: 3,
  emberRenderOrder: 5,
  emberSwayFrequency: 3,
  emberSeedStep: 2.1,
  emberZ: 0.004,
});

// Preserved draft-textures.mjs configuration from the approved film cut.
export const DRAFT_TEXTURES_DETAIL = Object.freeze({
  defaultFontWeight: 700,
  cardBandHeight: 3,
  cardPortraitY: 61,
  cardPortraitRadius: 49,
  cardPortraitClipHeight: 110,
  defenseNameSize: 30,
  defenseNameWidthRatio: 1.7,
  displayWeight: 900,
  cardPrintY: 113,
  cardNameSize: 21,
  cardNamePadding: 14,
  cardNameY: 128,
  cardSlotY: 150,
  priceBandHeight: 14,
  priceNameSize: 30,
  priceNamePadding: 30,
  priceNameY: 55,
  priceLabelY: 92,
  priceSize: 120,
  priceY: 210,
  overallY: 262,
  stampWidth: 320,
  stampHeight: 160,
  stampCenterX: 160,
  stampCenterY: 80,
  stampLeft: -150,
  stampTop: -60,
  stampFillWidth: 300,
  stampFillHeight: 120,
  stampFontSize: 96,
  stampTextWidth: 250,
  stampBaseline: 6,
  weekStroke: 4,
  weekSymbolX: 64,
  weekSymbolY: 120,
  placardBaselineDivisor: 4,
  columnLightWidth: 128,
  columnLightHeight: 8,
  columnLightFadeIn: 0.18,
  columnLightFadeOut: 0.82,
  waiverSize: 256,
  waiverInset: 4,
  waiverStroke: 18,
  waiverShaftTop: 52,
  waiverShaftBottom: 140,
  waiverArrowHalfWidth: 40,
  waiverArrowShoulder: 112,
  waiverArrowTip: 152,
  waiverTrayLeft: 62,
  waiverTrayTop: 150,
  waiverTrayBottom: 196,
  waiverTrayRight: 194,
  labelWidth: 512,
  labelHeight: 96,
  labelSize: 46,
  labelTextWidth: 490,
  labelWeight: 800,
  labelX: 256,
  labelY: 50,
});

// Preserved week-flame-icon.mjs configuration from the approved film cut.
export const WEEK_FLAME_ICON_DETAIL = Object.freeze({
  tipX: 64,
  tipY: 58,
  rightUpperControlX: 72,
  rightUpperControlY: 80,
  rightOuterControlX: 108,
  rightOuterControlY: 90,
  rightShoulderX: 92,
  rightShoulderY: 121,
  baseRightControlX: 75,
  baseRightControlY: 148,
  baseLeftControlX: 33,
  baseLeftControlY: 134,
  leftShoulderX: 37,
  leftShoulderY: 109,
  leftOuterControlX: 38,
  leftOuterControlY: 96,
  leftUpperControlX: 53,
  leftUpperControlY: 90,
  leftTipX: 52,
  leftTipY: 74,
  notchX: 61,
  notchY: 91,
  innerLowerControlX: 70,
  innerLowerControlY: 83,
  innerUpperControlX: 62,
  innerUpperControlY: 70,
});
