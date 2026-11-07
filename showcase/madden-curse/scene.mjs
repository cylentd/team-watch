import { SCENE_DETAIL as TUNING } from './constants-opening.mjs';
import { MACRO, FILM_INTRO } from "./constants-opening.mjs";
import * as THREE from 'three';
import { OPENING, SHOW } from "./constants.mjs";
import { clamp, mix } from './timeline.mjs';
import { makeGlint, GLINT } from './film-glint.mjs';
import { makeFlare } from './film-flare.mjs';
import { TITLE_DROP, makeTitleDrop } from './film-title-drop.mjs';
import { makeImpact } from './film-impact.mjs';
import { TITLE_WORDS, at } from './timing.mjs';
import { REVEAL_GLOW } from './draft-reveal-glow.mjs';
import { HANDOVER, handoverCamera } from './film-zoom.mjs';
import { STAGE, makeEnvironment } from './environment.mjs';
import { makeBlip } from './blip.mjs';
import { loadTrophy, fallbackTrophy, poseTrophy } from './trophy.mjs';
import { makeCast } from './cast.mjs';
import { HOP, hop } from './blip-hop.mjs';
import { CHAPTERS, filmMoment, filmPlan } from './film.mjs';
import { roomDraws } from './film-sets.mjs';
import { warmPlayback } from './scene-warmup.mjs';

const CAMERA = Object.freeze({near: .05, far: 80, wide: [3.2, 2.8, 7.4]});
// The opening's camera: it starts `radius` from the trophy's axis at the ball, turns `orbit` radians
// round it while it pulls back to the wide shot by the time the title forms (OPENING.logoAt).
// Over the title's hold it pushes in by `push` and drifts `drift` radians around the stationary trophy.

// The film's opening (rule 21, revision 7, 2026-11-04): the trophy stays centred, the title is a lower
// third, so the wide shot pulls back by `reach` and `lift` slides the frame's content up by that share of
// its height, above the bar. The promo keeps its title column. Measured from the rev 7 stills.
// Chapter 17: the opening hands over by pushing straight into the trophy's ball until the frame whites out
// (film-zoom.mjs). ~~Revision 8: the camera tilted down by `exit.look` and sank by `exit.drop` as the spots swung
// onto the floor, under a light sweeping down~~.
   // the glint sits on the ball, this high above the stage
const BALL = new THREE.Vector3(0, STAGE.height + FILM_INTRO.glint, 0);   // the ball's centre, the zoom's end
const CAST_WALK = 2;   // seconds Blip takes to walk to the trophy before the final title
const BLIP_HOPS = OPENING.hops, BLIP_SCALE = .93;
/* Blip's hops start so that each lands on a beat and the last lands on the title's hit (blip-hop.mjs:
   a hop touches down `HOP.land` of its length before it ends). */
export const HOP_START = OPENING.logoAt - OPENING.revealDuration * (1 - HOP.land / BLIP_HOPS);

/* Blip at `x` on the stage, lifted and squashed by his hop; his width bulges as his height presses. */
export function placeBlip(blip, x, floor, step) {
  blip.root.position.set(x, floor + step.lift, TUNING.blipStageZ);
  blip.root.scale.set(BLIP_SCALE * (2 - step.squash), BLIP_SCALE * step.squash, BLIP_SCALE * (2 - step.squash));
}

function disposeObjects(scene) {
  const geometries = new Set(), materials = new Set(), textures = new Set();
  scene.traverse(object => {
    if (object.geometry) geometries.add(object.geometry);
    const entries = Array.isArray(object.material) ? object.material : [object.material];
    entries.filter(Boolean).forEach(material => {
      materials.add(material);
      [...Object.values(material), ...Object.values(material.uniforms ?? {}).map(entry => entry.value)]
        .filter(value => value?.isTexture).forEach(value => textures.add(value));
    });
  });
  geometries.forEach(value => value.dispose());
  materials.forEach(value => value.dispose());
  textures.forEach(value => value.dispose());
  scene.background?.dispose();
}

