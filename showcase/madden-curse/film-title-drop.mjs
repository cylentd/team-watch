import { FILM_TITLE_DROP_DETAIL as TUNING } from './constants-title.mjs';
import { TITLE_DROP, RIM, PAINT } from "./constants-title.mjs";
export { TITLE_DROP, RIM };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { COPY } from './content.mjs';
import { fontsReady } from './draft-textures.mjs';
import { TITLE_WORDS } from './timing.mjs';
import { flareAmount } from './film-flare.mjs';
import { HANDOVER, zoomAmount } from './film-zoom.mjs';
import { TITLE_FONT } from "./film-title-place.mjs";

/* The title lands (David, revision 14: "it must LAND, not fade in"). Each word of THE MADDEN CURSE is a heavy
   block of stacked letter layers that falls from above the frame, tipped back so its thickness shows, and slams
   flat into the lower third on its own hit of the three-hit "dun dun dunnn" (timing.json `opening.titleWords`;
   THE on OPENING.logoAt, with Blip's last landing). On its hit frame a word squashes for one film frame;
   film-impact.mjs plays its burst, and the beams flash (`titleFlash`). The last word's hit is the biggest
   (`hits`) and only it shakes the camera, for three frames, and lights a lime rim on the trophy (`rimAmount`).
   Chapter 17, David's look: Team Watch's palette. THE MADDEN in the site's warm ink with a bevel, CURSE in the
   brand lime with a glow (~~a red slash before THE~~), the site's condensed display face (the lower third's,
   --display) set tighter, and a deeper extrusion with dark sides. ~~Chrome-white letters, 10 layers 0.3
   deep~~ (rev 14). The zoom into the ball (film-zoom.mjs) drops the title out of frame.
   The letters live in the camera's frame, `distance` in front of it, left-aligned at `left` with the last
   row's baseline at `baseline` (fractions of the frame). A desktop sets one row `width` of the frame wide;
   the tagline sits at the row's right end on its baseline. A phone sets two rows, THE MADDEN over CURSE, its
   tagline under them (film-title-place.mjs). ~~On the stage floor in front of the trophy~~ (revision 14). */

/* The lime rim on the trophy at CURSE's hit: up in `rise` seconds, then settling over `settle` to `rest` of its
   peak for the hold. A point light behind the trophy's right shoulder, in world units. */

const WORDS = `${COPY.titleTop} ${COPY.titleBottom}`.split(' ');
if (WORDS.length !== TITLE_WORDS.length || WORDS.length !== TITLE_DROP.hits.length)
  throw new Error(`timing.json: opening.titleWords has ${TITLE_WORDS.length} times for ${WORDS.length} title words`);

/* One word `time` seconds into the film, landing at `at`: hidden until it falls, then in the bar. `drop` runs 1
   at the top of the fall to 0 on the hit, accelerating; `squash` is its hit frame. */
function wordDrop(time, at) {
  const age = time - at, {fall, frame} = TITLE_DROP;
  const fallen = age < 0 ? (age + fall) / fall : 1;
  return {age, visible: age >= -fall, drop: age < 0 ? 1 - fallen * fallen : 0,
    squash: age >= 0 && Math.floor(age / frame + TUNING.frameEpsilon) === 0};
}

/* Every word, in order, `time` seconds into the film. */
export const titleWords = time => WORDS.map((word, index) => ({word, at: TITLE_WORDS[index], hit: TITLE_DROP.hits[index],
  ...wordDrop(time, TITLE_WORDS[index])}));

/* The camera's offset from the last word's hit: three frames, then still. */
export function titleShake(time) {
  const age = time - TITLE_WORDS[TITLE_WORDS.length - 1], step = Math.floor(age / TITLE_DROP.frame + TUNING.frameEpsilon);
  return age >= 0 && step < TITLE_DROP.shake.length ? [...TITLE_DROP.shake[step]] : [0, 0];
}

/* The beams' flash, 0..1: each word's hit flares them by its `flash`. */
export const titleFlash = time => Math.max(0, ...titleWords(time).map(word => flareAmount(word.age) * word.hit.flash));

/* The lime rim's strength, 0..1, `time` seconds into the film. */
export function rimAmount(time) {
  const age = time - TITLE_WORDS[TITLE_WORDS.length - 1], {rise, settle, rest} = RIM;
  if (age < 0) return 0;
  if (age < rise) return age / rise;
  const fade = Math.min(1, (age - rise) / settle);
  return rest + (1 - rest) * (1 - fade) ** 2;
}

