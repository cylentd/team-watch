/* The Compare sheet's strips: one bar per stat, split into a cell per player on the cards' own
   columns, the stat's name above it (STYLE.md "Alignment": a lane read across centres its value;
   a label sits above what it labels). The best of a strip is bold. A player with no number for a
   stat shows a dash, so a waiver pickup with no profile still sits in every strip he has data for.

   Red zone is his share of the team's red-zone plays, targets and carries together, where the
   profile carries both team totals (David, 2026-09-30: a receiver on a team that runs near the goal
   line looks good on targets alone); else of targets. */
function cmpRz(p){
  const prof = profileFor(p), r = prof && prof.red_zone;
  if (!r) return null;
  const tt = r.team_targets, tc = r.team_carries;
  if (typeof tt === "number" && typeof tc === "number" && tt + tc > 0) return ((r.targets || 0) + (r.carries || 0)) / (tt + tc);
  return typeof tt === "number" && tt > 0 ? (r.targets || 0) / tt : null;
}

function cmpStripHTML(label, cells, best){
  const vals = cells.map(c => c ? c.v : null).filter(v => v !== null);
  const top = vals.length > 1 && best ? (best === "low" ? Math.min(...vals) : Math.max(...vals)) : null;
  const cell = c => !c ? `<span class="cmp-v none">—</span>`
    : `<span class="cmp-v${c.v === top ? " best" : ""}">${c.txt}</span>`;
  return `<div class="cmp-row-s"><span class="cmp-l">${label}</span><div class="cmp-strip">${cells.map(cell).join("")}</div></div>`;
}

/* Whose share: targets for receivers, carries for backs, "team share" when the set is mixed. */
function cmpShareLabel(ps){
  const pos = new Set(ps.map(p => p.pos));
  if (pos.size > 1) return t("profile.compare.share");
  return [...pos][0] === "RB" ? t("profile.compare.shareCar") : t("profile.compare.shareTgt");
}

function cmpStripsHTML(ps){
  const opp = ps.map(p => { const rk = cmpRankRow(p), d = rk && rk.opp ? seasonDefRank(rk.opp, p.pos) : null;
    return d ? {v: d[0], txt: `${ordinal(d[0])}<small>${esc(rk.opp)}</small>`} : null; });
  const share = ps.map(p => { const r = poolRow(p.slug);
    return r && ledeShareLabel(p.pos) && typeof r.share === "number" ? {v: r.share, txt: Math.round(r.share) + "%"} : null; });
  const rz = ps.map(p => { const v = cmpRz(p); return v === null ? null : {v, txt: Math.round(v * 100) + "%"}; });
  const last = ps.map((p, i) => { const rows = gamelogRows(p.slug).slice(-3);
    return rows.length ? {v: null, txt: cmpSparkHTML(rows, i)} : null; });
  return `<div class="cmp-strips" style="--n:${ps.length}">`
    + cmpStripHTML(t("profile.compare.opp"), opp, "low")
    + cmpStripHTML(cmpShareLabel(ps), share, "high")
    + cmpStripHTML(t("profile.compare.rz"), rz, "high")
    + cmpStripHTML(t("profile.compare.last"), last, null) + `</div>`;
}

/* The last three weeks as bars in his colour, on one scale across the sheet, his mean beside them. */
function cmpSparkHTML(rows, i){
  const all = cmpPlayers().flatMap(p => gamelogRows(p.slug).slice(-3).map(r => r.pts || 0));
  const hi = Math.max(1, ...all), mean = rows.reduce((s, r) => s + (r.pts || 0), 0) / rows.length;
  const bars = rows.map(r => `<i style="height:${Math.max(2, Math.round((r.pts || 0) / hi * 20))}px" title="${t("profile.compare.weekPts", {wk: r.wk, pts: (r.pts || 0).toFixed(1)})}"></i>`).join("");
  return `<span class="cmp-spark cmp-s${i}">${bars}</span><small>${mean.toFixed(1)}</small>`;
}
