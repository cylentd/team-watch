/* ------------------------------------------------------------------
   PREVIEW's hand-off to Slips. From 2026-10-03 to 2026-10-09 a box-score section, "From this game to your
   slip", repeated every player call with his line row (storyboard "Slips research board", frame 3). Since
   ledger #82 (2026-10-09) each player call carries it: his yards are a tap to his lines in the Slips player
   sheet (dossier.js pvPlayerHTML), and under the players one button, "All N players in Slips", opens Slips
   on this game's kickoff with its card in view. Facts and the take's own words only; never advice.
------------------------------------------------------------------ */
/* The board's rows for this game: both clubs, either spelling. */
function pvSlipRows(g){
  const want = new Set([schedCode(g.away), schedCode(g.home)]);
  return PROPS.map((p, i) => [p, i]).filter(([p]) => {
    const ts = slTeams(p.game);
    return ts.length === 2 && ts.every(c => want.has(schedCode(c))) && slVisible(p);
  });
}

/* "All N players in Slips ›", or nothing when Slips holds no line for the game. */
function pvSlipAllHTML(g){
  const rows = pvSlipRows(g), n = new Set(rows.map(([p]) => slSlug(p))).size;
  if (!n) return "";
  const first = rows[0][0];
  return `<button type="button" class="chip pv-slgo" data-testid="preview-slip-all" data-pvslips="${esc(first.win || "")}" data-pvgame="${esc(first.game)}">${t("preview.slip.all", {n})}${SL_CHEV}</button>`;
}

/* Slips on this game's kickoff, its card in view. The dossier's history entry stays and so does
   PV_OPEN: Back from Slips lands on the dossier, not the slate (layers.js, layerForget / layerAdopt). */
function pvToSlips(b){
  GAL_WIN = b.dataset.pvslips || "ALL";
  SL_FOCUS = b.dataset.pvgame;
  layerForget("preview");
  window.scrollTo(0, 0);
  navGo("parlay");
}

function wirePvSlip(v){
  v.querySelectorAll("[data-slplayer]").forEach(b => b.addEventListener("click", () => playerSheetOpen(b.dataset.slplayer, b)));
  v.querySelectorAll("[data-slpick]").forEach(b => b.addEventListener("click", () => slPick(b)));
  v.querySelectorAll("[data-pvslips]").forEach(b => b.addEventListener("click", () => pvToSlips(b)));
  wireTray(v);
}
