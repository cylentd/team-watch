/* The fourth profile section: the next opponent. Leads with the verdict. An untested verdict
   (WR/TE, METHODOLOGY 12.36-12.39) always reads "on paper" with its UNTESTED tag beside it; the
   tag's title and tap show `method`. A tested one (the RB position factor) shows `method` quietly. */
function verdictLineHTML(nx){
  if (!VERDICT_CLASS[nx.verdict]) return `<p class="pf-cap pf-quiet">${t("profile.next.noCall")}</p>`;
  const pill = `<span class="pf-v ${VERDICT_CLASS[nx.verdict]}">${verdictWord(nx.verdict)}</span>`;
  if (nx.tested) return `<div class="pf-verdict">${pill}</div>`;   // its method line follows the basis
  return `<div class="pf-verdict">${pill}<span class="pf-onpaper">${t("profile.next.onPaper")}</span>
      <button type="button" class="pf-untested" title="${esc(nx.method)}" aria-expanded="false" aria-controls="pf-method">${FLASK_ICON}${t("profile.next.untested")}</button>
    </div>
    <p class="pf-cap pf-quiet" id="pf-method" hidden>${esc(nx.method)}</p>`;
}

function zonesTableHTML(prof, nx){
  if (prof.pos !== "WR" && prof.pos !== "TE") return "";
  if (!nx.zones || !nx.zones.length) return `<p class="pf-cap pf-quiet">${t("profile.next.zonesSilent")}</p>`;
  return `<table class="pf-table">
    <thead><tr><th>${t("profile.next.colZone")}</th><th>${t("profile.next.colIndex")}</th><th>${t("profile.next.colRank")}</th><th>${t("profile.next.colFaced")}</th></tr></thead>
    <tbody>${nx.zones.map(z => `<tr><th scope="row">${zoneWord(z.zone)}</th><td>${Number(z.def_index).toFixed(2)}x</td><td>#${z.rank}<small>/${z.of}</small></td><td>${z.targets}</td></tr>`).join("")}</tbody>
  </table>`;
}

function nextHTML(prof){
  const nx = prof.next;
  if (!nx) return secHTML(t("profile.next.labelBare"), `<p class="pf-cap pf-quiet">${t("profile.next.bye")}</p>`);
  const where = nx.home ? t("profile.next.home") : t("profile.next.away");
  const stale = nx.dc_same === false
    ? `<span class="pf-stale" title="${t("profile.next.staleTip", {season: nx.man_season})}">${t("profile.next.stale")}</span>` : "";
  const man = nx.man_pct === null || nx.man_pct === undefined ? "" : `
    <div class="pf-metric">
      <div class="pf-metric-h"><span>${t("profile.next.man", {season: nx.man_season})}</span>${stale}</div>
      ${shareBarHTML("", nx.man_pct, nx.man_pct_league, false)}
    </div>`;
  const rz = !nx.rz ? "" : `
    <div class="pf-metric">
      <div class="pf-metric-h"><span>${t("profile.next.rz", {n: nx.rz.faced})}</span><span class="pf-word">${esc(nx.rz.verdict || "")}</span></div>
      ${shareBarHTML("", nx.rz.rate, nx.rz.league_rate, false)}
    </div>`;
  const f = nx.factor;
  const factor = !f ? "" : `
    <div class="pf-factor">
      <span>${t("profile.next.factor", {pos: esc(prof.pos)})}</span>
      <b>${Number(f.factor).toFixed(2)}x</b>
      <span>${t("profile.next.factorRank", {rank: f.rank, of: f.of})}</span>
      <span class="pf-word">${esc(f.verdict || "")}</span>
    </div>`;
  return secHTML(t("profile.next.label", {wk: nx.week, where, opp: esc(nx.opp)}),
    verdictLineHTML(nx)
    + `<p class="pf-basis">${esc(nx.basis || "")}</p>`
    + (nx.tested && VERDICT_CLASS[nx.verdict] ? `<p class="pf-cap">${esc(nx.method)}</p>` : "")
    + zonesTableHTML(prof, nx)
    + `<div class="pf-metrics">${man}${rz}</div>`
    + factor,
    t("profile.next.legend"));
}
