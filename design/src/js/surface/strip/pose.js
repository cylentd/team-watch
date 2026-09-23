/* ------------------------------------------------------------------
   STRIP POSE — where each figure is, one frame at a time.

   `f` is the play itself, 0 to 1. `hold` is the beat AFTER it, also 0 to 1: a tackler carrying on
   through the hit, a dropped ball bouncing, a fumble coming loose, a scorer's momentum taking him
   into the end zone. Parked on a finished play, hold is 1 and everything is at rest. That is what
   makes the whole thing scrubbable: any (i, f, hold) draws the same picture every time.

   Every function here takes `S`, the scene handle place.js builds -- its elements, its anchors and
   its geometry. Positions are set on the ANCHORS, in field percent; place.js is what reads back
   where the browser put them and moves the flat sprites there.
------------------------------------------------------------------ */

/* Everything the rest of a frame is derived from, worked out once. */
function stFrame(S, p, f, hold){
  const g = S.g, dir = S.dir;
  const x = {p, f, e: g.endOf(p), c: g.catchOf(p), FL: g.flightOf(p), DROP: g.dropOf(p)};
  x.fl = g.flightFrac(p, f);
  x.after = f >= 1 ? hold : 0;
  x.inAir = p.k !== "rush";
  x.picked = p.k === "int";
  x.inc = p.k === "inc" || x.picked;
  x.caught = p.k === "pass" && f >= x.FL;
  x.taken = x.picked && f >= 1;
  x.loose = !!p.fum && f >= 1;
  x.loss = (x.e - p.from) * dir < 0;
  x.big = p.k !== "inc" && p.k !== "fg" && !x.picked && Math.abs(x.e - p.from) >= 20;
  /* contact comes while both men are still moving, so neither brakes before the hit */
  x.HIT = p.k === "pass" ? x.FL + (1 - x.FL) * .8 : .8;
  x.met = !!p.tk && !x.picked && f >= x.HIT;
  /* A real route (3+ air yards) has a stem and a break: release, run downfield while the passer
     drops, then close under the ball. A screen or swing caught at or behind the line is not that
     route run backwards -- there is no downfield break to show -- so he takes his release step,
     holds it while the pocket sets up, and moves only once the ball is thrown. */
  x.shallow = p.k === "pass" && g.airOf(p) < 3;
  x.route = p.from + dir * (x.shallow ? 1 : 2.5);
  const back = dir * stClamp(g.airOf(p) * .45, 4, 15);
  x.open = x.shallow ? x.route
    : dir > 0 ? Math.max(x.route + dir, x.c - back) : Math.min(x.route + dir, x.c - back);
  return x;
}

/* Where the man the play belongs to is at play fraction u. */
function stCarrierAt(S, x, u){
  const p = x.p, dir = S.dir;
  if (p.k !== "pass") return x.inAir
    ? stLerp(stLerp(p.from, x.e, .4), x.e - (x.picked ? dir * 4 : 0), u)
    : stLerp(p.from, x.e, u);
  if (u < x.DROP) return x.shallow ? x.route : stLerp(x.route, x.open, u / x.DROP);
  if (u < x.FL) return stLerp(x.open, x.c, (u - x.DROP) / (x.FL - x.DROP));
  return stLerp(x.c, x.e, x.FL < 1 ? (u - x.FL) / (1 - x.FL) : 1);
}

function stPoseCarrier(S, x){
  const p = x.p, f = x.f, dir = S.dir, a = stOut(x.after);
  const shove = p.tk && !x.picked ? (x.loss ? -dir : dir) * (x.loss ? 1.1 : .5) * a : 0;
  let cx = stCarrierAt(S, x, f) + shove;
  if (p.td && f >= 1) cx += dir * 2 * a;                  /* momentum carries a scorer on */
  /* a kicker never runs downfield: he starts two steps behind the spot and steps into the ball */
  if (p.k === "fg") cx = stLerp(p.from - dir * 2.5, p.from - dir * .6, stOut(Math.min(f / ST_KICKAT, 1)));
  S.anc.carrier.style.left = cx + "%";
  /* on a screen he comes BACK toward the passer for the ball, so turn him to face it */
  const settling = p.k === "pass" && f >= x.DROP && f < x.FL && (x.c - x.open) * dir < 0;
  const cl = S.el.carrier.classList;
  cl.toggle("settle", settling);
  /* no run cycle over zero ground on a shallow route during the drop; a kicker never runs at all */
  cl.toggle("run", p.k !== "fg" && f > 0 && f < 1 && !(x.shallow && f < x.DROP));
  cl.toggle("back", x.loss);
  cl.toggle("down", x.met);
  cl.toggle("has", (!x.inAir || x.caught) && !x.loose);
  cl.toggle("joy", !!p.td && f >= 1);
  cl.toggle("turbo", x.big && f > .25 && f < 1 && (!x.inAir || x.caught));
  if (p.k === "fg") stPoseKick(S, f);
  return cx;
}

