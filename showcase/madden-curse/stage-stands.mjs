import { STAGE_STANDS_DETAIL as TUNING } from './constants-lighting.mjs';
import { STANDS } from "./constants-lighting.mjs";
export { STANDS };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { spark } from './draft-flame.mjs';

/* The stadium behind the rig (David, chapter 17: "the huge black area top-left"): a faint ring of stand tiers
   round the stage and the far crowd's lights as soft bokeh, so no corner of the frame is empty black. It sits
   past the fog's reach, so it ignores the fog and stays this dim on its own. */

const random = (index, salt) => { const value = Math.sin(index * TUNING.randomIndexMultiplier + salt * TUNING.randomSaltMultiplier) * TUNING.randomOutputMultiplier; return value - Math.floor(value); };

/* The stand's face: dark tiers, each with a faint rail of light along its foot. */
function tiers() {
  const {width, height} = STANDS.texture, element = document.createElement('canvas');
  element.width = width; element.height = height;
  const context = element.getContext('2d'), row = height / STANDS.tiers;
  context.fillStyle = css(PALETTE.background); context.fillRect(0, 0, width, height);
  for (let tier = 0; tier < STANDS.tiers; tier++) {
    const shade = context.createLinearGradient(0, tier * row, 0, (tier + 1) * row);
    shade.addColorStop(0, css(PALETTE.background)); shade.addColorStop(1, css(PALETTE.stand));
    context.fillStyle = shade; context.fillRect(0, tier * row, width, row * (1 - STANDS.tierLine));
    context.fillStyle = css(PALETTE.slab); context.fillRect(0, (tier + 1 - STANDS.tierLine) * row, width, row * STANDS.tierLine * TUNING.tierLineOpacity);
  }
  const map = new THREE.CanvasTexture(element);
  map.colorSpace = THREE.SRGBColorSpace; map.wrapS = THREE.RepeatWrapping;
  return map;
}

export function makeStands() {
  const group = new THREE.Group(), {radius, bottom, top, segments, opacity, bokeh} = STANDS;
  const wall = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, top - bottom, segments, 1, true),
    new THREE.MeshBasicMaterial({map: tiers(), color: new THREE.Color(1, 1, 1).multiplyScalar(STANDS.lift), side: THREE.BackSide, transparent: true, opacity, fog: false, depthWrite: false}));
  wall.position.y = (top + bottom) / 2;
  const positions = new Float32Array(bokeh.count * TUNING.positionComponents), colours = new Float32Array(bokeh.count * TUNING.colorComponents);
  const crowd = new THREE.Color(PALETTE.crowd), colour = new THREE.Color();
  for (let index = 0; index < bokeh.count; index++) {
    const angle = random(index, 1) * Math.PI * 2, height = bokeh.low + (bokeh.high - bokeh.low) * random(index, 2) ** TUNING.heightDistributionExponent;
    const near = radius - bokeh.inset;
    positions.set([Math.cos(angle) * near, height, Math.sin(angle) * near], index * TUNING.positionComponents);
    colour.copy(crowd).multiplyScalar(bokeh.opacity * (TUNING.glowBaseline + TUNING.glowRange * random(index, TUNING.glowSalt)));
    colours.set([colour.r, colour.g, colour.b], index * TUNING.colorComponents);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, TUNING.positionComponents));
  geometry.setAttribute('color', new THREE.BufferAttribute(colours, TUNING.colorComponents));
  const lights = new THREE.Points(geometry, new THREE.PointsMaterial({map: spark(), vertexColors: true, size: bokeh.size[1],
    sizeAttenuation: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false}));
  wall.renderOrder = lights.renderOrder = -1;   // behind everything on the stage
  group.add(wall, lights);
  return {group};
}
