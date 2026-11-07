import { DRAFT_TEXTURES_DETAIL as TUNING } from './constants-draft-surfaces.mjs';
import { CELL } from "./constants-draft-surfaces.mjs";
export { CELL };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { cardName } from './draft-data.mjs';
import { flameIcon } from './week-flame-icon.mjs';

/* Every printed surface of the draft room is drawn once into a canvas: the board's cards share one
   atlas, the five featured cards get their own sharper faces. Text uses the page's two faces. */
// The board shows rounds 1-10 (David, 2026-11-03): every story pick went in round 8 or earlier, and four
// fewer rows let the wall shot stand closer. The atlas is drawn at 2x (3072 x 3360, inside the 4096
// texture limit every phone GPU meets) from the 256px heads, so a 256px head is drawn at its own size
// (rule 24; 1.5x until 2026-11-04 read soft at 1080p); the five featured faces at 4x (512 x 672) from the 512px ones.

const HERO = Object.freeze({width: 512, height: 672});
const ANISOTROPY = 8;   // cards are seen at an angle in every close shot; three.js clamps it to the GPU's maximum
const BACK_LAYOUT = 256;   // the price tag's layout was drawn on a 256px-wide face; it scales from there
const INK = Object.freeze({white: css(PALETTE.white), muted: css(PALETTE.muted), slab: css(PALETTE.slab), edge: css(PALETTE.slabEdge),
  paper: css(PALETTE.cardSurface), print: css(PALETTE.print), broadcast: css(PALETTE.broadcast)});
const UI = 'Archivo, sans-serif';
export const DISPLAY = 'Shoulders, Impact, sans-serif';   // also the title's 3D letters (film-title-drop.mjs)
const DRAINED = 'grayscale(1) brightness(.85) contrast(1.15)';   // trades/curses.css .tr-fire img

export function loadImage(sources) {
  return new Promise(resolve => {
    const [first, ...rest] = sources;
    if (!first) return resolve(null);
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => loadImage(rest).then(resolve);
    image.src = first;
  });
}

// The sharpest cut first, falling back a size where ff-jarvis has none (heads/xl is 512px, lg 256px, root 96px).
export const headshots = (slug, large = false) =>
  [...(large ? [`../../heads/xl/${slug}.webp`] : []), `../../heads/lg/${slug}.webp`, `../../heads/${slug}.webp`];

export async function fontsReady() {
  try { await Promise.all([document.fonts.load(`900 40px ${DISPLAY}`), document.fonts.load(`700 20px ${UI}`)]); } catch { /* system faces */ }
}

function canvas(width, height) {
  const element = document.createElement('canvas');
  element.width = width; element.height = height;
  return [element, element.getContext('2d')];
}

export function texture(element) {
  const result = new THREE.CanvasTexture(element);
  result.colorSpace = THREE.SRGBColorSpace;
  result.anisotropy = ANISOTROPY;
  return result;
}

function fit(context, text, size, width, face = UI, weight = TUNING.defaultFontWeight) {
  let px = size;
  do { context.font = `${weight} ${px}px ${face}`; px -= 1; } while (context.measureText(text).width > width && px > size / 2);
}

/* One card face: position band, headshot, "C. Hubbard", then "WR · 8.12" (round.pick) like a war-room board. */
function card(context, x, y, scale, pick, image, drained = false) {
  const width = CELL.width * scale, height = CELL.height * scale, color = css(PALETTE[pick.pos] ?? PALETTE.silver);
  context.fillStyle = INK.paper; context.fillRect(x, y, width, height);
  context.fillStyle = color; context.fillRect(x, y, width, TUNING.cardBandHeight * scale);
  const cx = x + width / 2, cy = y + TUNING.cardPortraitY * scale, radius = TUNING.cardPortraitRadius * scale;
  context.save(); context.beginPath(); context.rect(x, y + TUNING.cardBandHeight * scale, width, TUNING.cardPortraitClipHeight * scale); context.clip();
  context.fillStyle = INK.paper; context.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
  if (image) { context.filter = drained ? DRAINED : 'none'; context.drawImage(image, cx - radius, cy - radius, radius * 2, radius * 2); }
  else {
    // A defense has no headshot: its disc is the position colour with the club's name on it.
    context.fillStyle = INK.paper; context.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
    context.fillStyle = INK.white; context.textAlign = 'center'; context.textBaseline = 'middle';
    fit(context, pick.name.toUpperCase(), TUNING.defenseNameSize * scale, radius * TUNING.defenseNameWidthRatio, DISPLAY, TUNING.displayWeight);
    context.fillText(pick.name.toUpperCase(), cx, cy + 2 * scale);
    context.textBaseline = 'alphabetic';
  }
  context.restore(); context.filter = 'none';
  context.fillStyle = INK.print; context.fillRect(x, y + TUNING.cardPrintY * scale, width, height - TUNING.cardPrintY * scale);
  context.textAlign = 'center'; context.fillStyle = INK.white;
  fit(context, cardName(pick.name), TUNING.cardNameSize * scale, width - TUNING.cardNamePadding * scale);
  context.fillText(cardName(pick.name), cx, y + TUNING.cardNameY * scale);
  context.font = `600 ${14 * scale}px ${UI}`; context.fillStyle = color;
  const slot = pick.overall - (pick.round - 1) * CELL.picksPerRound;
  context.fillText(`${pick.pos} · ${pick.round}.${slot}`, cx, y + TUNING.cardSlotY * scale);
}

