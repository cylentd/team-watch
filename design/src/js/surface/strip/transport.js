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

function stripMount(host, data, at){
  host.classList.add("stpanel");
  host.innerHTML = stripPanelHTML();
  const ctl = {data, ui: stUi(host), faces: data.faces || {},
               home: data.home.abbr, away: data.away.abbr, raf: 0, playing: false};
  ctl.ui.drives.innerHTML = data.drives.map((d, k) =>
    `<button type="button" role="tab" aria-selected="false">${esc(d.team || "")} · ${esc(stDriveTag(d))}</button>`).join("");
  stWire(ctl);
  stShowDrive(ctl, stClamp(at == null ? data.current : at, 0, data.drives.length - 1));
  return ctl;
}

/* A drive chip says how the drive ended, because that is what a reader is looking for when they
   scan a drive chart. ESPN's own result text is already short ("TD", "Punt", "Field Goal"). */
function stDriveTag(d){
  const r = String(d.result || "").trim();
  return r.length > 12 ? r.slice(0, 11) + "…" : (r || t("strip.drive.untitled"));
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

/* A scrub or a Prev/Next: slide from where we are to where we were asked for. An integer target
   reached from below also plays the beat after that play, so Next lands on a finished picture. */
function stGlide(ctl, target, ms){
  stStop(ctl);
  const from = +ctl.ui.slider.value, t0 = performance.now();
  if (ST_REDUCED || from === target) return stRender(ctl, target);
  const beat = target > from && Number.isInteger(target) && target > 0 ? ST_BEAT : 0;
  const tick = now => {
    const u = Math.min((now - t0) / ms, 1);
    const b = beat ? stClamp((now - t0 - ms) / beat, 0, 1) : 1;
    stRender(ctl, stLerp(from, target, stEase(u)), b);
    if (u < 1 || b < 1) ctl.raf = requestAnimationFrame(tick);
  };
  ctl.raf = requestAnimationFrame(tick);
}

/* Play on from wherever the scrubber sits -- at the end of the drive, from the top. Resuming
   mid-play re-enters the same timing curve (stEaseInv) rather than restarting it, so the figure
   carries on from where he is instead of jumping back. */
function stPlay(ctl){
  stStop(ctl);
  stSetPlaying(ctl, true);
  const g = ctl.pose.geom, ends = [];
  /* a play with a moment rests long enough for it to land, hold and fade */
  const rest = p => p.td ? 1800 : p.k === "int" ? 1600 : stMoment(p, ctl.drive.dir) ? 1600
    : p.tk || p.fum ? 900 : p.k === "inc" ? 600 : 0;
  ctl.plays.reduce((acc, p) =>
    (ends.push(acc += stMove(p, g) + (stEventful(p) || stMoment(p, ctl.drive.dir) ? ST_BEAT : 240) + rest(p)), acc), 0);
  let tm = +ctl.ui.slider.value;
  if (tm >= ctl.n) tm = 0;
  const i0 = Math.floor(tm), f0 = tm - i0, from = i0 ? ends[i0 - 1] : 0;
  const elapsed = from + (f0 ? stMove(ctl.plays[i0], g) * stEaseInv(f0) : 0);
  const t0 = performance.now() - elapsed;
  if (!elapsed) ctl.fired = -1;
  const tick = now => {
    const el = now - t0, i = ends.findIndex(end => el < end);
    if (i < 0){ stRender(ctl, ctl.n); return stSetPlaying(ctl, false); }
    const local = el - (i ? ends[i - 1] : 0), ms = stMove(ctl.plays[i], g);
    stRender(ctl, i + (ST_REDUCED ? 1 : stEase(Math.min(local / ms, 1))),
             ST_REDUCED ? 1 : stClamp((local - ms) / ST_BEAT, 0, 1));
    ctl.raf = requestAnimationFrame(tick);
  };
  stRender(ctl, tm);
  ctl.raf = requestAnimationFrame(tick);
}

/* Anything that changes the layout invalidates the arc cache and the caption floor: both were
   measured against the old one. Re-measuring is cheaper than being wrong by a phone's worth. */
function stAgain(ctl){
  if (!ctl.pose) return;
  ctl.pose.bump();
  stFitCap(ctl);
  stRender(ctl, +ctl.ui.slider.value);
}

function stWire(ctl){
  const ui = ctl.ui, v = () => +ui.slider.value;
  ui.slider.addEventListener("input", () => { stStop(ctl); stRender(ctl, v()); });
  ui.slider.addEventListener("change", () => stGlide(ctl, Math.round(v()), 250));
  ui.host.querySelector(".stprev").addEventListener("click", () => stGlide(ctl, Math.max(0, Math.ceil(v()) - 1), 700));
  ui.host.querySelector(".stnext").addEventListener("click", () =>
    stGlide(ctl, Math.min(ctl.n, Math.floor(v()) + 1), stMove(ctl.plays[Math.min(ctl.n - 1, Math.floor(v()))], ctl.pose.geom)));
  ui.play.addEventListener("click", () => ctl.playing ? stStop(ctl) : stPlay(ctl));
  ui.mode.addEventListener("click", () => {
    const m = ui.view.dataset.phone === "pan" ? "fit" : "pan";
    ui.view.dataset.phone = m;
    ui.mode.textContent = m === "pan" ? t("strip.view.pan") : t("strip.view.fit");
    stAgain(ctl);
  });
  ui.drives.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (b) stShowDrive(ctl, [...ui.drives.children].indexOf(b));
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
