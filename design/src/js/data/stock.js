/* ff-jarvis's market.stock (LIVE_MARKET_STOCK): market-implied points and role change per
   player. build.py's load_market_stock() re-keys the producer's players map by the same slug
   profileFor() (ui/matchup.js) uses, so this shares that lookup instead of hand-mirroring
   ff-jarvis's own norm_name join key. `backtested` is false (METHODOLOGY 12.46 failed its bar),
   so every render of this block is numbers only -- no verdict words. */
function stockFor(p){
  if (typeof LIVE_MARKET_STOCK === "undefined" || !LIVE_MARKET_STOCK || !p) return null;
  return LIVE_MARKET_STOCK.players[p.slug || slugOf(p.n)] || null;
}

/* The points a profile prints for his next game (2026-10-05). The one number is the projection
   (projFor, LIVE_PROJECTIONS): Season, Ranks, Start/Sit and the Matchup tab read it, so JSN is 16.7 on all
   of them. The stock row's own `pts` was a second source: the books' number on a priced row, the model
   without the line blend on a fallback row (16.8 against 16.7). It stays only as the books' number,
   labelled as theirs, and as the stand-in when the projection file has no row for him.
   -> {model, books}, either null. */
function stockPts(m, p){
  const proj = projFor(p), booked = m.src === "market" && !m.no_market;
  return {model: proj ?? (booked ? null : m.pts ?? null), books: booked ? m.pts ?? null : null};
}
