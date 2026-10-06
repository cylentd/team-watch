/* ============================== LEAGUE > TEAMS: THE LEAGUE BOARD ==============================
   2026-10-05 (leaf `teams`, hash #teams; storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y,
   option B). One row per team in a league, one column per position (QB, RB, WR, TE, FLX): the sum of this
   week's projected points of that team's starters there, in its best legal lineup (design/teams.py,
   LIVE_TEAMS; the page computes nothing). A cell is green 8% above the league's median for its column and
   red 8% below. A lime "+" in a corner is a spare starter on that team's bench. A tap on a row opens the
   team as a full page (lbpage.js, then tbpage.js); it never changes the reader's own team.

   The league is the one chip's (surface/league/switch.js): the league of the team on screen, ESPN's too,
   where Records and Trades are the Yahoo leagues' alone (2026-10-05: it had a Madden Curse / AYO / ESPN
   switch of its own until then). The reader's own team is pinned to the top row. */
const LB_EDGE = .08;                           // how far from the league's median a cell is tinted
const LB_COLS = ["QB", "RB", "WR", "TE", "FLX"];
let LB_SORT = null;                            // a column, or null for the lineup total

const lbData = () => (typeof LIVE_TEAMS !== "undefined" && LIVE_TEAMS) || null;
const lbOf = key => ((lbData() || {}).leagues || []).find(l => l.key === key) || null;
/* Every league the reader can look at: the Yahoo ones in the switch's order, then ESPN. */
const lbKeys = () => {
  const ks = myLeagueKeys();
  return [...ks.filter(k => TEAMS[k].site === "yahoo"), ...ks.filter(k => TEAMS[k].site !== "yahoo")];
};

/* The league of the team on screen (data/league.js lgFocusKey): the chip is the one pick since 2026-10-05,
   so the board, Recap, Records and Trades are always the same league. */
const lbLeagueKey = () => lgFocusKey();

/* A team's record, as the standings write it: 3–1, or 3–1–1 with a tie; "" with no standings. */
const lbRecord = tm => tm.w == null ? "" : tm.t ? `${tm.w}–${tm.l}–${tm.t}` : `${tm.w}–${tm.l}`;
const lbNum = v => Number(v).toFixed(1);

/* The columns this league has a slot for: a league with no flex draws no FLX. */
const lbCols = lg => LB_COLS.filter(c => lg.slots[c === "FLX" ? "FLEX" : c]);

/* Sorted by the picked column, else the lineup total, best first; the reader's own team on top of either. */
function lbRows(lg){
  const mine = myTeamLoad(), by = LB_SORT ? x => x.cols[LB_SORT] : () => 0;
  const rows = [...lg.teams].sort((a, b) => by(b) - by(a) || b.tot - a.tot || a.name.localeCompare(b.name));
  const i = mine ? rows.findIndex(x => x.key === mine) : -1;
  return i > 0 ? [rows[i], ...rows.slice(0, i), ...rows.slice(i + 1)] : rows;
}

/* "up" 8% or more over the league's median for the column, "dn" 8% or more under, else plain. */
const lbTone = (v, med) => !med ? "" : v >= med * (1 + LB_EDGE) ? "up" : v <= med * (1 - LB_EDGE) ? "dn" : "";

function lbCellHTML(tm, lg, c){
  const plus = tm.spare.includes(c) ? `<i class="lb-plus" title="${t("lboard.spare.title")}">+</i>` : "";
  return `<span class="lb-c ${lbTone(tm.cols[c], lg.median[c])}" role="cell">${lbNum(tm.cols[c])}${plus}</span>`;
}