export async function createRoom(container, label, contextLost, teams = [], draft = null) {
  const renderer = new THREE.WebGLRenderer({antialias: true, alpha: false, powerPreference: 'low-power'});
  renderer.setPixelRatio(Math.min(devicePixelRatio, OPENING.maxPixelRatio));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = TUNING.toneMappingExposure;
  renderer.shadowMap.enabled = true;
  renderer.localClippingEnabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(OPENING.cameraFov, 1, CAMERA.near, CAMERA.far);
  const environment = makeEnvironment(scene, renderer);
  const trophy = new THREE.Group();
  trophy.position.y = environment.stageHeight;
  scene.add(trophy);
  let modelFallback = false;
  try { trophy.add(await loadTrophy()); }
  catch { modelFallback = true; trophy.add(fallbackTrophy()); }
  const blip = makeBlip();
  scene.add(blip.root);
  const cast = await makeCast(scene, teams);
  // The film's Chapter 1 room, built only for ?film so the promo loads nothing it does not draw.
  const film = draft ? await (await import('./draft.mjs')).makeDraft(scene, draft, teams, trophy) : null;
  const room = {fog: scene.fog.density, exposure: renderer.toneMappingExposure,
    key: environment.key.position.clone(), target: environment.key.target.position.clone()};
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('role', 'img');
  renderer.domElement.setAttribute('aria-label', label);
  container.append(renderer.domElement);
  const lost = event => { event.preventDefault(); contextLost(); };
  renderer.domElement.addEventListener('webglcontextlost', lost);
  // Only the film gets the title's glint. ~~The rev 8 depth-of-field lens~~ is gone: it softened the subject (rule 19, rev 9).
  const glint = film ? makeGlint(scene, GLINT.trophy) : null;
  const flare = film ? makeFlare(scene) : null;   // the title's lens flare and floor haze (rev 13)
  // The title as a 3D object that drops and slams into the lower third, and its impact (rev 14, placed rev 15).
  // Rev 15: both ride with the camera. Chapter 17: one impact per title word.
  const title = film ? await makeTitleDrop(scene) : null;
  const impacts = film ? TITLE_DROP.hits.map(() => makeImpact(title.hud)) : [];
  const impact = film ? {pose: words => words.forEach((word, index) => impacts[index].pose(word.age, word.centre, word.halfWidth, word.frameHeight, word.hit, word)),
    hide: () => impacts.forEach(each => each.hide())} : null;
  const api = {renderer, scene, camera, trophy, blip, cast, environment, modelFallback, container, film, room, glint, flare, title, impact};
  if (film) {
    const beats = filmPlan().beats;
    const moments = [beats[0].start, beats[0].start + beats[0].duration / 2,
      beats[0].start + at('board', 'stand') + REVEAL_GLOW.duration / 2,
      ...beats.slice(1).map(beat => beat.start + beat.duration / 2), ...film.warmAt, TITLE_WORDS.at(-1), 0].map(time => filmMoment(time));
    await warmPlayback(renderer, scene, moment => drawRoom(api, moment, 0, false), moments, camera);
  }
  return {
    canvas: renderer.domElement, modelFallback,
    draw: (moment, rotation = 0, inspection = false) => drawRoom(api, moment, rotation, inspection),
    pick: pointer => cast.pick(pointer, camera),
    dispose: () => {
      renderer.domElement.removeEventListener('webglcontextlost', lost);
      film?.dispose();
      disposeObjects(scene); environment.environment.dispose();
      renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove();
    },
  };
}

/* Chapter 2 is a flat card over the canvas (trades-view.mjs), so the board draws only under the whip that sweeps
   the card in, holding the finale's last frame; once the card covers the frame the GPU rests. */
const BOARD_END = 1e-6;   // s before the finale's end: its last frame, still on the board
function boardUnder(moment) {
  if (!moment.transition) return null;
  const last = filmPlan().beats.findLast(beat => beat.chapter === 1);
  return {...filmMoment(last.start + last.duration - BOARD_END), transition: moment.transition};
}

/* The film's chapters past the board draw in the room only through a set (film-sets.mjs roomDraws): a DOM chapter
   draws nothing, except the trades card, which holds the board under its whips (boardUnder). */
