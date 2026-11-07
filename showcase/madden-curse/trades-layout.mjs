import { TRADES_LAYOUT_DETAIL as TUNING } from './constants-trades.mjs';
import { TRADES_FRAME } from "./constants-trades.mjs";
export { TRADES_FRAME };
import { OPENING } from './constants.mjs';

/* Chapter 2's frame (docs/madden-film-chapter2.md): Aura's avatar large and named, a rail fanning from him to each
   partner, each lead touching the winner's avatar, the 3-5 stamp under Aura's name, and the headline beside him on a
   desktop, above him on a phone (the focal cluster, docs/madden-film-craft.md "Reading and watching compete"). Pure:
   every position is a share of the frame, so Node tests the fit at any size. Shares are of the frame's height (H) or
   width (W) as named. The view passes what only a browser can measure: the headline's height and each partner's
   widest label (`items`, px). */

const spread = (from, to, count, index) => count === 1 ? (from + to) / 2 : from + (to - from) * index / (count - 1);

/* The point `t` of the way along `rail`, 0 at Aura's end, 1 at the partner's. */
export const railPoint = (rail, t) => ({x: rail.x1 + (rail.x2 - rail.x1) * t, y: rail.y1 + (rail.y2 - rail.y1) * t});

/* From circle `a`'s edge to circle `b`'s, along the line between their centres. */
export function edgeToEdge(a, b) {
  const dx = b.x - a.x, dy = b.y - a.y, length = Math.hypot(dx, dy), ux = dx / length, uy = dy / length;
  return {x1: a.x + ux * a.r, y1: a.y + uy * a.r, x2: b.x - ux * b.r, y2: b.y - uy * b.r};
}

/* The lowest y a rail reaches between x `from` and `to` (a rail is straight, so one of its ends in that span). */
function lowest(rail, from, to) {
  const at = x => rail.y1 + (rail.y2 - rail.y1) * (x - rail.x1) / (rail.x2 - rail.x1);
  const left = Math.max(from, Math.min(rail.x1, rail.x2)), right = Math.min(to, Math.max(rail.x1, rail.x2));
  return left > right ? -Infinity : Math.max(at(left), at(right));
}

/* Where along `rail` (0..1) it first enters `box` ([left, top, right, bottom]), walking from its start: a light
   running to a badge stops there, and 1 when the rail never meets it. */
export function railEntry(rail, [left, top, right, bottom]) {
  let enter = 0, leave = 1;
  for (const [start, delta, low, high] of [[rail.x1, rail.x2 - rail.x1, left, right], [rail.y1, rail.y2 - rail.y1, top, bottom]]) {
    if (Math.abs(delta) < TUNING.parallelEpsilon) { if (start < low || start > high) return 1; continue; }
    const a = (low - start) / delta, b = (high - start) / delta;
    enter = Math.max(enter, Math.min(a, b)); leave = Math.min(leave, Math.max(a, b));
  }
  return enter <= leave ? enter : 1;
}

/* The phone's partner centres across the width: the labels justified from one margin to the other, so both outer
   margins match and every gap between two labels is the same. */
function rowCentres(width, items, margin) {
  const count = items.length;
  if (count === 1) return [width / 2];
  const room = (width - 2 * margin - items.reduce((sum, item) => sum + item, 0)) / (count - 1);
  let left = margin;
  return items.map(item => { const centre = left + item / 2; left += item + room; return centre; });
}

