/* ============================== LEAGUE: RIVALRY AND HISTORY ==============================
   The team on screen against this week's opponent, all-time; then the league's records as a fixed
   list (nothing rotates on its own), then every champion, newest first. */

function lgRivalHTML(id){
  const opp = id ? lgOpp(id) : null;
  if (!opp) return "";
  const h = lgH2H(id, opp), o = lgH2H(opp, id);
  const games = h ? h.w + h.l + h.t : 0;
  const share = games ? Math.round(100 * (h.w + h.t / 2) / games) : 50;
  const big = (side, tid) => side && side.big
    ? t("league.rival.big", {team: lgName(tid), v: lgPts(side.big.v), y: side.big.y, wk: side.big.wk}) : "";
  const foot = !games ? t("league.rival.first")
    : [t("league.rival.since", {y: h.since}), big(h, id), big(o, opp)].filter(Boolean).join(" ");
  return `<section class="lg-sec" aria-label="${t("league.rival.aria")}">
    <h2 class="lg-hd">${t("league.rival.title")}<span>${t("league.rival.sub")}</span></h2>
    <div class="lg-rival">
      <div class="lg-rrow"><span>${lgName(id)}</span><span>${games ? h.w : 0}</span></div>
      <div class="lg-bar" role="img" aria-label="${t("league.rival.bar", {w: games ? h.w : 0, l: games ? h.l : 0})}"><i style="width:${share}%"></i></div>
      <div class="lg-rrow l"><span>${lgName(opp)}</span><span>${games ? h.l : 0}</span></div>
      <p class="lg-foot">${foot}</p>
    </div>
  </section>`;
}

/* Every fact spelled out, one copy key each (assemble.py --check reads literal lookups only). */
function lgFactHTML(f){
  const at = {v: lgPts(f.v), y: f.y, wk: f.wk, n: f.n, team: lgName(f.id), opp: lgName(f.opp)};
  const s = {
    high: () => t("league.fact.high", at), low: () => t("league.fact.low", at), blow: () => t("league.fact.blow", at),
    streak: () => t("league.fact.streak", at), pf: () => t("league.fact.pf", at),
    titles: () => t("league.fact.titles", {n: f.n, teams: (f.ids || []).map(lgName).join(", ")}),
  }[f.k];
  return s ? `<li class="lg-fact">${s()}</li>` : "";
}

function lgHistoryHTML(){
  const champs = LG.champs.map(c => `<li><span class="lg-y">${c.y}</span><span class="lg-cn">${lgName(c.id)}</span>
    <span class="lg-r">${t("league.champs.rec", {w: c.w, l: c.l})}</span></li>`).join("");
  return `<section class="lg-sec" aria-label="${t("league.hist.aria")}">
    <h2 class="lg-hd">${t("league.hist.title")}<span>${t("league.hist.since", {y: LG.since})}</span></h2>
    ${LG.facts.length ? `<ul class="lg-facts">${LG.facts.map(lgFactHTML).join("")}</ul>` : ""}
    ${champs ? `<h3 class="lg-sub">${t("league.champs.title")}</h3><ol class="lg-champs">${champs}</ol>` : ""}
  </section>`;
}