const FILM_CHAPTERS = Object.values(CHAPTERS);
function drawRoom(room, moment, rotation, inspection) {
  if (room.film && FILM_CHAPTERS.includes(moment.chapter) && !roomDraws(moment)) {
    if (moment.chapter !== CHAPTERS[2]) return;
    moment = boardUnder(moment);
    if (!moment) return;
  }
  const {renderer, camera, trophy, blip, environment, container} = room;
  const width = container.clientWidth, height = container.clientHeight;
  if (!width || !height) return;
  const mobile = width < OPENING.mobileWidth, amount = moment.pullback;
  if (renderer.domElement.width !== Math.floor(width * renderer.getPixelRatio()) ||
      renderer.domElement.height !== Math.floor(height * renderer.getPixelRatio())) renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.fov = mobile ? OPENING.phoneFov : OPENING.cameraFov;
  const drafting = Boolean(room.film) && FILM_CHAPTERS.includes(moment.chapter);   // the board, or a set that shows
  [trophy, environment.floor, environment.plinth, environment.ring, environment.banks, environment.haze.group].forEach(object => { object.visible = !drafting; });
  if (drafting) {
    room.cast.update({...moment, ensemble: 0, chapter: 'logo'}, mobile);
    const {exposure, key} = room.film.update(moment, camera, mobile, blip, {width, height});
    renderer.toneMappingExposure = exposure;
    environment.key.intensity = key.intensity;
    environment.key.position.set(...key.position); environment.key.target.position.set(...key.target);
    camera.updateProjectionMatrix();
    room.glint.sprite.visible = false;
    room.flare.hide(); room.title.hide(); room.impact.hide();
    renderer.render(room.scene, camera);
    return;
  }
  room.film?.hide(blip);
  room.scene.fog.density = room.room.fog;
  renderer.toneMappingExposure = room.room.exposure;
  environment.key.position.copy(room.room.key); environment.key.target.position.copy(room.room.target);
  // A macro shot of the trophy's metal, then one slow orbit and dolly out to the wide shot (David,
  // 2026-11-03): the distance eases in late, so the camera lingers close while it turns.
  const wide = mobile ? MACRO.widePhone : CAMERA.wide;
  const end = Math.atan2(wide[0], wide[2]), reach = Math.hypot(wide[0], wide[2]);
  // The title's hold keeps moving: a slow push in, a drift round the trophy and a turn of its metal.
  // The film's hold stops where the zoom into the ball starts, so the push leaves from one still pose.
  const device = mobile ? 'phone' : 'desk', film = Boolean(room.film);
  const holding = film ? Math.min(moment.time, HANDOVER.from) : moment.time;
  const hold = clamp((holding - OPENING.logoAt) / (OPENING.duration - OPENING.logoAt));
  const angle = mix(end - MACRO.orbit, end, amount) + MACRO.drift * hold;
  const far = film ? reach * FILM_INTRO.reach[device] : reach;
  const radius = mix(MACRO.radius, far, amount ** MACRO.dollyEase) * (1 - MACRO.push * hold);
  camera.position.set(Math.sin(angle) * radius, mix(MACRO.height, wide[1], amount), Math.cos(angle) * radius);
  const target = new THREE.Vector3(mobile || film ? 0 : TUNING.desktopTargetX * moment.logo, mix(MACRO.aim, mobile ? TUNING.phoneTargetY : TUNING.desktopTargetY, amount), 0);
  // The film's hand-over to the board: one straight push into the ball (film-zoom.mjs), the frame's lift
  // easing out so the ball ends centred.
  const zoom = film ? handoverCamera(moment.time, camera.position, target, BALL) : null;
  if (zoom) { camera.position.copy(zoom.position); target.copy(zoom.target); }
  const exit = 0;   // the spots stay on the trophy into the white (stage-lights.mjs `exit`)
  if (film) camera.setViewOffset(width, height, 0, height * FILM_INTRO.lift[device] * amount * (1 - zoom.amount), width, height);
  else if (mobile) camera.setViewOffset(width, height, 0, -height * MACRO.phoneOffset, width, height);
  else camera.clearViewOffset();
  camera.lookAt(target); camera.updateProjectionMatrix();
  poseTrophy(trophy, rotation);
  environment.haze.update(moment.time, camera.position);
  // Blip hops in from the right of the trophy to its left (blip-hop.mjs), once the pull-back shows the
  // floor, each hop landing on a beat and the last on the title's hit.
  const hopAt = HOP_START;
  const entrance = hop(clamp((moment.time - hopAt) / OPENING.revealDuration), BLIP_HOPS);
  placeBlip(blip, mix(TUNING.blipEntranceX, TUNING.blipRestX, entrance.travel), 0, entrance);
  blip.root.visible = moment.time >= hopAt;
  blip.root.rotation.z = 0;
  blip.head.rotation.y = inspection ? TUNING.inspectionYaw : mix(TUNING.entranceYaw, TUNING.logoYaw, moment.logo);
  environment.key.position.x = mix(TUNING.keyStartX, TUNING.keyEndX, moment.time / OPENING.duration);
  environment.rig.update(moment.time, blip.root.position, exit);
  environment.key.intensity = mix(TUNING.keyStartIntensity, TUNING.keyEndIntensity, moment.pullback);
  const teamShot = moment.chapter === 'team';
  const castShot = moment.ensemble > 0;
  trophy.visible = !teamShot;
  [environment.floor, environment.plinth, environment.ring, environment.banks, environment.haze.group].forEach(object => { object.visible = !teamShot; });
  blip.root.visible = !teamShot && moment.time >= hopAt;
  room.cast.update(moment, mobile);
  if (teamShot) {
    camera.clearViewOffset();
    camera.position.set(0, TUNING.castCameraY, mobile ? TUNING.phoneCastCameraZ : TUNING.desktopCastCameraZ);
    camera.lookAt(0, TUNING.castTargetY, 0);
    environment.key.position.set(TUNING.castKeyX, TUNING.castKeyY, TUNING.castKeyZ);
  } else if (castShot) {
    camera.clearViewOffset();
    camera.position.set(0, TUNING.finaleCameraY, mobile ? TUNING.phoneFinaleCameraZ : TUNING.desktopFinaleCameraZ);
    camera.lookAt(0, TUNING.finaleTargetY, 0);
    trophy.scale.setScalar(1);
    trophy.position.z = TUNING.finaleTrophyZ;
    const walk = hop(clamp((moment.elapsed - (SHOW.finaleAt - CAST_WALK)) / CAST_WALK), BLIP_HOPS);
    placeBlip(blip, mix(TUNING.blipFinaleStartX, TUNING.blipFinaleEndX, walk.travel), 0, walk);
    blip.head.rotation.y = moment.elapsed >= SHOW.finaleAt ? TUNING.blipFinaleYaw : TUNING.blipFinaleLook;
  }
  if (!castShot) { trophy.scale.setScalar(1); trophy.position.z = 0; }
  if (!room.glint) { renderer.render(room.scene, camera); return; }
  // The film: the title's hit flashes a glint on the ball.
  // Chapter 17: the glint and the flare fire on the title's biggest hit, its last word.
  const landed = moment.time - TITLE_WORDS[TITLE_WORDS.length - 1];
  room.glint.pose(landed, trophy.children[0] ?? trophy);
  if (room.glint.sprite.visible) room.glint.sprite.position.set(0, environment.stageHeight + FILM_INTRO.glint, 0);
  const ball = new THREE.Vector3(0, environment.stageHeight + FILM_INTRO.glint, 0);
  const flared = teamShot || castShot ? 0 : room.flare.pose(landed, ball, hold, moment.time);
  const drop = room.title.pose(moment.time, mobile, camera);
  const boost = teamShot || castShot ? 0 : Math.max(flared, drop.flash);   // every word's hit flashes the beams
  if (teamShot || castShot) { room.flare.hide(); room.title.hide(); room.impact.hide(); }
  else { room.impact.pose(drop.words.map(word => ({...word, frameHeight: drop.frameHeight}))); camera.position.x += drop.shake[0]; camera.position.y += drop.shake[1]; }
  environment.rig.update(moment.time, blip.root.position, exit, boost);
  renderer.render(room.scene, camera);
}
