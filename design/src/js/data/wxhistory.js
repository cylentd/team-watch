/* Which backtest lines a Weather game gets (2026-09-26), from LIVE_WX_HISTORY (design/wx_history.py,
   ff-jarvis's weather backtest, METHODOLOGY 12.53). The build has already summarised each condition
   into "does it matter" and "already in our projections"; the page only picks which conditions apply.

   A dome gets the dome line. An open-air stadium with a forecast gets one line per condition it
   meets: wind and cold at the backtest's own thresholds (shipped with the block), and rain or snow
   at a forecast chance of WT_WET_PCT or more. That last one is the page's bar, not the backtest's:
   the history is games where rain or snow actually fell, and the forecast is only a probability,
   so the line says both. A retractable roof gets none: the backtest keeps those games out of its
   cells (they are descriptive only there), and the roof may close. */
const WT_WET_PCT = 50;
const wtHistOk = () => typeof LIVE_WX_HISTORY !== "undefined" && !!LIVE_WX_HISTORY;

/* The conditions a game meets that the backtest covers, in a fixed order: dome, wind, cold, precip. */
function wtConditions(r){
  if (!wtHistOk()) return [];
  const th = LIVE_WX_HISTORY.thresholds || {}, out = [];
  if (r.roof === "dome") out.push("dome");
  else if (r.roof === "outdoor" && r.fc){
    if (th.wind_mph !== null && th.wind_mph !== undefined && r.mph >= th.wind_mph) out.push("wind");
    if (th.cold_f !== null && th.cold_f !== undefined && r.fc.temp_f <= th.cold_f) out.push("cold");
    if ((r.fc.precip_pct || 0) >= WT_WET_PCT) out.push("precip");
  }
  return out.filter(c => LIVE_WX_HISTORY.conditions[c]);
}

const wtSummary = cond => LIVE_WX_HISTORY.conditions[cond];