/* The last word, the title's biggest hit, with the camera's shake. */
export function titleDrop(time) {
  const words = titleWords(time), last = words[words.length - 1];
  return {age: last.age, visible: last.visible, drop: last.drop, squash: last.squash, shake: titleShake(time)};
}

/* The front face's paint per tone: a vertical gradient with a darker horizon band, like lit metal. */

function face(text, tone, front) {
  const {line, pad} = TITLE_DROP.texture, {tracking, bevel, glow} = TITLE_DROP.look;
  const element = document.createElement('canvas'), font = `${TITLE_FONT.weight} ${line}px ${TITLE_FONT.family}`, spacing = `${tracking * line}px`;
  const probe = element.getContext('2d'); probe.font = font; probe.letterSpacing = spacing;
  const metrics = probe.measureText(text), cap = probe.measureText('H').actualBoundingBoxAscent;
  const ink = metrics.width - tracking * line;   // letterSpacing also trails the last letter
  probe.letterSpacing = '0px';
  const space = probe.measureText(' ').width;
  element.width = Math.ceil(ink + pad * 2);
  element.height = line + pad * 2;
  const context = element.getContext('2d');
  context.font = font; context.letterSpacing = spacing; context.textAlign = 'left'; context.textBaseline = 'alphabetic';
  const x = pad, y = pad + line;
  if (front) {
    const paint = context.createLinearGradient(0, pad + line - cap, 0, y);
    PAINT[tone].forEach(([stop, colour]) => paint.addColorStop(stop, css(colour)));
    if (tone === 'lime') {   // the glow: the letters blurred in lime under the face
      context.shadowColor = css(PALETTE.brandLime); context.shadowBlur = glow * line;
      context.fillStyle = css(PALETTE.brandLime); context.fillText(text, x, y);
      context.shadowBlur = 0;
    }
    // The bevel: a shaded edge down-right and a lit one up-left, the face over them.
    const edge = bevel * line;
    context.fillStyle = css(tone === 'lime' ? PALETTE.limeShade : PALETTE.inkShade); context.fillText(text, x + edge, y + edge);
    context.fillStyle = css(PALETTE.white); context.fillText(text, x - edge * TUNING.edgeHighlightRatio, y - edge * TUNING.edgeHighlightRatio);
    context.fillStyle = paint; context.fillText(text, x, y);
  } else {
    const side = context.createLinearGradient(0, pad, 0, y);
    side.addColorStop(0, css(PALETTE.sideFace)); side.addColorStop(1, css(PALETTE.background));
    context.fillStyle = side; context.fillText(text, x, y);
  }
  const map = new THREE.CanvasTexture(element);
  map.colorSpace = THREE.SRGBColorSpace; map.anisotropy = TUNING.textureAnisotropy;
  return {map, width: element.width / line, height: element.height / line, pad: pad / line,
    ink: ink / line, space: space / line, cap: cap / line};
}

const material = map => new THREE.MeshBasicMaterial({map, transparent: true, depthWrite: false, depthTest: false, toneMapped: false, fog: false});

/* Stack `layers` copies of a front mesh and its side meshes back along the word's depth. */
function extrude(group, geometry, front, side) {
  for (let layer = TITLE_DROP.layers - 1; layer >= 0; layer--) {
    const mesh = new THREE.Mesh(geometry, layer ? side : front);
    mesh.position.z = -TITLE_DROP.depth * layer / (TITLE_DROP.layers - 1);
    mesh.renderOrder = TITLE_DROP.order + TITLE_DROP.layers - layer;   // the back layers first, the face last
    group.add(mesh);
  }
}

/* One word one font size tall, its origin on its first letter's left edge at its baseline, so it squashes onto
   the bar. */
function letters(text, index) {
  const group = new THREE.Group(), tone = TITLE_DROP.hits[index].tone, front = face(text, tone, true), side = face(text, tone, false);
  const geometry = new THREE.PlaneGeometry(front.width, front.height)
    .translate(front.width / 2 - front.pad, front.height / 2 - front.pad, 0);
  extrude(group, geometry, material(front.map), material(side.map));
  Object.assign(group.userData, {ink: front.ink, space: front.space, cap: front.cap});
  return group;
}

