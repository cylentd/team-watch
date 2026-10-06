/* ============================== LEAGUE > TEAMS: THE LEAGUE'S CARDS ==============================
   2026-10-05 (leaf `teams`, hash #teams; storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y),
   2026-10-06: roster cards instead of the table (trade finder, unit U3). One card per team in a league
   (lbcard.js): a strength strip of QB, RB, WR, TE, FLX (the sum of this week's projected points of that team's
   starters there, in its best legal lineup; design/teams.py, LIVE_TEAMS; the page computes nothing), then its
   starters and bench. A strip cell is green 8% above the league's median for its column and red 8% below. A
   lime "+" in a corner is a spare starter on that team's bench. A chip row sorts the cards (Total, QB, RB, WR,
   TE); the reader's own team is pinned first whatever the sort.

   The league is the one chip's (surface/league/switch.js): the league of the team on screen, ESPN's too,
   where Records and Trades are the Yahoo leagues' alone (2026-10-05: it had a Madden Curse / AYO / ESPN
   switch of its own until then). A card does not open anything; its foot's "Trades with them ›" opens the
   trade finder (finder/finder.js, leaf `trades`) on that team. */
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
   so the cards, Recap, Records and Trades are always the same league. */
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

/* The sort chips: Total, then each position the league starts (not FLX: it is a slot, not a position). One is
   always pressed; the lineup total is the default. */
function lbSortsHTML(lg){
  const chip = (c, label) => `<button type="button" class="lb-sort" data-testid="teams-sort" data-lbsort="${c || ""}"
    aria-pressed="${LB_SORT === c}" aria-label="${t("lboard.col.sort", {col: label})}">${label}</button>`;
  return `<div class="lb-sorts" role="group" aria-label="${t("lboard.sort.aria")}">${chip(null, t("lboard.sort.total"))}${
    lbCols(lg).filter(c => c !== "FLX").map(c => chip(c, c)).join("")}</div>`;
}

/* What the strip's numbers are: the week, over the chips. The page's week is schedWeek(), the one page week. */
const lbWhatHTML = () => { const wk = schedWeek(); return `<p class="lb-what">${wk ? t("lboard.key.what", {wk}) : t("lboard.key.whatNoWeek")}</p>`; };

/* What the two tints and the plus mean, under the cards. */
function lbKeyHTML(){
  const pct = LB_EDGE * 100;
  return `<div class="lb-key" data-testid="teams-key" role="group" aria-label="${t("lboard.key.aria")}">
    <span class="lb-k" data-testid="teams-key-item"><i class="lb-sw up"></i>${t("lboard.key.above", {pct})}</span>
    <span class="lb-k" data-testid="teams-key-item"><i class="lb-sw dn"></i>${t("lboard.key.below", {pct})}</span>
    <span class="lb-k" data-testid="teams-key-item"><i class="lb-plus">+</i>${t("lboard.key.spare")}</span></div>`;
}

/* A league whose rosters are missing keeps the switch, so the reader can go to one that has them. */
const lbEmptyHTML = () => `<div class="state-empty lb-empty" data-testid="teams-empty"><div><b>${t("lboard.empty.title")}</b>
  <span>${t("lboard.empty.sub")}</span></div></div>`;

function lbViewHTML(){
  const on = lbLeagueKey(), lg = lbOf(on), sw = lgChipHTML();
  if (!lg) return `<div class="wrap lb">${sw}${lbEmptyHTML()}</div>`;
  const cols = lbCols(lg);
  return `<div class="wrap lb">${sw}${lbWhatHTML()}${lbSortsHTML(lg)}
    <section class="lb-grid" data-testid="teams-grid" aria-label="${t("lboard.cards.aria")}">${lbRows(lg).map(tm => lbCardHTML(tm, lg, cols)).join("")}</section>
    ${lbKeyHTML()}</div>`;
}

/* "This is my team" on a card's foot: the team switch's own pick (teamswitch.js), so My teams, Live and the
   rest follow, and the board redraws with the card pinned as the reader's. */
function lbCardMine(key){
  pickTeam(key);
  document.querySelector(".lb-yours")?.focus({preventScroll: true});
}

/* A chip tap redraws the cards in place, so the switch above never moves; focus stays on the chip. */
function wireLb(v){
  wireLgChip(v);
  v.querySelectorAll("[data-lbsort]").forEach(b => b.addEventListener("click", () => {
    LB_SORT = b.dataset.lbsort || null;
    render();
    v.querySelector(`[data-lbsort="${b.dataset.lbsort}"]`)?.focus({preventScroll: true});
  }));
  v.querySelectorAll("[data-lbmine]").forEach(b => b.addEventListener("click", () => lbCardMine(b.dataset.lbmine)));
  v.querySelectorAll("[data-lbtrade]").forEach(b => b.addEventListener("click", () => tfOpenWith(b.dataset.lbtrade)));   // finder/finder.js
}
