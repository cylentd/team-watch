/* The Props tab (2026-09-29, David: "I want to be able to see his receptions, yds, tds as bar
   chart in the past X games"). One chart per market he is bet on, his last games from ff-jarvis's
   market log (as far back as it goes, up to twelve), drawn by the Parlay leg sheet's own bars
   (parlay/legsheet.js legBarsHTML): lime where he cleared this week's line, the line as a rule,
   the stat that drives the bet under each game. With no line posted yet (a Monday) the bars
   stand alone and the hit count goes.

   Its own tab rather than more rows under Season, which is already a row a week; and only for a
   player with a market log, so nobody gets an empty pane. */
const PF_PROP_MKTS = {QB: ["PASS", "RUSH"], RB: ["RUSH", "RECS", "REC", "TD"], WR: ["RECS", "REC", "TD"], TE: ["RECS", "REC", "TD"]};

function pfPropLog(slug){
  const log = typeof LIVE_MARKET !== "undefined" && LIVE_MARKET && LIVE_MARKET.logs ? LIVE_MARKET.logs[slug] : null;
  return log && log.g && log.g.length ? log : null;
}

/* This week's line on the market when one is posted, the leg sheet's own (legSide), but always
   read as the over: the leg sheet shows the side the model picks, and on a profile "under 1.5
   catches in 8 of 12" would be the model's bet posing as his record. No line: a bare row that
   legBarsHTML draws without a rule. */
function pfPropSide(p, mkt){
  const row = (typeof PROPS !== "undefined" ? PROPS : []).find(r => r.mkt === mkt && (r.slug || slugOf(r.n)) === p.slug);
  return row ? {row, s: {line: legSide(row).line, pick: "higher"}}
    : {row: {mkt, slug: p.slug, n: p.n, pos: p.pos}, s: {line: null, pick: "higher"}};
}

function propsHTML(p){
  const log = p && p.slug ? pfPropLog(p.slug) : null;
  if (!log) return "";
  // A market he never records (a receiver's rushing, a back with no catches) is a row of zeros.
  const mkts = (PF_PROP_MKTS[p.pos] || []).filter(m => (log.v[m] || []).some(v => v > 0));
  return mkts.map(m => {
    const {row, s} = pfPropSide(p, m);
    const bars = legBarsHTML(row, s, log);
    return bars ? secHTML(esc(MKT[m]), bars, "", "pf-sec-prop") : "";
  }).join("");
}
