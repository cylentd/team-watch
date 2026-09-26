/* ------------------------------------------------------------------
   STRIP TRANSPORT — mounting one game, and the controls that move through it.

   Play does not step from play to play at a fixed rate: a 3-yard plunge and an 80-yard bomb take
   different amounts of time to happen, and what follows a play differs too -- a tackle carries on,
   an incompletion bounces, a touchdown is worth resting on. So each play gets a glide length from
   its own distance, a beat after it, and a rest long enough for its moment to land and fade.
------------------------------------------------------------------ */

/* how long play p's glide runs: 850ms of setup plus 22ms a yard, floored so a stuff still reads
   and capped so a bomb does not outstay the moment waiting behind it */
const stMove = (p, g) => stClamp(850 + Math.abs(g.endOf(p) - p.from) * 22, 1000, 2600);
const stEventful = p => p.tk || p.fum || p.td || p.k === "inc" || p.k === "int";
const ST_BEAT = 900;
/* the pause before a play that does not follow the last one on the field: a new possession, or
   the next of a player's plays with other plays skipped in between */
const ST_LEAD = 500;

/* `at` is the drive to open at, shown finished; left out, a finished game opens at the kickoff
   and a live one at its latest play. `who` is the player the reader came from, spelled the way
   the play texts spell him ("M. Stafford"). */
function stripMount(host, data, at, who){
  host.classList.add("stpanel");
  host.innerHTML = stripPanelHTML();
  const ctl = {data, ui: stUi(host), faces: data.faces || {}, sel: {q: 0, me: false, who: who || null},
               home: data.home.abbr, away: data.away.abbr, raf: 0, playing: false, T: 0};
  ctl.ui.filt.innerHTML = stFiltHTML(ctl);
  stWire(ctl);
  stSelect(ctl, {});
  const open = at != null ? at : data.state === "post" ? null : data.current;
  if (open != null){
    const d = stClamp(open, 0, data.drives.length - 1);
    stSeek(ctl, ctl.reel.findIndex(s => s.d === d) + data.drives[d].plays.length);
  }
  stAgain(ctl);
  return ctl;
}

function stStop(ctl){
  cancelAnimationFrame(ctl.raf);
  stSetPlaying(ctl, false);
}

function stSetPlaying(ctl, on){
  ctl.playing = on;
  const label = on ? t("strip.control.pause") : t("strip.control.play");
  ctl.ui.play.innerHTML = (on ? ST_PAUSE_ICON : ST_PLAY_ICON) + `<span class="stw">${label}</span>`;
  ctl.ui.play.setAttribute("aria-label", label);
  ctl.ui.play.setAttribute("aria-pressed", String(on));
}

/* On a phone in Pan the field is wider than the view, so every paint keeps the ball in frame.
   A drag on the field itself never paints, so the reader is never fought for the scroll. */
function stKeepInView(ctl, x){
  const view = ctl.ui.view;
  if (view.scrollWidth <= view.clientWidth) return;
  const tf = ctl.turf.getBoundingClientRect(), v = view.getBoundingClientRect();
  /* scrollLeft is in the element's own pixels; the rects above are in screen pixels, which a
     transformed ancestor (the dialog's open animation) scales. Same correction as stPlace. */
  const k = v.width && view.clientWidth ? v.width / view.clientWidth : 1;
  view.scrollLeft += (tf.left - v.left + x / 100 * tf.width - v.width / 2) / k;
}

/* On a wide screen the field fills the column. Its geometry is pixel-built (ST_FIELD), so it is
   laid out narrower and scaled up whole -- figures, arcs and yard numbers together, a camera
   moving in rather than a field stretched under sprites of the old size. How far: until the
   column fills the dialog's height, and never below MIN_W of layout width, where 120 yards
   start to crowd. stPlace already corrects for a scaled ancestor. */
const ST_WIDE = "(min-width: 960px)", ST_ZOOM = {MIN_W: 420, MAX: 2.2};
function stScaleField(ctl){
  const {host, box, main, filt} = ctl.ui;
  box.classList.remove("zoomed");
  if (!matchMedia(ST_WIDE).matches) return;
  const W = box.clientWidth, H = box.offsetHeight, cs = getComputedStyle(host);
  if (!W || !H) return;
  const inner = host.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  const room = inner - filt.offsetHeight - parseFloat(cs.rowGap || 0) - (main.offsetHeight - H);
  const s = stClamp(Math.min(room / H, W / ST_ZOOM.MIN_W), 1, ST_ZOOM.MAX);
  if (s < 1.05) return;
  box.style.setProperty("--stz", s.toFixed(3));
  box.style.setProperty("--sth", H + "px");
  box.classList.add("zoomed");
}

/* A scrub or a Prev/Next: slide from where we are to where we were asked for. An integer target
   reached from below also plays the beat after that play, so Next lands on a finished picture. */
function stGlide(ctl, target, ms){
  stStop(ctl);
  const from = ctl.T, t0 = performance.now();
  if (ST_REDUCED || from === target) return stSeek(ctl, target);
  const beat = target > from && Number.isInteger(target) && target > 0 ? ST_BEAT : 0;
  const tick = now => {
    const u = Math.min((now - t0) / ms, 1);
    const b = beat ? stClamp((now - t0 - ms) / beat, 0, 1) : 1;
    stSeek(ctl, stLerp(from, target, stEase(u)), b);
    if (u < 1 || b < 1) ctl.raf = requestAnimationFrame(tick);
  };
  ctl.raf = requestAnimationFrame(tick);
}

