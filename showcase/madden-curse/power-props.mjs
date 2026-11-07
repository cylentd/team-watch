import { POWER_PROPS_DETAIL as TUNING } from './constants-power.mjs';
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { PROPS, stampMesh } from './draft-props.mjs';
import { PLATE_FACE, stampCentre } from './power-layout.mjs';
import { POWER_COPY } from './power-copy.mjs';

/* Chapter 5's stamps on the feature plate (docs/madden-film-chapter5.md, props; David 2026-11-05): "#3 power" over
   the plate's top edge and "4-4 actual" over its actual W-L, Chapter 1's stamps (draft-props.mjs) at the plate's
   scale. ~~The rank cube and the first-half file~~ are gone with the standings shuffle and the trophy finale.
   Meshes only; power-set.mjs poses them. */
const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, name) => values[name]);
const SIZE = PLATE_FACE.stamps.width / PROPS.stampWidth;   // stampMesh is PROPS.stampWidth wide

export function makeProps(feature) {
  const group = new THREE.Group();
  const stamps = {power: stampMesh(fill(POWER_COPY.power, {place: feature.power}), PALETTE.brandLime, PALETTE.print),
    actual: stampMesh(fill(POWER_COPY.actual, {place: feature.standing}), PALETTE.broadcast)};
  Object.values(stamps).forEach(mesh => { mesh.renderOrder = 2; group.add(mesh); });
  /* Pose both stamps on the feature plate `place` (power-pose.mjs plates[] and stamps, 0..1 each) at the scene's `dim`. */
  function pose(state, mobile, place) {
    const plate = state.plates[place - 1];
    Object.entries(stamps).forEach(([name, mesh]) => {
      const amount = state.stamps[name];
      mesh.visible = plate.visible && amount > TUNING.visibleThreshold;
      mesh.position.set(...stampCentre(place, plate, mobile, name));
      mesh.scale.setScalar(SIZE * Math.max(TUNING.scaleFloor, amount));
      mesh.material.color.setScalar(state.dim);
    });
  }
  return {group, pose, dispose() {
    group.traverse(object => { object.geometry?.dispose(); [object.material].flat().forEach(material => { material?.map?.dispose(); material?.dispose(); }); });
  }};
}
