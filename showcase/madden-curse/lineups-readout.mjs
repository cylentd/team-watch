import * as THREE from 'three';

/* Chapter 4's readout for the tests (tests/pages/madden_lineups_set.py): the desk's words are textures, so the
   set reports each printed surface's screen box in CSS px, measured with the last camera it was drawn through.
   Pure measurement; lineups-set.mjs owns the state it reads. */
const corner = new THREE.Vector3(), bounds = new THREE.Box3();

function shownInScene(object) {
  for (let node = object; node; node = node.parent) if (!node.visible) return false;
  return true;
}

function screenBox(points, camera, size) {
  const xs = [], ys = [];
  points.forEach(point => {
    corner.copy(point).project(camera);
    xs.push((corner.x + 1) / 2 * size.width); ys.push((1 - corner.y) / 2 * size.height);
  });
  return {left: Math.min(...xs), top: Math.min(...ys), right: Math.max(...xs), bottom: Math.max(...ys)};
}

const inside = (box, size) => box.left >= 0 && box.top >= 0 && box.right <= size.width && box.bottom <= size.height;

/* A printed plane: its four corners in world space. */
function planeCorners(mesh) {
  const {width, height, offsetY = 0} = mesh.userData;   // offsetY: a word printed off the plane's centre (a card's name band)
  return [[-1, -1], [-1, 1], [1, -1], [1, 1]].map(([sx, sy]) => mesh.localToWorld(new THREE.Vector3(sx * width / 2, offsetY + sy * height / 2, 0)));
}

function boxCorners(object) {
  bounds.setFromObject(object);
  const {min, max} = bounds;
  return [min.x, max.x].flatMap(x => [min.y, max.y].flatMap(y => [min.z, max.z].map(z => new THREE.Vector3(x, y, z))));
}

/* {labels, objects}: every printed word, then every solid the headline must not cross (shields, cards, Blip). */
export function measure(labels, objects, camera, size, drawn = true) {
  if (!camera || !size || !drawn) return {labels: [], objects: []};
  camera.updateMatrixWorld();
  const label = mesh => {
    const visible = shownInScene(mesh) && Math.abs(mesh.scale.y) > 0 && mesh.material.opacity > 0;
    const box = screenBox(planeCorners(mesh), camera, size);
    return {text: mesh.userData.text, kind: mesh.userData.kind, visible, inside: visible && inside(box, size), box};
  };
  const solid = object => {
    const visible = shownInScene(object), box = visible ? screenBox(boxCorners(object), camera, size) : {left: 0, top: 0, right: 0, bottom: 0};
    return {text: object.name, visible, inside: visible && inside(box, size), box};
  };
  return {labels: labels.map(label), objects: objects.map(solid)};
}
