import { DRAFT_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { LIGHT } from "./constants-draft-motion.mjs";
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { filmPlan } from './film.mjs';
import { mix } from './timeline.mjs';
import { BOARD, columnX, makeBoard } from "./draft-board.mjs";
import { cutHalves, stampMesh, station, weekLights } from './draft-props.mjs';
import { steal, traded, sleeper } from './draft-beats.mjs';
import { tradeProps } from './draft-trade.mjs';
import { CURSE, blipHome, columnPulse, curse, finale, homeward, injury, stationReveal } from './draft-curse.mjs';
import { blipFace } from './blip.mjs';
import { frame } from './draft-camera.mjs';
import { poseTable } from './draft-establish.mjs';
import { pathLight, makePathBeams, makeHeaderLights } from './draft-path-light.mjs';
import { BUILD, buildClock, buildCardLight, buildRailLight } from './draft-build.mjs';
import { makeRevealGlow } from './draft-reveal-glow.mjs';
import { makeBurn, ownerVisits } from './draft-burn.mjs';
import { seg } from './draft-motion.mjs';
import { stationLayout, trailStops } from './draft-floor.mjs';
import { stationText } from './draft-data.mjs';
import { FILM_COPY } from './film-copy.mjs';
import { makeFlame } from './draft-flame.mjs';
import { makeDraftGlints } from './film-glint.mjs';
import { fieldMarkings } from './environment.mjs';
import { buildSets } from './film-sets.mjs';
import './chapter-sets.mjs';

/* Chapter 1, Draft Receipts. Builds the room once; `update` poses all of it for one moment. */
// Light is linear: .16 reads as about half brightness on screen, enough to push the board back.
// The board's cards are lit evenly the whole fly-by (David rev 10: dark rows; ~~rows lit from .05 as the
// camera reached them, with a .7 flash~~, revision 8).
/* A team's pad colour on the waiver floor (rev 15, David: WARREN-TY's pad in the team's accent). The board has
   no team colours, so a team takes a palette accent by its id; the wire is the grey-blue PALETTE.blue. */
const TEAM_TINT = Object.freeze(['broadcast', 'lime', 'TE', 'boom', 'QB', 'DEF', 'WR', 'K']);   // no alert red: red means a bust

const FEATURED = ['steal', 'traded', 'sleeper', 'curse', 'injury'];
const POSES = {steal, traded, sleeper};
/* The trail's wide shot spans the stations before the last, from the leftmost to the rightmost; the reveal is the last's x. */
const trailSpan = (placed, end) => {
  const shown = placed.filter(entry => entry !== end).map(entry => entry.x);
  return {left: Math.min(...shown), right: Math.max(...shown), reveal: end.x};
};

export async function makeDraft(scene, draft, teams, trophy = null) {
  const board = await makeBoard(draft, teams, FILM_COPY);
  scene.add(board.group);
  const headerLights = makeHeaderLights(board.headers);
  const pathGlows = makePathBeams(board.cards);
  board.group.add(pathGlows.group);
  const revealGlow = makeRevealGlow(board.cards);
  board.group.add(revealGlow.mesh);
  // The board's own parts ride one pivot so the establishing shot can lay them flat as a table.
  const table = new THREE.Group();
  [...board.group.children].forEach(child => table.add(child));
  board.group.add(table);
  board.headers.forEach(header => { header.home = header.disc.position.y; });
  const plan = filmPlan(), index = Object.fromEntries(plan.beats.map((beat, at) => [beat.id, at]));
  const items = Object.fromEntries(FEATURED.map(beat => {
    const item = board.cards.get(draft.beats[beat].overall), root = new THREE.Group();
    item.mesh.add(root);
    item.props = {root, stampZ: BOARD.depth / 2 + TUNING.stampZ};
    return [beat, item];
  }));
  const add = (item, object, back = false) => {
    if (!back) return item.props.root.add(object);
    if (!item.props.back) { item.props.back = new THREE.Group(); item.props.back.rotation.y = Math.PI; item.props.root.add(item.props.back); }
    item.props.back.add(object);
  };
  const tag = item => `${item.pick.pos}${item.pick.finish}`;
  const through = draft.through;
  [['steal', false], ['sleeper', false], ['injury', false]].forEach(([beat, back]) => {
    items[beat].props.lights = weekLights(through); add(items[beat], items[beat].props.lights, back);
  });
  items.steal.props.stamp = stampMesh(tag(items.steal), PALETTE.broadcast); add(items.steal, items.steal.props.stamp, true);
  items.traded.props.stamp = stampMesh(tag(items.traded), PALETTE.down); add(items.traded, items.traded.props.stamp);
  items.steal.props.stamp.position.y = LIGHT.stampY;
  items.traded.props.stamp.position.y = LIGHT.stampY;
  items.injury.props.status = stampMesh(FILM_COPY.injuryStatus, PALETTE.print);
  const injuryPieces = cutHalves(items.injury.normal);
  injuryPieces.forEach(piece => board.group.add(piece));
  items.injury.props.status.position.x = LIGHT.status.x;
  items.injury.props.status.position.y = LIGHT.status.y;
  items.injury.props.status.scale.setScalar(LIGHT.status.scale);
  add(items.injury, items.injury.props.status);
  const steps = trailStops(draft.beats.curse.path);
  items.curse.props.flame = makeFlame();
  add(items.curse, items.curse.props.flame.group);
  const floor = new THREE.Group(); board.group.add(floor);
  // The draft room stands on the same dark turf as the opening, its yard lines faint (rev 17; ~~a plain dark floor~~).
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(...LIGHT.ground),
    new THREE.MeshBasicMaterial({color: PALETTE.turf, toneMapped: false}));
  ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; ground.add(fieldMarkings()); board.group.add(ground);
  const layouts = {desk: stationLayout(steps), phone: stationLayout(steps, true)}, stations = layouts.desk;
  const built = new Map(stations.map(entry => {
    const avatar = entry.kind === 'pit' ? null : board.headers.get(entry.team)?.disc.material;
    const tint = entry.kind === 'pit' ? PALETTE.blue : PALETTE[TEAM_TINT[entry.team % TEAM_TINT.length]];
    const mesh = station(entry.kind, stationText(entry), tint, avatar, entry.kind === 'pit' ? null : FILM_COPY.team[entry.team]);
    floor.add(mesh);
    return [entry.key, mesh];
  }));
  // Each owner's avatar burns while the card is on its pad and goes out when it leaves (draft-burn.mjs).
  const burns = [...ownerVisits(steps, CURSE.landings, CURSE.move)].map(([key, visits]) => {
    const burn = makeBurn(); built.get(key).add(burn.group);
    return {burn, visits};
  });
  // A station pops up just before the card first lands on it (draft-curse.mjs stationReveal).
  const arrival = new Map();
  steps.forEach((step, index) => { if (!arrival.has(step.station)) arrival.set(step.station, CURSE.landings[index]); });
  const last = steps.at(-1), lastStep = draft.beats.curse.path.at(-1);
  // The 0.0 lands on Godwin's own card as a stamp, so a phone reads it at the card's size.
  const tile = stampMesh((lastStep.points?.at(-1) ?? 0).toFixed(1), PALETTE.down); add(items.curse, tile);
  tile.position.y = LIGHT.stampY;
  const places = tradeProps(items.traded, draft, board, add);   // Aura's badge and the tag's cover (draft-trade.mjs)
  const glints = makeDraftGlints(scene);
  const blipState = {visible: false, position: new THREE.Vector3(), home: new THREE.Vector3(), squash: 1, lean: 0, look: 0, recoil: 0, scared: false};
  const colour = new THREE.Color(), unit = new THREE.Vector3(1, 1, 1);
  // The finale's build (draft-build.mjs): which step dims each column, nearest Romo's first.
  const winnerColumn = board.headers.get(draft.beats.finale.team).column;
  /* A card's light in the build, injury seconds `clock`, `seconds` into the beat: Romo's column steps up and goes
     full on the hit, the rest dim a group at a time. */
  const buildLight = (card, clock, seconds, finaleBeat) => {
    const column = board.headers.get(card.pick.team).column;
    return buildCardLight(clock, column, winnerColumn, LIGHT.focus, finaleBeat ? columnPulse(seconds) : LIGHT.focus);
  };
  // The camera's context: the featured cards, the trade's landing, the floor's stations, the winning column.
  const cameraCtx = (mobile, size) => {
    const placed = layouts[mobile ? 'phone' : 'desk'], layout = new Map(placed.map(entry => [entry.key, entry]));
    return {featured: Object.fromEntries(FEATURED.map(id => [id, items[id]])), landing: places.view,
      floorZ: layout.get('pit').z, finaleX: columnX(board.headers.get(draft.beats.finale.team).column), mobile, size,
      trail: trailSpan(placed, layout.get(last.station))};
  };
  // The later chapters' 3D sets (film-sets.mjs), built after the board; the film waits for them.
  const sets = buildSets(scene, {draft, teams, board: board.group, table, ground, trophy});
  await sets.ready;

  /* A set's moment: the set poses itself, the board's featured props hide, the camera takes the set's shot. */
  function poseSet(moment, camera, mobile, size, routed) {
    board.group.visible = true;
    scene.fog.density = LIGHT.fog;
    FEATURED.forEach(id => { items[id].props.root.visible = false; });
    glints.hide();
    const distance = frame(camera, moment, cameraCtx(mobile, size), routed.shake ?? 0);
    return {focus: distance, key: LIGHT.key, exposure: LIGHT.exposure};
  }

  function update(moment, camera, mobile, blip, size) {
    const routed = sets.update(moment, {camera, mobile, blip, size});   // hides every set that does not show
    if (routed) return poseSet(moment, camera, mobile, size, routed);
    board.group.visible = true;
    table.visible = true;   // a set may hide the board's wall
    scene.fog.density = LIGHT.fog;
    // `seconds` is the beat's motion clock: film seconds slowed by the beat's pace.
    const at = moment.beatIndex, beat = plan.beats[at], seconds = moment.beatProgress * beat.duration / beat.pace;
    poseTable(table, beat.id === 'board' ? seconds : Infinity);
    headerLights.update(seconds, beat.id === 'board');
    pathGlows.update(seconds, mobile, beat.id === 'board');
    revealGlow.update(seconds, beat.id === 'board');
    const placed = layouts[mobile ? 'phone' : 'desk'], layout = new Map(placed.map(entry => [entry.key, entry]));
    built.forEach((mesh, key) => {
      mesh.position.set(layout.get(key).x, 0, layout.get(key).z);
      mesh.scale.setScalar(Math.max(TUNING.scaleFloor, beat.id === 'curse' ? stationReveal(seconds, arrival.get(key)) : 1));
    });
    const pit = layout.get('pit');
    blipState.home.copy(blipHome(layout.get(steps[0].station), pit));   // between WARREN-TY's pad and the wire (rev 17)
    floor.visible = beat.id === 'curse';
    // The board beat has nothing on the floor, and the standing board's foot showed the turf as a bright green
    // band under it before the lower third's scrim rose (film 13.1; 2026-11-05). The room is dark there instead.
    ground.visible = beat.id !== 'board';
    injuryPieces.forEach(piece => { piece.visible = false; });
    Object.assign(blipState, {visible: false, squash: 1, lean: 0, look: 0, recoil: 0, scared: false});
    if (beat.id === 'curse') burns.forEach(({burn, visits}) => burn.update(seconds, visits));
    const lit = () => 1;
    const focus = beat.id === 'board' ? 1 : beat.id === 'finale' ? mix(LIGHT.focus, 1, seg(seconds, 0, LIGHT.focusIn))
      : at === 1 ? mix(1, LIGHT.focus, seg(seconds, 0, LIGHT.focusIn)) : LIGHT.focus;
    // In the finale the rails dim with the rest of the board, so only the winning column is lit.
    const rail = beat.id === 'finale' ? LIGHT.focus : focus;
    const clock = buildClock(beat.id, seconds), building = clock !== null && clock >= BUILD.steps[0];
    board.strips.forEach((strip, row) => strip.material.color.set(PALETTE.white)
      .multiplyScalar(LIGHT.strip * (building ? buildRailLight(clock, row) ?? rail : rail)));
    if (beat.id === 'finale') finale(seconds, board, draft.beats.finale.team);
    if (building && clock < BUILD.hit) board.glow.material.opacity = 0;
    if (beat.id !== 'finale') {
      board.glow.material.opacity = 0;
      board.headers.forEach(header => { header.disc.position.y = header.home; header.disc.scale.setScalar(1); });
    }
    board.cards.forEach(card => {
      card.mesh.position.copy(card.home); card.mesh.rotation.set(0, 0, 0); card.mesh.scale.setScalar(1); card.mesh.visible = true;
      if (card.normal) card.front.map = card.normal;
      // Ch17: from the injury's fade the build sets every card's light (draft-build.mjs). ~~The finale lit Romo's
      // column over its first 0.3 s and dimmed the rest~~ (rev 17).
      card.light = building ? buildLight(card, clock, seconds, beat.id === 'finale')
        : beat.id === 'board' ? pathLight(card.home.x, card.home.y, seconds, mobile) : lit(card.row) * focus;
      card.front.clippingPlanes = null;
    });
    let shake = 0;
    FEATURED.forEach(id => {
      const item = items[id], own = index[id];
      item.props.root.visible = at === own;
      item.props.root.scale.setScalar(1);   // the finale shrinks the props away; a seek back must restore them
      if (item.props.lights) item.props.lights.visible = true;
      [item.mesh.material].flat().forEach(material => { material.visible = true; });   // a seek back undoes the cut
      if (item.props.badge) item.props.badge.visible = false;   // the trade's pose shows it again
      if (at < own) return;
      // A beat's things leave at the next scene change: the card goes home (the board loop above put it
      // there, dimmed with the rest) and its stamps and lights go. The traded card stays beside Aura's badge,
      // off the board, without its stamp; the injured player's card is back whole in its slot.
      if (at > own && id !== 'traded') return;
      const local = at === own ? seconds : plan.beats[own].duration / plan.beats[own].pace;
      const result = id === 'curse' ? curse(local, item, Object.fromEntries(layout), steps, blipState, tile)
        : id === 'injury' ? injury(local, item, injuryPieces) : POSES[id](local, item, id === 'traded' ? places : blipState);
      // After its own beat a card keeps the board's light from the loop above, dimmed with the rest.
      if (at === own) { shake = result.shake; item.light = result.light; }
      if (beat.id === 'finale') {
        const back = homeward(seconds);
        item.mesh.position.lerp(item.home, back);
        item.mesh.rotation.set(mix(item.mesh.rotation.x, 0, back), mix(item.mesh.rotation.y, 0, back), mix(item.mesh.rotation.z, 0, back));
        item.mesh.scale.lerp(unit, back);
        item.props.root.scale.setScalar(1 - back);
        item.props.badge?.scale.setScalar(Math.max(TUNING.scaleFloor, 1 - back));
      }
      if (at !== own) Object.assign(blipState, {visible: false});
    });
    board.cards.forEach(card => {
      colour.set(PALETTE.white).multiplyScalar(card.light);
      card.front.color.copy(colour);
    });
    blip.root.visible = blipState.visible;
    if (blipState.visible) {
      blip.root.position.copy(blipState.position);
      blip.root.scale.set(LIGHT.blip, LIGHT.blip * blipState.squash, LIGHT.blip);
      blip.root.rotation.set(-blipState.recoil, 0, blipState.lean);   // a recoil leans him back, away from the camera
      blip.head.rotation.y = blipState.look;
    }
    blipFace(blip, blipState.scared);   // reset to false each frame above; only the curse sets it
    const distance = frame(camera, moment, cameraCtx(mobile, size), shake);
    glints.update(moment, items, tile);
    // The room comes up under the light sweeping down from the opening; a reduced-motion still is lit at once.
    return {focus: distance, key: LIGHT.key, exposure: LIGHT.exposure * (moment.beatProgress === 1 ? 1 : seg(moment.elapsed - plan.chapterAt, 0, LIGHT.exposureIn))};
  }

  function hide(blip) {
    board.group.visible = false;
    glints.hide();
    sets.hide();
    blip.root.rotation.set(0, 0, 0);
    blipFace(blip, false);
  }
  return {update, hide, dispose: sets.dispose, warmAt: sets.warmAt};
}
