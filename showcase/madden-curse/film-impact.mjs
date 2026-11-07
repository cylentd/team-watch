import { FILM_IMPACT_DETAIL as TUNING } from './constants-title.mjs';
import { IMPACT } from "./constants-title.mjs";
export { IMPACT };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { spark } from './draft-flame.mjs';

/* A title word's hit (David, revision 14; chapter 17: "should be crazier"). On the frame it lands, a white shock
   ring races out from the letters' foot and leaves a ring of embers that glows for a second and a half; sparks
   with trails burst up, fall under gravity and bounce once on the bar before they die; chips of the letters'
   own material tumble out; and a white dust puff rises and clears. CURSE's hit (`second`, `carpet`) adds a
   second, larger ring and a brief ember carpet across the whole frame. Every piece is a pure function of the
   time since the hit, so seeking the film shows the same frame every time. It plays at the lower-third bar, in
   the title's camera-riding group (film-title-drop.mjs), so every size is in frame heights and the rings lie
   `tilt` off edge-on, read as floor rings seen from above. A phone draws the `phone` share of each count, so it
   holds frame rate. Each word's `hit` (film-title-drop.mjs TITLE_DROP.hits) scales it. ~~72 sparks, no trails
   or bounce, one ring~~ (chapter 17 first pass). */

const TONE = {ink: PALETTE.ink, lime: PALETTE.brandLime};   // a chip's colour, the word's own face
const LONGEST = Math.max(IMPACT.sparks.life[1] + IMPACT.sparks.trail, IMPACT.embers.life, IMPACT.chips.life,
  IMPACT.dust.life, IMPACT.second.delay + IMPACT.second.life, 2 / IMPACT.carpet.speed + IMPACT.carpet.life);

const outCubic = value => 1 - (1 - value) ** TUNING.cubicExponent;
const random = (index, salt) => { const value = Math.sin(index * TUNING.randomIndexMultiplier + salt * TUNING.randomSaltMultiplier) * TUNING.randomOutputMultiplier; return value - Math.floor(value); };
const between = ([low, high], index, salt) => low + (high - low) * random(index, salt);

/* The ring `age` seconds after the hit, its radius in frame heights (times the hit's `scale`): null before it
   and once it has gone. */
export function ringAt(age, scale = 1) {
  const {life, from, to, opacity} = IMPACT.ring;
  if (age < 0 || age >= life) return null;
  return {radius: (from + (to - from) * outCubic(age / life)) * scale, opacity: opacity * (1 - age / life) ** TUNING.ringFadeExponent};
}

/* A spark's height over the bar `age` seconds after the hit, thrown up at `up` frame heights a second: it falls
   under gravity, bounces once with `bounce` of its landing speed, lands again and rests. */
export function sparkHeight(age, up) {
  const {gravity, bounce, lift} = IMPACT.sparks;
  if (age < 0) return lift;
  const first = (up + Math.sqrt(up * up + 2 * gravity * lift)) / gravity;
  if (age < first) return Math.max(0, lift + up * age - gravity * age * age / 2);
  const rebound = bounce * (gravity * first - up), second = 2 * rebound / gravity, after = age - first;
  return after < second ? Math.max(0, rebound * after - gravity * after * after / 2) : 0;
}

/* The ring of embers the shock ring leaves `age` seconds after the hit: how far out it has spread (0..1) and how
   bright it still is; null before the hit and once it has gone. */
export function embersAt(age) {
  const {life, out} = IMPACT.embers;
  if (age < 0 || age >= life) return null;
  return {spread: outCubic(Math.min(1, age / out)), opacity: (1 - age / life) ** TUNING.glowFadeExponent};
}

const FULL = Object.freeze({ring: 1, sparks: 1, dust: 1, tone: 'ink', second: 0, carpet: false});
const overlay = extra => ({transparent: true, depthWrite: false, depthTest: false, toneMapped: false, fog: false, ...extra});
const glowing = map => new THREE.PointsMaterial(overlay({map, vertexColors: true, blending: THREE.AdditiveBlending}));

/* A cloud of `count` points (or line segments, `ends` 2) with a colour per vertex. */
function cloud(count, ends, material) {
  const geometry = new THREE.BufferGeometry(), positions = new Float32Array(count * ends * TUNING.positionComponents), colours = new Float32Array(count * ends * TUNING.colorComponents);
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, TUNING.positionComponents));
  geometry.setAttribute('color', new THREE.BufferAttribute(colours, TUNING.colorComponents));
  const object = ends === 2 ? new THREE.LineSegments(geometry, material) : new THREE.Points(geometry, material);
  object.frustumCulled = false;
  return {object, geometry, positions, colours,
    done(drawn) { geometry.setDrawRange(0, drawn * ends); geometry.attributes.position.needsUpdate = geometry.attributes.color.needsUpdate = true; }};
}

