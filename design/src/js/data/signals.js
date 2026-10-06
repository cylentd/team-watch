/* A roster row's Trend, Rank and News cells, from two ff-jarvis sources and nothing hand-typed:
   - LIVE_SIGNALS (design/signals.py): weekly snap share from model.season.watch for the line,
     its verdict, and how many scanner stories name him in the last 72 hours.
   - LIVE_MARKET_STOCK: the delta (market-implied points against his previous game's price) and
     the position rank among priced players. Neither source is backtested, so no cell here turns
     a number into advice beyond watch's own verdict word.
   Runs at load from hydrate.js, so it indexes the blocks directly: slugOf is declared later. */
const RANK_OF = {};
function pricedAt(pos){
  if (RANK_OF[pos] === undefined){
    const all = (typeof LIVE_MARKET_STOCK !== "undefined" && LIVE_MARKET_STOCK) ? Object.values(LIVE_MARKET_STOCK.players) : [];
    RANK_OF[pos] = all.filter(s => s.pos === pos && s.rank !== null).length;
  }
  return RANK_OF[pos];
}

/* A missed week is left out of the line rather than drawn as zero snaps; a line needs two points. */
function trendLine(series){
  const v = (series || []).filter(x => x !== null && x !== undefined);
  return v.length >= 2 ? v : null;
}

/* watch's reason for a verdict, as a sentence a reader can act on (plan U3, 2026-10-05; the audit's
   "RISING snaps −5.0, share +19; buy or start" was jargon with a minus sign). ff-jarvis writes two
   shapes (model/season/watch.py verdict()): RISING "snaps {d:+.1f}, share {d:+.0f}; buy or start" and
   SELL HIGH "{luck:+.0%} over what the usage bought, on a part-time role". Anything else comes back as
   it was written, and nothing without a verdict is a sentence. Plain text: the caller escapes it. */
const SIG_NUM = "([+\\-\\u2212]?\\d+(?:\\.\\d+)?)";
function signalWords(verdict, why){
  if (!verdict || !why) return "";
  const move = n => {
    const v = parseFloat(String(n).replace("−", "-"));
    return {dir: Math.abs(v) < 0.05 ? "flat" : v > 0 ? "up" : "down", n: Math.abs(v)};
  };
  const phrase = (m, fmt) => m.dir === "flat" ? t("profile.signal.flat")
    : m.dir === "up" ? t("profile.signal.up", {n: fmt(m.n)}) : t("profile.signal.down", {n: fmt(m.n)});
  const rising = new RegExp(`^snaps ${SIG_NUM}, share ${SIG_NUM}; buy or start$`).exec(why);
  if (verdict === "RISING" && rising)
    return t("profile.signal.rising", {snaps: phrase(move(rising[1]), n => n.toFixed(1)), share: phrase(move(rising[2]), n => String(Math.round(n)))});
  const hot = new RegExp(`^${SIG_NUM}% over what the usage bought, on a part-time role$`).exec(why);
  if (verdict === "SELL HIGH" && hot) return t("profile.signal.hot", {n: Math.round(Math.abs(parseFloat(hot[1])))});
  return why;
}

function signalsFor(p){
  const sig = (typeof LIVE_SIGNALS !== "undefined" && LIVE_SIGNALS && p.slug && LIVE_SIGNALS.players[p.slug]) || {};
  const stock = (typeof LIVE_MARKET_STOCK !== "undefined" && LIVE_MARKET_STOCK && p.slug && LIVE_MARKET_STOCK.players[p.slug]) || null;
  const r = stock && stock.rank !== null ? stock.rank : null;
  const of = r === null ? 0 : pricedAt(stock.pos);
  return {
    trend: trendLine(sig.series),
    d: stock && stock.d_pts !== null ? stock.d_pts : null,
    rank: [r, of, stock ? (stock.d_rank || 0) : null, of ? 1 - (r - 1) / of : 0],
    news: sig.news || 0,
    hot: sig.hot ? 1 : 0,
    verdict: sig.verdict && sig.verdict !== "NEW" && sig.verdict !== "hold" ? sig.verdict : null,
    why: sig.why || "",
  };
}
