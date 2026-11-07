import { POWER_FRAME_DETAIL as TUNING } from './constants-power.mjs';
import * as THREE from 'three';

/* Fit a set of world points into a window of the frame (power-camera.mjs): the camera looks down `pitch` radians,
   square-on to the riser (yaw 0, rule 19), from the shortest distance at which every point lands inside `window`,
   in normalised device coordinates {left, right, bottom, top}. Pure, so the camera tests and the film agree. */
const FIT = Object.freeze({near: .5, far: 80, rounds: 40});   // distances searched, world units; bisection rounds

export function fitShot(points, pitch, window, fov, aspect) {
  const tan = Math.tan(THREE.MathUtils.degToRad(fov) / 2);
  const forward = new THREE.Vector3(0, -Math.sin(pitch), -Math.cos(pitch)), up = new THREE.Vector3(0, Math.cos(pitch), -Math.sin(pitch));
  const right = new THREE.Vector3(1, 0, 0), low = new THREE.Vector3(Infinity, Infinity, Infinity), high = low.clone().negate();
  points.forEach(point => { low.min(new THREE.Vector3(...point)); high.max(new THREE.Vector3(...point)); });
  const centre = low.add(high).multiplyScalar(TUNING.midpoint);
  const local = points.map(point => { const rel = new THREE.Vector3(...point).sub(centre); return {a: rel.dot(right), b: rel.dot(up), c: rel.dot(forward)}; });
  // For a distance, the band of offsets along one axis that keeps every point inside [from, to]: a point at depth
  // k (in units of the half-height) shows at (coordinate - offset) / k, so the offset lies in [p - to k, p - from k].
  const band = (distance, key, scale, from, to) => local.reduce(([lo, hi], point) => {
    const k = (distance + point.c) * tan * scale;
    return [Math.max(lo, point[key] - to * k), Math.min(hi, point[key] - from * k)];
  }, [-Infinity, Infinity]);
  const fits = distance => {
    const [xl, xh] = band(distance, 'a', aspect, window.left, window.right), [yl, yh] = band(distance, 'b', 1, window.bottom, window.top);
    return xl <= xh && yl <= yh ? {x: (xl + xh) / 2, y: (yl + yh) / 2} : null;
  };
  let near = FIT.near, far = FIT.far;
  for (let round = 0; round < FIT.rounds; round++) { const middle = (near + far) / 2; if (fits(middle)) far = middle; else near = middle; }
  const offset = fits(far), target = centre.clone().addScaledVector(right, offset.x).addScaledVector(up, offset.y);
  return {position: target.clone().addScaledVector(forward, -far), target};
}
