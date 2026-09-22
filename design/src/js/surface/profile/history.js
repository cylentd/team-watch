/* The three blocks LIVE_PEDIGREE/LIVE_USAGE/LIVE_GAMELOG/LIVE_PROJECTIONS add to the modal that
   #drawer never had room for: a bio strip, a season-so-far trend (usage and weekly box score,
   each a sparkline over the table), and a projected-vs-actual line. Every block renders nothing
   when its source has no row for this slug -- a deep bench player with real matchup data still
   opens cleanly with just that. */
function glNum(v){ return v === null || v === undefined ? "—" : v; }

/* The next game's forecast at whichever stadium it's actually played at -- his own team's when
   he's home, the opponent's when he's away. Domes render a quiet note instead of a temperature;
   a retractable roof still gets one, with a caveat, since whether it's closed is a game-time
   call this API has no way to know. */
function weatherHTML(prof){
  const nx = prof.next;
  if (typeof LIVE_WEATHER === "undefined" || !LIVE_WEATHER || !nx) return "";
  const w = LIVE_WEATHER.teams[nx.home ? prof.team : nx.opp];
  if (!w) return "";
  if (w.roof === "dome") return `<p class="pf-cap pf-weather">${t("profile.weather.dome")}</p>`;
  if (w.temp_f === null || w.temp_f === undefined) return "";
  const note = w.roof === "retractable" ? ` · ${t("profile.weather.retractable")}` : "";
  return `<p class="pf-cap pf-weather">${t("profile.weather.line", {temp: w.temp_f, wind: esc(w.wind || "—"), short: esc(w.short || "")})}${note}</p>`;
}

/* Round.pick, e.g. "3.04". Rounds and picks are both 1-based, so a 0 in either reads as unset. */
function fdPick(fd){
  return fd && fd.round && fd.pick ? `${fd.round}.${String(fd.pick).padStart(2, "0")}` : null;
}

function bioHTML(p){
  if (typeof LIVE_PEDIGREE === "undefined" || !LIVE_PEDIGREE) return "";
  const b = LIVE_PEDIGREE.players[p.slug];
  if (!b) return "";
  const fd = b.fantasy_draft || {};
  const chips = [
    b.age !== null && b.age !== undefined ? t("profile.bio.age", {n: b.age}) : null,
    b.height ? esc(b.height) : null,
    b.weight !== null && b.weight !== undefined ? t("profile.bio.weight", {n: b.weight}) : null,
    b.years_exp !== null && b.years_exp !== undefined
      ? (b.years_exp === 0 ? t("profile.bio.rookie") : t("profile.bio.years", {n: b.years_exp})) : null,
    b.depth ? t("profile.bio.depth", {n: b.depth, pos: esc(b.depth_pos || "")}) : null,
    b.bye !== null && b.bye !== undefined ? t("profile.bio.bye", {n: b.bye}) : null,
    b.draft_number !== null && b.draft_number !== undefined
      ? t("profile.bio.draftCapital", {n: b.draft_number, yr: b.entry_year ?? "—"}) : null,
    fdPick(fd.espn) ? t("profile.bio.fantasyDraft", {league: "ESPN", pick: fdPick(fd.espn)}) : null,
    fdPick(fd.yahoo) ? t("profile.bio.fantasyDraft", {league: "Yahoo", pick: fdPick(fd.yahoo)}) : null,
  ].filter(Boolean);
  return chips.length ? `<div class="pf-bio">${chips.map(c => `<span>${c}</span>`).join("")}</div>` : "";
}

/* USAGE (data/usage.js) is declared after this file loads, but only read here inside a function
   body -- by the time a click runs it, every top-level const in the page has already run. */
