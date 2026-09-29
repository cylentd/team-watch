/* ============================== LIVE: THE LEAGUE ==============================
   Which league is on screen, every game in it as its state over a row of two boxes, one team each
   (tap either to see both lineups), and every team's total against the week's median. Only a league
   that pays the top half a second win (ESPN's WIN_BONUS_TOP_HALF) draws the line in lime; in the
   others the ranking is for bragging and the line is grey. */

function gdLeaguesHTML(lg){
  if (GD.leagues.length < 2) return "";
  return `<div class="gd-leagues" role="group" aria-label="${t("live.leagues")}">${GD.leagues.map(l =>
    `<button type="button" data-gdleague="${esc(l.key)}" aria-pressed="${l.key === lg.key}">${esc(l.name)}</button>`).join("")}</div>`;
}

const GD_LOCK = `<svg viewBox="0 0 12 12" aria-hidden="true"><rect x="2.5" y="5.5" width="7" height="5" rx="1"/><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5"/></svg>`;
const GD_CUP = `<svg class="gd-cup" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 2.5h6v3.5a3 3 0 0 1-6 0z"/><path d="M5 3.5H3a2 2 0 0 0 2 3M11 3.5h2a2 2 0 0 1-2 3M8 9v2.5M5.5 13.5h5"/></svg>`;

/* A game's state, on the line above its two boxes so it can only belong to them: LIVE and how
   many are left while anyone plays (lime), how many are left before kickoff, or a lock and FINAL
   once every starter on both sides is done. Every game has one, so every game has the same shape. */
function gdGameState(a, b){
  const playing = a.playing + b.playing, left = playing + a.left + b.left;
  if (playing) return `<small class="gd-gs live">${t("live.state.live", {n: left})}</small>`;
  if (left) return `<small class="gd-gs">${t("live.state.left", {n: left})}</small>`;
  return `<small class="gd-gs">${GD_LOCK}${t("live.state.final")}</small>`;
}

/* Each box is a name and a score, nothing else (DESIGN.md "Say it in a shape": two things per
   repeated item). The side behind is grey; a finished game's winner gets the trophy, which also
   says the game is over. Who is top or bottom half is the ranking card's job, right below. */
function gdGamesHTML(lg, sides, on){
  const box = (s, cls, cup) => `<span class="gd-bx${cls}">
      <span class="gd-bx-n"><span>${esc(s.name)}</span>${cup ? GD_CUP : ""}</span><b>${gdNum(s.total)}</b></span>`;
  const rows = lg.games.map(g => {
    const a = sides[g[0]], b = sides[g[1]], picked = on && on[0] === g[0] && on[1] === g[1];
    const final = !(a.playing + b.playing + a.left + b.left);
    const side = (s, o) => box(s, s.total < o.total ? " behind" : "", final && s.total > o.total);
    return `<button type="button" class="gd-g${picked ? " on" : ""}${g.includes(lg.me) ? " mine" : ""}" data-gdgame="${esc(g.join(","))}"
      aria-pressed="${!!picked}">${gdGameState(a, b)}${side(a, b)}${side(b, a)}</button>`;
  }).join("");
  return `<section class="gd-games gd-card"><h3>${t("live.games", {week: lg.week})}</h3>${rows}</section>`;
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