function lbRowHTML(tm, lg, cols){
  const rec = lbRecord(tm), mine = tm.key === myTeamLoad();
  return `<div class="lb-row${mine ? " mine" : ""}" role="row" data-lbrow="${esc(tm.key)}">
    <div class="lb-rh" role="rowheader"><button type="button" class="lb-team" data-lbopen="${esc(tm.key)}"
      aria-label="${t("lboard.row.open", {name: esc(tm.name)})}"><b>${esc(tm.name)}</b>
      <small>${rec ? `${rec}<i>·</i>` : ""}<em>${lbNum(tm.tot)}</em></small></button></div>
    ${cols.map(c => lbCellHTML(tm, lg, c)).join("")}</div>`;
}

/* One sort button per column, and one for the team column, which is the lineup total. One is always
   pressed; tapping the pressed column goes back to the total. */
function lbHeadHTML(cols){
  const on = LB_SORT, th = (c, label, cls) => `<span role="columnheader" aria-sort="${on === c ? "descending" : "none"}">
    <button type="button" class="lb-h${cls}" data-lbsort="${c || ""}" aria-pressed="${on === c}"
      aria-label="${t("lboard.col.sort", {col: label})}">${label}</button></span>`;
  return `<div class="lb-head" role="row">${th(null, t("lboard.head.team"), " team")}${cols.map(c => th(c, c, "")).join("")}</div>`;
}

/* The board's week is schedWeek(), the one page week (data/schedule.js, 2026-10-05). */
function lbKeyHTML(){
  const pct = LB_EDGE * 100, wk = schedWeek();
  return `<div class="lb-key" role="group" aria-label="${t("lboard.key.aria")}">
    <span class="lb-what">${wk ? t("lboard.key.what", {wk}) : t("lboard.key.whatNoWeek")}</span>
    <span class="lb-k"><i class="lb-sw up"></i>${t("lboard.key.above", {pct})}</span>
    <span class="lb-k"><i class="lb-sw dn"></i>${t("lboard.key.below", {pct})}</span>
    <span class="lb-k"><i class="lb-plus">+</i>${t("lboard.key.spare")}</span></div>`;
}

/* A league whose rosters are missing keeps the switch, so the reader can go to one that has them. */
const lbEmptyHTML = () => `<div class="state-empty lb-empty"><div><b>${t("lboard.empty.title")}</b>
  <span>${t("lboard.empty.sub")}</span></div></div>`;

/* While the reader has no team in this league, one quiet line says how to set it: a team's page has the button. */
const lbPickHTML = lg => tbMine(lg) ? "" : `<p class="lb-pick">${t("lboard.board.pick")}</p>`;

function lbViewHTML(){
  const page = LB_PAGE ? lbPageHTML() : "";          // lbpage.js; "" when no page is open, or its team is gone
  if (page) return page;
  const on = lbLeagueKey(), lg = lbOf(on), sw = lgChipHTML();
  if (!lg) return `<div class="wrap lb">${sw}${lbEmptyHTML()}</div>`;
  const cols = lbCols(lg);
  return `<div class="wrap lb">${sw}${lbPickHTML(lg)}
    <div class="lb-grid" role="table" aria-label="${t("lboard.table.aria")}" style="--lb-n:${cols.length}">
      ${lbHeadHTML(cols)}${lbRows(lg).map(tm => lbRowHTML(tm, lg, cols)).join("")}</div>
    ${lbKeyHTML()}</div>`;
}

/* A header tap redraws the grid in place, so the switch above it never moves; focus stays on the header. */
function wireLb(v){
  if (LB_PAGE) return wireLbPage(v);
  wireLgChip(v);
  v.querySelectorAll("[data-lbsort]").forEach(b => b.addEventListener("click", () => {
    const c = b.dataset.lbsort || null;
    LB_SORT = c && c !== LB_SORT ? c : null;
    render();
    v.querySelector(`[data-lbsort="${b.dataset.lbsort}"]`)?.focus({preventScroll: true});
  }));
  v.querySelectorAll("[data-lbrow]").forEach(r => r.addEventListener("click", () => lbPageOpen(r.dataset.lbrow)));
}
