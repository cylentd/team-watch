
export const TRADES_FRAME = Object.freeze({
  desk: Object.freeze({
    aura: {x: .19, size: .28},                  // x of W, size of H: the subject at 28% of the height (rule 22 is a phone floor)
    partners: {x: .82, pitch: .2, size: .12},   // a column on the right centred on Aura's centre line (rule 28), H apart
    nameGap: .012,                              // H between an avatar and its name
    headGap: .035, headWidth: .3, railClear: .04,   // the headline: H right of Aura, W wide, H under the lowest rail it spans
    stampGap: .02, stamp: .085,                 // H under Aura's name; the stamp's type, H
    badge: .064, light: .045,                   // H: a lead's badge and a light, both over rule 30's 4%
    plateGap: .009,                             // H between a lead's plate and the avatar's rim, 8 px at 900
  }),
  phone: Object.freeze({
    aura: {x: .5, y: .7, size: .19, widthCap: .42},   // the bottom; size of H, at most .42 W
    partners: {y: .15, size: .095, widthCap: .2, margin: .04},   // a row across the top, W kept clear at each edge;
                                                  // the labels share what is left as even gaps (rule 36 wants 4% W)
    nameGap: .01,                               // H between a partner's name and its avatar under it, and Aura's name under him
    headGap: .02, headWidth: .9,                // the headline: H above Aura, W wide, centred
    node: .008, nodeClear: .04,                 // H: the rails' hub, and its clearance above the headline's top (rule 36)
    stampGap: .015, stamp: .055,
    badge: .05, light: .042,
    plateGap: .007,                             // H between a lead's plate and the avatar's rim, 6 px at 844
    junction: 1.5,                              // the beams' source light, a share of a light's size
  }),
  badgeType: .62,     // a badge's number, a share of its height
  stampBox: 1.3,      // the stamp's box height, a share of its type (its padding and rule; trades.css .trades-stamp)
  headHeight: .16,    // H: the headline's height until the browser measures it (two lines of the head type)
  name: .026,         // a name's type, H: its capitals stand .8 of it, so they clear rule 25's 2% of the height
  nameFloor: 17,      // px: tokens.css --film-floor's floor, so a name never falls under the film's smallest type
  push: .03,          // the slow push's last scale step about the frame's centre (timing.json trades `push`)
  // A beam is light, not a line (rule 33): a wide haze, a glow and a hot core, each H wide. Its haze stays inside the
  // desk headline's 4% rail clearance, so no glow crosses the words (rule 36). The core never thins under 2 px.
  beam: Object.freeze({haze: .03, glow: .012, core: .004, coreFloor: 2}),
  rim: .09,           // an avatar's silver rim, a share of its radius (draft-trade.mjs BADGE: .03 round a .3 avatar)
  glint: 1.1,         // the one flare, on the biggest lead's arrival: a share of a badge's height
  maskPad: .012,      // H of clear rail kept round the headline's ink
});
export const TRADES_MOTION = Object.freeze({
  bar: 2,           // s: one bar at 120 BPM (music-onsets.mjs), a drift light's trip along the bright half
  driftIn: .3,      // s the drifting lights take to come up after the hold starts
  driftGlow: .55,   // a drift light's peak, a share of a stopped light's
  breathe: .06,     // the stopped lights' slow swell in the hold, a share of their size
  stampFrom: 1.6,   // the stamp lands from this scale (rule 18's stamp, as Chapter 1's stamps land)
  whipShift: .06,   // the card's slide in with the whip, a share of the frame's width
  sweepSpan: 1.4, sweepLead: .2,   // film.css .wipe: the sweep's light sits at amount x 140% - 20% of the width
});

// Preserved trades-layout.mjs configuration from the approved film cut.
export const TRADES_LAYOUT_DETAIL = Object.freeze({
  parallelEpsilon: 1e-9,
});

// Preserved trades-view.mjs configuration from the approved film cut.
export const TRADES_VIEW_DETAIL = Object.freeze({
  glintQuarterTurnDegrees: 90,
});
