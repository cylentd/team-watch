/* ============================== LIVE: THE GAME SHEET'S CARDS ==============================
   One card per subject (DESIGN.md "Cards"): the scoreboard, the plays, top scorers, the box score.
   The first two are ESPN's (data/gameday/espn.js), the last two Sleeper's (/api/stats?teams=), so
   either source going quiet leaves the other's cards standing. Pure markup from GS_* state. */

/* The score, where the game is, and on a live game who has the ball where. The strip under it runs
   from the away club's goal line (left) to the home club's (right). */
function gsScoreHTML(){
  const g = GS_GAME, st = g ? g.state : gsSleeperState();
  const score = (club, esp) => esp && esp.score !== null ? esp.score : gdClubScore(club, club === GS.away ? GS.home : GS.away);
  const a = score(GS.away, g && g.away), h = score(GS.home, g && g.home), on = st !== "pre" && a !== null && h !== null;
  const side = (club, esp, s, o, cls) => `<div class="gs-t ${cls}${on && s < o ? " behind" : ""}">
      <span>${esc((esp && esp.name) || club)}</span><b>${on ? s : "—"}</b></div>`;
  const mid = st === "in" ? `<span class="gs-pill">${t("live.now.live")}</span>`
    : st === "post" ? `<span class="gs-final">${GD_LOCK}${t("live.state.final")}</span>`
    : `<span>${esc(gdClock(gdKickOf(GS.home) || 0))}</span>`;
  const detail = g && st === "in" ? `<span>${esc(g.detail)}</span>` : "";
  const now = g && g.now, x = now && typeof now.ytez === "number"
    ? (gdSameClub(GS.home, now.ball) ? now.ytez : 100 - now.ytez) : null;
  const sit = now ? `<p class="gs-sit">${t("live.sheet.ball", {club: esc(now.ball)})}${now.dd ? ` · ${esc(now.dd)}` : ""}</p>
      ${x === null ? "" : `<div class="gs-field" aria-hidden="true"><i style="left:${Math.max(0, Math.min(100, x))}%"></i></div>
      <div class="gs-ends"><span>${esc(GS.away)}</span><span>${esc(GS.home)}</span></div>`}` : "";
  return `<section class="gs-card gs-sb">
    <div class="gs-score">${side(GS.away, g && g.away, a, h, "a")}<div class="gs-mid">${mid}${detail}</div>${side(GS.home, g && g.home, h, a, "h")}</div>
    ${sit}</section>`;
}

/* ESPN's pre/in/post from Sleeper's state, for when ESPN has not answered. */
function gsSleeperState(){
  const st = gdByCode((GD_STATS && GD_STATS.games) || {}, GS.home);
  return st === "in_game" ? "in" : st === "complete" ? "post" : "pre";
}

function gsPlayHTML(p){
  return `<div class="gs-pl${p.sc ? " sc" : ""}"><span>${esc(t("live.sheet.clock", {q: p.q || "", c: p.clock}))}</span>
    <span>${esc(p.text)}${p.dd ? `<small>${esc(p.dd)}</small>` : ""}</span></div>`;
}

/* Drives newest first. The newest is open; every earlier one is a single line that opens on a tap,
   and stays open through the next poll. */
function gsPlaysHTML(){
  const head = `<h3><span>${t("live.sheet.plays")}</span><em>${GS_ERR ? "" : GS_GAME && GS_GAME.state === "in" ? t("live.sheet.every") : ""}</em></h3>`;
  const warn = GS_ERR ? `<p class="gs-warn">${esc(GS_ERR)}</p>` : "";
  if (!GS_GAME) return `<section class="gs-card gs-plays">${head}${warn || `<p class="gs-quiet">${GS.event ? t("live.sheet.loading") : t("live.sheet.noEspn")}</p>`}</section>`;
  if (!GS_GAME.drives.length) return `<section class="gs-card gs-plays">${head}${warn}<p class="gs-quiet">${t("live.sheet.noPlays")}</p></section>`;
  const n = GS_GAME.drives.length;
  const drives = GS_GAME.drives.map((d, i) => {
    const key = String(n - i), open = GS_OPEN.has(key) ? GS_OPEN.get(key) : i === 0;
    return `<details class="gs-drv" data-gsdrive="${key}"${open ? " open" : ""}><summary>
        <span class="gs-tm">${esc(d.team)}</span><span>${esc(d.line)}</span><b class="${d.sc ? "sc" : ""}">${esc(d.on ? t("live.sheet.onDrive") : d.res)}</b></summary>
      ${d.plays.map(gsPlayHTML).join("")}</details>`;
  }).join("");
  return `<section class="gs-card gs-plays">${head}${warn}${drives}</section>`;
}

