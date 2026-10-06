/* ============================== LEAGUE: THE GRUDGE (Yahoo Recap) ==============================
   Two teams, next week's pairing, as one point: the series record, one sentence on
   who owns it and who is hot, and the last meetings as W/L chips. (2026-09-27: it was a tale of the
   tape with six stat rows, a bar per meeting, a legend and two footnotes, and nobody could tell who
   owned the series. Titles and all-time records live on Records now.) */

/* The current run in the series from the team on screen's side: ["W", 3], ["L", 1], or null. */
function lgRun(m){
  if (!m || !m.length) return null;
  const won = x => x[2] > 0, last = won(m[m.length - 1]);
  let n = 0;
  for (let i = m.length - 1; i >= 0 && m[i][2] !== 0 && won(m[i]) === last; i--) n++;
  return [last ? "W" : "L", n];
}

/* Who owns it and who is hot, in one sentence. Every case spelled out for assemble.py --check. */
function lgGrudgeLine(id, opp, h, m){
  if (!m.length) return t("league.grudge.first");
  const lead = h.w > h.l ? id : h.l > h.w ? opp : null;
  // A shutout series is the whole story: nothing else in the line competes with it.
  if (m.length >= 3 && (!h.w || !h.l) && !h.t)
    return t("league.grudge.never", {lead: `<b>${lgMgr(lead)}</b>`, other: `<b>${lgMgr(lead === id ? opp : id)}</b>`, n: m.length});
  const run = lgRun(m), hot = run && run[1] >= 2 ? (run[0] === "W" ? id : opp) : null;
  const at = {lead: `<b>${lgMgr(lead)}</b>`, other: `<b>${lgMgr(hot)}</b>`, n: run && run[1]};
  if (lead && hot && hot !== lead) return t("league.grudge.ownsBut", at);
  if (lead && hot) return t("league.grudge.ownsAnd", at);
  if (lead) return t("league.grudge.owns", at);
  return hot ? t("league.grudge.evenRun", at) : t("league.grudge.even");
}

/* The team on screen against next week's opponent: the card alone, for Your game's disclosure (myrecap.js);
   nothing on a bye or with no schedule. */
function lgGrudgeBodyHTML(id){
  const opp = id ? lgOpp(id) : null;
  return opp && LG.teams.some(x => x.id === id) && LG.teams.some(x => x.id === opp) ? lgGrudgeCardHTML(id, opp) : "";
}

/* Whether the grudge cards show each meeting's margin instead of W/L chips: the reader's tap, kept
   for the session so a redraw keeps it. */
let LG_MARGINS = false;
const LG_MEETS = 12;

/* Each of the last meetings as a bar from the middle line: up and green when `id` won, down and red
   when it lost, its height the margin against the biggest shown. Then the point difference and each
   side's biggest win. */
function lgMarginsHTML(id, opp, h, o, m){
  const shown = m.slice(-LG_MEETS), top = Math.max(...shown.map(x => Math.abs(x[2]))) || 1;
  // A one-sided series draws only its own half: no empty half under a shutout.
  const up = shown.some(x => x[2] > 0), down = shown.some(x => x[2] < 0), half = up && down ? 50 : 100;
  const side = up && down ? "" : up ? " up" : " down";
  const bars = shown.map(x => `<i class="${x[2] > 0 ? "w" : "l"}" style="--h:${(half * Math.abs(x[2]) / top).toFixed(1)}%"></i>`).join("");
  const yrs = shown.map(x => `<span>'${String(x[0]).slice(2)}</span>`).join("");
  const diff = m.reduce((s, x) => s + x[2], 0);
  const big = (side, tid) => side && side.big ? `<dt>${t("league.grudge.bigWin", {team: lgMgr(tid), y: side.big.y, wk: side.big.wk})}</dt><dd>+${lgPts(side.big.v)}</dd>` : "";
  return `<div class="bp-gm">
      ${up ? `<span class="bp-gmk">${t("league.grudge.wonBy", {team: lgMgr(id)})}</span>` : ""}
      <div class="bp-gmp${side}" style="--n:${shown.length}" role="img" aria-label="${t("league.grudge.marginsAria", {n: shown.length, team: lgMgr(id)})}">${bars}</div>
      <div class="bp-gmy" style="--n:${shown.length}" aria-hidden="true">${yrs}</div>
      ${down ? `<span class="bp-gmk">${t("league.grudge.wonBy", {team: lgMgr(opp)})}</span>` : ""}
    </div>
    <dl class="bp-gfacts"><dt>${t("league.grudge.diff", {team: lgMgr(diff >= 0 ? id : opp)})}</dt><dd>+${lgPts(Math.abs(diff))}</dd>${big(h, id)}${big(o, opp)}</dl>`;
}

/* The inside of a grudge card, redrawn alone by its margins toggle (wireLeague). */
function lgGrudgeCardHTML(id, opp){
  const h = lgH2H(id, opp) || {w: 0, l: 0, t: 0, m: []}, m = h.m || [];
  const body = !m.length ? "" : LG_MARGINS ? lgMarginsHTML(id, opp, h, lgH2H(opp, id), m) : lgChipsHTML(m);
  return `<div class="bp-gcard" data-a="${id}" data-b="${opp}">
      <div class="bp-gvs"><span>${lgMgr(id)}</span><b>${h.t ? `${h.w}–${h.l}–${h.t}` : `${h.w}–${h.l}`}</b><span>${lgMgr(opp)}</span></div>
      <p class="bp-gline">${lgGrudgeLine(id, opp, h, m)}</p>
      ${body}
      ${m.length ? `<button class="bp-open" data-lgmargins aria-pressed="${LG_MARGINS}">${LG_MARGINS ? t("league.grudge.hideMargins") : t("league.grudge.showMargins")}</button>` : ""}
    </div>`;
}

/* The last meetings as W/L chips over their years, from the leading side. */
const lgChipsHTML = m => m.length ? `<div class="bp-gchips" role="img" aria-label="${t("league.grudge.chipsAria", {n: Math.min(10, m.length)})}">${
  m.slice(-10).map(x => `<span><i class="${x[2] > 0 ? "w" : "l"}">${x[2] > 0 ? t("league.grudge.w") : t("league.grudge.l")}</i>
    <small>'${String(x[0]).slice(2)}</small></span>`).join("")}</div>` : "";

/* One pairing's grudge card with its heading, from `id`'s side: the league page's biggest grudge. */
function lgPairGrudgeHTML(id, opp, title){
  if (!LG.teams.some(x => x.id === id) || !LG.teams.some(x => x.id === opp)) return "";
  return `<section class="lg-sec bp-grudge" aria-label="${title}">
    <h3 class="bp-hd">${title}<span>${t("league.tape.sub", {n: LG.week})}</span></h3>
    ${lgGrudgeCardHTML(id, opp)}
  </section>`;
}