const view = new THREE.Vector3();
/* A frame point (fractions from the top left) in the camera's own space, `distance` in front of it. The
   projection includes the film's view offset, so the bar lands where the CSS bar is. */
function inFrame(camera, x, y) {
  view.set(x * 2 - 1, 1 - y * 2, TUNING.projectionDepth).applyMatrix4(camera.projectionMatrixInverse);
  return view.multiplyScalar(TITLE_DROP.distance / -view.z).clone();
}

/* Where each word sits, in font sizes from the title's foot: [x, y] of its origin, for `place`'s rows, and the
   font size in world units, from the frame's width and height there. */
function layout(words, place, frameWidth, frameHeight) {
  const {space, cap} = words[0].userData, ink = words.map(word => word.userData.ink);
  const rowInk = place.rows.map(row => row.reduce((sum, index) => sum + ink[index], 0) + space * (row.length - 1));
  const byWidth = place.width * frameWidth / Math.max(...rowInk), byCap = place.cap ? place.cap * frameHeight / cap : Infinity;
  const size = Math.min(byWidth, byCap), spots = [];
  place.rows.forEach((row, rowIndex) => {
    let x = 0;
    row.forEach(index => { spots[index] = [x, (place.rows.length - 1 - rowIndex) * TITLE_DROP.leading]; x += ink[index] + space; });
  });
  return {size, spots};
}

/* The title's two builds (a desktop's one row, a phone's two) in a group that rides with the camera, the lime
   rim on the trophy, and `pose(time, mobile, camera)`, which places every word and returns each word's drop
   with its foot's centre and half-width, the frame there (all in that group's space, for its impact), the
   camera's shake and the beams' flash. */
export async function makeTitleDrop(scene) {
  await fontsReady();
  await document.fonts.load(`${TITLE_FONT.weight} 100px ${TITLE_FONT.family}`);
  const builds = {desk: WORDS.map(letters), phone: WORDS.map(letters)};
  const hud = new THREE.Group(), root = new THREE.Group();
  const rim = new THREE.PointLight(PALETTE.brandLime, 0, RIM.distance, RIM.decay);
  rim.position.set(...RIM.position); scene.add(rim);
  hud.matrixAutoUpdate = false;
  root.add(...builds.desk, ...builds.phone); hud.add(root); hud.visible = false; scene.add(hud);
  return {hud, root, rim, hide() { hud.visible = false; rim.intensity = 0; },
    pose(time, mobile, camera) {
      camera.updateMatrixWorld(); camera.updateProjectionMatrix();
      hud.matrix.copy(camera.matrixWorld); hud.matrixWorldNeedsUpdate = true;
      const device = mobile ? 'phone' : 'desk', place = TITLE_DROP[device], shown = builds[device];
      builds.desk.forEach(word => { word.visible = false; }); builds.phone.forEach(word => { word.visible = false; });
      const foot = inFrame(camera, place.left, place.baseline), top = inFrame(camera, place.left, 0);
      const frameLeft = inFrame(camera, 0, place.baseline).x;
      const frameWidth = inFrame(camera, place.left + 1, place.baseline).x - foot.x, frameHeight = (top.y - foot.y) / place.baseline;
      const {size, spots} = layout(shown, place, frameWidth, frameHeight), fallFrom = top.y - foot.y + size;
      const slide = HANDOVER.slide * frameHeight * zoomAmount(time);   // out of frame with the zoom into the ball
      const words = titleWords(time).map((drop, index) => {
        const word = shown[index], [x, y] = spots[index], [wide, low] = drop.squash ? TITLE_DROP.squash : [1, 1];
        word.visible = drop.visible;
        word.position.set(foot.x + x * size, foot.y + y * size + fallFrom * drop.drop - slide, foot.z);
        word.rotation.x = -TITLE_DROP.tilt * drop.drop;
        word.scale.set(size * wide, size * low, size);
        const halfWidth = word.userData.ink * size / 2;
        return {...drop, halfWidth, mobile, frameLeft, frameWidth,
          centre: new THREE.Vector3(foot.x + x * size + halfWidth, foot.y + y * size - slide, foot.z)};
      });
      hud.visible = words.some(word => word.visible);
      rim.intensity = RIM.intensity * rimAmount(time);
      return {words, frameHeight, shake: titleShake(time), flash: titleFlash(time)};
    }};
}
