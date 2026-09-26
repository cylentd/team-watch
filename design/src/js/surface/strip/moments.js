/* ------------------------------------------------------------------
   STRIP MOMENTS — what makes a play land: the hit, the pile, the sack, the big play, the
   touchdown and the turnover, plus the team colours they are all drawn in. (2026-09-26; the
   playable storyboard they were chosen from: https://claude.ai/artifact/JCZqUep7G9vDqrCw6roh1z)

   Every effect fires on something the play data states -- a named tackler, a second one, a sack
   flag, a gain of 20, a touchdown, an interception or a lost fumble -- never on a guess. And each
   is a one-shot on transform and opacity, or a canvas that removes itself, so the replay's cost
   stays where the 2026-09-26 performance pass left it. Reduced motion gets none of them: the pose
   still ends where the play did, which is the information.

   Two kinds of thing live here. Time (stWarp): the transport asks how a play's wall-clock time
   maps onto the play -- a hit-stop, a slow-motion window, a freeze. Paint (stMoments): stRender
   hands over each frame's state, and one-shots fire the first time their condition holds.
------------------------------------------------------------------ */

/* The kits for this drive: the offense is the drive's club, the defence the other one. Set as
   variables on the stage, so figure.css colours every figure from its role. A game without kits
   (a live one from ESPN) keeps the house blue and grey. */
function stKits(ctl){
  const {home, away} = ctl.data, st = ctl.ui.stage.style;
  const off = ctl.drive.team === home.abbr ? home.kit : ctl.drive.team === away.abbr ? away.kit : null;
  const def = off === home.kit ? away.kit : home.kit;
  const set = (k, kit) => {
    if (kit){ st.setProperty(`--kit-${k}`, kit.jersey); st.setProperty(`--kit-${k}-trim`, kit.trim); }
    else { st.removeProperty(`--kit-${k}`); st.removeProperty(`--kit-${k}-trim`); }
    ctl.ui.stage.dataset[`${k}dark`] = kit && kit.dark ? "1" : "";
  };
  set("o", off && off.jersey ? off : null);
  set("d", off && def && def.jersey ? def : null);
}

/* a gain of 20 or more that the ball carrier made, the same line stMoment draws its banner at */
const stBig = (p, dir) => p.k !== "inc" && p.k !== "fg" && p.k !== "int" && (p.to - p.from) * dir >= 20;
/* where in the play the big play happens: the catch, or the break on a run */
const stBreak = (p, g) => p.k === "pass" ? g.flightOf(p) : .35;

/* How a play's wall-clock time maps onto the play's own clock, `local` ms in, ms out.
   A hit-stop holds the frame of contact; the slow-motion window runs the catch of a big play at
   30%; a turnover freezes on the ball before anyone runs the other way. `extra` is what they add
   to the play's length, for stTimeline. */
function stWarp(p, dir, move){
  const g = stGeom(dir), at = f => move * stEaseInv(stClamp(f, 0, 1)), ev = [];
  if (!ST_REDUCED){
    if (p.tk && p.k !== "int") ev.push({at: at(g.hitOf(p)), stop: p.sack ? 110 : 70});
    if (stBig(p, dir)){ const c = stBreak(p, g); ev.push({a: at(c - .1), b: at(c + .12), rate: .3}); }
    if (p.k === "int") ev.push({at: move, stop: 260});
    if (p.fum && p.fum.lost) ev.push({at: move + .55 * ST_BEAT, stop: 260});
  }
  ev.sort((u, v) => (u.at ?? u.a) - (v.at ?? v.a));
  const cost = e => e.stop != null ? e.stop : (e.b - e.a) / e.rate - (e.b - e.a);
  return {
    extra: ev.reduce((s, e) => s + cost(e), 0),
    map(w){
      let off = 0;
      for (const e of ev){
        const s = (e.at ?? e.a) + off;
        if (w < s) break;
        if (e.stop != null){ if (w < s + e.stop) return e.at; }
        else if (w < s + (e.b - e.a) / e.rate) return e.a + (w - s) * e.rate;
        off += cost(e);
      }
      return w - off;
    },
  };
}

/* ---- paint ---- */

const stXY = el => (el.style.translate || "0px 0px").split(" ").map(parseFloat);

/* a one-shot element in the flat overlay, at a sprite's spot, removed when its animation ends */
function stFx(ctl, cls, [x, y], frames, ms, html = ""){
  const el = document.createElement("span");
  el.className = "stfx " + cls;
  el.innerHTML = html;
  el.style.translate = `${x}px ${y}px`;
  ctl.mo.layer.appendChild(el);
  el.animate(frames, {duration: ms, easing: "cubic-bezier(.16,1,.3,1)", fill: "forwards"}).onfinish = () => el.remove();
}

const ST_BURST = Array.from({length: 8}, (_, k) => `<i style="rotate:${k * 45}deg"></i>`).join("");

