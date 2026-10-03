/* ------------------------------------------------------------------
   PREVIEW's hand-off to Slips (2026-10-03, storyboard "Slips research board", frame 3). A box-score
   section, "From this game to your slip": each player Claude's take names who has a line this week,
   with his lines in the player sheet's own row (parlay/lineitem.js), so a side tapped here lands in
   the same tray as on Slips. Then "All N players in Slips", which opens Slips on this game's kickoff
   and brings its card into view. Facts and the take's own words only; never advice.
------------------------------------------------------------------ */
/* The one line a take player shows: his position's own yards market, else the first he has. */
const SL_PRIMARY = {QB: "PASS", RB: "RUSH", WR: "REC", TE: "REC"};

/* The board's rows for this game: both clubs, either spelling. */
function pvSlipRows(g){
  const want = new Set([schedCode(g.away), schedCode(g.home)]);
  return PROPS.map((p, i) => [p, i]).filter(([p]) => {
    const ts = slTeams(p.game);
    return ts.length === 2 && ts.every(c => want.has(schedCode(c))) && slVisible(p);
  });
}

function pvSlipRow(g){
  if (!LIVE_MARKET) return "";
  const rows = pvSlipRows(g), n = new Set(rows.map(([p]) => slSlug(p))).size;
  const ps = (g.take ? g.take.players : []).map(x => ({x, lines: slPlayerRows(x.slug)})).filter(o => o.lines.length)
    .map(({x, lines}) => ({x, n: lines.length, lines: [lines.find(i => PROPS[i].mkt === SL_PRIMARY[x.pos]) ?? lines.find(i => PROPS[i].mkt !== "TD") ?? lines[0]]}));
  if (!ps.length && !n) return "";
  const on = onSlipSlugs();
  const body = ps.map(({x, n: nl, lines}) => `<div class="pv-sl">
      <p class="pv-slh"><b>${shortName(x.n)}</b><small>${esc(x.pos)} · ${esc(x.team)}</small>${on.has(x.slug) ? `<span class="sl-on">${t("slips.onSlip")}</span>` : ""}</p>
      ${x.why ? `<p class="pv-slw">${esc(x.why)}</p>` : ""}
      ${lines.map(slLineHTML).join("")}
      <button type="button" class="chip pv-sln" data-slplayer="${esc(x.slug)}">${t("preview.slip.lines", {n: nl})}${SL_CHEV}</button>
    </div>`).join("");
  const first = rows[0] && rows[0][0];
  const go = n ? `<button type="button" class="chip pv-slgo" data-pvslips="${esc(first.win || "")}" data-pvgame="${esc(first.game)}">${t("preview.slip.all", {n})}${SL_CHEV}</button>` : "";
  return pvRow("handoff", t("preview.row.slip"), body + go);
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
