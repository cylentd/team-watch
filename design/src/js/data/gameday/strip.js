/* ============================== LIVE: WHICH LEAGUE, WHICH GAME ==============================
   Live opens on the reader's team's league (2026-10-05, storyboard
   https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP, option 2A). The team decides it: the one the
   reader picked (tw-team), else the first they follow that plays in a league here. Live's own league
   setting (tw-live-league) and its chips went the same day: to switch leagues, the reader switches
   teams. My league leads with a strip of the league's matchups, the reader's first.

   Pure functions of the data: the surface (surface/live/) passes in GD.leagues, the keys and the
   sides; tests/test_js_gdstrip.py runs them in Node. */

/* The league a team plays in, by its page key (design/gameday.py bakes it beside the team's name). */
const gdTeamLeague = (leagues, key) =>
  (key && leagues.find(lg => Object.values(lg.teams).some(t => t.key === key))) || null;

/* Live's league: that of the first of `keys` (the picked team, then the followed ones) that plays in
   one. A pick Live has no data for (a connected league) falls through to what is followed. */
function gdLeagueFor(leagues, keys){
  for (const k of keys){
    const lg = gdTeamLeague(leagues, k);
    if (lg) return lg;
  }
  return null;
}

/* The reader's team id in a league: the first of `keys` that plays there, or null. */
function gdTeamId(lg, keys){
  if (!lg) return null;
  for (const k of keys){
    const id = k && Object.keys(lg.teams).find(i => lg.teams[i].key === k);
    if (id) return id;
  }
  return null;
}

/* Three tabs since 2026-10-05: My league (id "league"), NFL (id "games") and TDs. A stored value from
   the four tabs before maps over: Matchup and League merged into My league. */
const GD_TAB_WAS = {matchup: "league", league: "league", games: "games", tds: "tds"};
const gdTabOf = v => GD_TAB_WAS[v] || "league";

const gdSameGame = (g, h) => !!(g && h) && g[0] === h[0] && g[1] === h[1];

/* The strip's order: the reader's game first, the rest as the league lists them, so a poll never
   reshuffles the chips. A team with no game this week (a bye, out of the fantasy playoffs, week 18)
   leads with the league's closest game instead: the smallest gap in `pts` (team id -> points); level
   gaps keep the league's order. Playoff weeks with fewer games simply return fewer. */
function gdStripOrder(games, pts, mine){
  if (!games.length) return [];
  const gap = g => Math.abs((pts[g[0]] || 0) - (pts[g[1]] || 0));
  let lead = mine ? games.findIndex(g => g.includes(mine)) : -1;
  if (lead < 0) lead = games.reduce((best, g, i) => gap(g) < gap(games[best]) ? i : best, 0);
  return [games[lead], ...games.filter((_, i) => i !== lead)];
}

/* The game the score head and the lineups show: the one tapped in the strip, else the reader's. A
   reader whose team has no game this week gets null, and the head says so rather than drawing an
   empty matchup. A tap remembered from another league is ignored. */
function gdGameOn(games, pick, mine){
  const tapped = pick && games.find(g => gdSameGame(g, pick));
  if (tapped) return tapped;
  return (mine && games.find(g => g.includes(mine))) || null;
}

/* A chip's state word: live while any starter on either side plays, else how many are still to play,
   else final. */
function gdChipState(a, b){
  const left = a.playing + b.playing + a.left + b.left;
  if (a.playing + b.playing) return {k: "live", n: left};
  return left ? {k: "left", n: left} : {k: "final", n: 0};
}

/* A team's name in a few whole words, for a chip 124px wide: whole words while they fit `max`, never
   ending on a joining word; a first word longer than that is cut with an ellipsis. */
const GD_JOIN = /^(the|of|in|a|an|and|&|\+|-|my)$/i;
function gdShortName(name, max = 12){
  const words = String(name).trim().split(/\s+/);
  if (words[0].length > max) return words[0].slice(0, max - 1) + "…";
  const out = [];
  for (const w of words){
    if ([...out, w].join(" ").length > max) break;
    out.push(w);
  }
  while (out.length > 1 && GD_JOIN.test(out[out.length - 1])) out.pop();
  return out.join(" ");
}
