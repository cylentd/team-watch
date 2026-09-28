/* THE TD BOARD (2026-09-27): under the TD slips on Slips' TDs chip, every anytime-TD line still to
   play at the chosen kickoff, ranked by the model's P(score) -- the one number grading found honest
   (ff-jarvis METHODOLOGY 12.31). One row a player: the model, DraftKings' own chance from its over
   price, his red-zone touches a game, and his games with a score in the last ten. A row opens the
   leg sheet, which carries the rest and the Add button.

   Under the slips, not behind a toggle: a toggle is another row of controls above the data
   (design/STYLE.md), and the chip that shows the TD slips is already the question "who scores". */
const TD_TOP = 20;       // rows before "Show all"
let TD_ALL = false;

function tdBoardRows(){
  const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
  return PROPS.map((p, i) => [p, i])
    .filter(([p]) => p.mkt === "TD" && typeof p.model === "number" && upcoming(p) && playing(p) && (GAL_WIN === "ALL" || inWin(p, win)))
    .sort((a, b) => b[0].model - a[0].model || a[0].n.localeCompare(b[0].n));
}

function tdRowHTML([p, i]){
  const dk = p.books && p.books.DraftKings, book = dk && typeof dk.over === "number" ? Math.round(amToProb(dk.over) * 100) : null;
  const log = legLog(p), rz = legRzPerGame(p, log);
  const tds = log && log.v.TD && log.v.TD.length ? `${log.v.TD.filter(v => v >= 1).length}/${log.v.TD.length}` : "";
  return `<button type="button" class="tdb-row${p.mine ? " mine" : ""}" data-legsheet="${i}" aria-haspopup="dialog">
      <span class="tdb-who"><b>${esc(nameInitial(p.n))}</b><small>${esc([p.pos, p.team].filter(Boolean).join(" · "))}</small></span>
      <span class="tdb-n tdb-model">${Math.round(p.model)}<i>%</i></span>
      <span class="tdb-n">${book === null ? "" : `${book}<i>%</i>`}</span>
      <span class="tdb-n">${rz === null ? "" : rz.toFixed(1)}</span>
      <span class="tdb-n">${tds}</span>
    </button>`;
}

function tdBoardHTML(){
  const rows = tdBoardRows();
  if (!rows.length) return "";
  const shown = TD_ALL ? rows : rows.slice(0, TD_TOP);
  return `<section class="tdb">
      <div class="tk-when"><h3>${t("tdboard.title")}</h3><span>${t("tdboard.meta", {n: rows.length})}</span></div>
      <div class="tdb-list">
        <div class="tdb-row tdb-head" aria-hidden="true"><span>${t("tdboard.col.player")}</span><span>${t("tdboard.col.model")}</span>
          <span>${t("tdboard.col.book")}</span><span>${t("tdboard.col.rz")}</span><span>${t("tdboard.col.last")}</span></div>
        ${shown.map(tdRowHTML).join("")}
      </div>
      ${rows.length > TD_TOP ? `<button type="button" class="chip tdb-all" data-tdall>${TD_ALL ? t("tdboard.less", {n: TD_TOP}) : t("tdboard.all", {n: rows.length})}</button>` : ""}
    </section>`;
}
