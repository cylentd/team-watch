import { WEEK_FLAME_ICON_DETAIL as TUNING } from './constants-draft-surfaces.mjs';
import { FLAME_ICON } from "./constants-draft-surfaces.mjs";
export { FLAME_ICON };
/* The week tile's flame icon, the one the smash weeks showed before revision 13 (David, rev 14: keep its
   shape and colour, animate it). Drawn in the tile's own canvas pixels (draft-textures.mjs WEEK_TILE, 128 x
   160), so the still tile and the live flame are the same path. Frame 0 is the icon exactly; frames 1-3
   wobble the outline and shift the inner tongue (the notch) by a few pixels, a 4-frame flicker cycle. */

/* Fill the flame on `context` in its tile position, with one frame's wobble. */
export function flameIcon(context, [tip, right, left, notchX, notchY] = FLAME_ICON.frames[0]) {
  context.beginPath(); context.moveTo(TUNING.tipX + tip, TUNING.tipY); context.bezierCurveTo(TUNING.rightUpperControlX + tip, TUNING.rightUpperControlY, TUNING.rightOuterControlX + right, TUNING.rightOuterControlY, TUNING.rightShoulderX + right, TUNING.rightShoulderY);
  context.bezierCurveTo(TUNING.baseRightControlX, TUNING.baseRightControlY, TUNING.baseLeftControlX + left, TUNING.baseLeftControlY, TUNING.leftShoulderX + left, TUNING.leftShoulderY); context.bezierCurveTo(TUNING.leftOuterControlX + left, TUNING.leftOuterControlY, TUNING.leftUpperControlX, TUNING.leftUpperControlY, TUNING.leftTipX + left / 2, TUNING.leftTipY);
  context.lineTo(TUNING.notchX + notchX, TUNING.notchY + notchY); context.bezierCurveTo(TUNING.innerLowerControlX + notchX, TUNING.innerLowerControlY, TUNING.innerUpperControlX + tip, TUNING.innerUpperControlY, TUNING.tipX + tip, TUNING.tipY); context.fill();
}
