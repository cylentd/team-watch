/* A hand on the dial, 2026-09-25. The six labels were the only way to pick a stat, and on a phone
   they are 30px targets on the rim of a chart that fills the width. Now the whole dial answers:

   - tap: picks the axis nearest the finger's angle;
   - drag: sweeps round the dial, picking each axis as the finger passes it;
   - hold: draws the compare ghost until the finger lifts.

   The target is .pf-radar-hit, an HTML circle over the disc (sheet.js says why it is HTML). */

/* How many starters a 12-team league rolls at each position, flex spread by usual use: the
   "starter" the ghost stands for is whoever is inside that line. */
const RADAR_STARTERS = {QB: 12, RB: 24, WR: 36, TE: 12};

/* The ghost: on every axis, where the median starter at his position sits. Starters are the top
   N on the position's first axis, which the producer orders volume-first (Wtd Opp, WOPR,
   dropbacks), so "starter" means "gets starter's work", not "was good on this axis" -- ranking
   by each axis in turn would put the median at the same radius on all six and draw a circle. */
function radarStarters(s){
  const lead = s.axes[0].id, n = RADAR_STARTERS[s.pos] || 24;
  const rows = USAGE.sheet.rows.filter(r => r.pos === s.pos && r.v[lead] !== null && r.v[lead] !== undefined)
    .sort((a, b) => b.v[lead] - a.v[lead]).slice(0, n);
  const med = xs => { const v = xs.slice().sort((a, b) => a - b), h = v.length >> 1; return v.length % 2 ? v[h] : (v[h - 1] + v[h]) / 2; };
  const by = {};
  s.axes.forEach(a => {
    const xs = rows.map(r => r.v[a.id]).filter(x => x !== null && x !== undefined);
    by[a.id] = xs.length ? valueRadius(s.pos, a.id, med(xs)) : null;
  });
  return {n, by};
}

/* Ghost drawn at fraction u between his shape (0) and the starters' (1): it grows out of him, so
   the eye follows each vertex to where a starter would be instead of comparing two still shapes. */
function radarGhost(g, st, u){
  const pts = g.end.map(([dx, dy], i) => {
    const len = Math.hypot(dx, dy) || 1, to = st.by[g.dots[i].dataset.col];
    const k = to === null || to === undefined ? 1 : 1 + ((to * g.R) / len - 1) * u;
    return [g.cx + dx * k, g.cy + dy * k];
  });
  g.ghost.setAttribute("points", radarPts(pts));
}

function wireRadarCompare(el, s, g){
  const chip = el.querySelector(".pf-radar-cmp");
  if (!g.ghost || !chip) return () => {};
  const st = radarStarters(s);
  let on = false, stop = () => {}, u = 0;
  const set = want => {
    if (want === on) return;
    on = want;
    el.classList.toggle("cmp", on);
    chip.textContent = on ? t("profile.sheet.compareOn", {n: st.n, pos: s.pos}) : t("profile.sheet.compare", {pos: s.pos});
    stop();
    stop = spring(u, on ? 1 : 0, x => { u = x; radarGhost(g, st, x); }, {k: 220, c: 22});
  };
  /* The chip toggles on a tap and holds on a press: a quick tap leaves it on, which is what a tap
     on a button means, and a press released after 300ms lets go, which is what holding means. */
  let downAt = 0;
  chip.addEventListener("pointerdown", e => { e.preventDefault(); downAt = e.timeStamp; if (!on) set(true); else downAt = -1; });
  chip.addEventListener("pointerup", e => { if (downAt < 0) set(false); else if (e.timeStamp - downAt > 300) set(false); });
  chip.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); set(!on); } });
  return set;
}

function wireRadarTouch(el, s, g, pick){
  const hit = el.querySelector(".pf-radar-hit");
  const labels = [...el.querySelectorAll(".pf-radar-l")];
  const compare = wireRadarCompare(el, s, g);
  if (!hit || labels.length !== s.axes.length) return;
  const n = s.axes.length;
  // The axis whose angle is nearest the pointer's, measured from the dial's own centre.
  const nearest = e => {
    const r = hit.getBoundingClientRect();
    const a = Math.atan2(e.clientY - r.top - r.height / 2, e.clientX - r.left - r.width / 2) + Math.PI / 2;
    return ((Math.round(a / (2 * Math.PI / n)) % n) + n) % n;
  };
  const go = i => {
    if (labels[i].classList.contains("on")) return;
    pick(labels[i]);
    if (navigator.vibrate) navigator.vibrate(4);
  };
  let down = null;
  hit.addEventListener("pointerdown", e => {
    if (e.button > 0) return;
    hit.setPointerCapture(e.pointerId);
    down = {x: e.clientX, y: e.clientY, scrub: false, held: false};
    down.timer = setTimeout(() => { if (down && !down.scrub){ down.held = true; compare(true); } }, 420);
  });
  hit.addEventListener("pointermove", e => {
    if (!down || down.held) return;
    if (!down.scrub && Math.hypot(e.clientX - down.x, e.clientY - down.y) > 8){
      down.scrub = true;
      clearTimeout(down.timer);
      el.classList.add("scrub");
    }
    if (down.scrub) go(nearest(e));
  });
  const end = e => {
    if (!down) return;
    clearTimeout(down.timer);
    if (down.held) compare(false);
    else if (!down.scrub && e.type === "pointerup") go(nearest(e));
    el.classList.remove("scrub");
    down = null;
  };
  hit.addEventListener("pointerup", end);
  hit.addEventListener("pointercancel", end);
}
