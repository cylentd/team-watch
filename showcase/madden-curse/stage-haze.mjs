import { HAZE } from "./constants-lighting.mjs";
export { HAZE };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';

export const HAZE_VERTEX = `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
const VERTEX = HAZE_VERTEX;
/* Value noise, shared with the title's floor haze (film-flare.mjs). */
export const HAZE_NOISE = `
  float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p) {
    vec2 cell = floor(p), part = fract(p); part = part * part * (3.0 - 2.0 * part);
    return mix(mix(hash(cell), hash(cell + vec2(1.0, 0.0)), part.x),
      mix(hash(cell + vec2(0.0, 1.0)), hash(cell + vec2(1.0)), part.x), part.y);
  }`;
const FRAGMENT = `
  uniform float time; uniform float seed; uniform float opacity; uniform vec3 colour;
  varying vec2 vUv;
  ${HAZE_NOISE}
  void main() {
    vec2 flow = vec2(vUv.x * 7.0 + time * 0.07 + seed, vUv.y * 2.0);
    float wisps = noise(flow) * 0.6 + noise(flow * 2.3 + vec2(time * 0.03, seed)) * 0.4;
    float sides = smoothstep(0.0, 0.18, vUv.x) * (1.0 - smoothstep(0.82, 1.0, vUv.x));
    float low = smoothstep(0.0, 0.28, vUv.y) * (1.0 - smoothstep(0.4, 1.0, vUv.y));
    gl_FragColor = vec4(colour, sides * low * smoothstep(0.12, 0.8, wisps) * opacity);
  }`;

export function makeHaze() {
  const group = new THREE.Group(), geometry = new THREE.PlaneGeometry(HAZE.width, HAZE.height);
  HAZE.layers.forEach((layer, index) => {
    const material = new THREE.ShaderMaterial({vertexShader: VERTEX, fragmentShader: FRAGMENT,
      uniforms: {time: {value: 0}, seed: {value: index}, opacity: {value: HAZE.opacity},
        colour: {value: new THREE.Color(PALETTE.silver)}},
      transparent: true, depthWrite: false, toneMapped: false, side: THREE.DoubleSide});
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(layer.x, layer.y, layer.z); group.add(mesh);
  });
  function update(seconds, camera) {
    group.children.forEach(mesh => {
      mesh.material.uniforms.time.value = seconds;
      mesh.rotation.y = Math.atan2(camera.x - mesh.position.x, camera.z - mesh.position.z);
    });
  }
  return {group, update};
}
