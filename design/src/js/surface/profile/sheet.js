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
  const v = Object.values(sheetValues(pos, axis));
  if (v.length < 2) return null;
  return Math.max(.04, Math.min(1, 1 - v.filter(x => x > elite).length / (v.length - 1)));
}

function sheetDefaultAxis(s){
  const by = USAGE.rankBy && USAGE.rankBy[s.pos];
  return s.axes.some(a => a.id === by) ? by : s.axes[0].id;
}

/* One axis per stat: his season rank among the position, first place at the rim and last at the
   centre, with a tick on each axis where its elite bar sits. Labels are buttons; the card under
   the sheet shows the chosen stat's number, rank, threshold and week-by-week line. */
function radarHTML(p){
  const s = sheetFor(p);
  if (!s) return "";
  const n = s.axes.length, cx = 200, cy = 170, R = 112;   // 400 x 340: side labels need the room
  const sel = sheetDefaultAxis(s);
  const ranks = s.axes.map(a => sheetRank(s.pos, a.id, p.slug));
  const k = i => { const rk = ranks[i]; return rk && rk[1] > 1 ? Math.max(.04, 1 - (rk[0] - 1) / (rk[1] - 1)) : .04; };
  const ang = i => -Math.PI / 2 + i * 2 * Math.PI / n;
  const xy = (i, r) => [cx + Math.cos(ang(i)) * R * r, cy + Math.sin(ang(i)) * R * r];
  const pts = r => s.axes.map((_, i) => xy(i, r).map(v => v.toFixed(1)).join(",")).join(" ");
  const rings = [.25, .5, .75].map(r => `<polygon class="pf-radar-ring" points="${pts(r)}"/>`).join("")
    + `<polygon class="pf-radar-ring rim" points="${pts(1)}"/>`;
  const spokes = s.axes.map((_, i) => { const [x, y] = xy(i, 1); return `<line class="pf-radar-axis" x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"/>`; }).join("");
  return `<div class="pf-sheet pos-${esc(String(s.pos).toLowerCase())}" data-slug="${esc(p.slug)}">
    <svg class="pf-radar" viewBox="0 0 400 340" role="img" aria-label="${t("profile.sheet.label")}">${rings}${spokes}
      ${eliteBarsHTML(s, ang, xy)}${shapeHTML(s, ranks, k, xy)}${axisLabelsHTML(s, ranks, sel, ang, xy)}</svg>
    <p class="pf-cap pf-quiet">${captionHTML(s, ranks, sel)}</p>
    <div class="pf-stat">${statDetailHTML(s, sel)}</div></div>`;
}

/* An axis he has no number for is left out of the shape rather than pinned at the centre: a
   receiver heatradar has not covered yet is unmeasured on four axes, not the worst in the league
   on them, and a shape pinched to the middle says the second thing. */
function shapeHTML(s, ranks, k, xy){
  const idx = s.axes.map((_, i) => i).filter(i => ranks[i] !== null);
  const pts = idx.map(i => xy(i, k(i)).map(v => v.toFixed(1)).join(",")).join(" ");
  const dots = idx.map(i => {
    const [x, y] = xy(i, k(i));
    return `<circle class="pf-radar-dot" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.5"/>`;
  }).join("");
  return `<polygon class="pf-radar-shape" points="${pts}"/>${dots}`;
}

/* The elite bar, as a short dash across its own axis: a shape reaching past it is elite there. */
function eliteBarsHTML(s, ang, xy){
  return s.axes.map((a, i) => {
    const er = eliteRadius(s.pos, a.id, a.elite);
    if (er === null) return "";
    const [x, y] = xy(i, er), dx = -Math.sin(ang(i)) * 6, dy = Math.cos(ang(i)) * 6;
    return `<line class="pf-radar-bar" x1="${(x - dx).toFixed(1)}" y1="${(y - dy).toFixed(1)}" x2="${(x + dx).toFixed(1)}" y2="${(y + dy).toFixed(1)}"/>`;
  }).join("");
}