/* The frame's moments. `fr` is the pose's state for this frame (pose.js, stFrame). */
function stMoments(ctl, p, i, fr){
  const key = ctl.at + ":" + i;
  if (!ctl.mo || ctl.mo.key !== key || !ctl.mo.layer.isConnected){
    if (ctl.mo) stGhosts(ctl, false);
    ctl.mo = {key, done: new Set(), trail: [], ghosts: null, layer: ctl.ui.stage.querySelector(".stactors")};
  }
  const live = ctl.playing && !ST_REDUCED, mo = ctl.mo, once = k => !mo.done.has(k) && mo.done.add(k);
  const el = n => ctl.ui.stage.querySelector(".stactor." + n);
  if (live){
    /* the hit: a burst where they meet, then dust where he goes down */
    if (fr.met && fr.f < 1 && once("hit")){
      const [a, b] = [stXY(el("carrier")), stXY(el("tk"))];
      stFx(ctl, "stburst", [(a[0] + b[0]) / 2, a[1] - 26], [{scale: .3, opacity: 1}, {scale: 1.5, opacity: 0}], 280, ST_BURST);
      if (p.sack) ctl.ui.stage.animate([{translate: "0 0"}, {translate: "-5px 2px"}, {translate: "4px -2px"},
        {translate: "-3px 1px"}, {translate: "2px 0"}, {translate: "0 0"}], {duration: 170});
    }
    if (fr.fell && once("dust")){
      const c = stXY(el("carrier"));
      [-1, 0, 1].forEach(d => stFx(ctl, "stpuff", c, [{translate: `${c[0]}px ${c[1]}px`, scale: .4, opacity: .9},
        {translate: `${c[0] + d * 16}px ${c[1] - 8}px`, scale: 1.8, opacity: 0}], 600));
    }
    /* the turnover: a red ring where the ball changed hands */
    if ((fr.taken || fr.grab >= 1) && once("turn")){
      stFx(ctl, "stpulse", stXY(el("tk")).map((v, k) => k ? v - 22 : v), [{scale: .6, opacity: 1}, {scale: 1.7, opacity: 0}], 420);
    }
    /* the touchdown: confetti in the scoring team's colours, from the end zone */
    if (p.td && fr.f >= 1 && once("td")) stConfetti(ctl);
  }
  el("carrier").classList.toggle("spike", live && !!p.td && fr.f >= 1 && fr.after >= .45);
  stPush(ctl, p, fr, live);
}

/* The big play: the camera pushes in on the break and afterimages trail him until he is down. */
function stPush(ctl, p, fr, live){
  const dir = ctl.drive.dir, big = live && stBig(p, dir), c = stBreak(p, ctl.pose.geom);
  const k = !big ? 0 : fr.f < c - .12 ? 0 : fr.f < c ? stEase((fr.f - c + .12) / .12)
    : 1 - stEase(stClamp((fr.f - c - .1) / .3, 0, 1));
  const st = ctl.ui.stage.style;
  if (k > 0){
    st.transformOrigin = `${stClamp(fr.at, 10, 90)}% 62%`;
    st.scale = (1 + .2 * k).toFixed(3);
  } else if (st.scale) st.scale = "";
  ctl.ui.box.classList.toggle("stpushing", k > 0);
  const trailing = big && fr.f > c && !fr.fell && fr.f < 1;
  if (trailing){
    ctl.mo.trail.push(ctl.ui.stage.querySelector(".stactor.carrier").style.translate);
    if (ctl.mo.trail.length > 12) ctl.mo.trail.shift();
  }
  stGhosts(ctl, trailing);
}

/* three copies of the carrier, 50, 100 and 150ms behind him */
function stGhosts(ctl, on){
  const mo = ctl.mo;
  if (!on){ if (mo.ghosts){ mo.ghosts.forEach(g => g.remove()); mo.ghosts = null; } return; }
  if (!mo.ghosts){
    const src = ctl.ui.stage.querySelector(".stactor.carrier");
    mo.ghosts = [1, 2, 3].map(n => {
      const g = src.cloneNode(true);
      g.classList.remove("carrier", "ring");
      g.classList.add("stghost");
      g.style.opacity = (.36 - n * .09).toFixed(2);
      src.parentNode.insertBefore(g, src);
      return g;
    });
  }
  const tr = mo.trail;
  mo.ghosts.forEach((g, n) => { g.style.translate = tr[Math.max(0, tr.length - 1 - (n + 1) * 3)] || ""; });
}

/* 60 flecks in the scoring team's jersey and trim, from the end zone, gone in 1.4s */
function stConfetti(ctl){
  const box = ctl.ui.box, ez = ctl.ui.stage.querySelector(".stez.tgt");
  if (!ez) return;
  const c = document.createElement("canvas"), r = box.getBoundingClientRect(), e = ez.getBoundingClientRect();
  const k = box.offsetWidth ? r.width / box.offsetWidth : 1, dpr = devicePixelRatio || 1;
  c.className = "stconfetti";
  box.appendChild(c);
  const W = box.offsetWidth, H = box.offsetHeight;
  c.width = W * dpr; c.height = H * dpr;
  const g = c.getContext("2d");
  g.scale(dpr, dpr);
  const css = getComputedStyle(ctl.ui.stage);
  const cols = [css.getPropertyValue("--kit-o").trim() || css.getPropertyValue("--lime").trim(),
                css.getPropertyValue("--kit-o-trim").trim() || css.getPropertyValue("--ink").trim(),
                css.getPropertyValue("--pads").trim()];
  const ox = (e.left + e.width / 2 - r.left) / k, oy = (e.top - r.top) / k;
  const ps = Array.from({length: 60}, () => ({x: ox + (Math.random() - .5) * 30, y: oy, vx: (Math.random() - .5) * 7,
    vy: -Math.random() * 7 - 3, a: Math.random() * 6, va: (Math.random() - .5) * .4, c: cols[Math.random() * 3 | 0]}));
  const t0 = performance.now();
  const tick = now => {
    const t = now - t0;
    g.clearRect(0, 0, W, H);
    g.globalAlpha = stClamp(1 - t / 1400, 0, 1);
    ps.forEach(q => {
      q.vy += .22; q.x += q.vx; q.y += q.vy; q.a += q.va;
      g.save(); g.translate(q.x, q.y); g.rotate(q.a); g.fillStyle = q.c; g.fillRect(-3, -1.5, 6, 3); g.restore();
    });
    if (t < 1400 && c.isConnected) requestAnimationFrame(tick); else c.remove();
  };
  requestAnimationFrame(tick);
}
