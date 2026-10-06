/* The sphere in the profile head (2026-09-28, David: "a spinning 3D sphere hexagon next to the
   player's name; if the user taps it, it expands into the player profile"). His stat sheet as a
   solid: a glass sphere, and inside it a crystal whose equator is the radar.

   Each usage stat is a vertex on the equator, at the angle sheet.js gives its axis and a radius
   from his rank, first place touching the glass -- the same k radarHTML draws with. Two poles make
   it a solid, their height his mean reach, so a better player is a bigger crystal from every side.
   Seen from ORB_PITCH above the equator; from straight overhead the crystal IS the flat radar,
   which is what the tap's morph (orbsheet.js) turns it into.

   A canvas with its own projection, not CSS 3D: CSS 3D has no curves, no spheres and no lighting,
   and faking a sphere from slices cost the pack edge two thirds of its frame rate (2026-09-27).
   Colours come from the tokens through getComputedStyle; no colour is spelled here.

   Motion (STYLE.md rule 1, rewritten 2026-09-28 for this): it turns like a turntable, one turn per
   ORB_TURN_MS, easing out of and back into the radar's own orientation and resting there
   ORB_REST_MS, so the familiar shape comes round every turn. Only while the head is on screen, the
   tab is visible and the sheet is shut; under reduced motion it draws once, at rest. */
const ORB_TAU = 2 * Math.PI;
const ORB_PITCH = 32 * Math.PI / 180, ORB_TOP = Math.PI / 2;
const ORB_TURN_MS = 14000, ORB_REST_MS = 2000;
const ORB_STATE = new WeakMap();   // badge -> {yaw}: where the turn is, so the morph starts there

/* The crystal's equator: [x, z, k] per measured axis, in sheet.js's axis order and angles. An axis
   with no rank is left out, as the flat shape leaves it out. */
function orbGeo(p){
  const s = sheetFor(p);
  if (!s) return null;
  const n = s.axes.length, verts = [];
  s.axes.forEach((a, i) => {
    const rk = sheetRank(s.pos, a.id, p.slug);
    if (!rk) return;
    const k = rk[1] > 1 ? Math.max(.04, 1 - (rk[0] - 1) / (rk[1] - 1)) : .04;
    const ang = -Math.PI / 2 + i * ORB_TAU / n;
    verts.push([k * Math.cos(ang), k * Math.sin(ang), k]);
  });
  return {s, verts, mean: verts.length ? verts.reduce((m, v) => m + v[2], 0) / verts.length : 0};
}

/* The token triples the drawing needs, read off an element whose class carries --tint-rgb. */
function orbColors(el){
  const cs = getComputedStyle(el);
  const trip = name => cs.getPropertyValue(name).trim().split(/\s+/).map(Number);
  return {tint: trip("--tint-rgb"), ink: trip("--ink-rgb"), core: trip("--void-rgb"), rim: trip("--line-2-rgb")};
}
const orbRgb = (c, a, s = 1) => `rgb(${Math.round(c[0] * s)} ${Math.round(c[1] * s)} ${Math.round(c[2] * s)} / ${a})`;

/* One frame. `yaw` turns the sphere about its axis, `pitch` is the camera's height above the
   equator (ORB_TOP is straight down), R the sphere's radius in CSS pixels. */
