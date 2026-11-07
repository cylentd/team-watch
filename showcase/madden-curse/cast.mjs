import { CAST_DETAIL as TUNING } from './constants-opening.mjs';
import { CAST } from "./constants-opening.mjs";
import * as THREE from 'three';
import { PALETTE, SHOW } from './constants.mjs';
import { clamp, mix } from './timeline.mjs';

function medallion(team, loader) {
  const root = new THREE.Group();
  const rim = new THREE.Mesh(new THREE.CylinderGeometry(CAST.radius, CAST.radius, CAST.depth, CAST.segments),
    new THREE.MeshStandardMaterial({color: PALETTE.silver, metalness: TUNING.rimMetalness, roughness: TUNING.rimRoughness}));
  rim.rotation.x = Math.PI / 2;
  root.add(rim);
  const face = new THREE.Mesh(new THREE.CircleGeometry(CAST.radius * TUNING.faceRadiusScale, CAST.segments),
    new THREE.MeshBasicMaterial({color: PALETTE.lime, toneMapped: false}));
  face.position.z = CAST.depth;
  root.add(face);
  const ready = new Promise(resolve => loader.load(team.avatar, texture => {
    texture.colorSpace = THREE.SRGBColorSpace;
    face.material.map = texture; face.material.color.set(PALETTE.white);
    face.material.needsUpdate = true; resolve();
  }, undefined, resolve));
  root.userData.teamId = team.id;
  return {root, ready};
}

function solo(root, team, progress, mobile) {
  const enter = 1 - Math.pow(1 - clamp(progress / SHOW.entranceFraction), TUNING.entranceExponent);
  const leave = clamp((progress - SHOW.exitFraction) / (1 - SHOW.exitFraction));
  const remaining = 1 - enter;
  root.position.set((mobile ? 0 : TUNING.desktopSoloX) - remaining * CAST.entrance + leave * CAST.entrance,
    (mobile ? TUNING.phoneSoloY : TUNING.desktopSoloY) + remaining * (team.motif === 'rise' ? -2 : TUNING.dropDistance), TUNING.soloZ);
  root.scale.setScalar((team.motif === 'stamp' ? mix(2, 1, enter) : mix(TUNING.scaleFrom, 1, enter)) * (mobile ? TUNING.phoneSoloScale : TUNING.desktopSoloScale));
  root.rotation.set(0, remaining * (team.motif === 'restore' ? CAST.spin : TUNING.entranceYaw),
    Math.sin(progress * Math.PI) * (team.motif === 'collision' ? TUNING.collisionRoll : TUNING.idleRoll));
}

export async function makeCast(scene, teams) {
  const loader = new THREE.TextureLoader();
  const cast = teams.map(team => medallion(team, loader));
  cast.forEach(item => scene.add(item.root));
  await Promise.all(cast.map(item => item.ready));
  return {
    update(moment, mobile) {
      cast.forEach((item, index) => {
        const active = moment.teamIndex === index;
        item.root.visible = active || moment.ensemble > 0;
        if (active) solo(item.root, teams[index], moment.teamProgress, mobile);
        else if (moment.ensemble > 0) {
          const columns = mobile ? CAST.phoneColumns : CAST.columns;
          const column = index % columns, row = Math.floor(index / columns);
          const offset = column - (columns - 1) / 2;
          const x = offset * (mobile ? TUNING.phoneColumnGap : TUNING.desktopColumnGap) + Math.sign(offset) * (mobile ? TUNING.phoneCenterGap : TUNING.desktopCenterGap);
          const y = (mobile ? TUNING.phoneEnsembleY : TUNING.desktopEnsembleY) + row * (mobile ? TUNING.phoneRowGap : CAST.rowHeight);
          item.root.position.set(x, mix(-2, y, moment.ensemble), TUNING.ensembleZ);
          item.root.scale.setScalar(CAST.small * (mobile ? TUNING.phoneEnsembleScale : 1));
          item.root.rotation.set(0, 0, 0);
        }
      });
    },
    pick(pointer, camera) {
      const ray = new THREE.Raycaster();
      ray.setFromCamera(pointer, camera);
      return ray.intersectObjects(cast.map(item => item.root), true)
        .find(hit => hit.object.parent.visible)?.object.parent.userData.teamId;
    },
  };
}
