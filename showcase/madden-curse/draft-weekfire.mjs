import { DRAFT_WEEKFIRE_DETAIL as TUNING } from './constants-draft-surfaces.mjs';
import { WEEK_FIRE } from "./constants-draft-surfaces.mjs";
export { WEEK_FIRE };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { spark } from './draft-flame.mjs';
import { texture } from './draft-textures.mjs';
import { FLAME_ICON, flameIcon } from './week-flame-icon.mjs';

/* A smash week's light burns (David, revision 14: "that does not look like fire"; he prefers the old icon).
   The tile's own flame icon, in its own orange, flickers through four drawn frames (week-flame-icon.mjs),
   pulsing 1.0 to 1.08 in step with them over a soft glow that pulses too, and 2-3 embers drift up from its
   tip. It ignites on the light's pop, which sits on an onset: it scales up from nothing with a flash, then
   flickers to the end of the beat. ~~A noise-shader flame in lime and orange~~ (revision 13: a blob).
   `embers` is capped per light, so eight lights on a phone add 24 points. */

let frames = null;   // the icon's four flicker frames, drawn once and shared by every light
function iconFrames() {
  frames ??= FLAME_ICON.frames.map(frame => {
    const element = document.createElement('canvas');
    [element.width, element.height] = WEEK_FIRE.tile;
    const context = element.getContext('2d');
    context.fillStyle = css(PALETTE.boom);
    flameIcon(context, frame);
    return texture(element);
  });
  return frames;
}

function glowTexture() {
  const size = WEEK_FIRE.tile[0], half = size / 2, element = document.createElement('canvas');
  element.width = element.height = size;
  const context = element.getContext('2d'), gradient = context.createRadialGradient(half, half, 0, half, half, half);
  gradient.addColorStop(0, css(PALETTE.boom)); gradient.addColorStop(1, 'transparent');
  context.fillStyle = gradient; context.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(element);
}

const backOut = value => 1 + (WEEK_FIRE.overshoot + 1) * (value - 1) ** TUNING.backOutExponent + WEEK_FIRE.overshoot * (value - 1) ** 2;
export const flickerFrame = (seconds, seed) => ((Math.floor(seconds * FLAME_ICON.fps + seed * FLAME_ICON.frames.length) %
  FLAME_ICON.frames.length) + FLAME_ICON.frames.length) % FLAME_ICON.frames.length;

/* One week light's fire, `width` x `height` the light's size; `update` takes the beat second and the pop, 0..1. */
export function weekFire(width, height, seed) {
  const [tileWidth, tileHeight] = WEEK_FIRE.tile;
  const at = ([x, y]) => [(x / tileWidth - TUNING.tileMidpoint) * width, (TUNING.tileMidpoint - y / tileHeight) * height];
  const [pivotX, pivotY] = at(FLAME_ICON.pivot), [glowX, glowY] = at(FLAME_ICON.centre), [tipX, tipY] = at(FLAME_ICON.tip);
  const group = new THREE.Group(), textures = iconFrames();
  const geometry = new THREE.PlaneGeometry(width, height).translate(-pivotX, -pivotY, 0);   // it scales from its base
  const icon = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({map: textures[0], transparent: true, depthWrite: false, toneMapped: false}));
  icon.position.set(pivotX, pivotY, TUNING.iconZ); icon.renderOrder = TUNING.iconRenderOrder;
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(width * WEEK_FIRE.glow, width * WEEK_FIRE.glow),
    new THREE.MeshBasicMaterial({map: glowTexture(), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  glow.position.set(glowX, glowY, TUNING.glowZ); glow.renderOrder = TUNING.glowRenderOrder;
  const positions = new Float32Array(WEEK_FIRE.embers * TUNING.positionComponents), colours = new Float32Array(WEEK_FIRE.embers * TUNING.colorComponents);
  const points = new THREE.BufferGeometry();
  points.setAttribute('position', new THREE.BufferAttribute(positions, TUNING.positionComponents));
  points.setAttribute('color', new THREE.BufferAttribute(colours, TUNING.colorComponents));
  const embers = new THREE.Points(points, new THREE.PointsMaterial({size: WEEK_FIRE.emberSize, map: spark(), vertexColors: true,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false}));
  embers.renderOrder = TUNING.emberRenderOrder;
  group.add(glow, icon, embers);
  const ember = new THREE.Color(PALETTE.boom), colour = new THREE.Color();

  function update(seconds, on) {
    const ignite = Math.min(1, Math.max(0, on)), frame = flickerFrame(seconds, seed);
    const pulse = FLAME_ICON.pulse[frame], flash = Math.sin(Math.PI * ignite);
    group.visible = ignite > 0;
    icon.material.map = textures[frame];
    icon.scale.setScalar(backOut(ignite) * (1 + FLAME_ICON.scale * pulse));
    glow.material.opacity = Math.min(1, ignite * (WEEK_FIRE.glowRest + WEEK_FIRE.glowPulse * pulse) + WEEK_FIRE.flash * flash);
    glow.scale.setScalar(1 + WEEK_FIRE.flashGrow * flash + FLAME_ICON.scale * pulse);
    for (let index = 0; index < WEEK_FIRE.embers; index++) {
      const rise = (seconds * WEEK_FIRE.emberSpeed + index / WEEK_FIRE.embers + seed) % 1;
      positions.set([tipX + Math.sin(seconds * TUNING.emberSwayFrequency + index * TUNING.emberSeedStep + seed) * WEEK_FIRE.emberSway * width * rise,
        tipY + rise * WEEK_FIRE.emberRise * height, TUNING.emberZ], index * TUNING.positionComponents);
      colour.copy(ember).multiplyScalar(ignite * (1 - rise));   // additive: dimmer is fainter, so each fades as it climbs
      colours.set([colour.r, colour.g, colour.b], index * TUNING.colorComponents);
    }
    points.attributes.position.needsUpdate = points.attributes.color.needsUpdate = true;
  }
  return {group, icon, glow, embers, update};
}