function orbDraw(cv, geo, col, yaw, pitch, R){
  const W = cv.clientWidth, dpr = window.devicePixelRatio || 1;
  if (!W) return;
  if (cv.width !== Math.round(W * dpr)){ cv.width = cv.height = Math.round(W * dpr); }
  const ctx = cv.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, W);
  const c = W / 2, sp = Math.sin(pitch), cp = Math.cos(pitch), sy = Math.sin(yaw), cy = Math.cos(yaw);
  // (x, up, z) -> screen x, screen y, and depth toward the eye
  const P = ([x, y, z]) => { const x1 = x * cy - z * sy, z1 = x * sy + z * cy;
    return {x: c + x1 * R, y: c + (z1 * sp - y * cp) * R, d: y * sp - z1 * cp}; };

  // The glass: dark at the core, lighter at the rim -- the flat radar's disc, in the round.
  const body = ctx.createRadialGradient(c, c, 0, c, c, R);
  body.addColorStop(0, orbRgb(col.core, .96)); body.addColorStop(1, orbRgb(col.rim, .92));
  ctx.beginPath(); ctx.arc(c, c, R, 0, ORB_TAU); ctx.fillStyle = body; ctx.fill();

  const rings = orbRings(P);
  orbStrokeRings(ctx, rings, col, false);
  if (geo.verts.length >= 3) orbCrystal(ctx, geo, col, P, R);
  geo.verts.forEach(v => { const q = P([v[0], 0, v[1]]);
    ctx.beginPath(); ctx.arc(q.x, q.y, Math.max(1.4, R / 28), 0, ORB_TAU); ctx.fillStyle = orbRgb(col.tint, 1); ctx.fill(); });
  orbStrokeRings(ctx, rings, col, true);

  ctx.beginPath(); ctx.arc(c, c, R, 0, ORB_TAU);
  ctx.strokeStyle = orbRgb(col.ink, .32); ctx.lineWidth = 1; ctx.stroke();
  // A glint high on the left: what makes a disc read as glass. It fades as the camera tops out,
  // so the flat chart the morph lands on carries no highlight across it.
  const gx = c - R * .38, gy = c - R * .42, glint = ctx.createRadialGradient(gx, gy, 0, gx, gy, R * .45);
  glint.addColorStop(0, orbRgb(col.ink, .2 * cp + .04)); glint.addColorStop(1, orbRgb(col.ink, 0));
  ctx.beginPath(); ctx.arc(c, c, R, 0, ORB_TAU); ctx.fillStyle = glint; ctx.fill();
}

/* The wireframe: the equator and its two rank rings (a third and two thirds of the way out, where
   the flat chart's rings sit), two latitudes, and three meridians that turn with the sphere and
   are what makes the turn visible. Sampled once per frame. */
function orbRings(P){
  const circle = f => Array.from({length: 73}, (_, i) => P(f(i / 72 * ORB_TAU)));
  const rings = [{pts: circle(t => [Math.cos(t), 0, Math.sin(t)]), w: 1.1}];
  [.55, -.55].forEach(y => { const q = Math.sqrt(1 - y * y);
    rings.push({pts: circle(t => [q * Math.cos(t), y, q * Math.sin(t)]), w: .8}); });
  [0, 60, 120].forEach(lon => { const l = lon * Math.PI / 180;
    rings.push({pts: circle(t => [Math.cos(t) * Math.cos(l), Math.sin(t), Math.cos(t) * Math.sin(l)]), w: .8}); });
  [1 / 3, 2 / 3].forEach(q => rings.push({pts: circle(t => [q * Math.cos(t), 0, q * Math.sin(t)]), w: .7, dash: true}));
  return rings;
}

/* Back halves faint, drawn before the crystal; front halves brighter, drawn after it. */
function orbStrokeRings(ctx, rings, col, front){
  rings.forEach(rg => {
    ctx.lineWidth = rg.w; ctx.setLineDash(rg.dash ? [2, 3] : []);
    ctx.strokeStyle = orbRgb(col.ink, front ? .24 : .08);
    ctx.beginPath();
    for (let i = 1; i < rg.pts.length; i++){
      const a = rg.pts[i - 1], z = rg.pts[i];
      if ((a.d + z.d > 0) === front){ ctx.moveTo(a.x, a.y); ctx.lineTo(z.x, z.y); }
    }
    ctx.stroke();
  });
  ctx.setLineDash([]);
}

/* Twelve faces (or two per measured axis), painted far to near, each lit by one light from the
   upper left, and translucent so the back of the solid shows through its front. Then the equator
   outlined in the tint at full strength: the radar's own edge, always inside the solid. */
