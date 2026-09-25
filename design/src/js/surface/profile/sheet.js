/* The stat sheet: the radar in the modal's left column and the card under it.

   Everything here reads USAGE.sheet, ff-jarvis's model.season.sheet. `axes` is the contract for
   what a position's shape is drawn from -- which stats, how to format them, the bar each has to
   clear to be elite -- and `rows` is one season-to-date row per player. Season and not this week
   on purpose: route data publishes a week behind, and one week of counting stats is mostly ties.
   The card under the sheet holds the week-by-week line instead, so both windows have a home.

   USAGE (data/usage.js) is declared after this file but only read inside a function body, at
   click time, when every top-level const in the page has already run. */
function sheetFor(p){
  const s = typeof USAGE !== "undefined" && USAGE ? USAGE.sheet : null;
  if (!s || !p || !p.slug) return null;
  const row = s.rows.find(r => r.slug === p.slug);
  const axes = row && s.axes[row.pos];
  return axes && axes.length ? {axes, row, pos: row.pos} : null;
}

/* {slug: value} for one axis across a position. Memoised: every open reranks, and `rows` holds
   the producer's whole position rather than the page's display cut, so this is the honest
   denominator -- "of 120 WRs" means the 120 who qualified, not the 80 the Grid draws. */
const SHEET_BY = {};
function sheetValues(pos, axis){
  const key = pos + "|" + axis;
  if (!SHEET_BY[key]){
    const by = {};
    USAGE.sheet.rows.forEach(r => {
      if (r.pos === pos && r.v[axis] !== null && r.v[axis] !== undefined) by[r.slug] = r.v[axis];
    });
    SHEET_BY[key] = by;
  }
  return SHEET_BY[key];
}

function sheetRank(pos, axis, slug){ return rankAmong(sheetValues(pos, axis), slug); }

/* Where an axis's elite bar falls on a radius drawn from rank: the radius a player sitting
   exactly on the threshold would take. Null when the axis has no published bar. */
function eliteRadius(pos, axis, elite){
  if (elite === null || elite === undefined) return null;
  return valueRadius(pos, axis, elite);
}

/* The radius any value would take on an axis: the same rank-to-radius rule the shape uses, for a
   number no player has to have -- the elite bar, or the starters' median the compare ghost draws. */
function valueRadius(pos, axis, x){
  const v = Object.values(sheetValues(pos, axis));
  if (v.length < 2) return null;
  return Math.max(.04, Math.min(1, 1 - v.filter(y => y > x).length / (v.length - 1)));
}

function sheetDefaultAxis(s){
  const by = USAGE.rankBy && USAGE.rankBy[s.pos];
  return s.axes.some(a => a.id === by) ? by : s.axes[0].id;
}

/* One axis per stat: his season rank among the position, first place at the rim and last at the
   centre, with a tick on each axis where its elite bar sits. Labels are buttons; the card under
   the sheet shows the chosen stat's number, rank, threshold and week-by-week line.

   The grid rings are circles, not polygons. Six concentric hexagons crossed by six spokes read
   as a drawn cube -- the eye resolves the three long diagonals into a box and the tinted shape
   inside it into a plane leaning in it -- which is exactly the one thing this chart must not
   look like. A round grid has no second reading, and a radius that means a percentile is round
   anyway. */
