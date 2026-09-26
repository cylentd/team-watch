/* This week > Weather's rows (2026-09-26): every game of this week, joined to the forecast at its
   stadium and to the reader's own players in it. Facts only: the page says what the sky is, never
   what it does to anyone, because no weather effect here has been backtested.

   Sources: LIVE_SCHEDULE (the week and its games, ESPN club codes), LIVE_WEATHER (ff-jarvis's
   model.clients.weather, keyed by the home club in nflverse codes; schedTeamRow bridges the two),
   and TEAMS (the rosters the Roster view draws). A forecast counts only when it is for this game's
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

/* The reader's own players in a game, both leagues, once each with every league he is in. A
   leaguemate's roster (data/mates.js) is not the reader's, so it is left out, as on Ranks. */
const WT_POS = ["QB", "RB", "WR", "TE", "K", "DST"];
function wtMine(g){
  const by = new Map();
  Object.values(TEAMS).filter(tm => !tm.mate).forEach(tm => (tm.roster || []).forEach(p => {
    const code = schedCode(p.team);
    if (code !== g.home && code !== g.away) return;
    const key = p.slug || `${p.n}|${p.pos}`;
    const row = by.get(key) || {p, leagues: []};
    if (!row.leagues.includes(tm.plat)) row.leagues.push(tm.plat);
    by.set(key, row);
  }));
  const rank = pos => { const i = WT_POS.indexOf(pos); return i < 0 ? WT_POS.length : i; };
  return [...by.values()].sort((a, b) => rank(a.p.pos) - rank(b.p.pos) || a.p.n.localeCompare(b.p.n));
}

/* {week, indoor, open}. Indoor is every dome, in kickoff order. Open is the rest (open air, a
   retractable roof, a club with no row), by the top of the wind range, most first; a game with no
   forecast sorts last. The sort is a plain ordering by one number, and the page labels it so. */
function wtRows(){
  const week = schedWeek();
  const rows = schedGamesOf(week).map(g => {
    const {roof, fc} = wtForecast(g);
    return {g, roof, fc, mph: fc ? wxWindMph(fc) : null, mine: wtMine(g)};
  });
  const open = rows.filter(r => r.roof !== "dome")
    .sort((a, b) => (b.mph === null ? -1 : b.mph) - (a.mph === null ? -1 : a.mph));
  return {week, indoor: rows.filter(r => r.roof === "dome"), open};
}
