/* What the weather does to scoring in a game (reworked 2026-09-26: only what moves scoring), from
   LIVE_WX_HISTORY (design/wx_history.py, ff-jarvis's weather backtest, METHODOLOGY 12.53/12.54).

   A game's conditions are the ones its forecast meets at the block's own thresholds: wind and cold
   from the backtest, the rain chance from the projections' weather_adjust. Only a condition with a
   proven position counts; a dome never does, because the stadium is not the forecast. The effects
   sum each position's means across the conditions met, the way the projection adds its cells. */
const wtHistOk = () => typeof LIVE_WX_HISTORY !== "undefined" && !!LIVE_WX_HISTORY;
const wtNum = v => v !== null && v !== undefined;

/* The proven conditions an open-air or retractable game's forecast meets: wind, precip, cold. */
function wtConditions(r){
  if (!wtHistOk() || !r.fc || r.roof === "dome") return [];
  const th = LIVE_WX_HISTORY.thresholds || {}, out = [];
  if (wtNum(th.wind_mph) && r.mph >= th.wind_mph) out.push("wind");
  if (wtNum(th.precip_pct) && (r.fc.precip_pct || 0) >= th.precip_pct) out.push("precip");
  if (wtNum(th.cold_f) && wtNum(r.fc.temp_f) && r.fc.temp_f <= th.cold_f) out.push("cold");
  return out.filter(c => (LIVE_WX_HISTORY.conditions[c] || {matters: []}).matters.length);
}

/* [{pos, pts}] summed over `conds`, rounded to the half point; a position that rounds to 0 drops.
   Order: the block's own (QB, WR, TE, K, RB), first seen first. */
function wtEffects(conds){
  const sum = new Map();
  conds.forEach(c => LIVE_WX_HISTORY.conditions[c].matters.forEach(m => sum.set(m.pos, (sum.get(m.pos) || 0) + m.mean)));
  return [...sum].map(([pos, v]) => ({pos, pts: Math.round(v * 2) / 2})).filter(e => e.pts !== 0);
}
