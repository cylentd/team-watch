import { ENVIRONMENT_DETAIL as TUNING } from './constants-opening.mjs';
import { STAGE } from "./constants-opening.mjs";
export { STAGE };
import * as THREE from 'three';
import { PALETTE, css } from './constants.mjs';
import { makeRig } from './stage-lights.mjs';
import { makeHaze } from './stage-haze.mjs';
import { makeStands } from './stage-stands.mjs';

function background() {
  const canvas = document.createElement('canvas');
  canvas.width = TUNING.fogWidth; canvas.height = TUNING.fogHeight;
  const context = canvas.getContext('2d');
  const gradient = context.createRadialGradient(TUNING.fogInnerX, TUNING.fogInnerY, TUNING.fogInnerRadius, TUNING.fogOuterX, TUNING.fogOuterY, TUNING.fogOuterRadius);
  gradient.addColorStop(0, css(PALETTE.background));
  gradient.addColorStop(TUNING.fogBackgroundStop, css(PALETTE.background));
  gradient.addColorStop(1, css(PALETTE.background));
  context.fillStyle = gradient;
  context.fillRect(0, 0, canvas.width, canvas.height);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function reflectionStudio() {
  const studio = new THREE.Scene();
  studio.background = new THREE.Color(PALETTE.background);
  const panels = [
    {position: [TUNING.leftPanelX, 2, 2], size: [TUNING.leftPanelWidth, TUNING.leftPanelHeight, TUNING.leftPanelDepth], color: PALETTE.white, intensity: TUNING.leftPanelIntensity},
    {position: [TUNING.rightPanelX, TUNING.rightPanelY, -2], size: [TUNING.rightPanelWidth, TUNING.rightPanelHeight, 2], color: PALETTE.silver, intensity: TUNING.rightPanelIntensity},
    {position: [1, TUNING.frontPanelY, TUNING.frontPanelZ], size: [2, TUNING.frontPanelHeight, TUNING.frontPanelDepth], color: PALETTE.white, intensity: 2},
    {position: [0, TUNING.overheadPanelY, 0], size: [TUNING.overheadPanelWidth, TUNING.overheadPanelHeight, TUNING.overheadPanelDepth], color: PALETTE.white, intensity: 2},
  ];
  panels.forEach(panel => {
    const light = new THREE.Mesh(new THREE.BoxGeometry(...panel.size),
      new THREE.MeshBasicMaterial({color: new THREE.Color(panel.color).multiplyScalar(panel.intensity)}));
    light.position.set(...panel.position); studio.add(light);
  });
  return studio;
}

export function fieldMarkings() {
  const group = new THREE.Group(), field = STAGE.field;
  const material = new THREE.MeshBasicMaterial({color: PALETTE.fieldLine, transparent: true, opacity: field.opacity, depthWrite: false});
  const line = new THREE.PlaneGeometry(field.width, field.line);
  const hash = new THREE.PlaneGeometry(field.hash, field.line);
  for (let row = 0; row < field.rows; row += 1) {
    const y = (row - (field.rows - 1) / 2) * field.spacing;
    const stripe = new THREE.Mesh(line, material);
    stripe.position.set(0, y, field.lift); group.add(stripe);
    for (let count = 1; count <= field.hashCount; count += 1) {
      [-1, 1].forEach(side => {
        const mark = new THREE.Mesh(hash, material);
        mark.position.set(side * field.hashX, y + count * field.hashSpacing, field.lift); group.add(mark);
      });
    }
  }
  return group;
}

export function makeEnvironment(scene, renderer) {
  const studio = reflectionStudio(), generator = new THREE.PMREMGenerator(renderer);
  const environment = generator.fromScene(studio, TUNING.environmentSigma);
  scene.environment = environment.texture;
  scene.background = background();
  scene.fog = new THREE.FogExp2(PALETTE.background, STAGE.fog);
  studio.traverse(object => { object.geometry?.dispose(); object.material?.dispose(); });
  generator.dispose();
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(STAGE.floor, STAGE.floor),
    new THREE.MeshStandardMaterial({color: PALETTE.turf, roughness: TUNING.floorRoughness, metalness: 0, envMapIntensity: TUNING.floorEnvironment}));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = TUNING.floorY;
  floor.receiveShadow = true;
  floor.add(fieldMarkings());
  scene.add(floor);
  const plinth = new THREE.Mesh(new THREE.CylinderGeometry(STAGE.radius, STAGE.radius, STAGE.height, TUNING.plinthSegments),
    new THREE.MeshStandardMaterial({color: PALETTE.background, roughness: TUNING.plinthRoughness, metalness: TUNING.plinthMetalness, envMapIntensity: TUNING.plinthEnvironment}));
  plinth.position.y = STAGE.height / 2;
  plinth.receiveShadow = true;
  scene.add(plinth);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(STAGE.radius, STAGE.ringHeight, TUNING.ringRadialSegments, TUNING.ringTubularSegments),
    new THREE.MeshStandardMaterial({color: PALETTE.silver, metalness: 1, roughness: TUNING.ringRoughness}));
  ring.rotation.x = Math.PI / 2;
  ring.position.y = TUNING.ringY;
  scene.add(ring);
  const key = new THREE.SpotLight(PALETTE.white, TUNING.keyIntensity, TUNING.keyDistance, TUNING.keyAngle, TUNING.keyPenumbra, TUNING.keyDecay);
  key.position.set(TUNING.keyX, TUNING.keyY, TUNING.keyZ); key.target.position.set(0, TUNING.keyTargetY, 0);
  key.castShadow = true;
  key.shadow.mapSize.set(STAGE.shadowSize, STAGE.shadowSize);
  key.shadow.bias = TUNING.keyShadowBias;
  scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(PALETTE.silver, TUNING.rimIntensity);
  rim.position.set(2, TUNING.rimY, TUNING.rimZ); scene.add(rim);
  scene.add(new THREE.HemisphereLight(PALETTE.white, PALETTE.background, TUNING.hemisphereIntensity));
  // The light banks behind the stage are a real rig now: heads, glows and four moving spots (stage-lights.mjs).
  const rig = makeRig(scene);
  // The stands behind the rig hide with it while the board is drafting (stage-stands.mjs).
  rig.group.add(makeStands().group);
  const haze = makeHaze(); scene.add(haze.group);
  return {key, environment, stageHeight: STAGE.height, floor, plinth, ring, banks: rig.group, rig, haze};
}
