import { MOBILE_FRAME } from "./constants-draft-motion.mjs";
export { MOBILE_FRAME };
import * as THREE from 'three';
import { OPENING } from './constants.mjs';
import { BOARD, CARD_HEIGHT, boardCentre, boardTop, columnX, rowY } from './draft-board.mjs';
import { CELL } from './draft-textures.mjs';
import { BUILD } from './draft-build.mjs';
import { inOutCubic, outCubic, seg } from './draft-motion.mjs';

export function phoneOverview(size = MOBILE_FRAME.reference) {
  const width = columnX(CELL.columns - 1) - columnX(0) + BOARD.card;
  const height = boardTop() + BOARD.avatar - rowY(CELL.rows - 1) + CARD_HEIGHT / 2;
  const lens = 2 * Math.tan(THREE.MathUtils.degToRad(OPENING.phoneFov / 2));
  const back = Math.max(width / (lens * size.width / size.height * MOBILE_FRAME.widthFill),
    height / (lens * MOBILE_FRAME.heightFill));
  const target = new THREE.Vector3(0, boardCentre(), 0);
  return {position: target.clone().add(new THREE.Vector3(0, 0, back)), target};
}

export function mobileBuildAt(clock) {
  if (clock === null || clock < BUILD.steps[0]) return null;
  return {pull: outCubic(seg(clock, BUILD.cameraFrom, BUILD.cameraFrom + MOBILE_FRAME.pull)),
    // The phone's framing and column light arrive together; the avatar rises afterward.
    reveal: inOutCubic(seg(clock, BUILD.hit - MOBILE_FRAME.reveal, BUILD.hit))};
}
