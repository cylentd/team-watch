/* ------------------------------------------------------------------
   STRIP SCENE — where a play is, as pure arithmetic, and the markup that draws the field.

   Coordinates are the ones /api/game already put every play on: ONE fixed field, 0 at the home
   goal line and 100 at the away one, with `dir` per drive saying which way that drive runs. The
   field never flips between drives; the figures turn around. (api/game.py says why: `yardLine` is
   the number painted on the grass, so BUF 15 and DET 15 both arrive as 15.)

   A play runs 0 to 1. Three kinds of play spend that differently:

     rush   the carrier walks from `from` to `to`, and that is all
     pass   a drop (the passer holds while the receiver runs), a flight, then the yards after the
            catch -- so the ball and the man are in different places for most of it
     fg     a swing that takes the first quarter, contact just past halfway through the swing, and
            a ball still climbing as it crosses the post rather than landing on the goal line
------------------------------------------------------------------ */

/* the standing plane the ball flies in, and how high the ball sits in a hand */
const ST_AIR = 150, ST_HAND = {x: 8, y: 17};
/* the swing takes the first quarter of the play; the foot meets the ball .55 of the way through it */
const ST_KICKAT = .3, ST_CONTACT = ST_KICKAT * .55;
/* a made kick sails on past the post rather than stopping on the end line, and is still 40% of its
   peak height when it gets there -- a kick that came down on the goal line would look blocked */
const ST_PAST = ST_EZ_PCT + 2, ST_FGEND = .6;

/* Every "where is this play" question, closed over one drive's direction. Nothing here touches the
   DOM, so the same functions answer for the marks painted into the field and for the figures. */
function stGeom(dir){
  const g = {};
  /* where a play ENDS on the field, which is not always `to`: an incompletion is drawn out to the
     depth it was thrown, and a kick carries through the post. */
  g.endOf = p => p.k === "inc" ? p.from + (p.depth || 20) * dir
    : p.k === "fg" ? p.to + dir * ST_PAST : p.to;
  /* a completion with yardsAfterCatch is two legs: the ball flies to the catch, the man runs the rest */
  g.catchOf = p => p.k === "pass" && p.yac != null ? p.to - dir * p.yac : g.endOf(p);
  g.airOf = p => (g.catchOf(p) - p.from) * dir;
  g.dropOf = p => p.k === "pass" ? .2 : p.k === "fg" ? ST_CONTACT : 0;
  /* how much of the play the ball is in the air for: the split between air yards and yards after
     the catch, floored at .35 so a screen still shows a throw rather than a teleport */
  g.flightOf = p => p.k !== "pass" ? 1
    : g.dropOf(p) + (1 - g.dropOf(p)) * (p.yac > 0
      ? stClamp(g.airOf(p) / (g.airOf(p) + p.yac), .35, 1) : 1);
  /* when the tackler meets him: late in a run, late in the run after a catch. Here rather than in
     pose.js because the transport's hit-stop has to freeze on the same instant the pose draws. */
  g.hitOf = p => p.k === "pass" ? g.flightOf(p) + (1 - g.flightOf(p)) * .8 : .8;
  g.peak = p => Math.min(ST_FIELD.PEAK, 14 + Math.abs(g.catchOf(p) - p.from) * 2.3);
  /* height of the ball u of the way through its flight. A pass comes back down to a hand; a kick's
     back half only sinks to ST_FGEND of the peak, because it is still rising over the crossbar. */
  g.arcH = (p, u) => p.k === "fg" && u > .5
    ? g.peak(p) * (1 - ST_FGEND * Math.pow((u - .5) / .5, 2))
    : 4 * g.peak(p) * u * (1 - u);
  g.flightFrac = (p, f) => stClamp((f - g.dropOf(p)) / (g.flightOf(p) - g.dropOf(p)), 0, 1);
  /* how far along the field the BALL has got at play fraction f: in flight, then carried */
  g.prog = (p, f) => {
    const FL = g.flightOf(p);
    return f < FL ? stLerp(p.from, g.catchOf(p), g.flightFrac(p, f))
      : stLerp(g.catchOf(p), g.endOf(p), FL < 1 ? (f - FL) / (1 - FL) : 1);
  };
  return g;
}

/* One play's mark on the turf: a bar for a run, a faint line under the arc plus a bar for the yards
   after the catch on a completion, a return line the other way on an interception. Each sits in its
   own clipped group so the mark can be REVEALED as the play runs rather than drawn all at once. */
