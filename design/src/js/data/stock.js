/* ff-jarvis's market.stock (LIVE_MARKET_STOCK): market-implied points and role change per
   player. build.py's load_market_stock() re-keys the producer's players map by the same slug
   profileFor() (ui/matchup.js) uses, so this shares that lookup instead of hand-mirroring
   ff-jarvis's own norm_name join key. `backtested` is false (METHODOLOGY 12.46 failed its bar),
   so every render of this block is numbers only -- no verdict words. */
function stockFor(p){
  if (typeof LIVE_MARKET_STOCK === "undefined" || !LIVE_MARKET_STOCK || !p) return null;
  return LIVE_MARKET_STOCK.players[p.slug || slugOf(p.n)] || null;
}
