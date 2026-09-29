/* ============================== LIVE: NFL NOW ==============================
   The NFL games on now, or the next kickoff's when none is (2026-09-28, storyboard
   https://claude.ai/artifact/7dtFfrweZG7mYE6oWSjmFb). Each is drawn the way a league game is, its
   state over two boxes, a club and its score, and a tap opens it in the game sheet (gamesheet.js).

   The score is Sleeper's: a club's defense row counts the points it allowed, which is the other
   club's score. /api/stats already carries every club of the week for that (gdUrl), so the card
   costs no request of its own. The schedule speaks ESPN's codes (WSH), Sleeper its own (WAS);
   GD_ALIAS holds the pairs. */

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

/* pre, live or final, from Sleeper's state and the kickoff, the way gdPlaying reads a club. */
function gdNflState(g, now){
  const st = gdByCode((GD_STATS && GD_STATS.games) || {}, g.home), k = Date.parse(g.kickoff);
  if (st === "complete") return "final";
  if (st === "in_game" || (k <= now && now < k + GD_GAME_MS)) return "live";
  return "pre";
}

/* The games in play; else those at the next kickoff (a Sunday's 1 PM is nine at once). */
function gdNowGames(now){
  const all = gdWeekGames().map(g => ({...g, st: gdNflState(g, now)}));
  const live = all.filter(g => g.st === "live");
  if (live.length) return live;
  const next = Math.min(...all.filter(g => g.st === "pre").map(g => Date.parse(g.kickoff)).filter(k => k > now));
  return isFinite(next) ? all.filter(g => g.st === "pre" && Date.parse(g.kickoff) === next) : [];
}

/* The club's score: the points the other club's defense allowed. */
function gdClubScore(club, other){
  const d = gdByCode((GD_STATS && GD_STATS.stats) || {}, other);
  return d ? +(d.pts_allow || 0) : null;
}

/* How many of my starters, in the league on screen, play in it. */
function gdMineIn(g, lg){
  const tm = lg && lg.teams[lg.me];
  if (!tm) return 0;
  return tm.lineup.filter(gdStarter).filter(r => r.team && (gdSameClub(g.home, r.team) || gdSameClub(g.away, r.team))).length;
}

function gdNowHTML(lg){
  const now = Date.now(), games = gdNowGames(now);
  if (!games.length) return "";
  const tiles = games.map(g => {
    const mine = gdMineIn(g, lg), yours = mine ? ` · ${t("live.now.yours", {n: mine})}` : "";
    const state = g.st === "live" ? `<small class="gd-gs live">${t("live.now.live")}${yours}</small>`
      : `<small class="gd-gs">${esc(gdClock(Date.parse(g.kickoff)))}${yours}</small>`;
    const a = gdClubScore(g.away, g.home), h = gdClubScore(g.home, g.away), on = g.st !== "pre" && a !== null && h !== null;
    const box = (club, s, o) => `<span class="gd-bx${on && s < o ? " behind" : ""}"><span class="gd-bx-n"><span>${esc(club)}</span></span>
      <b>${on ? s : "—"}</b></span>`;
    return `<button type="button" class="gd-g" data-gdnfl="${esc([g.espn || "", g.away, g.home].join(","))}" aria-haspopup="dialog">
      ${state}${box(g.away, a, h)}${box(g.home, h, a)}</button>`;
  }).join("");
  return `<section class="gd-now gd-card"><h3><span>${t("live.now.head")}</span><em>${t("live.now.tap")}</em></h3>
    <div class="gd-nfl">${tiles}</div></section>`;
}
