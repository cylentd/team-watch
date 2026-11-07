import { LINEUPS_SET_DETAIL as TUNING } from './constants-lineups.mjs';
import { LINEUPS_SET } from "./constants-lineups.mjs";
export { LINEUPS_SET };
import * as THREE from 'three';
import { PALETTE, TRANSITION } from './constants.mjs';
import { fontsReady } from './draft-textures.mjs';
import { seg } from './draft-motion.mjs';
import { blipFace } from './blip.mjs';
import { FILM_COPY } from './film-copy.mjs';
import { LINEUPS_COPY } from './lineups-copy.mjs';
import { registerSet, setOfBeat } from './film-sets.mjs';
import { checkLineups, lineupValues } from './lineups-data.mjs';
import { CLOCK, chapterSeconds } from './lineups-clock.mjs';
import { CARD, DESK, SHIELD, STATION, places } from './lineups-layout.mjs';
import { POSE, lineupsPose } from './lineups-pose.mjs';
import { badgeFace, cardFace, loadStrict } from './lineups-faces.mjs';
import { makeDesk } from './lineups-desk.mjs';
import { makeBackdrop } from './lineups-backdrop.mjs';
import { HIT, makeProps } from './lineups-props.mjs';
import { makeHeadline } from './lineups-headline.mjs';
import { LIFT, REDUCED, shot } from './lineups-camera.mjs';
import { measure } from './lineups-readout.mjs';

/* Chapter 4, Start/sit regrets (docs/madden-film-chapter4.md, "Cinematic revision", David 2026-11-05): Gibbs's DEF
   station and Lamarley's TE station on one desk in front of Chapter 5's riser, a lit stage behind it, posed every
   frame from lineups-pose.mjs, and the DOM headline over them. The film waits for both portraits and both badges
   (`ready`, rule 49); one that fails rejects it, the set disposes itself and the room falls back (app.mjs). */

const reducedMotion = () => globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
const state = {built: 0, disposed: 0, ready: false, shown: false, chapter: null, camera: null, slot: null, view: null, size: null, labels: [], objects: []};
const flashColor = new THREE.Color(PALETTE.down);

/* What the tests read (tests/pages/madden_lineups_set.py): counts, the last pose, and each printed word's box. */
export function lineupsReadout() {
  // A DOM chapter returns before the room draws or hides its sets (scene.mjs drawRoom), so the desk counts as shown
  // only while the room still shows the chapter it was last posed in.
  const {built, disposed, ready, camera, slot} = state, chapter = globalThis.document?.querySelector('[data-room]')?.dataset.chapter;
  const shown = state.shown && chapter === state.chapter;
  return {built, disposed, ready, shown, camera, slot, ...measure(state.labels, state.objects, state.view, state.size, shown)};
}

async function prepare(teams) {
  const response = await fetch(new URL('./lineups-receipts.json', import.meta.url));
  if (!response.ok) throw new Error('Lineup receipt unavailable: ' + response.status);
  const cast = lineupValues(checkLineups(await response.json()));
  await fontsReady();
  const [w5] = cast.tightends, portrait = player => new URL(player.portrait, import.meta.url).href;
  const avatar = id => { const source = teams.find(team => team.id === id)?.avatar; if (!source) throw new Error('Lineup badge missing: ' + id); return source; };
  const images = await Promise.all([portrait(w5.starter), portrait(w5.bench), avatar(cast.defenseTeam), avatar(cast.tightendTeam),
    ...cast.defense.map(entry => new URL(LINEUPS_COPY.defenseCard.logos[entry.name], import.meta.url).href)].map(loadStrict));
  return {cast, images};
}

/* The x the camera looks at, from its own pure shot, so the key light follows the station on a seek too. */
const lookX = (seconds, mobile) => shot(seconds < CLOCK.second ? 'lineup-defense' : 'lineup-tightends',
  seconds < CLOCK.second ? seconds : seconds - CLOCK.second, {mobile}).target.x;
