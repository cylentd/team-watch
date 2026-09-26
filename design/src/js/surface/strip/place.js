/* ------------------------------------------------------------------
   STRIP PLACE — the measuring layer, and the one function that draws a whole frame.

   The field is a tilted 3D plane; the figures, the ball and the goalposts are flat sprites over
   it. Nothing here projects a coordinate by hand. pose.js puts an invisible anchor at a field
   percent INSIDE the scene, and stPlace reads back where the browser actually put it. That is not
   a dodge around one Chromium bug (elements in a nested preserve-3d context get mis-sorted against
   each other and the figure gets sliced by the turf it stands on) -- it is also the only way the
   goalpost's crossbar can be measured rather than guessed at.
------------------------------------------------------------------ */

/* The scene handle: elements, anchors, geometry and the two bits of mutable state (which play's
   figures are currently in the DOM, and which layout the arc cache was measured against). */
function stBind(root, drive, id, faces){
  const q = s => root.querySelector(s);
  const S = {
    root, id, faces, plays: drive.plays, dir: drive.dir, g: stGeom(drive.dir),
    el: {carrier: q(".stactor.carrier"), qb: q(".stactor.qb"), tk: q(".stactor.tk"), tk2: q(".stactor.tk2"),
         fly: q(".stactor.stfly"), miss: q(".stactor.stmiss"), shadow: q(".stshadow"),
         postA: q(".stactor.postA"), postB: q(".stactor.postB"), arcs: q(".starcs")},
    anc: {carrier: q(".a-carrier"), qb: q(".a-qb"), tk: q(".a-tk"), tk2: q(".a-tk2"), fly: q(".a-fly"),
          miss: q(".a-miss"), probe: q(".a-probe"),
          nA: q(".a-nA"), fA: q(".a-fA"), nB: q(".a-nB"), fB: q(".a-fB")},
    clips: drive.plays.map((p, i) => root.querySelectorAll(`#${id}g${i} rect, #${id}a${i} rect`)),
    marks: [...root.querySelectorAll(".stturf svg g[data-i]")],
    memo: {}, ver: 0, shown: -1, clipKey: [],
  };
  S.el.arcs.innerHTML = S.plays.map((p, j) => p.k === "rush" ? ""
    : `<polyline class="${p.k === "inc" || p.k === "int" ? "inc" : "pass"}" data-j="${j}"/>`).join("");
  const pose = (i, f, hold = 1, all = false) => stPoseFrame(S, i, f, hold, all);
  /* the arc cache is measured against a layout; anything that moves the field invalidates it */
  pose.bump = () => { S.ver++; };
  /* whose feet the ring goes under when he is on the play; null leaves it on the carrier */
  pose.mark = who => { S.mark = who; S.shown = -1; };
  pose.geom = S.g;
  return pose;
}

const ST_ARC_N = 16;

/* How much an ancestor is scaling the strip right now. getBoundingClientRect reports SCREEN
   pixels, so inside a transformed ancestor every measured gap comes back multiplied -- while the
   `translate` written back onto a sprite is applied in the element's own, unscaled coordinates.
   Dividing closes that loop.

   This is not hypothetical and it is not only about the open animation: the strip opens in a
   dialog that grows from scale(.2), so a frame measured mid-transition put the figures a hundred
   pixels above the field and left them there. Reading the factor every frame also means nothing
   has to know when the transition ended. */
const stScale = root => {
  const w = root.getBoundingClientRect().width;
  return w && root.offsetWidth ? w / root.offsetWidth : 1;
};

/* Where play j's arc falls ON SCREEN. The arc is a shape in the tilted plane, so rather than
   projecting it we walk the probe along it inside the scene and read back each point. Memoised
   per layout: the walk costs 17 forced reflows, which is not something to do every frame. */
