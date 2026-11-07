import { LINEUPS_LAYOUT_DETAIL as TUNING } from './constants-lineups.mjs';
import { DESK, STATION, BLIP, LAYOUTS } from "./constants-lineups.mjs";
export { DESK, STATION, BLIP };
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';

/* Chapter 4's lineup desk (docs/madden-film-chapter4.md, "Cinematic revision", David 2026-11-05): where the desk,
   both stations and everything that lands on them stand, on a desktop and a phone. Pure numbers in the room's
   units (Chapter 1's card is 0.5 wide), so the pose (lineups-pose.mjs), the camera (lineups-camera.mjs), the meshes
   (lineups-desk.mjs) and the tests all use the same places. */

   // each station's centre x
// A shield is a little wider than a card and about 1.4 cards tall, so SAINTS reads as a big word (storyboard).
export const SHIELD = Object.freeze({width: .56, height: .9, depth: .07, shoulder: .25, tip: .3, sink: .05});
export const CARD = Object.freeze({width: BOARD.card, height: CARD_HEIGHT, depth: BOARD.depth, sink: .04});
// A card's printed stamp (draft-props.mjs stampMesh is .28 x .14): .12 tall is 7% of the phone's crane frame, over
// rule 30's 4%, and leaves the phone's up shot room for START's name band and stamp at its bottom edge.
export const STAMP = Object.freeze({width: .24, height: .12, shield: .28, shieldHeight: .14});
// The share of a card's height its name band takes (lineups-faces.mjs FACE.band / FACE.height, 92 / 672).
export const BAND = 92 / 672;
// START / BENCH / DEF placards (512 x 160 textures), each standing `gap` clear of the card or shelf beside it.
// The phone's are smaller so its stack (START card, placard, shelf, rack card) fits one 40% crane frame (rule 22).
export const SIGN = Object.freeze({desk: {width: .4, height: .125, gap: .03}, phone: {width: .26, height: .08, gap: .02}});
export const SHELF = Object.freeze({height: .02});
           // draft.mjs LIGHT.blip, Chapter 1's size; smaller on a phone
// The ledge plinth: raised, set back from the slot (the eject goes up and back-left), its two slots apart.
const LEDGE = Object.freeze({rise: .08, pitch: .62, back: .25});

const seat = DESK.height - SHIELD.sink + SHIELD.height / 2;            // a shield's centre, seated in its socket
const cardSeat = DESK.height - CARD.sink + CARD.height / 2;            // a card's centre, seated in its socket

/* Each layout, in world units. The desktop sets the rack high right of START and the nameplates at each station's
   left; the phone stacks the rack straight above START and centres each nameplate under its slot, so a 390 px frame
   holds each station's words whole (composition table, David 2026-11-05: "the bottom is like cut off"). */
// Blip's spots and the nameplates (badge x, name x) are offsets from the station's slot: Gibbs's socket, START.

/* The places of one layout: [x, y, z] centres. */
export function places(mobile) {
  const layout = LAYOUTS[mobile ? 'phone' : 'desk'], sign = SIGN[mobile ? 'phone' : 'desk'];
  const gx = STATION.gibbs, lx = STATION.lamarley, z = DESK.line;
  const ledgeY = DESK.height + LEDGE.rise - SHIELD.sink + SHIELD.height / 2, ledgeX = gx + layout.ledge, ledgeZ = z - LEDGE.back;
  const start = [lx + layout.start, cardSeat, z];
  const startTop = cardSeat + CARD.height / 2, signY = startTop + sign.gap + sign.height / 2;
  // The phone's rack card stands on a shelf just over START's placard; the desktop's at its own height, high right.
  const rackY = mobile ? signY + sign.height / 2 + sign.gap + SHELF.height + CARD.height / 2 : layout.rack.y;
  const rack = [mobile ? start[0] : lx + layout.rack.x, rackY, z + layout.rack.z];
  const socket = [gx + layout.socket, seat, z], front = DESK.front + TUNING.deskFaceZ;
  const startSign = [start[0] - (mobile ? TUNING.phoneStartSignInset : TUNING.desktopStartSignInset), signY, z + TUNING.startSignZ];
  return {
    socket, front, sign, band: CARD.height * BAND,
    ledge: [[ledgeX - LEDGE.pitch / 2, ledgeY, ledgeZ], [ledgeX + LEDGE.pitch / 2, ledgeY, ledgeZ]],
    plinth: [ledgeX, DESK.height + LEDGE.rise / 2, ledgeZ],
    start, rack, shelf: rackY - CARD.height / 2 - SHELF.height / 2,
    // Every role word sits right above its card (rule 26: words, never colour alone); DEF is on the desk's face.
    startSign, benchSign: [rack[0], rackY + CARD.height / 2 + sign.gap + sign.height / 2, rack[2] + TUNING.benchSignZ],
    defSign: [socket[0], layout.def, front],
    // The week stamp stands beside START, so the pair reads W5 START even in a phone's narrow frame.
    week: [start[0] + layout.week.x, signY, z + TUNING.weekSignZ], weekSize: {width: layout.week.width, height: layout.week.height},
    plates: {gibbs: layout.plate.gibbs.map(x => socket[0] + x), lamarley: layout.plate.lamarley.map(x => start[0] + x), y: layout.plate.y,
      lamarleyY: layout.plate.lamarleyY ?? layout.plate.y, badge: layout.plate.badge, width: layout.plate.width, height: layout.plate.height},
    blip: {gibbs: [socket[0] + layout.blip.gibbs, DESK.height, z + layout.blip.z], peek: [socket[0] + layout.blip.peek, DESK.height, z + layout.blip.z],
      lamarley: [start[0] + layout.blip.lamarley, DESK.height, z + (layout.blip.lamarleyZ ?? layout.blip.z)], scale: layout.blip.scale},
  };
}

/* The corners of a box centred on `centre`, for framing and the camera tests. */
export const corners = (centre, width, height, depth = 0) =>
  [-1, 1].flatMap(sx => [-1, 1].flatMap(sy => [-1, 1].map(sz =>
    [centre[0] + sx * width / 2, centre[1] + sy * height / 2, centre[2] + sz * depth / 2])));
