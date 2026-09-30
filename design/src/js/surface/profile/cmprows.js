/* The Compare sheet's rows: one number per player per row, the best of each row lit. Each row
   reads a source the profile already reads and shows a dash where a player has none, so a waiver
   pickup with no profile still sits in every row he has data for.

   The red zone is his share of the team's red-zone plays, targets and carries together, where the
   profile carries both team totals (David, 2026-09-30: a receiver on a team that runs near the goal
   line looks good on targets alone). Where it carries only the targets, the share is of targets and
   the cell says so. */
function cmpRz(p){
  const prof = profileFor(p), r = prof && prof.red_zone;
  if (!r) return null;
  const tt = r.team_targets, tc = r.team_carries;
  if (typeof tt === "number" && typeof tc === "number" && tt + tc > 0){
    const n = (r.targets || 0) + (r.carries || 0);
    return {v: n / (tt + tc), n, of: tt + tc, unit: t("profile.compare.rzPlays")};
  }
  if (typeof tt === "number" && tt > 0) return {v: (r.targets || 0) / tt, n: r.targets || 0, of: tt, unit: t("profile.compare.rzTargets")};
  return null;
}

function cmpStatHTML(label, cells, best, note){
  const vals = cells.map(c => c ? c.v : null).filter(v => v !== null);
  const top = vals.length > 1 ? (best === "low" ? Math.min(...vals) : Math.max(...vals)) : null;
  const cell = (c, i) => !c ? `<span class="cmp-v cmp-s${i} none">—</span>`
    : `<span class="cmp-v cmp-s${i}${c.v === top ? " best" : ""}">${c.txt}${c.sub ? `<small>${c.sub}</small>` : ""}</span>`;
  return `<div class="cmp-stat"><div class="cmp-stat-h lbl"><span>${label}</span>${note ? `<span>${note}</span>` : ""}</div>
    <div class="cmp-vals">${cells.map(cell).join("")}</div></div>`;
}

function cmpLastHTML(ps){
  const logs = ps.map(p => gamelogRows(p.slug).slice(-3));
  const hi = Math.max(1, ...logs.flat().map(r => r.pts || 0));
  const cell = (rows, i) => !rows.length ? `<span class="cmp-v cmp-s${i} none">—</span>`
    : `<span class="cmp-v cmp-s${i} cmp-spark">${rows.map(r => `<i style="height:${Math.max(2, Math.round((r.pts || 0) / hi * 22))}px" title="${t("profile.compare.week", {wk: r.wk, pts: (r.pts || 0).toFixed(1)})}"></i>`).join("")}<small>${(rows[rows.length - 1].pts || 0).toFixed(1)}</small></span>`;
  return `<div class="cmp-stat"><div class="cmp-stat-h lbl"><span>${t("profile.compare.last")}</span><span>${t("profile.compare.lastNote")}</span></div>
    <div class="cmp-vals">${logs.map(cell).join("")}</div></div>`;
}

function cmpRowsHTML(ps){
  const proj = ps.map(p => { const v = projFor(p), rk = cmpRankRow(p);
    return v === null ? null : {v, txt: v.toFixed(1), sub: rk ? esc(rk.pos) + rk.rank : ""}; });
  const opp = ps.map(p => { const rk = cmpRankRow(p), d = rk && rk.opp ? seasonDefRank(rk.opp, p.pos) : null;
    return d ? {v: d[0], txt: esc(rk.opp), sub: ordinal(d[0])} : null; });
  const share = ps.map(p => { const r = poolRow(p.slug), lab = ledeShareLabel(p.pos);
    return r && lab && typeof r.share === "number" ? {v: r.share, txt: Math.round(r.share) + "%", sub: esc(lab)} : null; });
  const rz = ps.map(p => { const r = cmpRz(p);
    return r ? {v: r.v, txt: Math.round(r.v * 100) + "%", sub: `${r.n}/${r.of} ${r.unit}`} : null; });
  return cmpStatHTML(t("profile.compare.proj"), proj, "high", t("profile.compare.projNote"))
    + cmpStatHTML(t("profile.compare.opp"), opp, "low", t("profile.compare.oppNote"))
    + cmpStatHTML(t("profile.compare.share"), share, "high")
    + cmpStatHTML(t("profile.compare.rz"), rz, "high")
    + cmpLastHTML(ps);
}
