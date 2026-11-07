import { POWER_TEXTURES_DETAIL as TUNING } from './constants-power.mjs';
import { SHEET } from "./constants-power.mjs";
export { SHEET };
import { PALETTE, css } from './constants.mjs';
import { DISPLAY, texture } from './draft-textures.mjs';

/* Chapter 5's printed surfaces, each drawn once into a power-of-two canvas (like draft-textures.mjs, so every one
   mipmaps sharp): a plate's face, its badge, its record and its actual W-L, and a slot's place numeral. A plate's
   name uses draft-textures.mjs teamName, so the riser reads like Chapter 1's cards (storyboard). */
const UI = 'Archivo, sans-serif';
const INK = Object.freeze({white: css(PALETTE.white), silver: css(PALETTE.silver), muted: css(PALETTE.muted), slab: css(PALETTE.slab),
  paper: css(PALETTE.cardSurface), print: css(PALETTE.print), broadcast: css(PALETTE.broadcast)});
// Canvas sizes, px. The badge at its own 128px cut (rule 24: an image is drawn at its own size, never resampled
// down). The face is one shared 256 square: its bands are axis-aligned, so the 3:4 plate stretches it cleanly.
      // the actual W-L: one small line under it

function canvas(width, height) {
  const element = document.createElement('canvas');
  element.width = width; element.height = height;
  return [element, element.getContext('2d')];
}
function fit(context, text, size, width, face, weight) {
  let px = size;
  do { context.font = `${weight} ${px}px ${face}`; px -= 1; } while (context.measureText(text).width > width && px > size / 2);
}

/* The plate's face, shared by all twelve: Chapter 1's card surface lit from above (a gradient to the slab), the
   broadcast rim band along the top, the print block under the badge like the card's name band, and a thin silver
   edge so the plate's outline reads against the dark riser. */
export function plateFace() {
  const {size, band, print, edge} = SHEET.face, [element, context] = canvas(size, size);
  const light = context.createLinearGradient(0, 0, 0, size);
  light.addColorStop(0, INK.paper); light.addColorStop(1, INK.slab);
  context.fillStyle = light; context.fillRect(0, 0, size, size);
  const block = context.createLinearGradient(0, size * print, 0, size);
  block.addColorStop(0, INK.print); block.addColorStop(1, INK.slab);
  context.fillStyle = block; context.fillRect(0, size * print, size, size * (1 - print));
  context.fillStyle = INK.broadcast; context.fillRect(0, 0, size, band);

  return texture(element);
}

/* A team's badge: its avatar in a circle with a silver ring, transparent round it. */
export function badge(image) {
  const size = SHEET.badge, half = size / 2, [element, context] = canvas(size, size);
  context.save(); context.beginPath(); context.arc(half, half, half - SHEET.ring, 0, Math.PI * 2); context.clip();
  context.fillStyle = INK.slab; context.fillRect(0, 0, size, size);
  if (image) context.drawImage(image, 0, 0, size, size);
  context.restore();
  context.strokeStyle = INK.silver; context.lineWidth = SHEET.ring;
  context.beginPath(); context.arc(half, half, half - SHEET.ring / 2, 0, Math.PI * 2); context.stroke();
  return texture(element);
}

/* A plate's record, "56-32" or "6-2", in the display face filling its line (rule 23: big enough to read on a phone). */
export function record(text) {
  const {width, height, size, margin} = SHEET.line, [element, context] = canvas(width, height);
  context.fillStyle = INK.white; context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, text, size, width - 2 * margin, DISPLAY, TUNING.displayWeight);
  context.fillText(text, width / 2, height / 2 + margin / TUNING.baselineDivisor);
  return texture(element);
}

/* The actual W-L under the all-play record, small and silver: "6-2 actual". */
export function actualLine(text) {
  const {width, height, size, margin} = SHEET.small, [element, context] = canvas(width, height);
  context.fillStyle = INK.silver; context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, text.toUpperCase(), size, width - 2 * margin, UI, TUNING.labelWeight);
  context.fillText(text.toUpperCase(), width / 2, height / 2 + margin / TUNING.baselineDivisor);
  return texture(element);
}

/* A slot's place numeral, silver on the lip's front. */
export function numeral(place) {
  const size = SHEET.numeral, [element, context] = canvas(size, size);
  context.fillStyle = INK.silver; context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, String(place), SHEET.numeralSize, size, DISPLAY, TUNING.displayWeight);
  context.fillText(String(place), size / 2, size / 2 + SHEET.border / 2);
  return texture(element);
}
