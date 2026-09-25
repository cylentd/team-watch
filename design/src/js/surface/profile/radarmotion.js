/* The radar's motion, 2026-09-25. In JS and not CSS because what moves is geometry: a polygon's
   `points` and each vertex's position are attributes no transition can tween. The springs in
   base/tokens.css are the same physics sampled for CSS; this is the live version of it.

   Everything here answers either the chart arriving or a hand on it, and nothing loops. Under
   prefers-reduced-motion every call lands on its end state in the same frame. */

/* A damped spring from `from` to `to`, calling onFrame with each value. Stiffness 300 and damping
   20 (ratio .58) overshoots by about 11%: enough that a vertex visibly lands, not so much that a
   rank looks like it wobbles. Returns a cancel. */
function spring(from, to, onFrame, o = {}){
  const k = o.k || 300, c = o.c || 20, done = o.done || (() => {});
  if (REDUCED()){ onFrame(to); done(); return () => {}; }
  let x = from, v = 0, last = null, start = null, id = 0;
  const tick = now => {
    if (start === null) start = now + (o.delay || 0);
    if (now < start){ id = requestAnimationFrame(tick); return; }
    const dt = last === null ? 1 / 60 : Math.min(.032, (now - last) / 1000);
    last = now;
    v += (-k * (x - to) - c * v) * dt;
    x += v * dt;
    if (Math.abs(x - to) < 5e-4 && Math.abs(v) < 5e-3){ onFrame(to); done(); return; }
    onFrame(x);
    id = requestAnimationFrame(tick);
  };
  onFrame(from);
  id = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(id);
}

/* The chart as numbers: the hub, and each drawn vertex as an offset from it. Read back from the
   rendered SVG, so sheet.js stays the one place the geometry is decided. */
function radarGeo(el){
  const svg = el.querySelector(".pf-radar");
  const dots = svg ? [...svg.querySelectorAll(".pf-radar-dot")] : [];
  if (!dots.length) return null;
  const cx = +svg.dataset.cx, cy = +svg.dataset.cy, R = +svg.dataset.r;
  const end = dots.map(d => [+d.getAttribute("cx") - cx, +d.getAttribute("cy") - cy]);
  return {el, svg, cx, cy, R, dots, end, f: end.map(() => 1),
    shape: svg.querySelector(".pf-radar-shape"), ghost: svg.querySelector(".pf-radar-ghost"),
    mark: svg.querySelector(".pf-radar-mark"), ping: svg.querySelector(".pf-radar-ping")};
}

const radarPts = pts => pts.map(p => p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");

/* Draw every vertex at its fraction `g.f[i]` of the way out, and the shape and marker with it. */
function radarDraw(g){
  const pts = g.end.map(([dx, dy], i) => [g.cx + dx * g.f[i], g.cy + dy * g.f[i]]);
  pts.forEach(([x, y], i) => {
    g.dots[i].setAttribute("cx", x.toFixed(1));
    g.dots[i].setAttribute("cy", y.toFixed(1));
  });
  if (g.shape) g.shape.setAttribute("points", radarPts(pts));
  const on = g.dots.findIndex(d => d.classList.contains("on"));
  if (on < 0) return;
  [g.mark, g.ping].forEach(c => {
    if (!c) return;
    c.setAttribute("cx", pts[on][0].toFixed(1));
    c.setAttribute("cy", pts[on][1].toFixed(1));
  });
}

/* Each vertex springs out along its own axis, one after another, instead of the whole shape
   scaling up at once: the radius is the rank, so each stat earns its own reach. A vertex that
   passes its elite arc on the way out lights the arc as it crosses -- "elite on this stat" as a
   moment the reader sees, not two numbers to compare. The CSS scale-in stands down (.js-grow). */
function radarGrow(g){
  g.el.classList.add("js-grow");
  const bars = {};
  g.svg.querySelectorAll(".pf-radar-bar").forEach(b => { bars[b.dataset.col] = b; });
  g.dots.forEach((d, i) => {
    const bar = bars[d.dataset.col], len = Math.hypot(g.end[i][0], g.end[i][1]);
    const r = bar ? +bar.dataset.r : Infinity;
    let lit = len < r || REDUCED();                      // never crosses, or no motion: nothing to light
    spring(0, 1, x => {
      g.f[i] = x;
      radarDraw(g);
      if (!lit && x * len >= r){ lit = true; bar.classList.add("hit"); }
    }, {delay: 160 + i * 70});
  });
}

/* The card's number counts up to itself, so a swap reads as a new reading rather than a label
   change. The text is only ever the formatted value with its unit around it; the final frame
   writes the original string back, so nothing rounds differently from usageFmt. */
function countUp(b, delay = 0){
  if (!b || REDUCED()) return;
  const txt = b.textContent, m = txt.match(/-?\d+(\.\d+)?/);
  if (!m) return;
  const end = parseFloat(m[0]), dp = m[1] ? m[1].length - 1 : 0;
  const pre = txt.slice(0, m.index), post = txt.slice(m.index + m[0].length), ms = 420;
  let t0 = null;
  const tick = now => {
    if (t0 === null) t0 = now + delay;
    const u = Math.max(0, Math.min(1, (now - t0) / ms)), e = 1 - Math.pow(1 - u, 3);
    b.textContent = u < 1 ? pre + (end * e).toFixed(dp) + post : txt;
    if (u < 1) requestAnimationFrame(tick);
  };
  b.textContent = pre + (0).toFixed(dp) + post;
  requestAnimationFrame(tick);
}