/* The box's players, each scored by the league on screen, best first. */
function gsScored(lg){
  const box = (GS_BOX && GS_BOX.box) || {};
  const mine = new Set(((lg && lg.teams[lg.me]) || {lineup: []}).lineup.map(r => r.sid));
  return Object.entries(box).map(([sid, p]) => ({sid, ...p, pts: lg ? gdPts(lg.rules, p, p.s) : null, line: gdLine(p, p.s), mine: mine.has(sid)}))
    .sort((a, b) => (b.pts || 0) - (a.pts || 0));
}

function gsTopHTML(){
  const lg = gdLeague(), rows = gsScored(lg).slice(0, 5);
  const head = `<h3><span>${t("live.sheet.top")}</span><em>${lg ? t("live.sheet.scoring", {name: esc(lg.name)}) : ""}</em></h3>`;
  if (!rows.length) return `<section class="gs-card gs-top">${head}<p class="gs-quiet">${GS_BOX_ERR ? t("live.sheet.noSleeper") : GS_BOX ? t("live.sheet.noStats") : t("live.sheet.loading")}</p></section>`;
  return `<section class="gs-card gs-top">${head}${rows.map(r => `<div class="gs-sc${r.mine ? " mine" : ""}">
      <span><b>${esc(gdShort(r))}</b> <small>${esc(r.team)}</small><em>${esc(r.line)}</em></span><b>${gdNum(r.pts || 0)}</b></div>`).join("")}</section>`;
}

/* One club at a time: passing, rushing, receiving, each its own table, most yards first. Built on
   each call so every copy key is a literal t() (assemble.py --check finds keys that way). */
function gsGroups(){
  const yds = t("live.sheet.yds"), td = t("live.sheet.td");
  return [
    [t("live.sheet.passing"), "pass_att", "pass_yd", [[t("live.sheet.ca"), s => `${s.pass_cmp || 0}/${s.pass_att || 0}`], [yds, s => s.pass_yd || 0], [td, s => s.pass_td || 0], [t("live.sheet.int"), s => s.pass_int || 0]]],
    [t("live.sheet.rushing"), "rush_att", "rush_yd", [[t("live.sheet.car"), s => s.rush_att || 0], [yds, s => s.rush_yd || 0], [td, s => s.rush_td || 0]]],
    [t("live.sheet.receiving"), "rec_tgt", "rec_yd", [[t("live.sheet.rec"), s => s.rec || 0], [t("live.sheet.tgt"), s => s.rec_tgt || 0], [yds, s => s.rec_yd || 0], [td, s => s.rec_td || 0]]]];
}

function gsBoxHTML(){
  const club = GS_TEAM || GS.away, lg = gdLeague();
  const players = gsScored(lg).filter(p => gdSameClub(club, p.team));
  const seg = `<div class="gs-seg" role="group" aria-label="${t("live.sheet.box")}">${[GS.away, GS.home].map(c =>
    `<button type="button" data-gsteam="${esc(c)}" aria-pressed="${c === club}">${esc(gsClubName(c))}</button>`).join("")}</div>`;
  const tables = gsGroups().map(([label, has, sort, cols]) => {
    const rows = players.filter(p => p.s[has]).sort((a, b) => (b.s[sort] || 0) - (a.s[sort] || 0));
    if (!rows.length) return "";
    return `<table class="gs-tbl"><caption>${label}</caption><thead><tr><th></th>${cols.map(c => `<th>${c[0]}</th>`).join("")}</tr></thead>
      <tbody>${rows.map(p => `<tr${p.mine ? ` class="mine"` : ""}><td>${esc(gdShort(p))}</td>${cols.map(c => `<td>${c[1](p.s)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  }).join("");
  return `<section class="gs-card gs-box"><h3><span>${t("live.sheet.box")}</span></h3>${seg}${tables || `<p class="gs-quiet">${t("live.sheet.noStats")}</p>`}</section>`;
}

const gsClubName = c => {
  const g = GS_GAME, side = g && (gdSameClub(c, g.away.abbr) ? g.away : gdSameClub(c, g.home.abbr) ? g.home : null);
  return (side && side.name) || c;
};

function gsSheetHTML(){
  return `<button type="button" class="gs-grab" data-gsclose aria-label="${t("common.action.close")}"></button>
    <h2 class="gs-title" id="gs-title">${esc(t("live.sheet.title", {away: GS.away, home: GS.home}))}</h2>
    <div class="gs-cols">${gsScoreHTML()}${gsPlaysHTML()}${gsTopHTML()}${gsBoxHTML()}</div>`;
}
