/* What LIVE_GAMELOG and LIVE_PROJECTIONS give the modal: the weekly box-score rows and their
   columns (read by the Season table, season.js, since 2026-09-28; the old Log table and its
   sparkline are gone), the replay link a played week carries, and the projection's component
   means. Each renders nothing when its source has no row for this slug. */
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

/* A week's row opens that game's replay -- the second of the two ways in, the first being a name
   on the Live board. The whole row is the target (2026-09-26: the week number alone was a 9px
   target nobody found); the week stays a real button inside it, so the keyboard and a screen
   reader still have one control per row. A plain number and a plain row when the schedule has no
   ESPN id for the game (an older history row): a control that does nothing is worse than none.

   No play mark since 2026-09-29 (David: "I don't think we need carrots for the week"). Three lime
   marks on the played weeks competed with the lime row that says which game is next, and lime on
   this table means "now". The row still lights under a pointer and presses under a thumb. */
function weekOpens(p, r){
  const club = r.team || p.team;
  return typeof stGameFor === "function" && stGameFor(club, r.wk) ? club : null;
}

function weekCell(p, r){
  if (!weekOpens(p, r)) return r.wk;
  return `<button type="button" class="pf-wk" aria-label="${esc(t("strip.open.week", {n: r.wk}))}">${r.wk}</button>`;
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

/* Lives in the Season pane, under the table: what the lime row's projection is made of.

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
