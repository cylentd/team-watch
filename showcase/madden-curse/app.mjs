import { APP_DETAIL as TUNING } from './constants-playback.mjs';
import { OPENING, SHOW } from './constants.mjs';
import { COPY } from './content.mjs';
import { FILM_COPY } from './film-copy.mjs';
import { showMoment } from './timeline.mjs';
import { filmMoment, filmPlan } from './film.mjs';
import { flareAt, zoomAmount } from './film-zoom.mjs';
import { endcardPose, identPose, winkAt } from './film-ident.mjs';
import { TITLE_PLACE } from './film-title-place.mjs';
import { mountReview } from './film-review.mjs';
import { createSound } from './audio.mjs';
import { checkDraft } from './draft-data.mjs';
import { makeReceipts } from './receipts.mjs';
import { checkTrades } from './trades-data.mjs';
import { makeTrades } from './trades-view.mjs';
import { checkWaivers } from './waivers-data.mjs';
import { makeWaivers } from './waivers-view.mjs';

import { loadEdition, report, story, readTeam } from './editorial.mjs';

let edition, receipt = () => {}, trades = () => {}, waivers = () => {}, waiverCard = null, review = null;
let preparedRoom = null, initializationFailed = false;
const query = new URLSearchParams(location.search);
if (query.has('embed')) document.body.dataset.embed = '';
/* ?film plays the midseason film (the opening, then Chapter 1); without it the 40 s promo is unchanged. */
const film = query.has('film');
const program = film ? {duration: filmPlan().duration, moment: filmMoment} : {duration: SHOW.duration, moment: showMoment};
const TEXT = film ? {...COPY, ...FILM_COPY.ui} : COPY;
if (film) document.body.dataset.film = '';
// The tagline sits on the 3D title's own baseline (film-title-place.mjs), so the CSS reads the letters' numbers.
if (film) [['desk', TITLE_PLACE.desk], ['phone', TITLE_PLACE.phone]].forEach(([device, place]) =>
  ['baseline', 'left'].forEach(key => document.body.style.setProperty(`--film-title-${key}-${device}`, place[key])));
if (film) document.body.style.setProperty('--film-tag-gap', TITLE_PLACE.tag);
const root = document.querySelector('[data-room]');
const select = name => root.querySelector(`[data-${name}]`);
const motion = matchMedia('(prefers-reduced-motion: reduce)');
const state = {time: program.duration, playing: false, started: false, inspection: false,
  rotation: 0, frame: 0, previous: 0, room: null, disposed: false, pointer: null};
const sound = createSound(film), listeners = new AbortController();
const options = {signal: listeners.signal};
document.querySelectorAll('[data-copy]').forEach(element => {
  if (element.dataset.copy === 'brand') element.setAttribute('aria-label', TEXT.brand);
  else element.textContent = TEXT[element.dataset.copy];
});
document.title = COPY.pageTitle;

// Reduced motion stills the promo; the film still plays, as one still per beat.
const still = () => motion.matches && !film;
function status(key) { select('status').textContent = TEXT[key]; }
function notice(key) { select('notice').hidden = false; select('notice').textContent = TEXT[key]; }

function discardPrepared() {
  const room = preparedRoom;
  preparedRoom = null;
  room?.dispose();
}

