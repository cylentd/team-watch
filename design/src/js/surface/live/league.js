/* ============================== LIVE: THE LEAGUE ==============================
   Which league is on screen, every game in it as a row of two boxes, one team each (tap either to
   see both lineups), and every team's total against the week's median. Only a league that pays the
   top half a second win (ESPN's WIN_BONUS_TOP_HALF) tags TOP/BOT and draws the line in lime; in
   the others the ranking is for bragging and the line is grey. */

function gdLeaguesHTML(lg){
  if (GD.leagues.length < 2) return "";
  return `<div class="gd-leagues" role="group" aria-label="${t("live.leagues")}">${GD.leagues.map(l =>
    `<button type="button" data-gdleague="${esc(l.key)}" aria-pressed="${l.key === lg.key}">${esc(l.name)}</button>`).join("")}</div>`;
}

/* One slot per starter, in lineup order: filled grey when he is done, lime while he plays, empty
   until his game starts. Which side still has a man going reads off the box it sits in. */
const GD_METER = {complete: "", in_game: "on", pre_game: "pre"};
const gdMeterHTML = s => `<span class="gd-meter" aria-hidden="true">${s.rows.map(r => `<i class="${GD_METER[r.state]}"></i>`).join("")}</span>`;

const GD_LOCK = `<svg viewBox="0 0 12 12" aria-hidden="true"><rect x="2.5" y="5.5" width="7" height="5" rx="1"/><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5"/></svg>`;

/* A game's state as a tag: LIVE and who is left while anyone plays, how many are left before,
   LOCKED once every starter on both sides is done. */
function gdGameState(a, b){
  const playing = a.playing + b.playing, left = playing + a.left + b.left;
  if (playing) return `<small class="gd-gs live">${t("live.state.live", {n: left})}</small>`;
  if (left) return `<small class="gd-gs">${t("live.state.left", {n: left})}</small>`;
  return `<small class="gd-gs">${GD_LOCK}${t("live.state.locked")}</small>`;
}

function gdGamesHTML(lg, sides, on){
  const ladder = lg.median ? gdLadder(Object.values(sides)) : null;
  const top = ladder ? new Set(ladder.rows.filter(r => r.top).map(r => r.id)) : null;
  const box = (s, win) => `<span class="gd-bx${win ? " win" : ""}${s.id === lg.me ? " mine" : ""}">
      <span>${esc(s.name)}</span><span class="gd-bx-foot"><b>${gdNum(s.total)}</b>${top
        ? `<small class="${top.has(s.id) ? "top" : ""}">${top.has(s.id) ? t("live.top") : t("live.bottom")}</small>` : ""}</span>
      ${gdMeterHTML(s)}</span>`;
  const rows = lg.games.map(g => {
    const a = sides[g[0]], b = sides[g[1]], picked = on && on[0] === g[0] && on[1] === g[1];
    return `<button type="button" class="gd-g${picked ? " on" : ""}${g.includes(lg.me) ? " mine" : ""}" data-gdgame="${esc(g.join(","))}"
      aria-pressed="${!!picked}">${box(a, a.total > b.total)}${box(b, b.total > a.total)}${gdGameState(a, b)}</button>`;
  }).join("");
  const key = `<p class="gd-key"><span><i></i>${t("live.key.done")}</span><span><i class="on"></i>${t("live.key.playing")}</span>`
    + `<span><i class="pre"></i>${t("live.key.pre")}</span></p>`;
  return `<section class="gd-games gd-card"><h3>${t("live.games", {week: lg.week})}</h3>${rows}${key}</section>`;
}

function gdLadderHTML(lg, sides){
  const {median, rows} = gdLadder(Object.values(sides));
  const cut = rows.findIndex(r => !r.top);
  const row = (r, i) => `<div class="gd-l${r.id === lg.me ? " mine" : ""}">
      <span>${i + 1}</span><span>${esc(r.name)}</span>
      <small class="${r.total >= median ? "up" : "dn"}">${gdSigned(r.total - median)}</small><b>${gdNum(r.total)}</b></div>`;
  const line = `<div class="gd-median${lg.median ? "" : " quiet"}"><span>${t("live.median", {n: gdNum(median)})}</span></div>`;
  const head = lg.median ? t("live.medianHead") : `${t("live.rankHead")} <em>${t("live.rankNote")}</em>`;
  return `<section class="gd-ladder gd-card"><h3><span>${head}</span></h3>
    ${rows.map((r, i) => (i === cut ? line : "") + row(r, i)).join("")}</section>`;
}