function stMark(p, i, g, id, BASE, dir){
  const clip = ` clip-path="url(#${id}g${i})"`;
  if (p.k === "rush"){
    /* backwards is a loss whichever way the drive runs, so it is `dir` that decides the colour,
       never which of `from` and `to` is the larger number */
    const loss = (p.to - p.from) * dir < 0 ? " loss" : "";
    return `<g data-i="${i}"${clip}><line class="rush${loss}" stroke-width="8" x1="${p.from}" y1="${BASE}" x2="${p.to}" y2="${BASE}"/>`
      + `<line class="sep" x1="${p.to}" y1="${BASE - 6}" x2="${p.to}" y2="${BASE + 6}"/></g>`;
  }
  if (p.k !== "pass") return "";
  const c = g.catchOf(p);
  return `<g data-i="${i}"${clip}><line class="rush" stroke-width="2" stroke-opacity=".4" x1="${p.from}" y1="${BASE}" x2="${c}" y2="${BASE}"/>`
    + (p.yac > 0
      ? `<line class="rush" stroke-width="8" x1="${c}" y1="${BASE}" x2="${p.to}" y2="${BASE}"/>`
        + `<line class="sep" x1="${p.to}" y1="${BASE - 6}" x2="${p.to}" y2="${BASE + 6}"/>`
      : "") + "</g>";
}

/* The field's own contents: the clip paths every mark is revealed through, the marks, the standing
   air plane, and the anchors the flat sprites in .stactors are placed from each frame. */
function stFieldHTML(plays, g, id, label, dir){
  const BASE = ST_FIELD.BASE;
  let defs = "", air = "", marks = "";
  plays.forEach((p, i) => {
    defs += `<clipPath id="${id}g${i}"><rect y="0" height="${ST_FIELD.GH}"/></clipPath>`;
    air += `<clipPath id="${id}a${i}"><rect y="-20" height="${ST_AIR + 40}"/></clipPath>`;
    if (p.k === "int") defs += `<clipPath id="${id}r${i}"><rect y="0" height="${ST_FIELD.GH}"/></clipPath>`;
  });
  plays.forEach((p, i) => {
    if (p.k !== "int") return;
    marks += `<g data-i="${i}" clip-path="url(#${id}r${i})">`
      + `<line class="ret" stroke-width="8" x1="${p.to}" y1="${BASE}" x2="${p.to - dir * (p.ret || 0)}" y2="${BASE}"/></g>`;
  });
  plays.forEach((p, i) => { marks += stMark(p, i, g, id, BASE, dir); });
  return `<svg viewBox="0 0 100 ${ST_FIELD.GH}" preserveAspectRatio="none" role="img" aria-label="${esc(label)}">`
    + `<defs>${defs}</defs>${marks}</svg>`
    + `<span class="stshadow" style="top:${BASE - 4}px"></span>`
    + `<div class="stair" style="top:${BASE - ST_AIR}px">`
    + `<svg viewBox="0 0 100 ${ST_AIR}" preserveAspectRatio="none" aria-hidden="true"><defs>${air}</defs></svg>`
    + '<i class="stanc a-qb"></i><i class="stanc a-tk"></i><i class="stanc a-tk2"></i><i class="stanc a-carrier"></i>'
    + '<i class="stanc a-fly"></i><i class="stanc a-miss"></i><i class="stanc a-probe"></i></div>';
}

/* The flat overlay: everything that must stay screen-upright, in one 2D layer over the tilted field. */
const stActorsHTML = () => '<div class="stactors"><svg class="starcs" aria-hidden="true"></svg>'
  + `<div class="stactor stpost postA">${ST_POST}</div><div class="stactor stpost postB">${ST_POST}</div>`
  + `<div class="stactor stmiss"><svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 1.5l7 7M8.5 1.5l-7 7"/></svg>${t("strip.tag.incomplete")}</div>`
  + '<div class="stactor stfig qb"></div><div class="stactor stfig tk"></div><div class="stactor stfig tk2"></div>'
  + '<div class="stactor stfig carrier"></div>'
  + `<div class="stactor stfly">${ST_BALL}</div></div>`;

/* The whole stage for one drive. `dir` sends the play the right way; the field itself never flips. */
function stStageHTML(drive, id, home, away){
  const g = stGeom(drive.dir), toward = drive.dir > 0 ? "B" : "A";
  const ez = (side, abbr) => `<div class="stez${side === toward ? " tgt" : ""}">${esc(abbr || "")}${stPostAnchors(side)}</div>`;
  return `<div class="stplane" style="--ez:${ST_FIELD.EZ}%;--base:${ST_FIELD.BASE}px">`
    + ez("A", home) + `<div class="stturf"><span class="strz ${drive.dir > 0 ? "r" : "l"}"></span>${stYards()}`
    + '<span class="stltg"><i>1st</i></span><span class="stahead"></span>'
    + stFieldHTML(drive.plays, g, id, drive.label || "", drive.dir)
    + "</div>" + ez("B", away) + "</div>" + stActorsHTML();
}