function radarHTML(p){
  const s = sheetFor(p);
  if (!s) return "";
  /* The viewBox bleeds 34 units past the chart box on each side. A flank label is anchored
     outwards from x = cx ± 1.2R, so its length runs away from the centre: "Breakaway" at this
     size is 78 units wide and ended at x = -12, clipped by the viewBox and visibly closer to the
     edge than "Opp%" opposite it. The bleed is symmetric, so the chart stays centred whatever
     the six labels happen to be.

     R is 134 and the labels ride at 1.14R rather than 1.2R, because the dial was taking barely
     half the width of its own column while the label ring took the rest. Both numbers are at
     their limit for this viewBox: the top label's cap sits at y = 3 against an edge of 0, the
     bottom label's second line at y = 351 against 360, and "Breakaway" anchored outward ends at
     x = -31 against -34. Moving either further needs a bigger box, not a bigger radius. */
  const n = s.axes.length, cx = 200, cy = 176, R = 134, LR = 1.14;   // -34..434 x 0..360 viewBox
  const sel = sheetDefaultAxis(s);
  const ranks = s.axes.map(a => sheetRank(s.pos, a.id, p.slug));
  const k = i => { const rk = ranks[i]; return rk && rk[1] > 1 ? Math.max(.04, 1 - (rk[0] - 1) / (rk[1] - 1)) : .04; };
  const ang = i => -Math.PI / 2 + i * 2 * Math.PI / n;
  const xy = (i, r) => [cx + Math.cos(ang(i)) * R * r, cy + Math.sin(ang(i)) * R * r];
  const ring = (r, cls, i) => `<circle class="pf-radar-ring${cls}" style="--i:${i}" cx="${cx}" cy="${cy}" r="${(R * r).toFixed(1)}"/>`;
  const rings = [.25, .5, .75].map((r, i) => ring(r, "", 2 - i)).join("") + ring(1, " rim", 0);
  /* Ticks, not spokes. A full spoke's only job is to say where an axis is, and the label and the
     vertex both already say that -- meanwhile six of them crossed the translucent shape, showing
     through it and turning the fill muddy. The tick keeps the anchoring and leaves the middle of
     the chart to the data. */
  const spokes = s.axes.map((_, i) => {
    const [x0, y0] = xy(i, .93), [x1, y1] = xy(i, 1);
    return `<line class="pf-radar-axis" style="--i:${i}" x1="${x0.toFixed(1)}" y1="${y0.toFixed(1)}" x2="${x1.toFixed(1)}" y2="${y1.toFixed(1)}"/>`;
  }).join("");
  /* The dial's touch target is an HTML circle over the disc, not the SVG itself: touch-action is
     only reliable on HTML boxes, and it has to be `none` on the dial (a drag scrubs the axes)
     while the label ring around it still scrolls the modal. Percentages of the viewBox, so it
     tracks the chart at every width. */
  const pc = (a, b) => (a / b * 100).toFixed(2) + "%";
  const hit = `left:${pc(cx - R + 34, 468)};top:${pc(cy - R, 360)};width:${pc(2 * R, 468)};height:${pc(2 * R, 360)}`;
  const shaped = ranks.filter(r => r !== null).length >= 3;
  return `<div class="pf-sheet pos-${esc(String(s.pos).toLowerCase())}" data-slug="${esc(p.slug)}"><div class="pf-radar-box">
    <svg class="pf-radar" viewBox="-34 0 468 360" role="img" aria-label="${t("profile.sheet.label")}" data-cx="${cx}" data-cy="${cy}" data-r="${R}">
      ${radarDefsHTML(cx, cy, R)}
      <circle class="pf-radar-disc" cx="${cx}" cy="${cy}" r="${R}"/>
      <g class="pf-radar-grid">${rings}${spokes}</g>
      ${eliteBarsHTML(s, ang, xy, sel, cx, cy, R, n)}
      ${shaped ? `<polygon class="pf-radar-ghost" points=""/>` : ""}
      <g class="pf-radar-grow">${shapeHTML(s, ranks, k, xy, sel, cx, cy)}</g>
      <circle class="pf-radar-hub" cx="${cx}" cy="${cy}" r="2"/>
      ${axisLabelsHTML(s, ranks, sel, ang, xy, LR)}
      ${shaped ? `<text class="pf-radar-cmp" role="button" tabindex="0" x="-30" y="14">${t("profile.sheet.compare", {pos: esc(s.pos)})}</text>` : ""}</svg>
    <div class="pf-radar-hit" style="${hit}"></div></div>
    <div class="pf-stat">${statDetailHTML(s, sel)}</div></div>`;
}