function draw() {
  const moment = program.moment(!state.started && !motion.matches ? OPENING.duration : state.time, motion.matches);
  if (!state.started && !motion.matches) moment.chapter = 'logo';
  if (state.inspection) Object.assign(moment, showMoment(OPENING.duration), {chapter: 'logo'});
  story(moment, edition); receipt(moment); trades(moment); waivers(moment, motion.matches);
  state.room?.draw(moment, state.rotation, state.inspection);
  root.dataset.chapter = moment.chapter;
  // The light sweeping through a scene change (film.mjs transitionAt, film.css .wipe).
  const sweep = moment.transition;
  root.style.setProperty('--wipe', sweep ? sweep.amount : 0);
  root.style.setProperty('--wipe-glow', sweep ? Math.sin(Math.PI * sweep.amount) : 0);
  root.dataset.wipe = sweep?.kind ?? 'none';
  // The zoom into the ball (film-zoom.mjs): the tagline slides out with it and the frame whites out into the board.
  const zooming = film && state.started && !state.inspection;
  root.style.setProperty('--zoom', zooming ? zoomAmount(state.time) : 0);
  root.style.setProperty('--flare', zooming ? flareAt(state.time) : 0);
  // The TEAM WATCH tag is an ident: the opening only, until the last chapter's close (film-ident.mjs).
  const ident = film && state.started && !state.inspection ? identPose(state.time) : {opacity: 1, scale: 1};
  root.style.setProperty('--ident', ident.opacity);
  root.style.setProperty('--ident-scale', ident.scale);
  root.dataset.ident = ident.opacity > 0 ? 'visible' : 'hidden';
  const ending = zooming ? endcardPose(state.time, motion.matches) : {active: false, black: 0, logo: 0};
  root.dataset.endcard = ending.active;
  root.style.setProperty('--end-black', ending.black);
  root.style.setProperty('--end-logo', ending.logo);
  root.style.setProperty('--end-wink', zooming ? winkAt(state.time, motion.matches) : 0);
  root.style.setProperty('--logo', moment.hero);
  root.style.setProperty('--progress', state.time / program.duration);
  select('identity').setAttribute('aria-hidden', moment.hero === 0);
  root.querySelector('[role=progressbar]').setAttribute('aria-valuenow', state.time.toFixed(2));
  select('play').textContent = TEXT[state.playing ? 'pause' : !state.started ? 'play' : moment.complete ? 'replay' : 'resume'];
  select('play').disabled = still() || !state.room;
  select('inspect').setAttribute('aria-pressed', state.inspection);
  select('inspect').textContent = TEXT[state.inspection ? 'finishInspect' : 'inspect'];
  select('seek').value = state.time; review?.update(state.time);
  root.dataset.mode = state.inspection ? 'inspect' : 'show';
  root.dataset.playing = state.playing; root.dataset.started = state.started;
}

/* The controls hide while the film plays, so they never cover the scene; a touch, a move or a key
   brings them back for AWAKE_MS. */
const AWAKE_MS = 2000;   // David rev 16: the bar hides after 2 s without a move
let asleep = 0;
function wake() {
  root.dataset.awake = '';
  clearTimeout(asleep);
  asleep = setTimeout(() => { delete root.dataset.awake; }, AWAKE_MS);
}

function pause(key = 'paused') {
  state.playing = false; cancelAnimationFrame(state.frame); state.frame = 0;
  sound.stop(); status(key); draw();
}

function seekTo(time) {
  state.started = true; state.inspection = false; state.time = time; sound.seek(time); pause();
}

function tick(timestamp) {
  if (!state.playing || state.disposed) return;
  const delta = Math.max(0, (timestamp - state.previous) / OPENING.milliseconds);
  state.previous = timestamp;
  state.time = Math.min(program.duration, sound.clock(state.time, delta) ?? state.time + delta);   // the music leads when it plays
  if (review) state.time = review.wrap(state.time);   // a looping beat starts over (film-review.mjs)
  sound.update(state.time); draw();
  if (state.time >= program.duration) pause('complete');
  else state.frame = requestAnimationFrame(tick);
}

function play() {
  if (!state.room || still()) return;
  if (state.playing) return pause();
  if (state.time >= program.duration) { state.time = 0; sound.start(); }
  state.started = true; state.playing = true; state.inspection = false; state.rotation = 0;
  sound.play(state.time);
  state.previous = performance.now(); status('playing'); draw();
  state.frame = requestAnimationFrame(tick);
}

function inspect() {
  pause('inspectHint'); state.time = program.duration; state.inspection = !state.inspection;
  status(state.inspection ? 'inspectHint' : 'ready'); draw();
  if (state.inspection) state.room.canvas.focus();
}

function rotate(amount) {
  if (!state.inspection) return;
  state.rotation = Math.max(-OPENING.inspectionLimit, Math.min(OPENING.inspectionLimit, state.rotation + amount));
  draw();
}

function fallback(key = 'webglError') {
  const room = state.room;
  state.room = null; state.time = program.duration; state.inspection = false;
  room?.dispose();
  pause(key); root.dataset.phase = 'fallback';
  root.setAttribute('aria-busy', 'false'); select('controls').inert = false;
  select('story').hidden = true;
  select('play').disabled = true; select('inspect').disabled = true;
  root.style.setProperty('--logo', 1);
  select('identity').setAttribute('aria-hidden', 'false');
}

