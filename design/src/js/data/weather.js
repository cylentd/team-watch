/* This week > Weather's rows (2026-09-26): every game of this week, joined to the forecast at its
   stadium, split into the games whose weather moves scoring (what it does comes from the
   backtest, data/wxhistory.js; who it hits from LIVE_WX_HITS) and the rest. No roster is read.

   Sources: LIVE_SCHEDULE (the week and its games, ESPN club codes), LIVE_WEATHER (ff-jarvis's
   model.clients.weather, keyed by the home club in nflverse codes; schedTeamRow bridges the two),
   and LIVE_WX_HITS (design/wx_hits.py). A forecast counts only when it is for this game's
   kickoff: LIVE_WEATHER holds each stadium's NEXT home kickoff, which after a game is next week's. */

/* The forecast at a game's stadium: {roof, fc}. `roof` is null when the club is not in the block;
   `fc` is null for a dome, a missing forecast, or one for another kickoff. */
function wtForecast(g){
  const w = schedTeamRow(typeof LIVE_WEATHER !== "undefined" ? LIVE_WEATHER : null, g.home);
  if (!w) return {roof: null, fc: null};
  const thisGame = !w.kickoff || Date.parse(w.kickoff) === Date.parse(g.kickoff);
  const has = w.roof !== "dome" && thisGame && w.temp_f !== null && w.temp_f !== undefined;
  return {roof: w.roof || null, fc: has ? w : null};
}

/* Who a game's weather hits: each side's top QB, two WRs and TE by projected points (LIVE_WX_HITS,
   design/wx_hits.py), away side first. League-wide on purpose: the view is public, so it never
   reads a roster. */
function wtHits(g){
  const block = typeof LIVE_WX_HITS !== "undefined" ? LIVE_WX_HITS : null;
  return [g.away, g.home].flatMap(team => schedTeamRow(block, team) || []);
}

/* {week, moves, indoor, open, played}. `moves` is every game whose forecast meets a proven
   condition (data/wxhistory.js), with `conds` and `effects`, most points moved first. The rest
   split into domes and the others (open air, retractable, a club with no row), each in kickoff
   order. A game that has kicked off has no forecast left, so it goes to `played`. */
function wtRows(){
  const week = schedWeek(), now = Date.now();
  const rows = schedGamesOf(week).map(g => {
    const {roof, fc} = wtForecast(g);
    const r = {g, roof, fc, mph: fc ? wxWindMph(fc) : null};
    r.conds = wtConditions(r);
    r.effects = r.conds.length ? wtEffects(r.conds) : [];
    r.hits = r.effects.length ? wtHits(g) : [];
    return r;
  }).sort((a, b) => Date.parse(a.g.kickoff) - Date.parse(b.g.kickoff));
  const played = rows.filter(r => Date.parse(r.g.kickoff) <= now);
  const ahead = rows.filter(r => !played.includes(r));
  const weight = r => r.effects.reduce((s, e) => s + Math.abs(e.pts), 0);
  const moves = ahead.filter(r => r.effects.length).sort((a, b) => weight(b) - weight(a));
  const rest = ahead.filter(r => !r.effects.length);
  return {week, moves, indoor: rest.filter(r => r.roof === "dome"), open: rest.filter(r => r.roof !== "dome"), played};
}
