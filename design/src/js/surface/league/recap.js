/* ============================== LEAGUE: THE WEEK ==============================
   The recap of one decided week: the chips pick the week, the team on screen's own game comes
   first, then six awards the league chat argues about, two to a row on a phone. */

/* Every award label spelled out: assemble.py --check finds a copy key only as a literal lookup. */
const lgAwardLabel = k => ({top: t("league.award.top"), low: t("league.award.low"), blow: t("league.award.blow"),
  close: t("league.award.close"), luck: t("league.award.luck"), unluck: t("league.award.unluck")})[k];

function lgAwardHTML(k, a){
  if (!a) return "";
  const v = k === "blow" || k === "close" ? `+${lgPts(a.v)}`
    : k === "luck" ? `${lgPts(a.v)}<small>${t("league.award.won")}</small>`
    : k === "unluck" ? `${lgPts(a.v)}<small>${t("league.award.lost")}</small>` : lgPts(a.v);
  return `<div class="lg-aw"><span class="lg-aw-k">${lgAwardLabel(k)}</span>
    <span class="lg-aw-t">${lgName(a.id)}</span><span class="lg-aw-v">${v}</span></div>`;
}

/* The team on screen's game that week: both scores, the winner in full ink, then one line with the
   margin and the all-time series against that opponent. */
function lgYoursHTML(w, id){
  const g = w.games.find(x => x.a === id || x.b === id);
  if (!g) return `<div class="lg-yours"><span class="lg-lbl">${t("league.yours.label")}</span><p class="lg-line">${t("league.yours.none")}</p></div>`;
  const mine = g.a === id ? g.ap : g.bp, theirs = g.a === id ? g.bp : g.ap, opp = g.a === id ? g.b : g.a;
  const m = lgPts(Math.abs(mine - theirs));
  const res = mine > theirs ? t("league.yours.won", {m}) : mine < theirs ? t("league.yours.lost", {m}) : t("league.yours.tied");
  const h = lgH2H(id, opp);
  const series = h ? (h.t ? t("league.yours.seriesTies", {w: h.w, l: h.l, t: h.t, team: lgName(opp)})
    : t("league.yours.series", {w: h.w, l: h.l, team: lgName(opp)})) : "";
  const row = (tid, pts, win) => `<span class="${win ? "w" : "l"}">${lgName(tid)}</span><span class="lg-pts${win ? "" : " l"}">${lgPts(pts)}</span>`;
  return `<div class="lg-yours"><span class="lg-lbl">${t("league.yours.label")}</span>
    <div class="lg-score">${row(id, mine, mine >= theirs)}${row(opp, theirs, theirs >= mine)}</div>
    <p class="lg-line">${res} ${series}</p></div>`;
}

function lgRecapHTML(id){
  const w = lgWeek();
  if (!w) return `<section class="lg-sec"><p class="lg-none">${t("league.empty")}</p></section>`;
  const chips = LG.weeks.map(x => `<button class="chip" data-lgweek="${x.week}" aria-pressed="${x === w}">${t("league.recap.wk", {n: x.week})}</button>`).join("");
  // No heading: the pressed chip names the week, and the hero already names the league. The first
  // score then sits about 60px higher on a phone (STYLE.md: the data starts by ~200px).
  return `<section class="lg-sec" aria-label="${t("league.recap.aria")}">
    <div class="setrow lg-weeks" role="group" aria-label="${t("league.recap.weeks")}">${chips}</div>
    ${id ? lgYoursHTML(w, id) : ""}
    <div class="lg-awards">${["top", "low", "blow", "close", "luck", "unluck"].map(k => lgAwardHTML(k, w.awards[k])).join("")}</div>
  </section>`;
}