/* The card's frame for a `width` x `height` viewport and `count` partners, in px. */
export function tradesLayout(width, height, count, {headHeight = TRADES_FRAME.headHeight * height, items = []} = {}) {
  const phone = width < OPENING.mobileWidth, frame = TRADES_FRAME[phone ? 'phone' : 'desk'];
  const capped = (share, cap) => Math.min(share * height, cap === undefined ? Infinity : cap * width);
  const name = Math.max(TRADES_FRAME.nameFloor, TRADES_FRAME.name * height);
  const stampHeight = frame.stamp * height * TRADES_FRAME.stampBox;
  const auraR = capped(frame.aura.size, frame.aura.widthCap) / 2, partnerR = capped(frame.partners.size, frame.partners.widthCap) / 2;
  const badge = {height: frame.badge * height, font: frame.badge * height * TRADES_FRAME.badgeType};
  // Aura's own stack: his avatar, his name under it, the stamp under that.
  const stack = y => {
    const aura = {x: frame.aura.x * width, y, r: auraR};
    const auraName = {x: aura.x, top: aura.y + aura.r + frame.nameGap * height};
    const stamp = {x: aura.x, top: auraName.top + name + frame.stampGap * height, size: frame.stamp * height};
    return {aura, auraName, stamp};
  };
  let parts;
  if (phone) {
    const own = stack(frame.aura.y * height), {aura} = own;
    const sizes = Array.from({length: count}, (_, index) => Math.max(items[index] ?? 0, 2 * partnerR));
    const xs = rowCentres(width, sizes, frame.partners.margin * width);
    const partners = xs.map(x => ({x, y: frame.partners.y * height, r: partnerR}));
    partners.forEach(partner => {
      partner.name = {x: partner.x, bottom: partner.y - partner.r - frame.nameGap * height};
      partner.badge = {x: partner.x, y: partner.y + partner.r + frame.plateGap * height, side: 'below'};
    });
    const headWidth = frame.headWidth * width;
    const headline = {left: (width - headWidth) / 2, width: headWidth, bottom: aura.y - aura.r - frame.headGap * height, align: 'center'};
    // The hub's soft light, not only its core, keeps the clearance above the headline.
    const nodeR = frame.node * height, glow = frame.junction * frame.light * height / 2;
    const hub = {x: aura.x, y: headline.bottom - headHeight - frame.nodeClear * height - Math.max(nodeR, glow), r: nodeR};
    parts = {...own, partners, headline, node: hub, rails: partners.map(partner => edgeToEdge(hub, partner)),
      bounds: {top: partners[0].name.bottom - name, bottom: own.stamp.top + stampHeight}};
  } else {
    // Laid out about Aura's centre line at 0, then moved so the top and bottom margins match (rule 28).
    const own = stack(0), {aura} = own, pitch = frame.partners.pitch * height;
    const partners = Array.from({length: count}, (_, index) => ({x: frame.partners.x * width,
      y: (index - (count - 1) / 2) * pitch, r: partnerR}));
    partners.forEach(partner => {
      partner.name = {x: partner.x, top: partner.y + partner.r + frame.nameGap * height};
      partner.badge = {x: partner.x - partner.r - frame.plateGap * height, y: partner.y, side: 'left'};
    });
    const rails = partners.map(partner => edgeToEdge(aura, partner));
    const left = aura.x + aura.r + frame.headGap * height, headWidth = frame.headWidth * width;
    const under = Math.max(...rails.map(rail => lowest(rail, left, left + headWidth)));
    const headline = {left, width: headWidth, top: Math.max(aura.y, under + frame.railClear * height), align: 'left'};
    const top = Math.min(aura.y - aura.r, partners[0].y - partnerR);
    const bottom = Math.max(own.stamp.top + stampHeight, partners.at(-1).name.top + name, headline.top + headHeight);
    const shift = (height - top - bottom) / 2;
    [aura, ...partners, partners.map(partner => partner.badge)].flat().forEach(point => { point.y += shift; });
    partners.forEach(partner => { partner.name.top += shift; });
    own.auraName.top += shift; own.stamp.top += shift; headline.top += shift;
    rails.forEach(rail => { rail.y1 += shift; rail.y2 += shift; });
    parts = {...own, partners, headline, node: null, rails, bounds: {top: top + shift, bottom: bottom + shift}};
  }
  const {beam: shares} = TRADES_FRAME;
  const beam = {haze: shares.haze * height, glow: shares.glow * height, core: Math.max(shares.coreFloor, shares.core * height)};
  return {phone, width, height, ...parts, name, badge, beam, glint: TRADES_FRAME.glint * badge.height, rim: TRADES_FRAME.rim,
    light: frame.light * height, junction: phone ? frame.junction * frame.light * height : 0,
    push: TRADES_FRAME.push, maskPad: TRADES_FRAME.maskPad * height};
}