function ringMesh(width) {
  const mesh = new THREE.Mesh(new THREE.RingGeometry(1 - width, 1, TUNING.ringSegments, 1, Math.PI, Math.PI),
    new THREE.MeshBasicMaterial(overlay({color: PALETTE.white, blending: THREE.AdditiveBlending, side: THREE.DoubleSide})));
  mesh.rotation.x = -Math.PI / 2 + IMPACT.ring.tilt;
  return mesh;
}

export function makeImpact(parent) {
  const group = new THREE.Group(), glow = spark();
  const ring = ringMesh(IMPACT.ring.width), outer = ringMesh(IMPACT.second.width);
  const heads = cloud(IMPACT.sparks.count, 1, glowing(glow));
  const trails = cloud(IMPACT.sparks.count, 2, new THREE.LineBasicMaterial(overlay({vertexColors: true, blending: THREE.AdditiveBlending})));
  const embers = cloud(IMPACT.embers.count, 1, glowing(glow)), carpet = cloud(IMPACT.carpet.count, 1, glowing(glow));
  const plane = new THREE.Group();   // the rings' floor plane, for the embers
  plane.rotation.x = ring.rotation.x; plane.add(embers.object);
  const chipMaterial = new THREE.MeshBasicMaterial(overlay({side: THREE.DoubleSide}));
  const chipShape = new THREE.PlaneGeometry(1, 1);
  const chips = Array.from({length: IMPACT.chips.count}, () => new THREE.Mesh(chipShape, chipMaterial));
  const dust = Array.from({length: IMPACT.dust.count}, () => new THREE.Sprite(new THREE.SpriteMaterial(overlay({map: glow, color: PALETTE.white}))));
  const pieces = [ring, outer, heads.object, trails.object, plane, carpet.object, ...chips, ...dust];
  pieces.forEach(piece => { piece.renderOrder = IMPACT.order; });
  embers.object.renderOrder = IMPACT.order;
  group.add(...pieces);
  group.visible = false;
  parent.add(group);
  const white = new THREE.Color(PALETTE.white), amber = new THREE.Color(PALETTE.boom), colour = new THREE.Color();
  const share = (piece, mobile) => (mobile ? IMPACT[piece].phone : IMPACT[piece].count);

  function poseRings(age, centre, unit, hit) {
    const shock = ringAt(age, hit.ring);
    ring.visible = Boolean(shock);
    if (shock) { ring.position.copy(centre); ring.scale.setScalar(shock.radius * unit); ring.material.opacity = shock.opacity; }
    const {delay, life, opacity} = IMPACT.second, late = (age - delay) / life;
    outer.visible = hit.second > 0 && late >= 0 && late < 1;
    if (outer.visible) {
      outer.position.copy(centre);
      outer.scale.setScalar((IMPACT.ring.from + (IMPACT.ring.to - IMPACT.ring.from) * outCubic(late)) * hit.second * hit.ring * unit);
      outer.material.opacity = opacity * (1 - late) ** TUNING.ringFadeExponent;
    }
  }

  function poseSparks(age, centre, halfWidth, unit, hit, mobile) {
    const {life, up, out, drag, trail, amber: amberShare, size} = IMPACT.sparks;
    const flying = Math.round(share('sparks', mobile) * hit.sparks), at = (index, time) => {
      const spread = (1 - Math.exp(-drag * time)) / drag;
      return [centre.x + (random(index, TUNING.sparkAcrossSalt) - TUNING.randomCenter) * 2 * halfWidth + (random(index, 2) - TUNING.randomCenter) * 2 * out * spread * unit,
        centre.y + sparkHeight(time, between(up, index, TUNING.sparkUpSalt)) * unit, centre.z + (random(index, TUNING.sparkDepthSalt) - TUNING.randomCenter) * out * spread * unit];
    };
    heads.object.material.size = size * unit;
    for (let index = 0; index < flying; index++) {
      const left = Math.max(0, 1 - age / between(life, index, 1));
      colour.copy(random(index, TUNING.sparkColorSalt) < amberShare ? amber : white).multiplyScalar(left);
      const head = at(index, age), tail = at(index, Math.max(0, age - trail));
      heads.positions.set(head, index * TUNING.positionComponents); heads.colours.set([colour.r, colour.g, colour.b], index * TUNING.colorComponents);
      trails.positions.set([...head, ...tail], index * TUNING.lineComponents);
      trails.colours.set([colour.r, colour.g, colour.b, 0, 0, 0], index * TUNING.lineComponents);   // the trail fades to nothing
    }
    heads.done(flying); trails.done(flying);
  }

  function poseEmbers(age, centre, unit, hit, mobile) {
    const glowAt = embersAt(age), count = share('embers', mobile);
    plane.visible = Boolean(glowAt);
    if (!glowAt) return;
    plane.position.copy(centre);
    embers.object.material.size = IMPACT.embers.size * unit;
    const reach = IMPACT.ring.to * hit.ring * unit * glowAt.spread;
    for (let index = 0; index < count; index++) {
      const angle = Math.PI * 2 * (index + random(index, TUNING.emberAngleSalt)) / count, radius = reach * between(IMPACT.embers.reach, index, TUNING.emberReachSalt);
      const flicker = TUNING.emberFlickerBase + TUNING.emberFlickerAmplitude * Math.sin(age * IMPACT.embers.flicker + index * TUNING.emberFlickerPhase);
      colour.copy(amber).lerp(white, random(index, TUNING.emberColorSalt) * TUNING.emberWhiteMix).multiplyScalar(glowAt.opacity * flicker);
      embers.positions.set([Math.cos(angle) * radius, Math.sin(angle) * radius, 0], index * TUNING.positionComponents);
      embers.colours.set([colour.r, colour.g, colour.b], index * TUNING.colorComponents);
    }
    embers.done(count);
  }

  function poseChips(age, centre, halfWidth, unit, hit, mobile) {
    const {life, size, up, out, spin} = IMPACT.chips, count = share('chips', mobile), left = 1 - age / life;
    chipMaterial.color.setHex(TONE[hit.tone]);
    chipMaterial.opacity = Math.min(1, Math.max(0, left) * TUNING.chipOpacityGain);
    chips.forEach((chip, index) => {
      chip.visible = index < count && left > 0;
      if (!chip.visible) return;
      const spread = (1 - Math.exp(-IMPACT.sparks.drag * age)) / IMPACT.sparks.drag;
      chip.position.set(centre.x + (random(index, TUNING.chipAcrossSalt) - TUNING.randomCenter) * 2 * halfWidth + (random(index, TUNING.chipSpreadSalt) - TUNING.randomCenter) * 2 * out * spread * unit,
        centre.y + sparkHeight(age, between(up, index, TUNING.chipUpSalt)) * unit, centre.z + (random(index, TUNING.chipDepthSalt) - TUNING.randomCenter) * out * spread * unit);
      chip.scale.setScalar(between(size, index, TUNING.chipSizeSalt) * unit);
      chip.rotation.set(spin * age * random(index, TUNING.chipSpinXSalt), spin * age * random(index, TUNING.chipSpinYSalt), spin * age * random(index, TUNING.chipSpinZSalt));
    });
  }

  function poseCarpet(age, centre, unit, hit, word, mobile) {
    carpet.object.visible = hit.carpet && Boolean(word);
    if (!carpet.object.visible) return;
    const {life, speed, depth, size, rise} = IMPACT.carpet, count = share('carpet', mobile);
    carpet.object.material.size = size * unit;
    let lit = 0;
    for (let index = 0; index < count; index++) {
      const x = word.frameLeft + random(index, TUNING.carpetAcrossSalt) * word.frameWidth;
      // A wave from the word outward: each ember lights as it passes, then dies.
      const since = age - Math.abs(x - centre.x) / (speed * word.frameWidth), glowFor = since / life;
      const bright = since >= 0 && glowFor < 1 ? (1 - glowFor) ** TUNING.carpetFadeExponent : 0;
      colour.copy(amber).lerp(white, random(index, TUNING.carpetColorSalt) * TUNING.carpetWhiteMix).multiplyScalar(bright);
      carpet.positions.set([x, centre.y + ((random(index, TUNING.carpetRiseSalt) - TUNING.randomCenter) * depth + rise * Math.max(0, glowFor)) * unit,
        centre.z + (random(index, TUNING.carpetDepthSalt) - TUNING.randomCenter) * depth * unit], index * TUNING.positionComponents);
      carpet.colours.set([colour.r, colour.g, colour.b], index * TUNING.colorComponents);
      lit = index + 1;
    }
    carpet.done(lit);
  }

  function poseDust(age, centre, halfWidth, unit, hit) {
    const {life, from, to, opacity, rise, spread} = IMPACT.dust, puff = Math.min(1, age / life);
    dust.forEach((sprite, index) => {
      const across = (index / (dust.length - 1) - TUNING.randomCenter) * 2 * halfWidth * spread;
      sprite.visible = age < life;
      sprite.position.set(centre.x + across, centre.y + (from / 2 + rise * outCubic(puff)) * unit, centre.z);
      sprite.scale.setScalar((from + (to - from) * outCubic(puff)) * unit * hit.dust);
      sprite.material.opacity = opacity * (1 - puff) ** 2;
    });
  }

  /* The impact `age` seconds after the hit, at `centre` (the letters' foot), along letters `halfWidth` wide, in a
     frame `unit` high, as big as `hit` says. `word` (film-title-drop.mjs pose) gives the frame's left edge and
     width for the carpet, and whether this is a phone. */
  function pose(age, centre, halfWidth, unit, hit = FULL, word = null) {
    group.visible = age >= 0 && age < LONGEST;
    if (!group.visible) return;
    const mobile = Boolean(word?.mobile);
    poseRings(age, centre, unit, hit);
    poseSparks(age, centre, halfWidth, unit, hit, mobile);
    poseEmbers(age, centre, unit, hit, mobile);
    poseChips(age, centre, halfWidth, unit, hit, mobile);
    poseCarpet(age, centre, unit, hit, word, mobile);
    poseDust(age, centre, halfWidth, unit, hit);
  }
  return {group, ring, sparks: heads.object, dust, pose, hide() { group.visible = false; }};
}