function wire() {
  ['pointermove', 'pointerdown', 'keydown'].forEach(name => root.addEventListener(name, wake, options));
  select('seek').addEventListener('input', event => seekTo(Number(event.target.value)), options);
  select('read').addEventListener('click', () => { pause(); readTeam(); }, options);
  window.addEventListener('message', event => {
    if (event.origin === location.origin && event.source === parent && event.data?.type === 'madden-pause') pause();
  }, options);
  select('viewport').addEventListener('click', event => {
    if (film || state.time < SHOW.castAt || state.inspection || !state.started) return;
    const bounds = select('viewport').getBoundingClientRect();
    const id = state.room?.pick({x: (event.clientX - bounds.left) / bounds.width * 2 - 1, y: 1 - (event.clientY - bounds.top) / bounds.height * 2});
    if (id) { pause(); readTeam(id); }
  }, options);
  select('play').addEventListener('click', play, options);
  select('inspect').addEventListener('click', inspect, options);
  select('sound').addEventListener('click', async () => {
    try {
      const enabled = await sound.toggle();
      select('sound').textContent = TEXT[enabled ? 'soundOn' : 'soundOff'];
      select('sound').setAttribute('aria-pressed', enabled);
    } catch { notice('soundError'); }
  }, options);
  document.addEventListener('visibilitychange', () => { if (document.hidden && state.playing) pause(); }, options);
  motion.addEventListener('change', () => { if (motion.matches) { state.time = program.duration; pause('reduced'); } else { status('ready'); draw(); } }, options);
  root.addEventListener('keydown', event => {
    if (event.key === 'Escape' && state.inspection) inspect();
    if (!state.inspection || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault(); rotate(event.key === 'ArrowLeft' ? TUNING.keyboardLeftStep : TUNING.keyboardRightStep);
  }, options);
  const viewport = select('viewport');
  viewport.addEventListener('pointerdown', event => {
    if (!state.inspection) return;
    state.pointer = event.clientX; viewport.setPointerCapture(event.pointerId);
  }, options);
  viewport.addEventListener('pointermove', event => {
    if (state.pointer === null) return;
    rotate((event.clientX - state.pointer) * OPENING.dragSensitivity); state.pointer = event.clientX;
  }, options);
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(name => viewport.addEventListener(name, () => { state.pointer = null; }, options));
}

select('seek').max = program.duration; select('seek').value = program.duration;
select('seek').setAttribute('aria-label', TEXT.seek);
root.querySelector('[role=progressbar]').setAttribute('aria-valuemax', program.duration);
const resize = new ResizeObserver(() => { if (!state.disposed && state.room) draw(); });
resize.observe(root); wire();
window.addEventListener('pagehide', () => {
  state.disposed = true; cancelAnimationFrame(state.frame); resize.disconnect();
  listeners.abort(); sound.dispose(); state.room?.dispose(); discardPrepared(); waiverCard?.dispose();
}, {once: true});

let failure = 'editionError';
try {
  edition = await loadEdition();
  if (state.disposed) throw new Error('Disposed');
  report(edition);
  const draft = film ? checkDraft(edition.draft) : null;
  if (draft) receipt = makeReceipts(draft);
  // Chapter 2's card (trades-view.mjs): its avatars decode with the scene's warm-up, before Play (rule 49).
  const card = film ? makeTrades(root, checkTrades(edition.trades, edition.teams), edition.teams) : null;
  if (card) trades = card.update;
  if (film) {
    const response = await fetch(new URL('./waivers-receipts.json', import.meta.url), options);
    if (!response.ok) throw new Error('Waiver receipt unavailable: ' + response.status);
    waiverCard = makeWaivers(root, checkWaivers(await response.json()), edition.teams);
    waivers = waiverCard.update;
  }
  failure = 'webglError';
  const { createRoom } = await import('./scene.mjs');
  const baseReady = Promise.all([createRoom(select('viewport'), TEXT.canvas, fallback, edition.teams, draft), card?.ready])
    .then(([room]) => {
      if (state.disposed || initializationFailed) { room.dispose(); return room; }
      preparedRoom = room; root.dataset.baseReady = 'true'; return room;
    });
  const [room] = await Promise.all([baseReady, waiverCard?.ready]);
  if (state.disposed) discardPrepared();
  else {
    preparedRoom = null;
    state.room = room; root.dataset.phase = room.modelFallback ? 'study' : 'ready';
    root.setAttribute('aria-busy', 'false'); select('controls').inert = false;
    review = film ? mountReview(root, {seek: seekTo, jump: time => sound.seek(time), toggle: play, duration: program.duration}, listeners.signal) : null;
    select('inspect').disabled = false;
    status(motion.matches ? 'reduced' : 'ready');
    if (room.modelFallback) notice('modelError');
    draw();
  }
} catch (error) {
  initializationFailed = true; discardPrepared();
  console.error(error); fallback(failure);
}