/* Two gradients, both anchored to the chart's own centre rather than to a bounding box, so the
   shape's colour depends on how far out it reaches and not on how wide it happens to be.

   The disc runs dark at the hub to lighter at the rim, which is the scale itself made visible:
   the caption says "1st at the rim" once, and the surface says it continuously. The fill runs
   dense at the hub to thin at the rim, so a shape that reaches has an airy edge and a shape
   pinched to the middle looks like the dense little knot it is.

   Stop colours live in CSS (sheet.css) rather than on the stops, both because a colour literal
   in JS is a lint error here and because the tint is a position token the class already carries. */
function radarDefsHTML(cx, cy, R){
  const at = `gradientUnits="userSpaceOnUse" cx="${cx}" cy="${cy}" r="${R}"`;
  return `<defs>
    <radialGradient id="pf-disc-g" ${at}>
      <stop class="pf-disc-0" offset="0"/><stop class="pf-disc-1" offset="1"/>
    </radialGradient>
    <radialGradient id="pf-fill-g" ${at}>
      <stop class="pf-fill-0" offset="0"/><stop class="pf-fill-1" offset="1"/>
    </radialGradient>
  </defs>`;
}

/* An axis he has no number for is left out of the shape rather than pinned at the centre: a
   receiver heatradar has not covered yet is unmeasured on four axes, not the worst in the league
   on them, and a shape pinched to the middle says the second thing. */
function shapeHTML(s, ranks, k, xy, sel, cx, cy){
  const idx = s.axes.map((_, i) => i).filter(i => ranks[i] !== null);
  const pts = idx.map(i => xy(i, k(i)).map(v => v.toFixed(1)).join(",")).join(" ");
  /* Under three measured axes there is no shape to draw, and <polygon> with two points renders
     as a bare line between them -- which reads as a broken chart rather than as a player the
     route data has not covered yet. The vertices still plot, because they are real, and the
     count says why the rest is missing. Rashee Rice in week 2 is the case: WOPR and RZ Tgts
     measured, the four route-derived stats not. */
  const poly = idx.length >= 3 ? `<polygon class="pf-radar-shape" points="${pts}"/>` : "";
  const note = idx.length >= 3 ? ""
    : `<text class="pf-radar-note" x="${cx}" y="${cy + 46}" text-anchor="middle">${t("profile.sheet.partial", {n: idx.length, of: s.axes.length})}</text>`;
  /* Each vertex carries its own stat id, so picking a label lights the point it belongs to.
     Without it the highlight moved on the label and the shape never answered. */
  const dots = idx.map(i => {
    const [x, y] = xy(i, k(i));
    return `<circle class="pf-radar-dot${s.axes[i].id === sel ? " on" : ""}" data-col="${esc(s.axes[i].id)}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.5"/>`;
  }).join("");
  /* Two rings at the selected vertex, both moved by wireSheet on a pick. `mark` is the resting
     state -- a target on the point being read, which is where the number it describes actually
     is; a tinted spoke out from the centre did the same job but drew a line across the shape to
     do it. `ping` fires once on a change. Neither carries a data-col, so the sweep that lights
     the label, tick and dot leaves them alone. */
  const si = s.axes.findIndex(a => a.id === sel);
  const [px, py] = idx.includes(si) ? xy(si, k(si)) : [0, 0];
  const at = `cx="${px.toFixed(1)}" cy="${py.toFixed(1)}"`;
  return `${poly}${note}
    <circle class="pf-radar-mark" ${at} r="11"/>
    <circle class="pf-radar-ping" ${at} r="6"/>${dots}`;
}

/* The elite bar as an arc across the whole sector its axis owns, not a tick on the axis line.

   Two reasons, and the second is the real one. A 14-unit dash sitting in open space had nothing
   to belong to -- six of them read as scratches on the glass, which is what they looked like.
   And a threshold is a contour, not a point: drawn as an arc, the player's own shape visibly
   crosses outside it or falls inside it, so "elite on this stat" becomes something you see
   rather than something you work out from two numbers in the card.

   The arc spans the axis's angle plus or minus half a sector, so the six arcs tile the circle
   without touching. An axis the producer publishes no bar for simply has no arc.

   Each arc carries its own ELITE tag, sitting just outside it -- on the side the shape has to
   reach to clear it, so the word marks the zone rather than the line. Only the selected axis's
   tag is shown, because six of them at once is a wall of the same word. This replaces the legend
   that used to sit under the chart saying "dashed arc = elite": a code explained in a caption is
   a code the reader has to carry back to the picture, and the fix is to put the word on the
   thing. Tag and arc share the axis id, so the same `data-col` sweep lights both. */
