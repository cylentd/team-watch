/* ============================== LIVE: THE LEAGUE ==============================
   Which league is on screen, every game in it (tap one to see both lineups), and, in a league that
   pays the top half a second win (ESPN's WIN_BONUS_TOP_HALF), the median line and who sits above
   it right now. */

function gdLeaguesHTML(lg){
  if (GD.leagues.length < 2) return "";
  return `<div class="gd-leagues" role="group" aria-label="${t("live.leagues")}">${GD.leagues.map(l =>
    `<button type="button" data-gdleague="${esc(l.key)}" aria-pressed="${l.key === lg.key}">${esc(l.name)}</button>`).join("")}</div>`;
}

function gdGamesHTML(lg, sides, on){
  const ladder = lg.median ? gdLadder(Object.values(sides)) : null;
  const top = ladder ? new Set(ladder.rows.filter(r => r.top).map(r => r.id)) : null;
  const team = (s, win) => `<span class="gd-g-team${win ? " win" : ""}${s.id === lg.me ? " mine" : ""}">
      <span>${esc(s.name)}${top ? ` <small class="${top.has(s.id) ? "top" : ""}">${top.has(s.id) ? t("live.top") : t("live.bottom")}</small>` : ""}</span>
      <b>${gdNum(s.total)}</b></span>`;
  const rows = lg.games.map(g => {
    const a = sides[g[0]], b = sides[g[1]], picked = on && on[0] === g[0] && on[1] === g[1];
    const left = a.playing + a.left + b.playing + b.left;
    return `<button type="button" class="gd-g${picked ? " on" : ""}${g.includes(lg.me) ? " mine" : ""}" data-gdgame="${esc(g.join(","))}">
      ${team(a, a.total > b.total)}${team(b, b.total > a.total)}
      <small class="gd-g-left">${left ? t("live.gameLeft", {n: left}) : t("live.gameFinal")}</small></button>`;
  }).join("");
  return `<section class="gd-games"><h3>${t("live.games", {week: lg.week})}</h3>${rows}</section>`;
}

function gdLadderHTML(lg, sides){
  const {median, rows} = gdLadder(Object.values(sides));
  const cut = rows.findIndex(r => !r.top);
  const row = (r, i) => `<div class="gd-l${r.id === lg.me ? " mine" : ""}">
      <span>${i + 1}</span><span>${esc(r.name)}</span>
      <small class="${r.total >= median ? "up" : "dn"}">${gdSigned(r.total - median)}</small><b>${gdNum(r.total)}</b></div>`;
  const line = `<div class="gd-median"><span>${t("live.median", {n: gdNum(median)})}</span></div>`;
  return `<section class="gd-ladder"><h3>${t("live.medianHead")}</h3>
    ${rows.map((r, i) => (i === cut ? line : "") + row(r, i)).join("")}</section>`;
}
