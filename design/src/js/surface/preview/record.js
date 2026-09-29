/* ------------------------------------------------------------------
   PREVIEW's record (2026-09-29, storyboard option A; David: "going with safe is just saying we go
   with Vegas"). A card atop the slate keeps Claude's score against the spread: the season, by
   confidence, and how often his win % landed closer to the result than the market's. A tap opens
   every week (a table, then each week's games) in the slate's place on a phone, the dossier's on a
   desktop, as a layer Back closes (chrome/layers.js). Before a graded game, one line says when the
   record starts, never a row of zeros.

   Colour map: --up / --down only a graded HIT / MISS; a push and a pass are grey. The chips are the
   slate's (lime is Claude).
------------------------------------------------------------------ */
const pvRecByConf = r => [["strong", t("preview.conf.strong")], ["solid", t("preview.conf.solid")], ["lean", t("preview.conf.lean")]]
  .map(([c, label]) => `<span>${label} <b>${pvWL(r.by_conf[c])}</b></span>`).join("");

/* The card: "CLAUDE VS THE SPREAD · EVERY WEEK ›", 25–21–2 and 54% hit, by confidence, win % closer.
   The weeks it covers are the sheet's rows. */
function pvRecordHTML(){
  const r = pvRecord();
  if (!r || !r.weeks.length) return `<p class="pv-rec0">${t("preview.rec.empty", {n: LIVE_PREVIEW.week})}</p>`;
  const hit = pvHit(r.ats);
  return `<button class="pv-rec${PV_REC ? " cur" : ""}" data-pvrec aria-expanded="${PV_REC}">
    <span class="pv-rec-t"><span>${t("preview.rec.title")}</span><span class="pv-rec-more">${t("preview.rec.more")}</span></span>
    <span class="pv-rec-big"><b>${pvWL(r.ats)}</b><small>${t("preview.rec.vs")}</small>${hit != null ? `<em>${t("preview.rec.hit", {n: hit})}</em>` : ""}</span>
    <span class="pv-rec-row">${pvRecByConf(r)}</span>
    ${r.graded ? `<span class="pv-rec-row">${t("preview.rec.closer", {n: r.closer, m: r.graded})}</span>` : ""}${pvRecBlind(r.blind)}</button>`;
}

/* The blind number's line, once it has a graded game: its own record against the spread, and how far
   its margin landed from the final beside the market's (points, on average). */
const pvRecBlind = b => b ? `<span class="pv-rec-row"><span>${t("preview.rec.blind", {wl: `<b>${pvWL(b.ats)}</b>`})}</span>${
  b.mae_blind != null && b.mae_market != null ? `<span>${t("preview.rec.mae", {b: b.mae_blind.toFixed(1), m: b.mae_market.toFixed(1)})}</span>` : ""}</span>` : "";

const pvOf = (n, m) => m ? t("preview.rec.of", {n, m}) : "–";

function pvRecTable(r){
  const tr = (label, ats, strong, fav, favOf, closer, graded) => `<tr><th scope="row">${label}</th><td>${pvWL(ats)}</td>
    <td>${strong ? pvWL(strong) : "–"}</td><td>${pvOf(fav, favOf)}</td><td>${pvOf(closer, graded)}</td></tr>`;
  return `<table class="pv-rt">
    <thead><tr><th>${t("preview.rec.col.week")}</th><th>${t("preview.rec.col.ats")}</th><th>${t("preview.conf.strong")}</th>
      <th>${t("preview.rec.col.fav")}</th><th>${t("preview.rec.col.closer")}</th></tr></thead>
    <tbody>${r.weeks.map(w => tr(w.week, w.ats, w.strong, w.fav, w.fav_of, w.closer, w.graded)).join("")}</tbody>
    <tfoot>${tr(t("preview.rec.season"), r.ats, r.by_conf.strong, r.fav, r.fav_of, r.closer, r.graded)}</tfoot></table>`;
}

/* One graded game: the matchup and the final (winner first), the HIT / MISS / PUSH / PASS tag, then
   Claude's side and chip under it. */
function pvRecGame(g){
  const res = g.result || {}, hw = res.home > res.away, w = hw ? g.home : g.away;
  const fin = res.home == null ? "" : `${esc(w)} ${hw ? res.home : res.away}–${hw ? res.away : res.home}`;
  const side = g.side ? `<span class="pv-side">${pvSideWords(g.side, g.side === g.home ? g.spread_home : -g.spread_home)}</span>` : "";
  const tag = {hit: ["hit", t("preview.rec.hit.hit")], miss: ["miss", t("preview.rec.hit.miss")], push: ["push", t("preview.rec.hit.push")]}[g.hit]
    || ["pass", t("preview.rec.hit.pass")];
  return `<li class="pv-rg"><span class="pv-rg-m">${esc(g.away)} @ ${esc(g.home)}</span><span class="pv-rg-f">${fin}</span>
    <b class="pv-hit ${tag[0]}">${tag[1]}</b><span class="pv-rg-a">${side}${pvConfHTML(g.side ? g.conf : null)}</span></li>`;
}

/* Every week: the table, what "closer" means, then each week's games, the newest open. */
function pvRecSheetHTML(){
  const r = pvRecord();
  const weeks = r.weeks.map((w, j) => `<section class="pvd-row full"><details class="pv-rw"${j === 0 ? " open" : ""}>
    <summary>${t("preview.rec.weekgames", {n: w.week, ats: pvWL(w.ats)})}</summary>
    <ul class="pv-rgl">${w.games.map(pvRecGame).join("")}</ul></details></section>`).join("");
  return `<section class="pv-rz" aria-label="${t("preview.rec.sheet", {n: r.through})}">
    <button class="pv-back" data-pvrecback>${t("preview.back")}</button>
    <article class="pvd-card pv-rcard"><section class="pvd-row full"><h3 class="pvd-rt">${t("preview.rec.sheet", {n: r.through})}</h3>
      ${pvRecTable(r)}
      <p class="pv-note">${t("preview.rec.favs", {n: r.fav, m: r.fav_of, c: r.covered, g: r.n})}</p>
      <p class="pv-note">${t("preview.rec.explain")}</p>
      ${r.blind ? `<p class="pv-note">${t("preview.rec.blindexplain")}</p>` : ""}</section>${weeks}</article></section>`;
}