function eliteBarsHTML(s, ang, xy, sel, cx, cy, R, n){
  const half = Math.PI / n * .82;
  return s.axes.map((a, i) => {
    const er = eliteRadius(s.pos, a.id, a.elite);
    if (er === null) return "";
    const r = er * R, a0 = ang(i) - half, a1 = ang(i) + half, on = a.id === sel ? " on" : "";
    const pt = t2 => `${(cx + Math.cos(t2) * r).toFixed(1)},${(cy + Math.sin(t2) * r).toFixed(1)}`;
    /* At the arc's end, not its middle. The middle of the arc is the axis itself, which is
       exactly where that stat's own vertex sits -- on a stat whose bar is near the rim the tag
       landed on top of the point and its marker ring. The end of the arc is always clear of
       every vertex, and only one tag is ever shown so two cannot collide. */
    const tr = Math.min(r + 9, R - 7);
    const tx = cx + Math.cos(a1) * tr, ty = cy + Math.sin(a1) * tr;
    return `<path class="pf-radar-bar${on}" data-col="${esc(a.id)}" data-r="${r.toFixed(1)}" fill="none" d="M ${pt(a0)} A ${r.toFixed(1)} ${r.toFixed(1)} 0 0 1 ${pt(a1)}"/>`
      + `<text class="pf-radar-bartag${on}" data-col="${esc(a.id)}" x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" text-anchor="middle" dominant-baseline="middle">${t("profile.sheet.eliteTag")}</text>`;
  }).join("");
}

function axisLabelsHTML(s, ranks, sel, ang, xy, LR){
  return s.axes.map((a, i) => {
    const [x, y] = xy(i, LR), c = Math.cos(ang(i)), sn = Math.sin(ang(i));
    const anchor = c > .3 ? "start" : c < -.3 ? "end" : "middle";
    // The two-line block sits above a top axis, below a bottom one, centred on a side one.
    const ys = sn < -.7 ? y - 12 : sn > .7 ? y + 6 : y - 5;
    const rk = ranks[i] ? rankMark(ranks[i]) : "—";
    return `<text class="pf-radar-l${a.id === sel ? " on" : ""}" style="--i:${i}" data-col="${esc(a.id)}" role="button" tabindex="0" x="${x.toFixed(1)}" y="${ys.toFixed(1)}" text-anchor="${anchor}"><tspan x="${x.toFixed(1)}">${esc(a.label)}</tspan><tspan class="pf-radar-v" x="${x.toFixed(1)}" dy="19">${rk}</tspan></text>`;
  }).join("");
}

/* The caption's denominator is the opening axis's own, not the largest across all six: those
   differ (everyone with a target, but only those with routes), and one caption cannot be right
   for six. The card carries each axis's exact "of N" as the reader taps through. */
/* The denominator and the sample, per axis, for the card's header line -- not a caption under
   the chart. It was a paragraph of its own saying "Out of 120 WRs · 2 games", which repeated the
   lede's own "of 120" a hundred pixels below it and cost the left column 20px it did not have:
   24 of 30 players overflowed the modal by exactly the height of that block and its neighbours.
   In the header it costs nothing, sits beside the stat it belongs to, and still follows a pick,
   which matters because a receiver ranks among everyone with a target on one stat and only among
   those with routes on the next. */
function statMetaText(s, sel, withGames){
  const of = (sheetRank(s.pos, sel, s.row.slug) || [])[1] || 0;
  // Games played only when the stat has no weekly rows to name a window with; otherwise the
  // window says the sample and "2 gm" beside "wk 1" would be two different counts of it.
  return withGames ? t("profile.sheet.metaGames", {of, g: s.row.g}) : t("profile.sheet.meta", {of});
}
