import { POWER_DRESS_DETAIL as TUNING } from './constants-power.mjs';
import { DRESS } from "./constants-power.mjs";
export { DRESS };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { inOutCubic, seg } from './draft-motion.mjs';
import { BACKLIGHT, backdropTexture } from './draft-backdrop.mjs';
import { beatTiming } from './timing.mjs';
import { makeBoardStage } from './draft-stage.mjs';
import { makeHaze } from './stage-haze.mjs';
import { TIMES } from './power-clock.mjs';
import { RISER, TROPHY, slot, trophySpot } from './power-layout.mjs';

/* Chapter 5's set dressing (David, 2026-11-05: "The wide shot also looks bad because it's so bare"): Chapter 1's
   stage wings and crown behind the riser (draft-stage.mjs), its blue-lit back wall (draft-backdrop.mjs), haze over
   the turf (stage-haze.mjs), a pool of key light on the floor, a rim light from behind that catches the plates'
   metal edges, and two stadium lights that swing onto the trophy as it lowers (power-close `trophy`). */

// A board-beat second at which Chapter 1's wings stand fully lit (draft-backdrop.mjs backlightAt), so the stage's
// own update raises them; the dress then sets their opacity each frame.
const LIT = beatTiming('board').duration - BACKLIGHT.out - .05;

const additive = options => new THREE.MeshBasicMaterial({transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false, ...options});
const homes = ({x, low, high}) => new Map([[0, {home: {x: -x, y: low}}], [1, {home: {x, y: high}}]]);
const materialsOf = group => { const found = new Set(); group.traverse(object => [object.material].flat().forEach(material => material && found.add(material))); return [...found]; };

function beam() {
  const geometry = new THREE.ConeGeometry(1, 1, TUNING.coneSegments, 1, true);
  geometry.translate(0, TUNING.coneApexOffset, 0); geometry.rotateX(-Math.PI / 2);   // apex at the origin, opening along +z
  return new THREE.Mesh(geometry, additive({color: PALETTE.white, map: backdropTexture(), opacity: DRESS.beams.opacity, side: THREE.DoubleSide}));
}

export function makeDress() {
  const group = new THREE.Group();
  const stages = {desk: makeBoardStage(homes(DRESS.wings.desk)), phone: makeBoardStage(homes(DRESS.wings.phone))};
  Object.values(stages).forEach(stage => { stage.update(LIT, true); group.add(stage.group); });
  const stageMaterials = {desk: materialsOf(stages.desk.group), phone: materialsOf(stages.phone.group)};
  const glow = backdropTexture();
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), additive({map: glow, color: PALETTE.broadcast}));
  const pool = new THREE.Mesh(new THREE.PlaneGeometry(...DRESS.pool.size), additive({map: glow, color: PALETTE.white}));
  pool.rotation.x = -Math.PI / 2;
  const haze = makeHaze();
  const rim = new THREE.DirectionalLight(PALETTE.white, DRESS.rim.intensity);
  rim.position.set(...DRESS.rim.position);
  const beams = [beam(), beam()], spot = new THREE.SpotLight(PALETTE.white, 0, 0, DRESS.beams.spot.angle, DRESS.beams.spot.penumbra, 0);
  group.add(wall, pool, haze.group, rim, rim.target, ...beams, spot, spot.target);
  const aim = new THREE.Vector3(), side = new THREE.Vector3(), centre = new THREE.Vector3();

  /* Dress the set for `state` (power-pose.mjs) at film second `time`, seen from `camera`. */
  function update(state, time, mobile, camera) {
    const device = mobile ? 'phone' : 'desk', dim = state.dim;
    Object.entries(stages).forEach(([name, stage]) => { stage.group.visible = name === device; });
    stageMaterials[device].forEach(material => { material.opacity = dim; });
    const top = slot(1, mobile), front = slot(TIER_FRONT, mobile), [width, height] = DRESS.wall.size;
    const reach = 2 * (DRESS.wings[device].x + RISER.plate.width), tall = top.y + RISER.plate.height + TROPHY.height;
    wall.scale.set(reach * width, tall * height, 1);
    wall.position.set(0, tall / 2, BACKLIGHT.depth);
    const swell = state.wave === null ? 0 : Math.sin(Math.PI * state.wave);
    wall.material.opacity = (DRESS.wall.level + DRESS.wall.wave * swell) * dim;
    pool.position.set(0, TUNING.poolY, front.z + DRESS.pool.z - 1);
    pool.material.opacity = DRESS.pool.level * dim;
    haze.group.position.set(0, 0, front.z + DRESS.haze.z - 1);
    haze.update(time, camera.position);
    rim.target.position.set(0, top.y, top.z);
    // The stadium lights come on with the pull back, aimed at the riser's ends, and swing onto the trophy as it lowers.
    const [x, y, z] = trophySpot(mobile), on = time >= TIMES.pull[0] ? 1 : 0, turn = inOutCubic(seg(time, TIMES.trophy[0], TIMES.trophy[0] + DRESS.beams.swing));
    centre.set(x, y + state.trophy.height * (state.trophy.visible ? 1 : 0) + TROPHY.height / 2, z);
    beams.forEach((mesh, index) => {
      const [sx, sy, sz] = DRESS.beams[device][index];
      side.set(index ? DRESS.wings[device].x : -DRESS.wings[device].x, front.y, front.z);
      aim.copy(side).lerp(centre, turn);
      mesh.visible = on > 0;
      mesh.position.set(sx, sy, sz); mesh.lookAt(aim);
      const length = mesh.position.distanceTo(aim);
      mesh.scale.set(DRESS.beams.radius, DRESS.beams.radius, length);
      mesh.material.opacity = DRESS.beams.opacity * dim;
    });
    spot.position.set(...DRESS.beams[device][0]); spot.target.position.copy(aim);
    spot.intensity = DRESS.beams.spot.intensity * on * turn;
  }
  return {group, update, dispose() { glow.dispose(); }};
}
const TIER_FRONT = 12;   // a place on the front, lowest row (power-layout.mjs: places 7-12 desk, 10-12 phone)
