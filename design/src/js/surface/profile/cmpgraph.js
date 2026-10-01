/* Compare's graph: the profile's own stat sheet (sheet.js) with every player on it (storyboard v5,
   https://claude.ai/artifact/BLusCqR3ZToXGQ8Kr3nVZM). The same dial, rings, ticks, elite arcs and
   "#rank over the stat" labels, from radarkit.js and sheet.js, so it reads as the chart the reader
   already knows. All shapes are shaded in their player's colour; the one in focus is brighter and
   his ranks are on the labels, so the dial opens as his profile does. A tap on another player's
   card moves the focus (cmp.js).

   Six axes are a position's own six, so the graph draws only when every player shares one; a RB
   beside a WR keeps the cards and the rows. */
const cmpK = rk => rk && rk[1] > 1 ? Math.max(.04, 1 - (rk[0] - 1) / (rk[1] - 1)) : null;

function cmpGraphHTML(ps, on){
  const sheets = ps.map(sheetFor);
  if (new Set(ps.map((p, i) => sheets[i] ? sheets[i].pos : p.pos)).size > 1) return "";
  if (sheets.filter(Boolean).length < 2) return "";
  const fi = sheets[on] ? on : sheets.findIndex(Boolean), s = sheets[fi];
  const g = radarGeom(s.axes.length);
  const ranks = s.axes.map(a => sheetRank(s.pos, a.id, ps[fi].slug));
  const order = ps.map((_, i) => i).filter(i => sheets[i] && i !== fi).concat(fi);
  return `<div class="pf-sheet cmp-graph cmp-s${fi}"><div class="pf-radar-box">
    <svg class="pf-radar" viewBox="-34 0 ${g.VW} ${g.VH}" role="img" aria-label="${t("profile.compare.radar")}">
      ${radarDefsHTML(g.cx, g.cy, g.R)}
      <circle class="pf-radar-disc" cx="${g.cx}" cy="${g.cy}" r="${g.R}"/>
      <g class="pf-radar-grid">${radarGridHTML(g)}</g>
      ${eliteBarsHTML(s, g.ang, g.xy, null, g.cx, g.cy, g.R, g.n)}
      ${order.map(i => cmpShapeHTML(s, ps[i], i, i === fi, g)).join("")}
      <circle class="pf-radar-hub" cx="${g.cx}" cy="${g.cy}" r="2"/></svg>
    ${axisLabelsHTML(s, ranks, i => cmpK(ranks[i]) ?? .04, null, g.ang, g.xy, g.at, g.R, "span")}</div></div>`;
}

/* One player's shape. An axis he has no rank on is left out, as the profile does (sheet.js
   shapeHTML); under three measured axes only the points plot. */
function cmpShapeHTML(s, p, i, front, g){
  const pts = s.axes.map((a, j) => [j, cmpK(sheetRank(s.pos, a.id, p.slug))]).filter(([, r]) => r !== null)
    .map(([j, r]) => g.xy(j, r).map(v => v.toFixed(1)));
  const st = front ? " front" : " dim";
  const dots = pts.map(([x, y]) => `<circle class="cmp-dot cmp-s${i}${st}" cx="${x}" cy="${y}" r="3"/>`).join("");
  return (pts.length >= 3 ? `<polygon class="cmp-shape cmp-s${i}${st}" points="${pts.map(q => q.join(",")).join(" ")}"/>` : "") + dots;
}