/* how long reel play k glides for, in its own drive's geometry */
const stMoveAt = (ctl, k) => {
  const s = ctl.reel[k], dr = ctl.data.drives[s.d];
  return stMove(dr.plays[s.i], stGeom(dr.dir));
};

/* When each reel play starts and ends, in ms from the top of the reel. A play with a moment
   rests long enough for it to land, hold and fade. */
function stTimeline(ctl){
  let acc = 0;
  return ctl.reel.map((s, k) => {
    const dr = ctl.data.drives[s.d], p = dr.plays[s.i], m = stMoment(p, dr.dir), prev = ctl.reel[k - 1];
    const rest = p.td ? 1800 : p.k === "int" ? 1600 : m ? 1600 : p.tk || p.fum ? 900 : p.k === "inc" ? 600 : 0;
    const start = acc + (prev && (prev.d !== s.d || prev.i !== s.i - 1) ? ST_LEAD : 0), move = stMoveAt(ctl, k);
    acc = start + move + (stEventful(p) || m ? ST_BEAT : 240) + rest;
    return {start, move, end: acc};
  });
}

/* Play on from wherever the scrubber sits -- at the end of the reel, from the top. Resuming
   mid-play re-enters the same timing curve (stEaseInv) rather than restarting it, so the figure
   carries on from where he is instead of jumping back. */
function stPlay(ctl){
  stStop(ctl);
  stSetPlaying(ctl, true);
  const tl = stTimeline(ctl), R = ctl.reel.length;
  let T = ctl.T;
  if (T >= R) T = 0;
  const i0 = Math.floor(T), f0 = T - i0;
  const elapsed = f0 ? tl[i0].start + tl[i0].move * stEaseInv(f0) : i0 ? tl[i0 - 1].end : 0;
  const t0 = performance.now() - elapsed;
  if (!elapsed) ctl.fired = -1;
  const tick = now => {
    const el = now - t0, k = tl.findIndex(x => el < x.end);
    if (k < 0){ stSeek(ctl, R); return stSetPlaying(ctl, false); }
    const local = el - tl[k].start, ms = tl[k].move;
    if (local < 0) stSeek(ctl, k);
    else stSeek(ctl, k + (ST_REDUCED ? 1 : stEase(Math.min(local / ms, 1))),
                ST_REDUCED ? 1 : stClamp((local - ms) / ST_BEAT, 0, 1));
    ctl.raf = requestAnimationFrame(tick);
  };
  stSeek(ctl, T);
  ctl.raf = requestAnimationFrame(tick);
}

/* Anything that changes the layout invalidates the arc cache and the caption floor: both were
   measured against the old one. Re-measuring is cheaper than being wrong by a phone's worth. */
function stAgain(ctl){
  if (!ctl.pose) return;
  stScaleField(ctl);
  ctl.pose.bump();
  stFitCap(ctl);
  stSeek(ctl, ctl.T);
}

function stWire(ctl){
  const ui = ctl.ui, v = () => +ui.slider.value;
  ui.slider.addEventListener("input", () => { stStop(ctl); stSeek(ctl, v()); });
  ui.slider.addEventListener("change", () => stGlide(ctl, Math.round(v()), 250));
  ui.host.querySelector(".stprev").addEventListener("click", () => stGlide(ctl, Math.max(0, Math.ceil(ctl.T) - 1), 700));
  ui.host.querySelector(".stnext").addEventListener("click", () => {
    const R = ctl.reel.length, k = Math.min(R - 1, Math.floor(ctl.T));
    stGlide(ctl, Math.min(R, Math.floor(ctl.T) + 1), stMoveAt(ctl, k));
  });
  ui.play.addEventListener("click", () => ctl.playing ? stStop(ctl) : stPlay(ctl));
  ui.mode.addEventListener("click", () => {
    const m = ui.view.dataset.phone === "pan" ? "fit" : "pan";
    ui.view.dataset.phone = m;
    ui.mode.textContent = m === "pan" ? t("strip.view.pan") : t("strip.view.fit");
    stAgain(ctl);
  });
  ui.filt.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b || b.disabled) return;
    if (b.classList.contains("stme")) stSelect(ctl, {me: !ctl.sel.me});
    else stSelect(ctl, {q: +b.dataset.q});
  });
  /* a row plays its own play: from the moment before the snap to the beat after it */
  ui.list.addEventListener("click", e => {
    const b = e.target.closest(".strow");
    if (!b) return;
    const k = +b.dataset.k;
    stStop(ctl);
    stSeek(ctl, k);
    stGlide(ctl, k + 1, stMoveAt(ctl, k));
  });
  /* the chevrons march only while the field is on screen; an animation nobody sees is battery */
  new IntersectionObserver(([e]) => ui.stage.classList.toggle("offscreen", !e.isIntersecting)).observe(ui.stage);
  ST_MOUNTED.add(ctl);
}

/* Every mounted strip, so one resize listener serves them all and a torn-down host drops out. */
const ST_MOUNTED = new Set();
addEventListener("resize", () => ST_MOUNTED.forEach(ctl => {
  if (ctl.ui.host.isConnected) stAgain(ctl); else { stStop(ctl); ST_MOUNTED.delete(ctl); }
}));
if (document.fonts && document.fonts.ready){
  document.fonts.ready.then(() => ST_MOUNTED.forEach(ctl => { if (ctl.ui.host.isConnected) stAgain(ctl); }));
}
