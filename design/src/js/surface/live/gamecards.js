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
  /* ESPN's summary says where the game is; until it loads, the scoreboard's clock does ("Q3 4:12", "Half"). */
  const cl = g ? null : gdClockOf(GS.home);
  const detail = g && st === "in" ? `<span>${esc(g.detail)}</span>`
    : cl && cl.state === "in" ? `<span>${esc(cl.label)}</span>` : "";
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
  const every = GS_ERR ? "" : GS_GAME && GS_GAME.state === "in" ? t("live.sheet.every") : "";
  const head = every ? `<h3><em>${every}</em></h3>` : "";
  const warn = GS_ERR ? `<p class="gs-warn">${esc(GS_ERR)}</p>` : "";
  if (!GS_GAME) return `<section class="gs-card gs-plays" data-gsscroll>${head}${warn || `<p class="gs-quiet">${GS.event ? t("live.sheet.loading") : t("live.sheet.noEspn")}</p>`}</section>`;
  if (!GS_GAME.drives.length) return `<section class="gs-card gs-plays" data-gsscroll>${head}${warn}<p class="gs-quiet">${t("live.sheet.noPlays")}</p></section>`;
  const n = GS_GAME.drives.length;
  const drives = GS_GAME.drives.map((d, i) => {
    const key = String(n - i), open = GS_OPEN.has(key) ? GS_OPEN.get(key) : i === 0;
    return `<details class="gs-drv" data-gsdrive="${key}"${open ? " open" : ""}><summary>
        <span class="gs-tm">${esc(d.team)}</span><span>${esc(d.line)}</span><b class="${d.sc ? "sc" : ""}">${esc(d.on ? t("live.sheet.onDrive") : d.res)}</b></summary>
      ${d.plays.map(gsPlayHTML).join("")}</details>`;
  }).join("");
  return `<section class="gs-card gs-plays" data-gsscroll>${head}${warn}${drives}</section>`;
}

/* The box's players, each scored by the league on screen, best first. */
function gsScored(lg){
  const box = (GS_BOX && GS_BOX.box) || {};
  const mine = new Set(gdMineLineup(lg).map(r => r.sid));
  return Object.entries(box).map(([sid, p]) => ({sid, id: sid, ...p, pts: lg ? gdPts(lg.rules, p, p.s) : null, line: gdLine(p, p.s), mine: mine.has(sid), fol: sid in GS_FOLLOW}))
    .sort((a, b) => (b.pts || 0) - (a.pts || 0));
}

/* A small flat star; filled while followed (CSS). One tap toggles the follow (gamesheet.js). */
const GS_STAR = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.4l2.6 5.5 6 .8-4.4 4.2 1.1 6L12 17l-5.3 2.9 1.1-6-4.4-4.2 6-.8z"/></svg>`;
function gsStar(p){
  const name = gdShort(p), label = p.fol ? t("live.sheet.unfollow", {name}) : t("live.sheet.follow", {name});
  return `<button type="button" class="gs-star" data-gsfollow="${esc(p.id)}" data-sid="${esc(p.sid || "")}" data-slug="${esc(p.slug || "")}"
    data-n="${esc(p.n)}" data-pos="${esc(p.pos)}" data-team="${esc(p.team)}" aria-pressed="${!!p.fol}" aria-label="${esc(label)}">${GS_STAR}</button>`;
}

/* Every player of the reader's teams in this game, in every league (gdMine; none until they pick or
   follow a team), then everyone followed. The player the reader came
   from (GS.slug) leads, wherever he is rostered, mine or an opponent's. Scored by the league on screen. */
function gsYours(){
  const lg = gdLeague(), seen = new Set(), out = [], box = (GS_BOX && GS_BOX.box) || {};
  const pre = (GS_GAME ? GS_GAME.state : gsSleeperState()) === "pre";    // no stats are a zero before kickoff
  const here = club => gdSameClub(GS.away, club) || gdSameClub(GS.home, club);
  const add = r => {
    const id = r.sid || r.slug;
    if (!id || seen.has(id) || !here(r.team)) return;
    seen.add(id);
    const s = pre ? null : (GD_STATS &&GD_STATS.stats && GD_STATS.stats[r.sid]) || (box[r.sid] || {}).s || null;
    out.push({id, sid: r.sid || "", slug: r.slug || "", n: r.n, pos: r.pos, team: r.team, line: gdLine(r, s), s,
              pts: lg ? gdPts(lg.rules, r, s) : null, fol: id in GS_FOLLOW, focus: !!GS.slug && r.slug === GS.slug});
  };
  for (const l of GD.leagues) gdMineLineup(l).forEach(add);
  Object.values(GS_FOLLOW).forEach(add);
  if (GS.slug && !out.some(r => r.focus))
    for (const l of GD.leagues) for (const tm of Object.values(l.teams)) tm.lineup.filter(r => r.slug === GS.slug).forEach(add);
  return out.sort((a, b) => b.focus - a.focus);
}