export function atlas(picks, images) {
  const scale = CELL.atlasScale, [element, context] = canvas(CELL.width * CELL.columns * scale, CELL.height * CELL.rows * scale);
  picks.forEach(pick => card(context, pick.column * CELL.width * scale, (pick.round - 1) * CELL.height * scale, scale, pick, images.get(pick.slug)));
  return texture(element);
}

export function heroFront(pick, image, drained = false) {
  const [element, context] = canvas(HERO.width, HERO.height);
  card(context, 0, 0, HERO.width / CELL.width, pick, image, drained);
  return texture(element);
}

/* The price tag on a featured card's back: what the draft paid, in the position's colour. */
export function heroBack(pick, label) {
  const [element, context] = canvas(HERO.width, HERO.height), k = HERO.width / BACK_LAYOUT;
  context.fillStyle = INK.paper; context.fillRect(0, 0, HERO.width, HERO.height);
  context.fillStyle = INK.print; context.fillRect(0, 0, HERO.width, TUNING.priceBandHeight * k);
  context.textAlign = 'center'; context.fillStyle = INK.white;
  fit(context, cardName(pick.name), TUNING.priceNameSize * k, HERO.width - TUNING.priceNamePadding * k, UI, TUNING.displayWeight);
  context.fillText(cardName(pick.name), HERO.width / 2, TUNING.priceNameY * k);
  context.textAlign = 'center'; context.fillStyle = INK.print; context.font = `700 ${22 * k}px ${UI}`;
  context.fillText(label, HERO.width / 2, TUNING.priceLabelY * k);
  context.fillStyle = INK.print; fit(context, `${pick.pos}${pick.price}`, TUNING.priceSize * k, HERO.width - TUNING.priceNamePadding * k, DISPLAY, TUNING.displayWeight);
  context.fillText(`${pick.pos}${pick.price}`, HERO.width / 2, TUNING.priceY * k);
  context.fillStyle = INK.print; context.font = `600 ${20 * k}px ${UI}`;
  context.fillText(`#${pick.overall}`, HERO.width / 2, TUNING.overallY * k);
  return texture(element);
}

export function stamp(text, color, ink = PALETTE.white) {
  const [element, context] = canvas(TUNING.stampWidth, TUNING.stampHeight);
  context.translate(TUNING.stampCenterX, TUNING.stampCenterY);
  context.fillStyle = css(color); context.fillRect(TUNING.stampLeft, TUNING.stampTop, TUNING.stampFillWidth, TUNING.stampFillHeight);
  context.fillStyle = css(ink); context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, text, TUNING.stampFontSize, TUNING.stampTextWidth, DISPLAY, TUNING.displayWeight); context.fillText(text, 0, TUNING.stampBaseline);
  return texture(element);
}

// The week's label fills a third of the tile, so W1..W8 is over 2% of the frame wherever a light is 4%.
const WEEK_TILE = Object.freeze({width: 128, height: 160, labelY: 52, labelSize: 54});
export function weekTile(marker) {
  const [element, context] = canvas(WEEK_TILE.width, WEEK_TILE.height);
  const color = css(PALETTE[marker.flame ? 'boom' : marker.tier === 'bust' ? 'down' : marker.tier === 'solid' ? 'up' : 'muted']);
  context.fillStyle = INK.slab; context.fillRect(0, 0, WEEK_TILE.width, WEEK_TILE.height);
  context.strokeStyle = color; context.lineWidth = TUNING.weekStroke; context.strokeRect(2, 2, WEEK_TILE.width - TUNING.weekStroke, WEEK_TILE.height - TUNING.weekStroke);
  context.textAlign = 'center'; context.fillStyle = INK.white;
  context.font = `800 ${WEEK_TILE.labelSize}px ${UI}`; context.fillText(marker.week, WEEK_TILE.width / 2, WEEK_TILE.labelY);
  context.fillStyle = color;
  if (marker.flame && marker.live) {
    // The flame icon flickers live over this part of the tile (draft-weekfire.mjs, revision 14).
  } else if (marker.flame) {
    flameIcon(context);
  } else {
    context.font = '900 52px ' + DISPLAY;
    context.fillText(marker.tier === 'solid' ? '+' : marker.tier === 'bust' ? '!' : 'X', TUNING.weekSymbolX, TUNING.weekSymbolY);
  }
  return texture(element);
}

