import * as THREE from 'three';
import { poseTrophy } from './trophy.mjs';
import { TROPHY, trophySpot } from './power-layout.mjs';

/* Chapter 5's finale borrows the opening's trophy (scene.mjs createRoom hands its group over, film-sets.mjs
   context `trophy`; David, 2026-11-05: "The trophy returns"). The rig stands it on the riser's summit for
   power-pose.mjs `trophy`, and `release` puts it back exactly where the opening stood it, hidden: the room shows it
   again only in the opening (scene.mjs drawRoom), so a seek before 88.077 or into Chapters 1-4 never finds it
   on the riser. `ball` is an empty at the ball's centre, for the ident's glint. */
export function makeTrophyRig(trophy) {
  const home = {position: trophy.position.clone(), scale: trophy.scale.clone(), rotation: trophy.rotation.clone()};
  // The model's height and foot in its own units, measured once at its home pose; the fallback model's numbers when
  // the group is empty (a test, or a model still loading).
  const measured = new THREE.Box3().setFromObject(trophy), size = measured.getSize(new THREE.Vector3());
  const known = Number.isFinite(size.y) && size.y > 0;
  const model = known ? size.y / home.scale.y : TROPHY.model, foot = known ? (measured.min.y - home.position.y) / home.scale.y : 0;
  const ball = new THREE.Object3D();
  let held = false;

  function release() {
    if (!held) { trophy.visible = false; return; }
    trophy.position.copy(home.position); trophy.scale.copy(home.scale); trophy.rotation.copy(home.rotation);
    trophy.visible = false; held = false;
  }
  /* Stand the trophy for `state` ({visible, height, spin}); not visible releases it. */
  function pose(state, mobile) {
    if (!state.visible) { release(); return; }
    held = true;
    const scale = TROPHY.height / model, [x, y, z] = trophySpot(mobile);
    trophy.visible = true;
    trophy.scale.setScalar(scale);
    trophy.position.set(x, y + state.height - foot * scale, z);
    poseTrophy(trophy, state.spin);
    ball.position.set(x, y + state.height + (TROPHY.ball - foot) * scale, z);
    ball.updateMatrixWorld();
  }
  return {pose, release, ball};
}
