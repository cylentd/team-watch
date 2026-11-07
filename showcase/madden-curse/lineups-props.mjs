import { LINEUPS_PROPS_DETAIL as TUNING } from './constants-lineups.mjs';
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { stamp } from './draft-textures.mjs';
import { makeImpact } from './film-impact.mjs';
import { CARD, SHIELD, STAMP } from './lineups-layout.mjs';
import { FACE, PRINT_LAYER, defenseWord, plateFace, printed, shieldShape } from './lineups-faces.mjs';
import { LINEUPS_COPY } from './lineups-copy.mjs';

/* Chapter 4's moving pieces (docs/madden-film-chapter4.md, "Set and props"): the three DEF shields with their name,
   week and score, the two TE cards with their scores, the border-light shafts, the slot's red flash and the hits'
   sparks (film-impact.mjs). lineups-set.mjs poses them from lineups-pose.mjs every frame. ~~Six lime tokens~~
   (2026-11-05, David chose "Score slams, shield ejects"). */
export const SHAFT = Object.freeze({length: .6 * CARD.height, opacity: .55});   // storyboard: rises 0.6 card heights
// Each hit's sparks, small: a desk prop, not a title word (film-impact.mjs FULL is the title's CURSE).
export const HIT = Object.freeze({ring: .45, sparks: .3, dust: .6, tone: 'lime', second: 0, carpet: false});
const SHIELD_PRINT = Object.freeze({logo: .26, logoSize: .22, name: .07, week: -.055, score: -.25, nameWidth: .5, weekHeight: .1, scoreHeight: .2});
// The plate's bevelled edge catches the key and the rim (rule 35: polished silver, not a grey slab).
const BEVEL = Object.freeze({bevelEnabled: true, bevelSize: .014, bevelThickness: .014, bevelSegments: 3});
// Chapter 1's materials (draft-board.mjs): a card's metal sides, and the plate's polished face.
const METAL = Object.freeze({side: {metalness: .6, roughness: .35}, plate: {metalness: .45, roughness: .3}});
// A card's name band, in world units, and its score stamp just under it: the top of the card is what a phone's
// crane keeps of the other card at the frame's bottom edge, so the name and the score stay in frame together.
const BAND = CARD.height * FACE.band / FACE.height, STAMP_GAP = .015;

let fade = null;   // one vertical fade for every shaft, opaque at its root
function fadeTexture() {
  if (fade) return fade;
  const element = document.createElement('canvas'); element.width = TUNING.sleeveTextureWidth; element.height = TUNING.sleeveTextureHeight;
  const context = element.getContext('2d'), ramp = context.createLinearGradient(0, TUNING.sleeveTextureHeight, 0, 0);
  ramp.addColorStop(0, css(PALETTE.white)); ramp.addColorStop(1, `${css(PALETTE.white)}00`);
  context.fillStyle = ramp; context.fillRect(0, 0, TUNING.sleeveTextureWidth, TUNING.sleeveTextureHeight);
  fade = new THREE.CanvasTexture(element);
  return fade;
}

/* A shaft of light up the four sides of a `width` x `depth` mouth (rule 46: light rises from a rectangular border). */
function sleeve(width, depth, color) {
  const group = new THREE.Group();
  const material = new THREE.MeshBasicMaterial({color, map: fadeTexture(), transparent: true, opacity: 0, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false});
  [[width, 0, depth / 2, 0], [width, 0, -depth / 2, 0], [depth, width / 2, 0, Math.PI / 2], [depth, -width / 2, 0, Math.PI / 2]]
    .forEach(([across, x, z, turn]) => {
      const side = new THREE.Mesh(new THREE.PlaneGeometry(across, 1), material);
      side.position.set(x, TUNING.sleeveSideY, z); side.rotation.y = turn; group.add(side);
    });
  return {group, update(strength) {
    group.visible = strength > 0;
    group.scale.y = SHAFT.length;
    material.opacity = SHAFT.opacity * strength;
  }};
}

const sideMetal = () => new THREE.MeshStandardMaterial({color: PALETTE.slabEdge, ...METAL.side});

/* A DEF shield: a bevelled silver plate on a steel body, its name printed, and its week and score stamps keyed so the
   set can slam them (lineups-pose.mjs shieldStamps). */