/* A pad's word: one big display word, edge to edge, readable from the far camera on a phone. */
// `shadow`: a soft dark halo under the letters, so a white word reads on any floor (rev 15).
export const PLACARD = Object.freeze({width: 512, height: 160, size: 150, margin: 24, shadow: 18});
export function placard(text, color) {
  const [element, context] = canvas(PLACARD.width, PLACARD.height);
  context.fillStyle = color; context.textAlign = 'center'; context.textBaseline = 'middle';
  context.shadowColor = css(PALETTE.background); context.shadowBlur = PLACARD.shadow;
  fit(context, text, PLACARD.size, PLACARD.width - PLACARD.margin, DISPLAY, TUNING.displayWeight);
  context.fillText(text, PLACARD.width / 2, PLACARD.height / 2 + PLACARD.margin / TUNING.placardBaselineDivisor);
  return texture(element);
}

/* The winning column's light (rule 28): a solid broadcast-blue band behind the whole column that
   fades out only at its sides, so it shows in every gap around the column's cards. */
export function columnLight() {
  const width = TUNING.columnLightWidth, height = TUNING.columnLightHeight, [element, context] = canvas(width, height);
  const band = context.createLinearGradient(0, 0, width, 0), blue = css(PALETTE.broadcast);
  band.addColorStop(0, `${blue}00`); band.addColorStop(TUNING.columnLightFadeIn, blue); band.addColorStop(TUNING.columnLightFadeOut, blue); band.addColorStop(1, `${blue}00`);
  context.fillStyle = band; context.fillRect(0, 0, width, height);
  return texture(element);
}

/* A stop's team name under its avatar: the display face, white, filling its plate (rule 17). */
export const TEAM_NAME = Object.freeze({width: 512, height: 128, size: 96, margin: 12});
export function teamName(text) {
  const [element, context] = canvas(TEAM_NAME.width, TEAM_NAME.height);
  context.fillStyle = INK.white; context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, text.toUpperCase(), TEAM_NAME.size, TEAM_NAME.width - TEAM_NAME.margin * 2, DISPLAY, TUNING.displayWeight);
  context.fillText(text.toUpperCase(), TEAM_NAME.width / 2, TEAM_NAME.height / 2 + TEAM_NAME.margin / 2);
  return texture(element);
}

/* The waiver wire's sign: an arrow dropping into a tray, in the curse's rim colour. */
export function waiverIcon() {
  const size = TUNING.waiverSize, [element, context] = canvas(size, size), middle = size / 2;
  context.fillStyle = INK.slab; context.beginPath(); context.arc(middle, middle, middle - TUNING.waiverInset, 0, Math.PI * 2); context.fill();
  context.strokeStyle = css(PALETTE.silver); context.fillStyle = css(PALETTE.silver);
  context.lineWidth = TUNING.waiverStroke; context.lineCap = 'round'; context.lineJoin = 'round';
  context.beginPath(); context.moveTo(middle, TUNING.waiverShaftTop); context.lineTo(middle, TUNING.waiverShaftBottom); context.stroke();
  context.beginPath(); context.moveTo(middle - TUNING.waiverArrowHalfWidth, TUNING.waiverArrowShoulder); context.lineTo(middle, TUNING.waiverArrowTip); context.lineTo(middle + TUNING.waiverArrowHalfWidth, TUNING.waiverArrowShoulder); context.stroke();
  context.beginPath(); context.moveTo(TUNING.waiverTrayLeft, TUNING.waiverTrayTop); context.lineTo(TUNING.waiverTrayLeft, TUNING.waiverTrayBottom); context.lineTo(TUNING.waiverTrayRight, TUNING.waiverTrayBottom); context.lineTo(TUNING.waiverTrayRight, TUNING.waiverTrayTop); context.stroke();
  return texture(element);
}

export function label(text, color = INK.muted) {
  const [element, context] = canvas(TUNING.labelWidth, TUNING.labelHeight);
  context.fillStyle = color; context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, text.toUpperCase(), TUNING.labelSize, TUNING.labelTextWidth, UI, TUNING.labelWeight); context.fillText(text.toUpperCase(), TUNING.labelX, TUNING.labelY);
  return texture(element);
}