function axisLabelsHTML(s, ranks, sel, ang, xy){
  return s.axes.map((a, i) => {
    const [x, y] = xy(i, 1.2), c = Math.cos(ang(i)), sn = Math.sin(ang(i));
    const anchor = c > .3 ? "start" : c < -.3 ? "end" : "middle";
    // The two-line block sits above a top axis, below a bottom one, centred on a side one.
    const ys = sn < -.7 ? y - 12 : sn > .7 ? y + 6 : y - 5;
    const rk = ranks[i] ? rankMark(ranks[i]) : "—";
    return `<text class="pf-radar-l${a.id === sel ? " on" : ""}" data-col="${esc(a.id)}" role="button" tabindex="0" x="${x.toFixed(1)}" y="${ys.toFixed(1)}" text-anchor="${anchor}"><tspan x="${x.toFixed(1)}">${esc(a.label)}</tspan><tspan class="pf-radar-v" x="${x.toFixed(1)}" dy="17">${rk}</tspan></text>`;
  }).join("");
}

/* The caption's denominator is the opening axis's own, not the largest across all six: those
   differ (everyone with a target, but only those with routes), and one caption cannot be right
   for six. The card carries each axis's exact "of N" as the reader taps through. */
function captionHTML(s, ranks, sel){
  const of = (ranks[s.axes.findIndex(a => a.id === sel)] || [])[1] || 0;
  const tied = ranks.some(rk => rk && rk[2]) ? ` · ${t("profile.sheet.tied")}` : "";
  return t("profile.sheet.caption", {pos: esc(s.pos), of, g: s.row.g}) + tied;
}

/* His weeks on one stat, oldest first. The Grid carries every sheet stat weekly as well as
   season-to-date, so the card's line and the radar's radius are the same number over different
   windows -- never two different definitions of the stat. */
function statWeeks(slug, axis){
  if (typeof USAGE === "undefined" || !USAGE) return [];
  return USAGE.rows.filter(r => r.slug === slug && r.v[axis] !== null && r.v[axis] !== undefined)
    .sort((a, b) => a.wk - b.wk);
}

/* The card under the sheet for one stat: his season number, his rank on it, the elite bar and
   whether he clears it, and the weeks as a line. */
function statDetailHTML(s, axis){
  const a = s.axes.find(x => x.id === axis) || s.axes[0];
  const slug = s.row.slug, v = s.row.v[a.id];
  const rk = sheetRank(s.pos, a.id, slug);
  const rank = rk ? `<small class="pf-stat-r">${rankMarkOf(rk)}</small>` : "";
  const bar = a.elite === null || a.elite === undefined || v === null || v === undefined ? ""
    : `<small class="pf-stat-d ${v >= a.elite ? "up" : "down"}">${t("profile.stat.elite", {n: usageFmt(a.elite, a.fmt)})}</small>`;
  const wk = statWeeks(slug, a.id);
  const line = wk.length ? sparkHTML(wk.map(r => r.v[a.id]), 160, 36) : "";
  const weeks = wk.length
    ? `<span class="pf-stat-wk">${t("profile.stat.weeks", {a: wk[0].wk, b: wk[wk.length - 1].wk})}</span>` : "";
  return `<div class="pf-stat-h"><span class="pf-stat-l">${esc(a.label)}</span>${weeks}</div>
    <b>${usageFmt(v, a.fmt)}</b><span class="pf-stat-side">${rank}${bar}</span>${line}`;
}

/* Tapping a stat on the sheet swaps the card under it and moves the highlight. */
function wireSheet(d){
  const el = d.querySelector(".pf-sheet");
  if (!el) return;
  const s = sheetFor({slug: el.dataset.slug});
  if (!s) return;
  const pick = node => {
    el.querySelectorAll(".pf-radar-l").forEach(x => x.classList.toggle("on", x === node));
    el.querySelector(".pf-stat").innerHTML = statDetailHTML(s, node.dataset.col);
  };
  el.querySelectorAll(".pf-radar-l").forEach(node => {
    node.addEventListener("click", () => pick(node));
    node.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); pick(node); } });
  });
}
