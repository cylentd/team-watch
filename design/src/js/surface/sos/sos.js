/* ------------------------------------------------------------------
   SCHEDULE — Stats > Schedule (leaf `schedule`, 2026-10-05, plan U7). Which teams face the softest
   defenses at a position: the 32 teams easiest first, the points the opposing defenses allow that position
   per game, and the opponents week by week with the byes marked. Context, not backtested: the file's own
   label is the one line under the heading, and no row says start, sit, buy or sell.

   Hidden from the sub-row (NAV_HIDDEN, data/navmap.js): #schedule and navGo("schedule") open it. One
   control row, position then weeks (STYLE.md). The rows are a list to read, with nothing to tap.
   Data: LIVE_SOS (design/sos.py) cut by data/sos.js sosView(); this file only draws what that returns.
------------------------------------------------------------------ */
let SOS_PICK_POS = "RB";
let SOS_PICK_WIN = "next4";

/* Every key spelled out: assemble.py --check cannot see one built from a variable. */
const sosWinLabel = win => ({next4: t("sos.win.next4"), ros: t("sos.win.ros"), playoffs: t("sos.win.playoffs")})[win] || win;

const sosGames = n => (n === 0 ? t("sos.row.game.none") : n === 1 ? t("sos.row.game.one") : t("sos.row.game.many", {n}));

/* One week: the opponent's code over the week number, or BYE. No colour for good or bad, except the next game's
   when its defense's form flagged (`form`): that cell takes the note's arrow and colour, so the note names no team. */
function sosCellHTML(c, form){
  const aria = c.bye ? t("sos.cell.byeAria", {week: c.week}) : t("sos.cell.gameAria", {week: c.week, opp: esc(c.opp)});
  const mark = form ? `<span aria-hidden="true">${form.trend === "up" ? t("dform.arrow.up") : t("dform.arrow.down")}</span>` : "";
  return `<li class="sos-c${c.bye ? " bye" : ""}${form ? ` df ${form.trend}` : ""}" data-testid="schedule-cell" aria-label="${aria}"><i>${c.week}</i><span class="sos-o"><b>${c.bye ? t("sos.cell.bye") : esc(c.opp)}</b>${mark}</span></li>`;
}

/* The next opponent's defense form (2026-11-14, data/defform.js) takes the games count's place: the cells under the
   row already show every game and bye, and the row keeps its two lines and its numbers (rank, points). Words carry the
   trend; its two numbers and the context mark are the tip, since two per-game numbers beside the row's own would read
   as one comparison. At 360px the line has room for the words or a team code, not both: the marked cell names him. */
function sosFormHTML(f){
  return `<span class="sos-form ${f.trend}" data-testid="schedule-form" data-trend="${f.trend}" title="${dfTip(f)}" aria-label="${dfTip(f)}">${f.trend === "up" ? t("dform.vs.up", {df: esc(f.def)}) : t("dform.vs.down", {df: esc(f.def)})}</span>`;
}

function sosRowHTML(r, weeks){
  const pts = r.pts === null ? "" : r.pts.toFixed(1);
  const form = dfNext(typeof LIVE_SOS === "undefined" ? null : LIVE_SOS, SOS_PICK_POS, weeks, r.cells);
  const next = form ? r.cells.find(c => !c.bye) : null;
  return `<li class="sos-row" data-testid="schedule-row">
    <span class="sos-n">${r.rank === null ? "" : r.rank}</span>
    <span class="sos-who"><b class="sos-team">${esc(r.team)}</b>${form ? sosFormHTML(form) : `<span class="sos-g">${sosGames(r.games)}</span>`}</span>
    <span class="sos-pts" data-testid="schedule-pts" ${pts ? `aria-label="${t("sos.row.ptsAria", {n: pts})}"` : ""}>${pts ? t("sos.row.pts", {n: `<b data-testid="schedule-pts-value">${pts}</b>`}) : ""}</span>
    <ol class="sos-cells" data-testid="schedule-cells">${r.cells.map(c => sosCellHTML(c, c === next ? form : null)).join("")}</ol>
  </li>`;
}

/* SOS_PICK_POS is Stats' one position as Schedule shows it (data/statspos.js, 2026-10-06). */
statsPosView("schedule", {attr: "sospos", label: p => p, use: p => { SOS_PICK_POS = p; }});

/* The one control row: position, then the weeks. Chips, not selects: each is a short set that stays visible.
   On a phone the position is the strip above the bottom bar (chrome/statspos.js) and the weeks stand alone. */
function sosControlsHTML(){
  const seg = (label, attr, cur, items, tid) => `<div class="sos-seg" role="group" aria-label="${label}">${
    items.map(([k, text]) => `<button type="button" class="chip" data-testid="${tid}" data-${attr}="${k}" aria-pressed="${cur === k}">${text}</button>`).join("")}</div>`;
  const pos = spChipsOn() ? seg(t("sos.pos.label"), "sospos", SOS_PICK_POS, statsPosList("schedule").map(p => [p, p]), "schedule-pos-chip") : "";
  return `<div class="sos-ctl" data-testid="schedule-control">${pos}${seg(t("sos.win.label"), "soswin", SOS_PICK_WIN, SOS_WINDOWS.map(w => [w, sosWinLabel(w)]), "schedule-win-chip")}</div>`;
}

function sosPageHTML(){
  const v = sosView(typeof LIVE_SOS === "undefined" ? null : LIVE_SOS, SOS_PICK_POS, SOS_PICK_WIN);
  if (!v) return `<div class="wrap"><div class="state-empty" data-testid="schedule-empty" style="min-height:220px">
    <div><b>${t("sos.empty.title")}</b><span>${t("sos.empty.sub")}</span></div></div></div>`;
  return `<div class="wrap sos">
    ${sosControlsHTML()}
    <div class="sos-head" data-testid="schedule-head"><h2 data-testid="schedule-title">${t("sos.head.title", {pos: SOS_PICK_POS, span: v.span})}</h2><p data-testid="schedule-label">${esc(v.label)}</p></div>
    <ol class="sos-list">${v.rows.map(r => sosRowHTML(r, v.weeks)).join("")}</ol>
  </div>`;
}

function wireSos(v){
  v.querySelectorAll("[data-sospos]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.sospos === SOS_PICK_POS) return;
    statsPick(b.dataset.sospos); render();
  }));
  v.querySelectorAll("[data-soswin]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.soswin === SOS_PICK_WIN) return;
    SOS_PICK_WIN = b.dataset.soswin; render();
  }));
}
