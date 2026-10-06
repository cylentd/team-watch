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

/* One week: the opponent's code over the week number, or BYE. Never a colour for good or bad. */
function sosCellHTML(c){
  const aria = c.bye ? t("sos.cell.byeAria", {week: c.week}) : t("sos.cell.gameAria", {week: c.week, opp: esc(c.opp)});
  return `<li class="sos-c${c.bye ? " bye" : ""}" data-testid="schedule-cell" aria-label="${aria}"><i>${c.week}</i><b>${c.bye ? t("sos.cell.bye") : esc(c.opp)}</b></li>`;
}

function sosRowHTML(r){
  const pts = r.pts === null ? "" : r.pts.toFixed(1);
  return `<li class="sos-row" data-testid="schedule-row">
    <span class="sos-n">${r.rank === null ? "" : r.rank}</span>
    <span class="sos-who"><b class="sos-team">${esc(r.team)}</b><span class="sos-g">${sosGames(r.games)}</span></span>
    <span class="sos-pts" data-testid="schedule-pts" ${pts ? `aria-label="${t("sos.row.ptsAria", {n: pts})}"` : ""}>${pts ? t("sos.row.pts", {n: `<b data-testid="schedule-pts-value">${pts}</b>`}) : ""}</span>
    <ol class="sos-cells" data-testid="schedule-cells">${r.cells.map(sosCellHTML).join("")}</ol>
  </li>`;
}

/* The one control row: position, then the weeks. Chips, not selects: each is a short set that stays visible. */
function sosControlsHTML(){
  const seg = (label, attr, cur, items, tid) => `<div class="sos-seg" role="group" aria-label="${label}">${
    items.map(([k, text]) => `<button type="button" class="chip" data-testid="${tid}" data-${attr}="${k}" aria-pressed="${cur === k}">${text}</button>`).join("")}</div>`;
  return `<div class="sos-ctl" data-testid="schedule-control">${seg(t("sos.pos.label"), "sospos", SOS_PICK_POS, SOS_POS.map(p => [p, p]), "schedule-pos-chip")
    }${seg(t("sos.win.label"), "soswin", SOS_PICK_WIN, SOS_WINDOWS.map(w => [w, sosWinLabel(w)]), "schedule-win-chip")}</div>`;
}

function sosPageHTML(){
  const v = sosView(typeof LIVE_SOS === "undefined" ? null : LIVE_SOS, SOS_PICK_POS, SOS_PICK_WIN);
  if (!v) return `<div class="wrap"><div class="state-empty" data-testid="schedule-empty" style="min-height:220px">
    <div><b>${t("sos.empty.title")}</b><span>${t("sos.empty.sub")}</span></div></div></div>`;
  return `<div class="wrap sos">
    ${sosControlsHTML()}
    <div class="sos-head" data-testid="schedule-head"><h2 data-testid="schedule-title">${t("sos.head.title", {pos: SOS_PICK_POS, span: v.span})}</h2><p data-testid="schedule-label">${esc(v.label)}</p></div>
    <ol class="sos-list">${v.rows.map(sosRowHTML).join("")}</ol>
  </div>`;
}

function wireSos(v){
  v.querySelectorAll("[data-sospos]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.sospos === SOS_PICK_POS) return;
    SOS_PICK_POS = b.dataset.sospos; render();
  }));
  v.querySelectorAll("[data-soswin]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.soswin === SOS_PICK_WIN) return;
    SOS_PICK_WIN = b.dataset.soswin; render();
  }));
}