function stArcPoints(S, j){
  if (S.memo[j] && S.memo[j].ver === S.ver) return S.memo[j].pts;
  const p = S.plays[j], o = S.root.getBoundingClientRect(), k0 = stScale(S.root), pts = [];
  for (let k = 0; k <= ST_ARC_N; k++){
    const u = k / ST_ARC_N;
    S.anc.probe.style.left = stLerp(p.from, S.g.catchOf(p), u) + "%";
    S.anc.probe.style.bottom = S.g.arcH(p, u) + "px";
    const r = S.anc.probe.getBoundingClientRect();
    /* a kick leaves the ground, a pass leaves a hand, and an incompletion falls out of one */
    const lift = p.k === "fg" ? 0 : p.k === "inc" ? ST_HAND.y * (1 - u) : ST_HAND.y;
    pts.push([(r.left - o.left) / k0 + ST_HAND.x, (r.top - o.top) / k0 - lift - 4.5]);
  }
  S.memo[j] = {ver: S.ver, pts};
  return S.memo[j].pts;
}

/* Plays before i are drawn whole and stepped back; play i is drawn up to u. */
/* Only an arc whose drawn length or layout changed is rewritten: every attribute write on an SVG
   repaints it, and all but one arc are standing still on any given frame. */
function stDrawArcs(S, i, u0, whole){
  S.arcEls = S.arcEls || [...S.el.arcs.querySelectorAll("polyline")];
  S.arcEls.forEach(pl => {
    const j = +pl.dataset.j, u = j < i ? 1 : j > i ? 0 : u0, past = !whole && j < i;
    if (pl.classList.contains("past") !== past) pl.classList.toggle("past", past);
    const key = u ? u.toFixed(4) + "@" + S.ver : "0";
    if (pl.__key === key) return;
    pl.__key = key;
    if (!u) return pl.setAttribute("points", "");
    const all = stArcPoints(S, j), at = u * ST_ARC_N, k = Math.floor(at), out = all.slice(0, k + 1);
    if (k < ST_ARC_N) out.push([stLerp(all[k][0], all[k + 1][0], at - k),
                                stLerp(all[k][1], all[k + 1][1], at - k)]);
    pl.setAttribute("points", out.map(pt => pt[0].toFixed(1) + "," + pt[1].toFixed(1)).join(" "));
  });
}

/* Each mark on the turf is revealed by widening its clip rect. The revealed range runs from the
   snap to wherever the play has got AND spans the catch point once there is one, which matters on
   a screen pass, where the catch happens behind the line of scrimmage. */
function stReveal(S, i, f, all){
  S.plays.forEach((pl, j) => {
    const fj = j < i ? 1 : j > i ? 0 : f, cur = S.g.prog(pl, fj);
    const c0 = fj >= S.g.flightOf(pl) ? S.g.catchOf(pl) : pl.from;
    const lo = Math.min(pl.from, c0, cur), hi = Math.max(pl.from, c0, cur), key = lo + ":" + hi;
    /* unchanged clips are left alone: a write to one repaints the whole tilted field */
    if (S.clipKey[j] === key) return;
    S.clipKey[j] = key;
    S.clips[j].forEach(r => { r.setAttribute("x", lo); r.setAttribute("width", hi - lo); });
  });
  S.marks.forEach(gr => {
    const past = !all && +gr.dataset.i < i;
    if (gr.classList.contains("past") !== past) gr.classList.toggle("past", past);
  });
}

/* An interception's return line grows during the beat AFTER the catch, not during the play. */
function stRevealReturn(S, i, after){
  S.plays.forEach((pl, j) => {
    if (pl.k !== "int") return;
    const r = S.root.querySelector(`#${S.id}r${j} rect`);
    const w = (pl.ret || 0) * (j < i ? 1 : j > i ? 0 : stOut(after));
    r.setAttribute("x", S.dir > 0 ? pl.to - w : pl.to);
    r.setAttribute("width", w);
  });
}

/* Read where each anchor landed on screen and put its sprite there. Every read comes before any
   write: a read after a write forces the browser to lay the 3D scene out again, and interleaving
   them cost three and a half layouts a frame. */
