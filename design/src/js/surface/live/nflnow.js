/* ============================== LIVE: THE GAMES TAB ==============================
   Every NFL game of the week as a tile (2026-10-04, storyboard
   https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV, option A): live first, then the next kickoffs,
   then the finals. A tile is the game's clock over two clubs and their scores; one that holds
   starters of mine wears a lime edge and says how many. A tap opens the game in the game sheet
   (gamesheet.js). It replaced the NFL now card that drew above the matchup.

   The score is Sleeper's: a club's defense row counts the points it allowed, which is the other
   club's score. /api/stats already carries every club of the week for that (gdUrl), so the tab
   costs no request of its own. The clock is ESPN's (data/gameday/clock.js). The schedule speaks
   ESPN's codes (WSH), Sleeper its own (WAS); GD_ALIAS holds the pairs. */

/* A club's code in every spelling the schedule and Sleeper use. */
function gdCodes(club){
  return [club, GD_ALIAS[club], ...Object.keys(GD_ALIAS).filter(k => GD_ALIAS[k] === club)].filter(Boolean);
}
const gdByCode = (map, club) => { for (const c of gdCodes(club)) if (map && map[c] !== undefined) return map[c]; };
const gdSameClub = (a, b) => gdCodes(a).includes(b);

function gdWeekGames(){
  const week = (GD.leagues[0] || {}).week;
  return GD_GAMES.filter(g => g.week === week);
}

/* What data-gdnfl carries and wireLive hands to gsOpen: "espnEvent,away,home". */
const gdNflKey = g => [g.espn || "", g.away, g.home].join(",");

/* The club's score: the points the other club's defense allowed. */
function gdClubScore(club, other){
  const d = gdByCode((GD_STATS && GD_STATS.stats) || {}, other);
  return d ? +(d.pts_allow || 0) : null;
}

/* A club's game this week: its kickoff, whether it is at home, the other club, and the game's
   data-gdnfl key. */
function gdGameOf(club){
  if (!club) return null;
  const g = gdWeekGames().find(x => gdSameClub(x.home, club) || gdSameClub(x.away, club));
  if (!g) return null;
  const home = gdSameClub(g.home, club);
  return {kickoff: g.kickoff, home, opp: home ? g.away : g.home, key: gdNflKey(g)};
}

/* How many of the reader's starters, in the league on screen, play in it (0 without a team there). */
function gdMineIn(g, lg){
  return gdMineLineup(lg).filter(gdStarter).filter(r => r.team && (gdSameClub(g.home, r.team) || gdSameClub(g.away, r.team))).length;
}

/* Games on now, for the tab's lime count. */
function gdLiveCount(){
  return gdWeekGames().filter(g => gdClockOf(g.home).live).length;
}

/* Live games first, then the ones still to play by kickoff, finals last. */
function gdGamesSorted(){
  const rank = c => c.state === "in" ? 0 : c.state === "pre" ? 1 : 2;
  return gdWeekGames().map(g => ({g, c: gdClockOf(g.home)}))
    .sort((a, b) => rank(a.c) - rank(b.c) || Date.parse(a.g.kickoff) - Date.parse(b.g.kickoff));
}

/* The club's colour as the Games tab wears it on the dark panel: its first colour that holds ~3:1
   against --panel (relative luminance 0.12 and up), else its primary lifted toward white until it
   does, so a navy or forest club still wins in its own hue (2026-10-05: plain ink left 9 of 32
   clubs uncoloured). A colour that is black or grey has no hue to keep, and the row stays --ink. */
const GD_TILE_LUMA = 0.12;
function gdLift(hex){
  const rgb = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  if (Math.max(...rgb) - Math.min(...rgb) < 40) return null;
  for (let w = 0.1; w < 1; w += 0.1){
    const out = "#" + rgb.map(v => Math.round(v + (255 - v) * w).toString(16).padStart(2, "0")).join("");
    if (teamLuma(out) >= GD_TILE_LUMA) return out;
  }
  return null;
}
function gdClubTint(club){
  const c = gdByCode(TEAM_COLOURS, club);
  return c ? c.find(hex => teamLuma(hex) >= GD_TILE_LUMA) || gdLift(c[0]) || gdLift(c[1]) : null;
}

/* The ball beside the club that has it (U9): a small football, named for a screen reader. */
const GD_BALL = `<svg viewBox="0 0 20 12" aria-hidden="true"><g transform="rotate(-28 10 6)"><ellipse cx="10" cy="6" rx="9" ry="4.6"/><path d="M6.5 6h7M8 4.6v2.8M10 4.4v3.2M12 4.6v2.8"/></g></svg>`;
const gdBallMark = club => `<i class="gd-ball" role="img" aria-label="${esc(t("live.games.ball", {club}))}">${GD_BALL}</i>`;

/* A live tile's third line: the down and distance (or who has the ball), and the red-zone mark inside the 20. */
function gdSitHTML(sit){
  return `<small class="gd-sit"><span>${esc(gdSitText(sit))}</span>${sit.red ? `<em class="gd-rz">${t("live.games.red")}</em>` : ""}</small>`;
}

function gdGamesTabHTML(lg){
  const all = gdGamesSorted();
  if (!all.length) return `<div class="state-empty"><div><b>—</b><span>${t("live.games.none")}</span></div></div>`;
  const tiles = all.map(({g, c}) => {
    const mine = gdMineIn(g, lg), a = gdClubScore(g.away, g.home), h = gdClubScore(g.home, g.away);
    const on = c.state !== "pre" && a !== null && h !== null;
    const sit = c.state === "in" ? gdSitOf(g.home) : null;       // who has the ball, from the scoreboard's own read
    // the leader wears its club's colour, the trailer greys, a tie or no score stays plain
    const club = (code, s, o) => {
      const lead = on && s > o, tint = lead ? gdClubTint(code) : null;
      const ball = sit && gdSameClub(code, sit.ball) ? gdBallMark(code) : "";
      return `<span class="gd-tr${on && s < o ? " behind" : lead ? " lead" : ""}"${tint ? ` style="--tc:${tint}"` : ""}><span>${ball}${esc(code)}</span><b>${on ? s : "—"}</b></span>`;
    };
    return `<button type="button" class="gd-t ${c.state}${mine ? " mine" : ""}" data-gdnfl="${esc(gdNflKey(g))}" aria-haspopup="dialog">
      <small class="gd-ts"><span>${esc(c.label)}</span>${mine ? `<em>${t("live.games.yours", {n: mine})}</em>` : ""}</small>
      ${club(g.away, a, h)}${club(g.home, h, a)}${sit ? gdSitHTML(sit) : ""}</button>`;
  }).join("");
  return `<div class="gd-tiles">${tiles}</div>`;
}