/* The stage behind the desk comes up through the whip in and goes down through the crane onto Chapter 5's riser. */
const stageLevel = seconds => seg(seconds, -TRANSITION.window / 2, 0) * (1 - seg(seconds, CLOCK.end - TRANSITION.window / 2, CLOCK.end));

function factory(scene, {teams, table}) {
  const group = new THREE.Group(), base = {};
  group.visible = false; scene.add(group); state.built += 1;
  const room = document.querySelector('[data-room]') ?? document.body;
  let desk = null, props = null, cast = null, headline = null, stage = null, ownsBlip = false, lastBlip = null, gone = false;
  const ready = (async () => {
    const prepared = await prepare(teams);
    if (gone) return;
    cast = prepared.cast;
    const [fannin, henry, gibbsBadge, lamarleyBadge] = prepared.images;
    desk = makeDesk(cast, {gibbs: FILM_COPY.team[cast.defenseTeam], lamarley: FILM_COPY.team[cast.tightendTeam]});
    props = makeProps(cast, POSE.scores);
    stage = makeBackdrop([STATION.gibbs, STATION.lamarley]);
    props.cards[0].material.map = cardFace(cast.tightends[0].starter.name, fannin);
    props.cards[1].material.map = cardFace(cast.tightends[0].bench.name, henry);
    [gibbsBadge, lamarleyBadge].forEach((image, index) => { desk.badges[index].material.map = badgeFace(image); });
    props.shields.forEach((entry, index) => {
      entry.group.name = cast.defense[index].name;
      const map = new THREE.Texture(prepared.images[index + TUNING.badgeImageOffset]);
      map.colorSpace = THREE.SRGBColorSpace; map.needsUpdate = true;
      entry.logo.material.map = map; entry.logo.material.needsUpdate = true;
    });
    props.cards.forEach((entry, index) => { entry.group.name = cast.tightends[0][index ? 'bench' : 'starter'].name; });
    group.add(stage.group, desk.group, props.group);
    Object.assign(base, {strip: desk.strip.color.clone(), ledge: desk.ledgeLight.color.clone(), rack: desk.rackLight.color.clone(),
      gibbs: desk.rims.gibbs.color.clone(), start: desk.rims.start.color.clone()});
    headline = makeHeadline(room, cast, gibbsBadge.src);
    state.labels = [...desk.labels, ...props.labels];
    state.objects = [...props.shields, ...props.cards].map(entry => entry.group);
    state.ready = true;
  })();
  // A room that fails to build is never disposed (scene.mjs createRoom), so the set frees itself.
  ready.catch(() => set.dispose());

  const shine = (material, key, amount) => material.color.copy(base[key]).multiplyScalar(amount);
  const seat = (object, [x, y, z], height, squash) => {
    object.position.set(x, y - height * (1 - squash) / 2, z); object.scale.set(1, squash, 1);
  };

  function poseDesk(pose, mobile) {
    desk.place(mobile);
    pose.shields.forEach((entry, index) => {
      const {group: mesh, stamps} = props.shields[index], marks = pose.shieldStamps[index];
      mesh.visible = entry.visible;
      if (entry.visible) seat(mesh, entry.position, SHIELD.height, entry.squash);
      Object.entries(stamps).forEach(([key, stamp]) => { stamp.visible = marks[key].visible; stamp.scale.setScalar(marks[key].scale); });
    });
    pose.cards.forEach((entry, index) => {
      const {group: mesh} = props.cards[index];
      mesh.visible = entry.visible;
      if (entry.visible) seat(mesh, entry.position, CARD.height, entry.squash ?? 1);
    });
    shine(desk.strip, 'strip', pose.strip); shine(desk.ledgeLight, 'ledge', pose.ledge); shine(desk.rackLight, 'rack', pose.rims.rack);
    shine(desk.rims.gibbs, 'gibbs', pose.rims.gibbs); shine(desk.rims.start, 'start', pose.rims.start);
    desk.rims.gibbs.color.lerp(flashColor, pose.flash);   // the slot flashes red as a negative shield is kicked out
  }

  function poseMarks(pose, place) {
    Object.entries(pose.stamps).forEach(([key, entry]) => {
      if (key === 'week') return;
      const mesh = props.cards[entry.card].stamps.find(stamp => stamp.userData.key === key);
      mesh.visible = entry.visible; mesh.scale.setScalar(Math.max(entry.scale, TUNING.scaleFloor));
    });
    desk.weeks.forEach(mesh => {
      mesh.visible = pose.stamps.week.visible && mesh.userData.text === pose.stamps.week.text;
      mesh.scale.set(place.weekSize.width, place.weekSize.height * Math.max(pose.stamps.week.flip, TUNING.scaleFloor), 1);
    });
    const foot = ([x, , z], y = DESK.height) => new THREE.Vector3(x, y, z);
    const spots = {gibbs: foot(place.socket), flash: foot(place.socket), start: foot(place.start), rack: new THREE.Vector3(...place.rack)};
    Object.entries(props.shafts).forEach(([key, shaft]) => { shaft.group.position.copy(spots[key]); shaft.update(pose.shafts[key]); });
    Object.entries(props.impacts).forEach(([key, impact]) => impact.pose(pose.impacts[key], spots[key], LINEUPS_SET.hitHalf, LINEUPS_SET.hitUnit, HIT));
  }

  function poseBlip(blip, pose) {
    lastBlip = blip; ownsBlip = pose.blip.visible; blip.root.visible = pose.blip.visible;
    if (!pose.blip.visible) return;
    const {position, scale, squash, lean, nod, look} = pose.blip;
    blip.root.position.set(...position);
    blip.root.scale.set(scale, scale * squash, scale);
    blip.root.rotation.set(0, 0, -lean);
    blip.head.rotation.set(nod, look, 0);
    blipFace(blip, false);
    blip.root.name = 'Blip';
    if (!state.objects.includes(blip.root)) state.objects.push(blip.root);
  }

  const set = {ready, warmAt: [...CLOCK.landings, CLOCK.players, CLOCK.bench5, CLOCK.swap, CLOCK.bench8, CLOCK.outcome, CLOCK.second]
    .map(seconds => CLOCK.start + seconds + LINEUPS_SET.warm),
  update(moment, ctx) {
    if (!desk) return {};
    const reduced = reducedMotion(), mobile = ctx.mobile, seconds = chapterSeconds(moment.elapsed);
    const pose = lineupsPose(seconds, reduced, cast, mobile), place = places(mobile);
    group.visible = true; table.visible = false;
    REDUCED.clock = reduced ? seconds : null;   // before the camera frames this moment (draft.mjs update)
    poseDesk(pose, mobile); poseMarks(pose, place);
    desk.aim(lookX(seconds, mobile)); stage.update(stageLevel(seconds));
    if (ctx.blip) poseBlip(ctx.blip, pose);
    headline.update(seconds, reduced, mobile);
    Object.assign(state, {shown: true, chapter: moment.chapter, camera: setOfBeat(moment.beat)?.chapter ?? null, slot: pose.slot, view: ctx.camera, size: ctx.size});
    return {shake: pose.shake};
  },
  hide() {
    group.visible = false; headline?.hide(); state.shown = false; REDUCED.clock = null;
    if (ownsBlip && lastBlip) { lastBlip.root.visible = false; lastBlip.root.rotation.set(0, 0, 0); lastBlip.head.rotation.set(0, 0, 0); }
    ownsBlip = false;
  },
  dispose() {
    if (gone) return;
    gone = true; headline?.dispose(); headline = null;
    group.traverse(object => { object.geometry?.dispose(); [object.material].flat().forEach(material => { material?.map?.dispose(); material?.dispose(); }); });
    group.removeFromParent();
    Object.assign(state, {shown: false, labels: [], objects: [], view: null}); state.disposed += 1;
  }};
  return set;
}

registerSet('lineups', factory, {shot, lift: LIFT});
