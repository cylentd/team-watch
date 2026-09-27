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
  // Yahoo re-ids every team each season, so its head-to-head is this season's only (LG.scope).
  const span = LG.scope === "season" ? t("league.rival.season") : t("league.rival.since", {y: h && h.since});
  const foot = !games ? t("league.rival.first") : [span, big(h, id), big(o, opp)].filter(Boolean).join(" ");
  return `<section class="lg-sec" aria-label="${t("league.rival.aria")}">
    <h2 class="lg-hd">${t("league.rival.title")}<span>${t("league.rival.sub")}</span></h2>
    <div class="lg-rival">
      <div class="lg-rrow"><span>${lgName(id)}</span><span>${games ? h.w : 0}</span></div>
      ${games ? `<div class="lg-bar" role="img" aria-label="${t("league.rival.bar", {w: h.w, l: h.l})}"><i style="width:${share}%"></i></div>` : ""}
      <div class="lg-rrow l"><span>${lgName(opp)}</span><span>${games ? h.l : 0}</span></div>
      <p class="lg-foot">${foot}</p>
    </div>
  </section>`;
}

/* Every fact spelled out, one copy key each (assemble.py --check reads literal lookups only). */
/* A team in a fact or a champion row. ESPN: today's name by id. Yahoo, a past season: the name it had
   that year, and "now ..." when that manager's team is called something else today. */
function lgWho(id, name){
  const now = id != null && LG.teams.find(x => x.id === id);
  if (!name) return now ? esc(now.name) : t("league.former");
  return now && now.name !== name ? t("league.who.now", {name: esc(name), now: esc(now.name)}) : esc(name);
}

function lgFactHTML(f){
  const at = {v: lgPts(f.v), y: f.y, wk: f.wk, n: f.n, team: lgWho(f.id, f.name), opp: lgWho(f.opp, f.oppname)};
  const s = {
    high: () => t("league.fact.high", at), low: () => t("league.fact.low", at), blow: () => t("league.fact.blow", at),
    streak: () => t("league.fact.streak", at), pf: () => t("league.fact.pf", at),
    titles: () => t("league.fact.titles", {n: f.n, teams: (f.ids || []).map(lgName).join(", ")}),
  }[f.k];
  return s ? `<li class="lg-fact">${s()}</li>` : "";
}

/* A champion by today's name (ESPN, `id`) or by the name it won under (Yahoo, `name`); a Yahoo
   podium carries no record. */
function lgChampHTML(c){
  const who = lgWho(c.id, c.name);
  const rec = c.w != null ? t("league.champs.rec", {w: c.w, l: c.l}) : "";
  return `<li><span class="lg-y">${c.y}</span><span class="lg-cn">${who}</span><span class="lg-r">${rec}</span></li>`;
}

function lgHistoryHTML(){
  const champs = LG.champs.map(lgChampHTML).join("");
  return `<section class="lg-sec" aria-label="${t("league.hist.aria")}">
    <h2 class="lg-hd">${t("league.hist.title")}<span>${t("league.hist.since", {y: LG.since})}</span></h2>
    ${LG.facts.length ? `<ul class="lg-facts">${LG.facts.map(lgFactHTML).join("")}</ul>` : ""}
    ${champs ? `<h3 class="lg-sub">${t("league.champs.title")}</h3><ol class="lg-champs">${champs}</ol>` : ""}
  </section>`;
}
