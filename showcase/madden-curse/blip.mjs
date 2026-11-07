import { BLIP_DETAIL as TUNING } from './constants-opening.mjs';
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';

const SIZE = Object.freeze({width: .72, height: .57, depth: .25, corner: .1, screenDepth: .015});
// The scared face (rev 17): eyes 1.45x, and a flat zig-zag mouth across the smile's width, its points [x, y].
const SCARED = Object.freeze({eyes: 1.45, mouth: [[-.09, -.08], [-.045, -.065], [0, -.08], [.045, -.065], [.09, -.08]]});

function roundedBox(width, height, depth, radius, material) {
  const shape = new THREE.Shape(), left = -width / 2, bottom = -height / 2;
  shape.moveTo(left + radius, bottom);
  shape.lineTo(left + width - radius, bottom);
  shape.quadraticCurveTo(left + width, bottom, left + width, bottom + radius);
  shape.lineTo(left + width, bottom + height - radius);
  shape.quadraticCurveTo(left + width, bottom + height, left + width - radius, bottom + height);
  shape.lineTo(left + radius, bottom + height);
  shape.quadraticCurveTo(left, bottom + height, left, bottom + height - radius);
  shape.lineTo(left, bottom + radius);
  shape.quadraticCurveTo(left, bottom, left + radius, bottom);
  const mesh = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, {
    depth, bevelEnabled: true, bevelThickness: TUNING.bevelThickness, bevelSize: TUNING.bevelSize, bevelSegments: TUNING.bevelSegments, steps: 1,
  }), material);
  mesh.castShadow = true;
  return mesh;
}

function limb(start, end, radius, material) {
  const from = new THREE.Vector3(...start), to = new THREE.Vector3(...end);
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, from.distanceTo(to), TUNING.limbSegments), material);
  mesh.position.copy(from).add(to).multiplyScalar(TUNING.midpoint);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), to.sub(from).normalize());
  return mesh;
}

export function makeBlip() {
  const root = new THREE.Group(), head = new THREE.Group();
  const casing = new THREE.MeshStandardMaterial({color: PALETTE.silver, emissive: PALETTE.blipCase,
    emissiveIntensity: TUNING.casingEmission, envMapIntensity: TUNING.casingEnvironment, metalness: TUNING.casingMetalness, roughness: TUNING.casingRoughness});
  const screen = new THREE.MeshStandardMaterial({color: PALETTE.blipScreen, roughness: TUNING.screenRoughness, metalness: TUNING.screenMetalness});
  const ink = new THREE.MeshBasicMaterial({color: PALETTE.lime, toneMapped: false});
  head.add(roundedBox(SIZE.width, SIZE.height, SIZE.depth, SIZE.corner, casing));
  const face = roundedBox(TUNING.faceWidth, TUNING.faceHeight, SIZE.screenDepth, TUNING.faceCorner, screen);
  face.position.set(0, TUNING.faceY, TUNING.faceZ);
  head.add(face);
  const eyes = [TUNING.leftEyeX, TUNING.rightEyeX].map(horizontal => {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(TUNING.eyeRadius, TUNING.eyeWidthSegments, TUNING.eyeHeightSegments), ink);
    eye.scale.z = TUNING.eyeDepthScale;
    eye.position.set(horizontal, TUNING.eyeY, TUNING.eyeZ);
    head.add(eye);
    return eye;
  });
  const curve = points => new THREE.Mesh(new THREE.TubeGeometry(
    new THREE.CatmullRomCurve3(points.map(([x, y]) => new THREE.Vector3(x, y, TUNING.mouthZ))), TUNING.mouthSegments, TUNING.mouthRadius, TUNING.mouthRadialSegments, false), ink);
  const smile = curve([[TUNING.smileLeftX, TUNING.smileEdgeY], [0, TUNING.smileCenterY], [TUNING.smileRightX, TUNING.smileEdgeY]]);
  const wavy = curve(SCARED.mouth);
  wavy.visible = false;
  head.add(smile, wavy);
  head.add(limb([0, TUNING.antennaBaseY, TUNING.antennaZ], [0, TUNING.antennaTipY, TUNING.antennaZ], TUNING.antennaRadius, casing));
  const bulb = new THREE.Mesh(new THREE.SphereGeometry(TUNING.bulbRadius, TUNING.bulbWidthSegments, TUNING.bulbHeightSegments), ink);
  bulb.position.set(0, TUNING.bulbY, TUNING.bulbZ);
  head.add(bulb);
  head.position.y = TUNING.headY;
  root.add(head);
  for (const direction of [-1, 1]) {
    root.add(limb([direction * TUNING.shoulderX, TUNING.shoulderY, TUNING.shoulderZ], [direction * TUNING.handX, TUNING.handY, TUNING.handZ], TUNING.armRadius, casing));
    root.add(limb([direction * TUNING.ankleX, TUNING.ankleY, TUNING.ankleZ], [direction * TUNING.toeX, TUNING.toeY, TUNING.toeZ], TUNING.footRadius, casing));
  }
  return {root, head, face: {eyes, smile, wavy}};
}

/* Blip's scared face (David rev 17): eyes SCARED.eyes times wider and taller, the smile swapped for a wavy mouth. */
export function blipFace(blip, scared) {
  const size = scared ? SCARED.eyes : 1;
  blip.face.eyes.forEach(eye => { eye.scale.x = size; eye.scale.y = size; });
  blip.face.smile.visible = !scared;
  blip.face.wavy.visible = scared;
}
