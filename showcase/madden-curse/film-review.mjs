import { filmPlan } from './film.mjs';
import { FILM_COPY } from './film-copy.mjs';

/* The review menu on ?film (David, 2026-11-04): the opening and every beat with its start time, a Loop
   toggle for the beat on screen, and a scrubber naming it. The list comes from filmPlan, which reads
   timing.json, so a beat added or re-timed there shows here on the next reload. It carries the class
   `controls`, which the exporter and the still captures hide, so it is never in a cut. */
const BACK_GRACE = .3;   // seconds into a stop within which "previous" goes to the stop before (as media players do)
const SCRUB_STEP = 1 / 30;   // one frame of the 30 fps export
export const CLOSE_AFTER_MS = 3000;   // David 2026-11-04: the open list closes 3 s after the mouse leaves it
const COPY = FILM_COPY.review;

export function reviewStops() {
  const {chapterAt, beats} = filmPlan();
  return [{id: 'intro', at: 0, end: chapterAt, label: COPY.beats.intro},
    ...beats.map(beat => ({id: beat.id, at: beat.start, end: beat.start + beat.duration, label: COPY.beats[beat.id] ?? beat.id}))];
}

/* The stop playing at `time`. */
export const stopAt = (stops, time) => stops.findLast(stop => time >= stop.at) ?? stops[0];

/* Where J (direction -1) or K (+1) goes from `time`: the next stop's start, or back to this stop's start,
   or the one before it when `time` is within BACK_GRACE of this one's; clamped to the first and last. */
export function step(stops, time, direction) {
  if (direction > 0) return (stops.find(stop => stop.at > time) ?? stops.at(-1)).at;
  const index = stops.indexOf(stopAt(stops, time));
  return time - stops[index].at > BACK_GRACE ? stops[index].at : stops[Math.max(0, index - 1)].at;
}

/* With stop `index` looping, a time past its end wraps to its start; with no loop, time runs on. */
export function looped(stops, index, time) {
  if (index === null) return time;
  return time >= stops[index].end ? stops[index].at : time;
}

/* Whether the list is open after `event`: the tab or M toggles it; a jump, Esc or the mouse gone
   CLOSE_AFTER_MS closes it; anything else (dragging the scrubber) leaves it as it was. */
export function menuOpen(open, event) {
  if (event === 'toggle') return !open;
  return ['jump', 'escape', 'leave'].includes(event) ? false : open;
}

const clock = seconds => `${Math.floor(seconds / 60)}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;

/* Draws the menu into `root` and wires its keys. `seek(time)` jumps the film and pauses it, `jump(time)`
   moves it without pausing (the loop), `toggle()` plays or pauses. It starts as a one-line tab, the beat and
   the time (David 2026-11-04: the open list hid the scene); the tab or M opens the list. Returns the hooks app.mjs calls. */
export function mountReview(root, {seek, jump, toggle, duration}, signal) {
  const stops = reviewStops();
  const panel = document.createElement('nav');
  panel.className = 'controls film-review';
  panel.setAttribute('aria-label', COPY.label);
  panel.innerHTML = `<button type="button" class="film-review-head" aria-expanded="false" aria-controls="film-review-body"><span data-review-now></span><span data-review-time></span></button>
    <div class="film-review-body" id="film-review-body"><input type="range" min="0" step="${SCRUB_STEP}" data-review-scrub>
    <ol class="film-review-list"></ol>
    <button type="button" class="film-review-loop" aria-pressed="false" data-review-loop></button>
    <p class="film-review-keys"></p></div>`;
  const scrub = panel.querySelector('[data-review-scrub]'), loop = panel.querySelector('[data-review-loop]');
  const tab = panel.querySelector('.film-review-head');
  let open = false, leaving = null;
  const menu = event => {
    open = menuOpen(open, event); clearTimeout(leaving);
    panel.toggleAttribute('data-open', open); tab.setAttribute('aria-expanded', open);
  };
  tab.addEventListener('click', () => menu('toggle'), {signal});
  panel.addEventListener('mouseleave', () => { if (open) leaving = setTimeout(() => menu('leave'), CLOSE_AFTER_MS); }, {signal});
  panel.addEventListener('mouseenter', () => clearTimeout(leaving), {signal});
  signal.addEventListener('abort', () => clearTimeout(leaving));
  scrub.max = duration; scrub.setAttribute('aria-label', COPY.scrub);
  loop.textContent = COPY.loop; panel.querySelector('.film-review-keys').textContent = COPY.keys;
  const items = stops.map(stop => {
    const item = document.createElement('li'), button = document.createElement('button');
    button.type = 'button'; button.dataset.reviewStop = stop.id;
    button.innerHTML = '<span></span><span></span>';
    button.firstChild.textContent = stop.label; button.lastChild.textContent = clock(stop.at);
    button.addEventListener('click', () => { seek(stop.at); menu('jump'); }, {signal});
    item.append(button); panel.querySelector('ol').append(item);
    return button;
  });
  root.append(panel);
  let looping = null, now = 0;
  const setLoop = on => { looping = on ? stops.indexOf(stopAt(stops, now)) : null; loop.setAttribute('aria-pressed', on); };
  scrub.addEventListener('input', () => seek(Number(scrub.value)), {signal});
  loop.addEventListener('click', () => setLoop(looping === null), {signal});
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const key = event.key.toLowerCase();
    if (key === 'j' || key === 'k') { seek(step(stops, now, key === 'k' ? 1 : -1)); menu('jump'); }
    else if (key === 'l') setLoop(looping === null);
    else if (key === 'm') menu('toggle');
    else if (event.key === 'Escape' && open) menu('escape');
    else if (key === ' ' && event.target.type !== 'range') toggle();
    else return;
    event.preventDefault();
  }, {signal});
  return {
    // The time the film should be at after advancing to `time`: wraps inside a looping stop.
    wrap(time) { const wrapped = looped(stops, looping, time); if (wrapped !== time) jump(wrapped); return wrapped; },
    update(time) {
      now = time;
      const current = stopAt(stops, time);
      if (looping !== null && stops[looping] !== current) setLoop(true);   // a jump elsewhere loops the new stop
      panel.querySelector('[data-review-now]').textContent = current.label;
      panel.querySelector('[data-review-time]').textContent = clock(time);
      scrub.value = time;
      items.forEach(button => button.ariaCurrent = button.dataset.reviewStop === current.id ? 'step' : null);
    },
  };
}
