/* The two history blocks LIVE_GAMELOG/LIVE_PROJECTIONS add to the modal: the weekly box score
   (a points sparkline over the table) and the projected-vs-actual line with the model's
   component means. Each renders nothing when its source has no row for this slug -- a deep
   bench player with real matchup data still opens cleanly with just that. */
function glNum(v){ return v === null || v === undefined ? "—" : v; }

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
  const spark = `<div class="pf-spark-row">${sparkHTML(pts, 220, 44)}
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