/* The swing is over by ST_KICKAT and holds its follow-through after -- real kicks land in well
   under a second. Set as angles rather than as a CSS animation, so scrubbing lands mid-swing
   instead of finding a wall-clock animation already snapped to its end. */
function stPoseKick(S, f){
  const a = stKickAngles(f / ST_KICKAT);
  const set = (sel, deg) => { const node = S.el.carrier.querySelector(sel); if (node) node.style.rotate = deg + "deg"; };
  set(".near.hip", a.hip); set(".near .knee", a.knee); set(".torso", a.torso);
  set(".far.sh", a.armFar); set(".near.sh", a.armNear);
}

/* The passer, not the receiver, is who drops back -- and deeper for a shot downfield than for the
   quick game, which is the difference between a 3-step drop and a 7-step one. */
function stPoseQb(S, x){
  const p = x.p, f = x.f;
  const dist = p.k === "pass" ? (x.shallow ? 2 : S.g.airOf(p) >= 20 ? 6 : 4) : 3;
  S.anc.qb.style.left = (p.from - S.dir * dist * (x.DROP ? stOut(Math.min(f / x.DROP, 1)) : 0)) + "%";
  S.el.qb.style.display = x.inAir && p.qb ? "" : "none";
  S.el.qb.classList.toggle("run", f > 0 && f < x.DROP);
  S.el.qb.classList.toggle("back", f < x.DROP);
  S.el.qb.classList.toggle("threw", f > x.DROP);
  S.el.qb.classList.toggle("has", f <= x.DROP);
}

/* The defender: closing, then on him, then -- after a pick or a loose ball -- going the other way.
   Returns how far along that recovery is, which is also what decides whether the ball is drawn. */
function stPoseTk(S, x){
  const p = x.p, f = x.f, dir = S.dir, GAP = 2.9, a = stOut(x.after);
  const grab = p.fum && p.fum.lost && f >= 1 ? stOut(stClamp((x.after - .4) / .5, 0, 1)) : 0;
  const at = stCarrierAt(S, x, x.HIT);
  const closing = stLerp(at + dir * (GAP + 12), at + dir * GAP, f / x.HIT);
  S.anc.tk.style.left = (x.picked ? x.e - dir * (p.ret || 0) * a
    : f < x.HIT ? closing
    : stLerp(stCarrierAt(S, x, f) + dir * GAP, p.fum ? p.fum.spot : 0, grab)) + "%";
  S.el.tk.style.display = p.tk ? "" : "none";
  S.el.tk.style.opacity = Math.min(f * 8, 1);
  S.el.tk.classList.toggle("run", x.picked ? x.taken && x.after < 1 : grab ? grab < 1 : f > 0 && x.after < .6);
  S.el.tk.classList.toggle("down", x.met && !grab);
  S.el.tk.classList.toggle("has", x.taken || grab >= 1);
  return grab;
}

/* The ball, and the tag that names what happened to it where it came down. */
function stPoseBall(S, x, grab){
  const p = x.p, f = x.f, dir = S.dir, a = stOut(x.after);
  const hop = (n, top) => top * Math.abs(Math.sin(x.after * Math.PI * n)) * (1 - x.after);
  const bx = x.loose ? stLerp(stCarrierAt(S, x, 1), p.fum.spot, a)
    : stLerp(p.from, x.c, x.fl) + (x.inc && !x.picked ? dir * 2.4 * a : 0);
  const h = x.loose ? hop(2.5, 15)
    : x.inAir ? S.g.arcH(p, x.fl) + (x.inc && !x.picked ? hop(2, 12) : 0) : 0;
  const teed = p.k === "fg" && f <= x.DROP;               /* on the tee, waiting for the foot */
  S.el.fly.style.display = (x.inAir && !x.caught && !x.taken && f > x.DROP) || teed || (x.loose && grab < 1) ? "" : "none";
  S.anc.fly.style.left = bx + "%";
  S.anc.fly.style.bottom = h + "px";
  S.el.shadow.style.left = bx + "%";
  S.el.shadow.style.opacity = h > 2 ? .9 : 0;
  stPoseTag(S, x);
  return bx;
}

/* What the tag by the ball says. A fumble says two things in turn -- it is out, then who ended up
   with it. Every copy key is spelled out in full; assemble --check scans for literal lookups. */
function stPoseTag(S, x){
  const p = x.p, settled = x.loose && x.after >= .55;
  const say = x.taken ? t("strip.tag.intercepted")
    : x.inc && x.f >= 1 ? t("strip.tag.incomplete")
    : settled && p.fum.lost ? t("strip.tag.fumbleLost", {by: p.fum.by})
    : settled ? t("strip.tag.fumbleOwn", {by: p.fum.by})
    : x.loose ? t("strip.tag.fumble") : "";
  S.el.miss.style.display = say ? "" : "none";
  S.el.miss.classList.toggle("warn", x.loose && !(p.fum.lost && x.after >= .55));
  if (say && S.el.miss.lastChild.nodeValue !== say) S.el.miss.lastChild.nodeValue = say;
  S.anc.miss.style.left = (x.loose ? p.fum.spot : x.e) + "%";
}
