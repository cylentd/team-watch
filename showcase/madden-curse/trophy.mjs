import { TROPHY_DETAIL as TUNING } from './constants-opening.mjs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OPENING, PALETTE } from './constants.mjs';

const TROPHY_FACING = -.45;
export function poseTrophy(trophy, rotation = 0) {
  trophy.rotation.set(0, TROPHY_FACING + rotation, 0);
}

export function silverMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: PALETTE.silver, metalness: 1, roughness: TUNING.silverRoughness,
    clearcoat: TUNING.silverClearcoat, clearcoatRoughness: TUNING.silverClearcoatRoughness, envMapIntensity: TUNING.silverEnvironment,
  });
}

export function fallbackTrophy() {
  const root = new THREE.Group(), silver = silverMaterial();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(TUNING.fallbackTopRadius, TUNING.fallbackBottomRadius, TUNING.fallbackHeight, TUNING.pedestalSides), silver);
  body.position.y = TUNING.fallbackCenterY;
  body.rotation.y = TUNING.fallbackYaw;
  root.add(body);
  const football = new THREE.Mesh(new THREE.SphereGeometry(1, TUNING.footballWidthSegments, TUNING.footballHeightSegments), silver);
  football.scale.set(TUNING.footballWidth, TUNING.footballHeight, TUNING.footballDepth);
  football.rotation.z = TUNING.footballRoll;
  football.position.set(0, TUNING.footballY, 0);
  root.add(football);
  root.traverse(object => { if (object.isMesh) object.castShadow = true; });
  return root;
}

export async function loadTrophy() {
  const gltf = await new GLTFLoader().loadAsync(OPENING.modelUrl);
  const model = gltf.scene, bounds = new THREE.Box3().setFromObject(model);
  const size = bounds.getSize(new THREE.Vector3());
  if (!Number.isFinite(size.y) || size.y <= 0) throw new Error('Invalid trophy bounds');
  const scale = OPENING.trophyHeight / size.y;
  model.scale.multiplyScalar(scale);
  const normalized = new THREE.Box3().setFromObject(model);
  const center = normalized.getCenter(new THREE.Vector3());
  model.position.set(-center.x, -normalized.min.y, -center.z);
  const silver = silverMaterial();
  silver.clippingPlanes = [new THREE.Plane(new THREE.Vector3(0, 1, 0), TUNING.clippingHeight)];
  silver.clipShadows = true;
  model.traverse(object => {
    if (!object.isMesh) return;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    materials.forEach(material => material.dispose());
    object.material = silver;
    object.castShadow = true;
    object.receiveShadow = true;
  });
  const root = new THREE.Group();
  root.add(model);
  const pedestal = new THREE.Mesh(new THREE.CylinderGeometry(TUNING.pedestalTopRadius, TUNING.pedestalBottomRadius, TUNING.pedestalHeight, TUNING.pedestalSides, 1, false, Math.PI / TUNING.pedestalRotationDivisor), silverMaterial());
  pedestal.position.y = TUNING.pedestalCenterY;
  pedestal.castShadow = true;
  pedestal.receiveShadow = true;
  root.add(pedestal);
  return root;
}