function stPlace(S, x){
  const p = x.p, f = x.f, o = S.root.getBoundingClientRect(), el = S.el, anc = S.anc;
  const k = stScale(S.root);
  const lift = p.k === "fg" ? 0 : x.picked ? ST_HAND.y
    : x.inc ? ST_HAND.y * (1 - f)
    : x.loose ? ST_HAND.y * (1 - Math.min(x.after * 3, 1)) : ST_HAND.y;
  const at = a => { const r = a.getBoundingClientRect(); return [(r.left - o.left) / k, (r.top - o.top) / k]; };
  const put = [[el.carrier, anc.carrier, 0, 0], [el.qb, anc.qb, 0, 0], [el.tk, anc.tk, 0, 0], [el.tk2, anc.tk2, 0, 0],
    [el.fly, anc.fly, ST_HAND.x, -lift], [el.miss, anc.miss, ST_HAND.x, 0]].map(([node, a, dx, dy]) => {
    const [l, t] = at(a);
    return [node, l + dx, t + dy];
  });
  /* the goalposts only move when the layout does, so they are measured once per layout (and per
     ancestor scale, which the dialog's open animation changes) rather than every frame */
  const postKey = S.ver + "@" + k.toFixed(3) + "@" + o.width.toFixed(1);
  const posts = S.posts && S.posts.key === postKey ? null
    : [[el.postA, anc.nA, anc.fA], [el.postB, anc.nB, anc.fB]].map(([node, near, far]) => [node, at(near), at(far)]);
  put.forEach(([node, l, t]) => { node.style.translate = `${l}px ${t}px`; });
  if (posts){
    S.posts = {key: postKey};
    /* the uprights stay screen-vertical like the figures; only the crossbar's direction and length
       come from the scene, one anchor under each upright on the end line */
    posts.forEach(([node, [nl, nt], [fl, ft]]) => {
      node.style.translate = `${nl}px ${nt}px`;
      node.querySelector("path").setAttribute("d", stPostPath(fl - nl, ft - nt));
    });
  }
}

/* Who stands on the lime ring: the reader's own player when the reel is narrowed to him and he is
   on this play (as the passer, or even as a tackler), otherwise the man the play card names --
   until the defence has the ball, when it is whoever has it. */
function stRing(S, p, stolen){
  const on = stolen ? "tk" : S.mark && p.qb === S.mark ? "qb" : S.mark && p.tk === S.mark ? "tk"
    : S.mark && p.tk2 === S.mark ? "tk2" : "carrier";
  ["carrier", "qb", "tk", "tk2"].forEach(r => {
    if (S.el[r].classList.contains("ring") !== (r === on)) S.el[r].classList.toggle("ring", r === on);
  });
}

/* One whole frame. Returns the frame's state for moments.js, with `at` set to whatever the
   chevrons should point past: the ball while it is in the air, the man once he has it. */
function stPoseFrame(S, i, f, hold, all){
  const p = S.plays[i], x = stFrame(S, p, f, hold);
  stReveal(S, i, f, all);
  stRevealReturn(S, i, x.after);
  if (i !== S.shown){
    S.shown = i;
    S.el.carrier.innerHTML = stFigure(p.who);
    S.el.qb.innerHTML = p.qb ? stFigure(p.qb) : "";
    S.el.tk.innerHTML = p.tk ? stFigure(p.tk) : "";
    S.el.tk2.innerHTML = p.tk2 ? stFigure(p.tk2) : "";
  }
  const cx = stPoseCarrier(S, x);
  stPoseQb(S, x);
  x.grab = stPoseTk(S, x);
  stPoseTk2(S, x);
  const bx = stPoseBall(S, x, x.grab);
  stRing(S, p, x.taken || x.grab >= 1);
  stPlace(S, x);
  stDrawArcs(S, i, x.fl, all);
  x.at = x.inAir && !x.caught ? bx : cx;
  return x;
}
