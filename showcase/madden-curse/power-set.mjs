import { POWER_SET_DETAIL as TUNING } from './constants-power.mjs';
import { POWER_SET } from "./constants-power.mjs";
export { POWER_SET };
import * as THREE from 'three';
import { fontsReady } from './draft-textures.mjs';
import { blipFace } from './blip.mjs';
import { makeImpact } from './film-impact.mjs';
import { makeGlint } from "./film-glint.mjs";
import { FILM_COPY } from './film-copy.mjs';
import { registerSet } from './film-sets.mjs';
import { CAST } from './power-cast.mjs';
import { TIMES } from './power-clock.mjs';
import { powerPose } from './power-pose.mjs';
import { RISER, TIER, TROPHY, slot, trophySpot } from './power-layout.mjs';
import { makeRiser } from './power-riser.mjs';
import { makeProps } from './power-props.mjs';
import { makeDress } from './power-dress.mjs';
import { makeTrophyRig } from './power-trophy.mjs';
import { makeHeadline } from './power-headline.mjs';
import { REDUCED, lift, shot } from './power-camera.mjs';

/* Chapter 5, Midseason power rankings, as a 3D set in the room (docs/madden-film-chapter5.md, "Cinematic
   revision", David 2026-11-05): the riser on the board's footprint and its dressing, the plates that land in the
   standings and shuffle into power order, the feature's stamps, the opening's trophy lowering onto the summit, Blip
   and the headline over them. The film waits for the twelve badges (`ready`); a badge that fails rejects it, and
   the room falls back (app.mjs). */

const reducedMotion = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
const vector = point => new THREE.Vector3(...point);
let activeTrophy = null;

export function powerReadout() {
  return {bound: Boolean(activeTrophy), visible: Boolean(activeTrophy?.visible)};
}

/* Decode one badge; a failure rejects, so the film never plays without its riser (rule 24). */
function decode(source) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`power: badge ${source}`));
    image.src = source;
  });
}

function factory(scene, {teams, table, ground, trophy}) {
  activeTrophy = trophy ?? null;
  const group = new THREE.Group(), dimmed = new THREE.Color();
  group.visible = false; scene.add(group);
  const room = document.querySelector('[data-room]') ?? document.body, headline = makeHeadline(room);
  const front = makeImpact(group), back = makeImpact(group), glint = makeGlint(group, POWER_SET.glint);
  const rig = trophy ? makeTrophyRig(trophy) : null, dress = makeDress();
  group.add(dress.group);
  let riser = null, props = null, ownsBlip = false, lastBlip = null, groundBase = null;
  const ready = (async () => {
    if (!CAST.values) throw CAST.error ?? new Error('power: no receipts');
    await fontsReady();
    const order = CAST.values.order.map(team => ({...team, name: FILM_COPY.team[team.id] ?? team.name}));
    const images = Object.fromEntries(await Promise.all(order.map(async team =>
      [team.id, await decode(teams.find(entry => entry.id === team.id).avatar)])));
    riser = makeRiser(order, images); props = makeProps(CAST.values.feature);
    group.add(riser.group, props.group);
  })();
  // The caller sees the rejection through `ready`; the set takes its headline out of the page itself, since a room
  // that fails to build is never disposed (scene.mjs createRoom).
  ready.catch(() => { headline.dispose(); if (activeTrophy === trophy) activeTrophy = null; });

  /* The two impacts: the front one carries the front row's landing, the shuffle's and the trophy's; the back one the
     back row's landing and Blip's. Each shows the latest of its hits that has landed. */
  function poseImpacts(state, mobile) {
    const {impacts} = state, low = slot(TIER.places, mobile), high = slot(1, mobile), width = RISER.lip.width * TUNING.waveWidthScale;
    const latest = entries => entries.filter(entry => entry.age >= 0).at(-1) ?? entries[0];
    const a = latest([{age: impacts.standings, at: [0, low.y, low.z], own: POWER_SET.tier, width},
      {age: impacts.order, at: [0, low.y, low.z], own: POWER_SET.order, width}, {age: impacts.trophy, at: trophySpot(mobile), own: POWER_SET.trophy, width: TROPHY.radius * 2}]);
    const b = latest([{age: impacts.standings, at: [0, high.y, high.z], own: POWER_SET.tier, width},
      {age: impacts.blip, at: state.blip.position, own: POWER_SET.blip, width: RISER.blip}]);
    front.pose(a.age, vector(a.at), a.width, a.own.unit, a.own.hit, {mobile});
    back.pose(b.age, vector(b.at), b.width, b.own.unit, b.own.hit, {mobile});
  }

  function poseBlip(blip, state) {
    lastBlip = blip;
    blip.root.visible = state.blip.visible;
    ownsBlip = state.blip.visible;
    if (!state.blip.visible) return;
    const [x, y, z] = state.blip.position;
    blip.root.position.set(x, y + state.blip.lift, z);
    blip.root.scale.set(RISER.blip, RISER.blip * state.blip.squash, RISER.blip);
    blip.root.rotation.set(0, 0, 0);
    blip.head.rotation.y = 0;
    blipFace(blip, false);
  }

  return {ready, warmAt: [TIMES.standings, TIMES.shuffle[1], TIMES.feature, TIMES.verdict, TIMES.four, TIMES.pull[1], TIMES.trophy[1],
    TIMES.hops[1], TIMES.wave, TIMES.identIn, TIMES.last].map(time => time + POWER_SET.warm),
  update(moment, ctx) {
    if (!riser) return {};
    const reduced = reducedMotion(), mobile = ctx.mobile, time = moment.elapsed;
    REDUCED.clock = reduced ? time : null;
    const state = powerPose(time, reduced, CAST, mobile);
    group.visible = true; table.visible = false;
    groundBase ??= ground.material.color.clone();
    ground.material.color.copy(dimmed.copy(groundBase).multiplyScalar(state.dim));
    riser.pose(state, mobile, CAST.feature); props.pose(state, mobile, CAST.feature);
    dress.update(state, time, mobile, ctx.camera);
    rig?.pose(state.trophy, mobile);
    glint.pose(reduced || !rig ? -1 : time - TIMES.last, rig?.ball);
    poseImpacts(state, mobile);
    if (ctx.blip) poseBlip(ctx.blip, state);
    headline.update(time, reduced, mobile);
    return {shake: state.shake};
  },
  hide() {
    REDUCED.clock = null;
    group.visible = false; headline.hide(); rig?.release();
    if (groundBase) ground.material.color.copy(groundBase);
    // Blip leaves with the riser; the next pose that wants him (Chapter 1's, another set's) shows him again.
    if (ownsBlip && lastBlip) lastBlip.root.visible = false;
    ownsBlip = false;
  },
  dispose() {
    REDUCED.clock = null;
    if (activeTrophy === trophy) activeTrophy = null;
    rig?.release(); headline.dispose(); riser?.dispose(); props?.dispose(); dress.dispose();
    group.traverse(object => { object.geometry?.dispose(); [object.material].flat().forEach(material => { material?.map?.dispose(); material?.alphaMap?.dispose(); material?.dispose(); }); });
    group.removeFromParent();
    if (groundBase) ground.material.color.copy(groundBase);
  }};
}

registerSet('power', factory, {shot, lift});
