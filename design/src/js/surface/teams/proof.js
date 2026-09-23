/* A waiver card's evidence: three usage stats chosen by position, each with his rank at the
   position that week and an arrow against the week before.

   Everything reads the Grid (USAGE, data/usage.js): the stat's label and format come from the
   grid's own `cols`, the rank is the profile sheet's rankAmong/rankText (surface/profile/facts.js),
   so a card and the sheet never disagree on how a rank or a tie is written. Each slot lists the
   stats it would like, best first; the first one the grid carries for that position is used. A
   route share lands here the week the producer adds one to the weekly grid, with no edit. */
const WV_PROOF = {
  RB: [["snap"], ["car_share", "car"], ["rz"]],
  WR: [["route_pct", "routes", "snap"], ["tgt_pct"], ["adot"]],
  TE: [["route_pct", "routes", "snap"], ["tgt_pct"], ["rz_tgt"]],
  QB: [["dropbacks", "att"], ["rush"], ["rz_att"]],
};

function wvCol(pos, want){
  const cols = (USAGE.cols && USAGE.cols[pos]) || [];
  for (const id of want){ const c = cols.find(x => x.id === id); if (c) return c; }
  return null;
}

/* The latest week the grid has, and the one before it: "this week" is the league's week, not
   his, so a player who sat out reads as no number rather than an older one passed off as new. */
function wvWeeks(){
  const w = (USAGE.weeks || []).slice().sort((a, b) => a - b);
  const now = USAGE.through || w[w.length - 1];
  return [now, w.filter(x => x < now).pop()];
}

function wvWeekValue(slug, id, wk){
  const r = USAGE.rows.find(x => x.slug === slug && x.wk === wk);
  const v = r ? r.v[id] : null;
  return v === undefined ? null : v;
}

/* His rank on one stat among his position that week, as the sheet writes it: "TE5", "TE5*". */
function wvWeekRank(pos, id, slug, wk){
  const by = {};
  USAGE.rows.forEach(r => {
    if (r.pos === pos && r.wk === wk && r.v[id] !== null && r.v[id] !== undefined) by[r.slug] = r.v[id];
  });
  const rk = rankAmong(by, slug);
  return rk ? rankText(pos, rk) : null;
}

function wvTrendHTML(now, before){
  if (now === null || before === null || before === undefined) return "";
  const d = now - before;
  if (Math.abs(d) < 0.05) return `<i class="wvp-t flat" title="${t("waiver.proof.flatTip")}">${t("waiver.proof.flat")}</i>`;
  return d > 0
    ? `<i class="wvp-t up" title="${t("waiver.proof.upTip")}">${t("waiver.proof.up")}</i>`
    : `<i class="wvp-t down" title="${t("waiver.proof.downTip")}">${t("waiver.proof.down")}</i>`;
}

/* The line under his name: where he ranks on the stat his position is sorted by in the Grid. */
function wvUsageRankHTML(r){
  if (typeof USAGE === "undefined" || !USAGE) return "";
  const id = USAGE.rankBy && USAGE.rankBy[r.pos];
  const col = id && wvCol(r.pos, [id]);
  const [wk] = wvWeeks();
  const rank = col && wvWeekRank(r.pos, col.id, r.slug, wk);
  return rank ? `<span class="wvc-urank">${t("waiver.card.usageRank", {rank, stat: esc(col.label), wk})}</span>` : "";
}

/* The back's trend: one proof stat, every week the grid has, as a small line. One series, so no
   legend; the line in the de-emphasis ink and this week's point in the accent (dataviz: a stat
   tile's sparkline). A week he did not play is a gap, not a zero. Each point carries its week and
   value as a tooltip; the value and rank beside the line are the readable copy. */
const WV_SPARK = {w: 96, h: 28, pad: 4};

function wvSparkHTML(vals, weeks, fmt){
  const {w, h, pad} = WV_SPARK, got = vals.filter(v => v !== null);
  if (!got.length) return `<svg class="wvs" viewBox="0 0 ${w} ${h}" aria-hidden="true"></svg>`;
  const lo = Math.min(...got), span = (Math.max(...got) - lo) || 1;
  const x = i => weeks.length < 2 ? w / 2 : pad + i * (w - 2 * pad) / (weeks.length - 1);
  const y = v => h - pad - (v - lo) / span * (h - 2 * pad);
  let d = "", pen = false;
  vals.forEach((v, i) => {
    if (v === null){ pen = false; return; }
    d += `${pen ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)} `; pen = true;
  });
  const dots = vals.map((v, i) => v === null ? "" :
    `<circle class="${i === vals.length - 1 ? "now" : ""}" cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="${i === vals.length - 1 ? 3 : 2}"><title>${t("waiver.trend.point", {wk: weeks[i], v: usageFmt(v, fmt)})}</title></circle>`).join("");
  return `<svg class="wvs" viewBox="0 0 ${w} ${h}" role="img" aria-label="${t("waiver.trend.label")}"><path d="${d.trim()}"/>${dots}</svg>`;
}

function wvTrendsHTML(r){
  if (typeof USAGE === "undefined" || !USAGE || !WV_PROOF[r.pos]) return "";
  const weeks = (USAGE.weeks || []).slice().sort((a, b) => a - b).filter(k => k <= (USAGE.through || k));
  const [wk] = wvWeeks();
  const rows = WV_PROOF[r.pos].map(want => wvCol(r.pos, want)).filter(Boolean).map(c => {
    const vals = weeks.map(k => wvWeekValue(r.slug, c.id, k));
    const now = vals[vals.length - 1];
    const rank = now === null ? null : wvWeekRank(r.pos, c.id, r.slug, wk);
    return `<div class="wvt"><span class="wvp-l">${esc(c.label)}</span>${wvSparkHTML(vals, weeks, c.fmt)}
      <b>${usageFmt(now, c.fmt)}</b><span class="wvp-r">${rank || t("waiver.proof.noRank")}</span></div>`;
  });
  if (!rows.length) return "";
  const span = weeks.length > 1 ? t("waiver.trend.weeks", {a: weeks[0], b: weeks[weeks.length - 1]}) : t("waiver.trend.week", {a: weeks[0]});
  return `<div class="wvc-trends"><span class="wvt-span">${span}</span>${rows.join("")}</div>`;
}

function wvProofHTML(r){
  if (typeof USAGE === "undefined" || !USAGE || !WV_PROOF[r.pos]) return "";
  const [wk, prev] = wvWeeks();
  const cells = WV_PROOF[r.pos].map(want => wvCol(r.pos, want)).filter(Boolean).map(c => {
    const now = wvWeekValue(r.slug, c.id, wk);
    const rank = now === null ? null : wvWeekRank(r.pos, c.id, r.slug, wk);
    return `<div class="wvp"><span class="wvp-l">${esc(c.label)}</span>
      <b>${usageFmt(now, c.fmt)}</b>
      <span class="wvp-r">${rank || t("waiver.proof.noRank")}${wvTrendHTML(now, prev === undefined ? null : wvWeekValue(r.slug, c.id, prev))}</span></div>`;
  });
  return cells.length ? `<div class="wvc-proof">${cells.join("")}</div>` : "";
}