function orbCrystal(ctx, geo, col, P, R){
  const V = geo.verts.map(v => [v[0], 0, v[1]]), h = .2 + .5 * geo.mean;
  const N = [0, h, 0], S = [0, -h, 0], L = [-.45, -.6, .66], faces = [];
  V.forEach((v, j) => { const w = V[(j + 1) % V.length]; faces.push([N, v, w], [S, w, v]); });
  faces.map(f => f.map(P)).map(q => {
    const u = [q[1].x - q[0].x, q[1].y - q[0].y, (q[1].d - q[0].d) * R];
    const v = [q[2].x - q[0].x, q[2].y - q[0].y, (q[2].d - q[0].d) * R];
    const n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    const lit = Math.abs(n[0] * L[0] + n[1] * L[1] + n[2] * L[2]) / (Math.hypot(...n) || 1);
    return {q, d: (q[0].d + q[1].d + q[2].d) / 3, s: .38 + .62 * lit};
  }).sort((a, z) => a.d - z.d).forEach(f => {
    ctx.beginPath(); ctx.moveTo(f.q[0].x, f.q[0].y); ctx.lineTo(f.q[1].x, f.q[1].y); ctx.lineTo(f.q[2].x, f.q[2].y); ctx.closePath();
    ctx.fillStyle = orbRgb(col.tint, .6, f.s); ctx.fill();
    ctx.strokeStyle = orbRgb(col.tint, .35); ctx.lineWidth = .6; ctx.stroke();
  });
  ctx.beginPath(); V.map(P).forEach((q, j) => j ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y)); ctx.closePath();
  ctx.strokeStyle = orbRgb(col.tint, 1); ctx.lineWidth = Math.max(1.2, R / 40); ctx.stroke();
}

/* The turn's angle after `ms` of running time. u - sin(2πu)/2π leaves and arrives at zero speed,
   so the turn eases out of the rest and back into it; then it holds at 0, the radar's orientation. */
function orbYaw(ms){
  const ph = ms % (ORB_TURN_MS + ORB_REST_MS);
  if (ph >= ORB_TURN_MS) return 0;
  const u = ph / ORB_TURN_MS;
  return ORB_TAU * (u - Math.sin(ORB_TAU * u) / ORB_TAU);
}

function orbBadgeHTML(p){
  const s = sheetFor(p);
  if (!s) return "";
  const axis = s.axes.find(a => a.id === sheetDefaultAxis(s)) || s.axes[0];
  const rk = sheetRank(s.pos, axis.id, p.slug);
  return `<button type="button" class="pf-orb pos-${esc(String(s.pos).toLowerCase())}" data-testid="profile-orb" aria-label="${esc(t("profile.orb.open", {n: p.n}))}">
    <canvas aria-hidden="true"></canvas>
    ${rk ? `<span class="pf-orb-l"><b>${rankMark(rk)}</b> ${esc(axisName(axis))}</span>` : ""}</button>`;
}

/* Draws the badge and runs its turn until the badge leaves the page. Running time only advances
   while it is allowed to move, so a pause resumes the turn where it stopped rather than jumping. */
function wireOrb(btn, p){
  const cv = btn && btn.querySelector("canvas"), geo = cv && orbGeo(p);
  if (!geo) return;
  const col = orbColors(btn), st = {yaw: 0};
  ORB_STATE.set(btn, st);
  const draw = () => orbDraw(cv, geo, col, st.yaw, ORB_PITCH, cv.clientWidth / 2 * .92);
  draw();
  if (REDUCED()) return;
  // Turns from the first frame (2026-09-30: a still shape at an angle told the reader nothing, and the
  // 2 s it held first read as a stall); the rest comes after the first turn.
  let seen = true, run = 0, last = null;
  const io = new IntersectionObserver(e => { seen = e[e.length - 1].isIntersecting; });
  io.observe(btn);
  const frame = now => {
    if (!btn.isConnected){ io.disconnect(); return; }
    requestAnimationFrame(frame);
    const go = seen && !document.hidden && !btn.dataset.open && btn.closest(".modal.on");
    const dt = last === null ? 0 : Math.min(50, now - last);
    last = now;
    if (!go) return;
    run += dt;
    const y = orbYaw(run);
    if (y === st.yaw) return;
    st.yaw = y; draw();
  };
  requestAnimationFrame(frame);
}
