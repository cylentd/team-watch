/* What both radars draw with: the profile's stat sheet (sheet.js radarHTML) and Compare's graph
   (cmpgraph.js). One geometry and one frame, so the two read as the same chart (2026-09-30, David:
   Compare "changed up the look"). R 114 in a 468 x 392 box: sheet.js radarHTML says why. */
const RADAR = {cx: 200, cy: 196, R: 114, VW: 468, VH: 392};   // viewBox -34..434 x 0..392

function radarGeom(n){
  const {cx, cy, R, VW, VH} = RADAR;
  const ang = i => -Math.PI / 2 + i * 2 * Math.PI / n;
  const xy = (i, r) => [cx + Math.cos(ang(i)) * R * r, cy + Math.sin(ang(i)) * R * r];
  const pc = (a, b) => (a / b * 100).toFixed(2) + "%";
  const at = (x, y) => `left:${pc(x + 34, VW)};top:${pc(y, VH)}`;
  return {n, cx, cy, R, VW, VH, ang, xy, pc, at};
}

/* The rings and ticks. Ticks, not spokes: a full spoke's only job is to say where an axis is, and
   the label and the vertex already say that, while six of them crossed the translucent shape and
   turned the fill muddy. */
function radarGridHTML(g){
  const ring = (r, cls, i) => `<circle class="pf-radar-ring${cls}" style="--i:${i}" cx="${g.cx}" cy="${g.cy}" r="${(g.R * r).toFixed(1)}"/>`;
  const ticks = Array.from({length: g.n}, (_, i) => {
    const [x0, y0] = g.xy(i, .93), [x1, y1] = g.xy(i, 1);
    return `<line class="pf-radar-axis" style="--i:${i}" x1="${x0.toFixed(1)}" y1="${y0.toFixed(1)}" x2="${x1.toFixed(1)}" y2="${y1.toFixed(1)}"/>`;
  }).join("");
  return [.25, .5, .75].map((r, i) => ring(r, "", 2 - i)).join("") + ring(1, " rim", 0) + ticks;
}
