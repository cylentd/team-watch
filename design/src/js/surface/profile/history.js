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

/* A column group is drawn only when something actually happened in it. The old test was "does
   the row carry the key at all", and a back's gamelog carries pass_yds as a literal 0 every
   week -- so every back got two columns of zeros, and those were two of the columns that pushed
   the table into a sideways scroll. */
function gamelogCols(rows){
  const happened = key => rows.some(r => Number(r[key]) > 0);
  return GAMELOG_COLS.filter(c => happened(c.has));
}

function glSum(rows, key){
  const v = rows.filter(r => r[key] !== null && r[key] !== undefined);
  if (!v.length) return "—";
  const n = v.reduce((s, r) => s + Number(r[key]), 0);
  return Number.isInteger(n) ? n : n.toFixed(1);
}

/* The week number opens that game's drive strip -- the second of the two ways in, the first being
   a name on the Live board. A plain number when the schedule has no ESPN id for it (an older
   history row), because a control that does nothing is worse than no control. */
function weekCell(p, r){
  const club = r.team || p.team;
  if (typeof stGameFor !== "function" || !stGameFor(club, r.wk)) return r.wk;
  return `<button type="button" class="pf-wk" data-stripclub="${esc(club)}" data-stripwk="${r.wk}"
    data-stripname="${esc(p.n)}" aria-label="${esc(t("strip.open.week", {n: r.wk}))}">${r.wk}</button>`;
}

/* Every cell carries its own column name in `data-c`. On a phone the header row is dropped and
   each week becomes a block of labelled chips (history.css): at eighteen weeks and ten columns
   the alternative is a sideways drag, and a stat table you have to drag is one you do not read.
   The season total is a foot row rather than a block of its own, because it is the same columns,
   and it is the row that matters most once the season is long. */
function weeklyHistoryHTML(p){
  const rows = gamelogRows(p.slug);
  if (!rows.length) return "";
  const cols = gamelogCols(rows);
  const pts = rows.map(r => r.pts ?? 0);
  const spark = `<div class="pf-spark-row">${sparkHTML(pts, 220, 44)}
    <span class="pf-spark-v">${glNum(rows[rows.length - 1].pts)}<em>${t("profile.history.pts")}</em></span></div>`;
  const head = [t("profile.history.colWeek"), t("profile.history.colOpp"), t("profile.history.colPts")]
    .concat(cols.map(c => c.label()));
  const cell = (v, i, cls) => `<td class="${cls || ""}" data-c="${esc(head[i])}">${v}</td>`;
  /* Week, opponent and points are named classes, not positions: on a phone the block needs one
     thing the eye lands on per week, and that is the points. */
  const row = (wk, opp, ptsCell, get) => `<tr><th scope="row" class="gl-wk" data-c="${esc(head[0])}">${wk}</th>${cell(opp, 1, "gl-opp")}${cell(ptsCell, 2, "gl-pts")}
      ${cols.map((c, i) => cell(get(c), i + 3)).join("")}</tr>`;
  // weekCell, not r.wk: the week is a button into that game's drive strip when the schedule has
  // an ESPN id for it (panel.js binds the click, because openProfile rebuilds #modal every open).
  const body = rows.map(r => row(weekCell(p, r), esc(r.opp || "—"), glNum(r.pts), c => glNum(r[c.id]))).join("");
  const foot = row(t("profile.history.total"), t("profile.history.games", {n: rows.length}),
    glSum(rows, "pts"), c => glSum(rows, c.id));
  const table = `<div class="pf-table-scroll"><table class="pf-table pf-table-wk">
    <thead><tr>${head.map(h => `<th>${h}</th>`).join("")}</tr></thead>
    <tbody>${body}</tbody><tfoot>${foot}</tfoot></table></div>`;
  return secHTML(t("profile.history.label"), spark + table);
}

/* The producer's own mu keys, spelled out so a reader is not left deciding whether REC is
   catches or yards -- it is yards, and RECS is catches. An unmapped key passes through as it
   came, so a new component shows up rather than disappearing. */
const MU_LABEL = {
  PASS: () => t("profile.projection.muPass"),
  RUSH: () => t("profile.projection.muRush"),
  REC: () => t("profile.projection.muRec"),
  RECS: () => t("profile.projection.muRecs"),
  TD: () => t("profile.projection.muTd"),
};

/* Lives in the Log pane, under the weekly table: next week's number against the weeks behind it.

   It used to open "17.8 pts projected next game, 16.2 last game (wk 2)", which is the lede's own
   number and the sparkline's last point restated as a sentence -- nothing a reader who had
   scrolled this far had not already read twice. What was missing instead was who is claiming it,
   so that is the line now: ff-jarvis's model (model.market.projections), its scoring, and the
   season it was fitted through. */
function projectionHTML(p){
  if (typeof LIVE_PROJECTIONS === "undefined" || !LIVE_PROJECTIONS) return "";
  const proj = LIVE_PROJECTIONS.players[p.slug];
  if (!proj || proj.pts === null || proj.pts === undefined) return "";
  const m = LIVE_PROJECTIONS.meta || {};
  const src = t("profile.projection.source", {scoring: esc(m.scoring || "—"), through: esc(m.through || "—")});
  const mu = proj.mu
    ? Object.entries(proj.mu).map(([k, v]) =>
        `<span class="pf-mu"><em>${MU_LABEL[k] ? MU_LABEL[k]() : esc(k)}</em><b>${Number(v).toFixed(1)}</b></span>`).join("")
    : "";
  return secHTML(t("profile.projection.label"),
    `${mu ? `<div class="pf-mu-row">${mu}</div>` : ""}<p class="pf-cap pf-fine">${src}</p>`);
}