function shield(entry) {
  const group = new THREE.Group(), labels = [];
  const face = new THREE.MeshStandardMaterial({color: PALETTE.white, map: plateFace(), ...METAL.plate});
  const body = new THREE.Mesh(new THREE.ExtrudeGeometry(shieldShape(), {depth: SHIELD.depth, ...BEVEL}), [face, sideMetal()]);
  body.position.z = -SHIELD.depth / 2;
  const front = SHIELD.depth / 2 + BEVEL.bevelThickness + TUNING.shieldPrintZ, ink = entry.negative ? PALETTE.down : PALETTE.blue;
  const name = printed(defenseWord(entry.name.toUpperCase()), SHIELD_PRINT.nameWidth, SHIELD_PRINT.nameWidth / TUNING.defenseNameAspect, entry.name.toUpperCase(), 'name');
  const started = LINEUPS_COPY.defenseCard.started.replace('{week}', entry.week.slice(1));
  const points = LINEUPS_COPY.defenseCard.points.replace('{score}', entry.score);
  const week = printed(defenseWord(started), SHIELD_PRINT.nameWidth, SHIELD_PRINT.weekHeight, started, 'stamp');
  const score = printed(stamp(points, ink), SHIELD_PRINT.nameWidth, SHIELD_PRINT.scoreHeight, points, 'stamp');
  const win = new THREE.Object3D();
  const logo = printed(null, SHIELD_PRINT.logoSize, SHIELD_PRINT.logoSize, '', 'logo');
  logo.position.set(0, SHIELD_PRINT.logo, front);
  week.userData.key = 'week'; score.userData.key = 'score'; win.userData.key = 'win';
  [[name, SHIELD_PRINT.name], [week, SHIELD_PRINT.week], [score, SHIELD_PRINT.score]].forEach(([mesh, y]) => { mesh.position.set(0, y, front); labels.push(mesh); });
  group.add(body, logo, name, week, score);
  return {group, labels, logo, stamps: {week, score, win}};
}

/* A TE card: its face (the portrait texture arrives in `face`), Chapter 1's metal sides, and the score stamps it carries. */
function card(player, stamps) {
  const group = new THREE.Group(), labels = [];
  const material = new THREE.MeshBasicMaterial({color: PALETTE.white, toneMapped: false});
  const face = new THREE.Mesh(new THREE.PlaneGeometry(CARD.width, CARD.height), material);
  face.position.z = CARD.depth / 2 + PRINT_LAYER.face;
  // The readout measures the printed name, the band (lineups-readout.mjs), not the whole portrait.
  face.userData = {text: player.name, kind: 'card', width: CARD.width, height: BAND, offsetY: (CARD.height - BAND) / 2};
  const back = new THREE.Mesh(new THREE.BoxGeometry(CARD.width, CARD.height, CARD.depth), sideMetal());
  group.add(back, face); labels.push(face);
  const printedStamps = stamps.map(({key, text, scale, color}) => {
    const ink = color === PALETTE.brandLime ? PALETTE.print : PALETTE.white;
    const mesh = printed(stamp(text, color, ink), STAMP.width, STAMP.height, text, 'stamp');
    mesh.position.set(0, CARD.height / 2 - BAND - STAMP_GAP - STAMP.height * scale / 2, CARD.depth / 2 + PRINT_LAYER.ink);
    mesh.userData.key = key; mesh.userData.full = scale;
    group.add(mesh); labels.push(mesh);
    return mesh;
  });
  return {group, labels, material, stamps: printedStamps};
}

export function makeProps(cast, scales) {
  const group = new THREE.Group();
  const shields = cast.defense.map(shield);
  // Stamps ride their player's card: Fannin's 0.90 then 18.40, Henry's 11.90 then 4.50 (lineups-pose.mjs `card`).
  const [w5, w8] = cast.tightends, lime = PALETTE.brandLime, blue = PALETTE.broadcast;
  const cards = [card(w5.starter, [{key: 's5start', text: w5.starter.score, scale: scales.s5start, color: blue}, {key: 's8bench', text: w8.bench.score, scale: scales.s8bench, color: lime}]),
    card(w5.bench, [{key: 's5bench', text: w5.bench.score, scale: scales.s5bench, color: lime}, {key: 's8start', text: w8.starter.score, scale: scales.s8start, color: blue}])];
  const mouth = SHIELD.width + TUNING.defenseSleevePadding;
  // The slot's DEF purple shaft on each landing, and the red one that flashes as a negative shield is kicked out.
  const shafts = {gibbs: sleeve(mouth, TUNING.sleeveHeight, PALETTE.DEF), flash: sleeve(mouth, TUNING.sleeveHeight, PALETTE.down),
    start: sleeve(CARD.width + TUNING.starterSleevePadding, TUNING.sleeveHeight, PALETTE.TE), rack: sleeve(CARD.width, CARD.height, PALETTE.TE)};
  shafts.rack.group.rotation.x = Math.PI / 2;   // the rack's shaft fires toward the camera, never up into the headline (rule 36)
  group.add(...shields.map(entry => entry.group), ...cards.map(entry => entry.group), ...Object.values(shafts).map(entry => entry.group));
  const impacts = {gibbs: makeImpact(group), start: makeImpact(group), rack: makeImpact(group)};
  const labels = [...shields.flatMap(entry => entry.labels), ...cards.flatMap(entry => entry.labels)];
  return {group, shields, cards, shafts, impacts, labels};
}
