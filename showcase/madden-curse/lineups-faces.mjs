import { LINEUPS_FACES_DETAIL as TUNING } from './constants-lineups.mjs';
import { PLATE } from "./constants-lineups.mjs";
export { PLATE };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { texture } from './draft-textures.mjs';
import { SHIELD } from './lineups-layout.mjs';

/* The printed faces of Chapter 4's desk: the two TE cards, the badges, and the shield's outline. Words that are
   textures carry their text in `userData`, so the set's readout and the tests can name them (lineups-set.mjs). */
const UI = 'Archivo, sans-serif';
// A card face at the 512 px portrait's own width (rule 24): the name band on top, so a phone's crane, which keeps
// the other card at the frame's edge, still shows that card's name (composition table).
export const FACE = Object.freeze({width: 512, height: 672, band: 92, name: 58, rule: 8, inset: 12});
export const BADGE = 256;
export const PRINT_LAYER = Object.freeze({face: .008, ink: .016});
export function defenseWord(text) {
  const [element, context] = canvas(FACE.width, FACE.band);
  context.fillStyle = css(PALETTE.print); context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, text, FACE.name, FACE.width - FACE.inset * 2, UI, TUNING.defenseNameWeight);
  context.fillText(text, FACE.width / 2, FACE.band / 2);
  return texture(element);
}

/* An image that must arrive: rejects on an error, so a missing portrait fails the room (rule 49), unlike
   draft-textures.mjs loadImage, which falls back a size. */
export function loadStrict(source) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Lineup asset unavailable: ' + source));
    image.src = source;
  });
}

function canvas(width, height) {
  const element = document.createElement('canvas');
  element.width = width; element.height = height;
  return [element, element.getContext('2d')];
}

function fit(context, text, size, width, face, weight) {
  let px = size;
  do { context.font = `${weight} ${px}px ${face}`; px -= 1; } while (context.measureText(text).width > width && px > size / 2);
}

/* A TE card: the name in the position's teal band, the 512 px portrait under it. */
export function cardFace(name, image) {
  const [element, context] = canvas(FACE.width, FACE.height), teal = css(PALETTE.TE);
  context.fillStyle = css(PALETTE.cardSurface); context.fillRect(0, 0, FACE.width, FACE.height);
  const top = FACE.band, size = FACE.height - top;
  context.drawImage(image, (FACE.width - size) / 2, top, size, size);
  context.fillStyle = css(PALETTE.print); context.fillRect(0, 0, FACE.width, FACE.band);
  context.fillStyle = teal; context.fillRect(0, FACE.band - FACE.rule, FACE.width, FACE.rule);
  context.fillStyle = css(PALETTE.white); context.textAlign = 'center'; context.textBaseline = 'middle';
  fit(context, name, FACE.name, FACE.width - FACE.inset * 2, UI, TUNING.playerNameWeight);
  context.fillText(name, FACE.width / 2, (FACE.band - FACE.rule) / 2 + FACE.rule / 2);
  return texture(element);
}

/* A manager's badge, cut round. */
export function badgeFace(image) {
  const [element, context] = canvas(BADGE, BADGE);
  context.beginPath(); context.arc(BADGE / 2, BADGE / 2, BADGE / 2, 0, Math.PI * 2); context.clip();
  context.drawImage(image, 0, 0, BADGE, BADGE);
  return texture(element);
}

/* The DEF shield: straight sides down to `shoulder` above its foot, then tapering to a `tip`-wide foot, centred. */
export function shieldShape() {
  const half = SHIELD.width / 2, height = SHIELD.height;
  const shape = new THREE.Shape();
  shape.moveTo(-half, height / 2); shape.lineTo(half, height / 2); shape.lineTo(half, -height / 2);
  shape.lineTo(-half, -height / 2); shape.closePath();
  return shape;
}

/* The shield's broadcast plate (David 2026-11-05: "grey slabs"): polished silver falling from paper-bright at the top
   to steel at the foot, brushed, with a bright bevel line and a dark keyline inside its outline, like Chapter 1's
   hero cards. Mapped onto the extruded cap, whose UVs are the shape's own units (see `plateMap`). */

export function plateFace() {
  const width = PLATE.width, height = Math.round(width * SHIELD.height / SHIELD.width), [element, context] = canvas(width, height);
  const outline = inset => {
    const scale = 1 - inset * 2 / width, points = shieldShape().getPoints();
    context.beginPath();
    points.forEach(({x, y}, index) => {
      const px = (x * scale / SHIELD.width + TUNING.textureCenter) * width, py = (TUNING.textureCenter - y * scale / SHIELD.height) * height;
      if (index) context.lineTo(px, py); else context.moveTo(px, py);
    });
    context.closePath();
  };
  const fall = context.createLinearGradient(0, 0, 0, height);
  [PALETTE.paper, PALETTE.silver, PALETTE.muted].forEach((color, index) => fall.addColorStop(PLATE.stops[index], css(color)));
  context.fillStyle = fall; context.fillRect(0, 0, width, height);

  outline(PLATE.bevel); context.lineWidth = PLATE.bevelLine; context.strokeStyle = css(PALETTE.white) + PLATE.bevelAlpha; context.stroke();

  return plateMap(texture(element));
}
/* The cap's UVs run in world units across the shape, centred on 0: scale and shift the texture to fill it. */
function plateMap(map) {
  map.repeat.set(1 / SHIELD.width, 1 / SHIELD.height); map.offset.set(TUNING.textureCenter, TUNING.textureCenter);
  return map;
}

/* A plane printing `map`, tagged with the words it shows. */
export function printed(map, width, height, text, kind, options = {}) {
  const material = new THREE.MeshBasicMaterial({map, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1, toneMapped: false, ...options});
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, height), material);
  mesh.userData = {text, kind, width, height};
  return mesh;
}
