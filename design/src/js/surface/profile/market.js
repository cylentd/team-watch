/* The market row inside Details: what the books (or, lacking a line, the model) say about his
   next game. METHODOLOGY 12.46 failed its backtest (a move against his last game pointed the wrong
   way), so this is the levels only: no BUY/SELL, no "rising"/"falling", and since 2026-10-06 no arrow,
   no up/down colour and no z (the move over his sector's sd) on any line. */
function pfNum(v, digits){
  return v === null || v === undefined ? "—" : Number(v).toFixed(digits);
}

/* MKT_SHORT (data/market.js) already carries these labels for the parlay pool; reused as-is so
   there is one map, not two copies of the same content.json keys. */
function marketPricedText(markets){
  return (markets && markets.length) ? markets.map(k => MKT_SHORT[k] || k).join(" · ") : "—";
}

function marketHTML(prof){
  const m = stockFor(prof);
  if (!m) return "";
  // No UNTESTED tag since 2026-09-29 (details.js zoneReadHTML says why).
  const priced = (m.markets && m.markets.length)
    ? `<p class="pf-cap pf-fine" data-testid="profile-cap">${t("profile.market.priced", {markets: esc(marketPricedText(m.markets))})}</p>`
    : `<p class="pf-cap pf-quiet" data-testid="profile-cap">${t("profile.market.noMarket")}</p>`;
  /* The model's number is the projection every other view prints (stockPts, data/stock.js); the books'
     own number, with its move, sits on its own line and says whose it is. */
  const pts = stockPts(m, prof);
  const model = pts.model === null ? "" : `<p class="pf-cap" data-testid="profile-cap">${t("profile.market.model", {pts: pfNum(pts.model, 1)})}</p>`;
  if (m.no_market || m.src !== "market"){
    return subHTML(t("profile.market.label"), `
      ${model}
      ${priced}`);
  }
  return subHTML(t("profile.market.label"), `
    ${model}
    <p class="pf-cap" data-testid="profile-cap">${t("profile.market.line.pts", {pts: pfNum(pts.books, 1)})}</p>
    <p class="pf-cap" data-testid="profile-cap">${t("profile.market.line.role", {role: pfNum(m.role_pts, 1)})}</p>
    <p class="pf-cap" data-testid="profile-cap">${t("profile.market.line.rank", {pos: esc(m.pos), rank: m.rank ?? "—"})}</p>
    ${priced}`);
}