function gsYoursHTML(){
  const rows = gsYours();
  const list = rows.map(r => `<div class="gs-yr${r.focus ? " focus" : ""}">${gsStar(r)}
      <span><b>${esc(gdShort(r))}</b> <i class="gs-pos" data-pos="${esc(r.pos)}">${esc(r.pos)}</i><em>${esc(r.line)}</em></span>
      <b class="gs-pts">${r.pts === null ? "—" : gdNum(r.pts)}</b></div>`).join("");
  return `<section class="gs-card gs-yours"><h3><span>${t("live.sheet.yours")}</span></h3>
    ${rows.length ? `<div class="gs-yl" data-gsscroll>${list}</div>` : `<p class="gs-quiet">${t("live.sheet.yoursNone")}</p>`}</section>`;
}

function gsTopHTML(){
  const lg = gdLeague(), rows = gsScored(lg).slice(0, 5);
  const head = lg ? `<h3><em>${t("live.sheet.scoring", {name: esc(lg.name)})}</em></h3>` : "";
  if (!rows.length) return `<section class="gs-card gs-top" data-gsscroll>${head}<p class="gs-quiet">${GS_BOX_ERR ? t("live.sheet.noSleeper") : GS_BOX ? t("live.sheet.noStats") : t("live.sheet.loading")}</p></section>`;
  return `<section class="gs-card gs-top" data-gsscroll>${head}${rows.map(r => `<div class="gs-sc${r.mine ? " mine" : ""}">${gsStar(r)}
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
      <tbody>${rows.map(p => `<tr${p.mine ? ` class="mine"` : ""}><td>${gsStar(p)}${esc(gdShort(p))}</td>${cols.map(c => `<td>${c[1](p.s)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  }).join("");
  return `<section class="gs-card gs-box" data-gsscroll>${seg}${tables || `<p class="gs-quiet">${t("live.sheet.noStats")}</p>`}</section>`;
}

const gsClubName = c => {
  const g = GS_GAME, side = g && (gdSameClub(c, g.away.abbr) ? g.away : gdSameClub(c, g.home.abbr) ? g.home : null);
  return (side && side.name) || c;
};

/* Plays · Box score · Top scorers: taps only, the sideways swipe stays the game walker. From 960px the
   plays sit beside the rest, so the tab that would show them shows the box instead. */
function gsTabsHTML(tab){
  const label = {plays: t("live.sheet.plays"), box: t("live.sheet.box"), top: t("live.sheet.top")};
  return `<div class="gs-tabs" role="tablist" aria-label="${esc(t("live.sheet.tabs"))}">${GS_TABS.map(k =>
    `<button type="button" role="tab" class="gs-tab" data-gstab="${k}" aria-selected="${k === tab}">${label[k]}</button>`).join("")}</div>`;
}

/* The game on each side, in the order a swipe walks them (gamesheet.js gsNeighbours), with where it
   stands, so a swipe is never a guess. A tap steps too. At either end that side stays empty. */
function gsStepsHTML(){
  const [prev, next] = gsNeighbours();
  if (!prev && !next) return "";
  const btn = (g, k) => {
    if (!g) return `<span></span>`;
    const name = {away: esc(g.away), home: esc(g.home)};
    return `<button type="button" class="gs-step ${k < 0 ? "prev" : "next"}" data-gsstep="${k}"
      aria-label="${k < 0 ? t("live.sheet.prev", name) : t("live.sheet.next", name)}">
      <b aria-hidden="true">${k < 0 ? "‹" : "›"}</b><span>${t("live.sheet.step", name)}<small>${esc(gdClockOf(g.home).label)}</small></span></button>`;
  };
  return `<nav class="gs-steps" aria-label="${t("live.sheet.steps")}">${btn(prev, -1)}${btn(next, 1)}</nav>`;
}

function gsSheetHTML(){
  const tab = GS_WIDE.matches && GS_TAB === "plays" ? "box" : GS_TAB;
  return `<button type="button" class="gs-grab" data-gsclose aria-label="${t("common.action.close")}"></button>
    <div class="gs-bar"><h2 class="gs-title" id="gs-title">${esc(t("live.sheet.title", {away: GS.away, home: GS.home}))}</h2>
      <button type="button" class="gs-x" data-gsclose aria-label="${t("common.action.close")}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
    ${gsStepsHTML()}
    <div class="gs-main" data-tab="${tab}"><div class="gs-side">${gsScoreHTML()}${gsYoursHTML()}${gsTabsHTML(tab)}</div>
      <div class="gs-panes" data-gsscroll role="tabpanel">${gsPlaysHTML()}${gsBoxHTML()}${gsTopHTML()}</div></div>`;
}