function usageTrendHTML(p){
  if (typeof USAGE === "undefined") return "";
  const rows = USAGE.rows.filter(r => r.slug === p.slug).sort((a, b) => a.wk - b.wk);
  if (!rows.length) return "";
  const pos = rows[0].pos;
  const cols = (USAGE.cols && USAGE.cols[pos]) || [];
  if (!cols.length) return "";
  const rankId = (USAGE.rankBy && USAGE.rankBy[pos]) || cols[0].id;
  const rankCol = cols.find(c => c.id === rankId) || cols[0];
  const vals = rows.map(r => r.v[rankId] ?? 0);
  const spark = `<div class="pf-spark-row">${sparkHTML(vals, 220, 40)}
    <span class="pf-spark-v">${usageFmt(vals[vals.length - 1], rankCol.fmt)}<em>${esc(rankCol.label)}</em></span></div>`;
  const table = `<div class="pf-table-scroll"><table class="pf-table pf-table-wk"><thead><tr><th>${t("profile.trend.colWeek")}</th>
    ${cols.map(c => `<th>${esc(c.label)}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr><th scope="row">${r.wk}</th>
      ${cols.map(c => `<td>${usageFmt(r.v[c.id], c.fmt)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  return secHTML(t("profile.trend.label"), spark + table);
}

function gamelogRows(slug){
  return typeof LIVE_GAMELOG !== "undefined" && LIVE_GAMELOG
    ? LIVE_GAMELOG.rows.filter(r => r.slug === slug).sort((a, b) => a.wk - b.wk) : [];
}

/* Each label is a literal call to t(), not built from a variable: assemble.py --check finds
   every copy key by scanning for that literal form and cannot see one assembled from a
   template (see nav.js). */
const GAMELOG_COLS = [
  {id: "pass_yds", label: () => t("profile.history.colPassYds"), has: "pass_yds"},
  {id: "pass_td", label: () => t("profile.history.colPassTd"), has: "pass_yds"},
  {id: "car", label: () => t("profile.history.colCar"), has: "car"},
  {id: "rush_yds", label: () => t("profile.history.colRushYds"), has: "car"},
  {id: "rush_td", label: () => t("profile.history.colRushTd"), has: "car"},
  {id: "tgt", label: () => t("profile.history.colTgt"), has: "tgt"},
  {id: "rec", label: () => t("profile.history.colRec"), has: "tgt"},
  {id: "rec_yds", label: () => t("profile.history.colRecYds"), has: "tgt"},
  {id: "rec_td", label: () => t("profile.history.colRecTd"), has: "tgt"},
];

function weeklyHistoryHTML(p){
  const rows = gamelogRows(p.slug);
  if (!rows.length) return "";
  const has = key => rows.some(r => r[key] !== null && r[key] !== undefined);
  const cols = GAMELOG_COLS.filter(c => has(c.has));
  const pts = rows.map(r => r.pts ?? 0);
  const spark = `<div class="pf-spark-row">${sparkHTML(pts, 220, 40)}
    <span class="pf-spark-v">${glNum(rows[rows.length - 1].pts)}<em>${t("profile.history.pts")}</em></span></div>`;
  const table = `<div class="pf-table-scroll"><table class="pf-table pf-table-wk"><thead><tr><th>${t("profile.history.colWeek")}</th>
    <th>${t("profile.history.colOpp")}</th><th>${t("profile.history.colPts")}</th>
    ${cols.map(c => `<th>${c.label()}</th>`).join("")}</tr></thead>
    <tbody>${rows.map(r => `<tr><th scope="row">${r.wk}</th><td>${esc(r.opp || "—")}</td><td>${glNum(r.pts)}</td>
      ${cols.map(c => `<td>${glNum(r[c.id])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  return secHTML(t("profile.history.label"), spark + table);
}

function projectionHTML(p){
  if (typeof LIVE_PROJECTIONS === "undefined" || !LIVE_PROJECTIONS) return "";
  const proj = LIVE_PROJECTIONS.players[p.slug];
  if (!proj || proj.pts === null || proj.pts === undefined) return "";
  const rows = gamelogRows(p.slug);
  const last = rows[rows.length - 1];
  const line = last && last.pts !== null && last.pts !== undefined
    ? t("profile.projection.vsLast", {proj: proj.pts.toFixed(1), actual: last.pts.toFixed(1), wk: last.wk})
    : t("profile.projection.noActual", {proj: proj.pts.toFixed(1)});
  const mu = proj.mu
    ? Object.entries(proj.mu).map(([k, v]) => `<span class="pf-mu"><em>${esc(k)}</em><b>${Number(v).toFixed(1)}</b></span>`).join("")
    : "";
  return secHTML(t("profile.projection.label"), `<p class="pf-cap">${line}</p>${mu ? `<div class="pf-mu-row">${mu}</div>` : ""}`);
}
