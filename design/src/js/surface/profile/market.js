/* The market row inside Details: what the books (or, lacking a line, the model) say about his
   next game. METHODOLOGY 12.46 failed its backtest, so this is numbers only -- no BUY/SELL,
   no "rising"/"falling". A number can still carry an arrow and the existing up/down colour
   (roster.css's .delta), which the copy rule allows; the words never do. */
function pfDelta(v, digits){
  if (v === null || v === undefined) return "";
  const k = v > 0 ? "up" : v < 0 ? "down" : "flat";
  const g = v > 0 ? "▲" : v < 0 ? "▼" : "—";
  const n = Math.abs(v).toFixed(digits);
  return ` <span class="delta ${k}" data-testid="profile-delta">${g} ${n}</span>`;
}

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
  /* d_rank of exactly 0 (or null) gets no marker: "#2 — 0" beside a rank reads as a range, not
     as "no change." z describes the same role move as role_pts, so it sits on that line; the
     rank line holds rank and its own delta only. */
  return subHTML(t("profile.market.label"), `
    ${model}
    <p class="pf-cap" data-testid="profile-cap">${t("profile.market.line.pts", {pts: pfNum(pts.books, 1)})}${pfDelta(m.d_pts, 1)}</p>
    <p class="pf-cap" data-testid="profile-cap">${t("profile.market.line.role", {role: pfNum(m.role_pts, 1)})}${pfDelta(m.d_role_pts, 1)} · ${t("profile.market.line.z", {z: pfNum(m.z, 2)})}</p>
    <p class="pf-cap" data-testid="profile-cap">${t("profile.market.line.rank", {pos: esc(m.pos), rank: m.rank ?? "—"})}${m.d_rank ? pfDelta(m.d_rank, 0) : ""}</p>
    ${priced}`);
}
