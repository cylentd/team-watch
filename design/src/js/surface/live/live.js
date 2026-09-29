/* ------------------------------------------------------------------
   LIVE — every matchup in each of my leagues, scored live (2026-09-28, storyboard
   https://claude.ai/artifact/8qKDQUVxkz4F5naVPVQjhH).

   The lineups and each league's scoring rules are baked in (LIVE_GAMEDAY, design/gameday.py);
   the numbers come from Sleeper's live stats, trimmed to our players by /api/stats, and the page
   scores them itself (js/data/gameday/score.js). No ESPN cookies, no Yahoo API: one source for
   every league. The ESPN read this replaced (api/live.py) showed nothing on Sunday 2026-09-27.

   When it asks, and why:
     Live on screen, a game on       every 30 s. The edge caches the reply 15 s, so every reader
                                     shares one Sleeper read.
     Live on screen, nothing on      once, if what it has is older than 15 minutes (final numbers,
                                     a changed lineup), then it sleeps until the next kickoff.
     Another view, or tab hidden     never. Coming back asks at once.
------------------------------------------------------------------ */

const GD_POLL_MS = 30000;
const GD_IDLE_MS = 900000;
/* How long after kickoff a game might still be scoring: a bit over three hours of play, padded for
   overtime and a late start. Sleeper's own "complete" ends the window sooner. */
const GD_GAME_MS = 13500000;
/* How long a "+6.0" stays beside a number that just moved. */
const GD_PULSE_MS = 9000;

let GD_STATS = null;     /* the last good /api/stats reply */
let GD_ERR = "";
let GD_BUSY = false;
let GD_AT = 0;           /* epoch ms of the last good reply */
let GD_PULSE = {};       /* sid -> points just gained, for GD_PULSE_MS */
let GD_PULSE_T = 0;

const GD = typeof LIVE_GAMEDAY !== "undefined" && LIVE_GAMEDAY ? LIVE_GAMEDAY : {leagues: []};
/* Kickoffs, injected at build time by design/schedule.py; the drive strip reads this too. */
const GD_GAMES = (typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.games) || [];
const GD_ALIAS = (typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.alias) || {};

const gdOnScreen = () => SURFACE === "live" && document.visibilityState === "visible";

/* ---------------------------------------------------------------- which league, which game */

const GD_LEAGUE_KEY = "tw-live-league";
let GD_PICK = null;      /* the game on screen, as [away, home] ids; null = mine */

function gdLeague(){
  let k = null;
  try { k = localStorage.getItem(GD_LEAGUE_KEY); } catch (e) {}
  return GD.leagues.find(l => l.key === k) || GD.leagues[0] || null;
}
function gdSetLeague(key){
  try { localStorage.setItem(GD_LEAGUE_KEY, key); } catch (e) {}
  GD_PICK = null;
}
/* The game on screen: the picked one, else mine, else the first. */
function gdGame(lg){
  if (GD_PICK && lg.games.some(g => g[0] === GD_PICK[0] && g[1] === GD_PICK[1])) return GD_PICK;
  return lg.games.find(g => g.includes(lg.me)) || lg.games[0] || null;
}

/* ---------------------------------------------------------------- the clock */

/* A club's kickoff this week, from the schedule in either spelling ("WAS" / "WSH"). */
function gdKickOf(club){
  const now = Date.now(), names = [club, GD_ALIAS[club]].filter(Boolean);
  let best;
  for (const g of GD_GAMES){
    if (!names.includes(g.home) && !names.includes(g.away)) continue;
    const at = Date.parse(g.kickoff);
    if (!isNaN(at) && (best === undefined || Math.abs(at - now) < Math.abs(best - now))) best = at;
  }
  return best;
}
function gdClubs(){
  const out = new Set();
  for (const lg of GD.leagues) for (const tm of Object.values(lg.teams)) for (const r of tm.lineup) if (r.team) out.add(r.team);
  /* Every club of the week too, so the NFL now card's scores keep moving in a game none of ours is in. */
  for (const g of gdWeekGames()) out.add(g.home).add(g.away);
  return out;
}
/* A game of the week is being played. Sleeper saying every such game is
   complete ends the window early; its "in_game" keeps it open past the padding. */
function gdPlaying(now){
  const states = (GD_STATS && GD_STATS.games) || {};
  for (const club of gdClubs()){
    if (states[club] === "in_game") return true;
    const k = gdKickOf(club);
    if (k !== undefined && k <= now && now < k + GD_GAME_MS && states[club] !== "complete") return true;
  }
  return false;
}
function gdNextKick(now){
  let next;
  for (const club of gdClubs()){
    const k = gdKickOf(club);
    if (k !== undefined && k > now && (next === undefined || k < next)) next = k;
  }
  return next;
}

/* ---------------------------------------------------------------- fetching */

/* One URL for every reader of this page: every player in every league, sorted, so the edge
   caches a single reply for all of them. Every club of the week rides along in both spellings:
   its defense row is the other club's score on the NFL now card (nflnow.js). */
function gdUrl(){
  const ids = new Set();
  for (const lg of GD.leagues) for (const tm of Object.values(lg.teams)) for (const r of tm.lineup) if (r.sid) ids.add(r.sid);
  for (const g of GD_GAMES) if (g.week === (GD.leagues[0] || {}).week) for (const c of [g.home, g.away]) gdCodes(c).forEach(x => ids.add(x));
  const week = (GD.leagues[0] || {}).week;
  return week && ids.size ? `/api/stats?week=${week}&ids=${[...ids].sort().join(",")}` : null;
}

/* Sleeper directly, when our endpoint cannot answer: the whole week file (about 277 KB) and the
   schedule, cut here the way api/stats.py cuts them. Sleeper allows a browser to ask (checked
   2026-09-28, `access-control-allow-origin: *`), so Live survives our function being down. */
async function gdDirect(){
  const week = (GD.leagues[0] || {}).week, season = GD.season;
  const [rows, sched] = await Promise.all([
    fetch(`https://api.sleeper.com/stats/nfl/${season}/${week}?season_type=regular`).then(r => r.ok ? r.json() : null),
    fetch(`https://api.sleeper.com/schedule/nfl/regular/${season}`).then(r => r.ok ? r.json() : null)]);
  if (!rows || !sched) return null;
  const stats = {}, games = {};
  for (const r of rows) stats[String(r.player_id)] = r.stats || {};
  for (const g of sched) if (g.week === week){ games[g.home] = g.status; games[g.away] = g.status; }
  return {week, stats, games, direct: true};
}

async function gdFetch(){
  if (GD_BUSY) return;
  if (!PAGE_SERVED()){ GD_ERR = t("live.error.notServed"); paintLive(); return; }
  const url = gdUrl();
  if (!url) return;
  GD_BUSY = true;
  let payload = null, ok = false;
  try {
    const res = await fetch(url, {headers: {"Accept": "application/json"}});
    payload = await res.json().catch(() => null);
    ok = res.ok;
  } catch (e) { /* no response: Sleeper directly, below */ }
  if (!(ok && payload && payload.stats)){
    try { payload = await gdDirect(); ok = !!payload; } catch (e) { ok = false; }
  }
  GD_BUSY = false;
  if (ok && payload && payload.stats){
    gdNote(GD_STATS, payload);
    GD_STATS = payload; GD_ERR = ""; GD_AT = Date.now();
  } else {
    GD_ERR = (payload && payload.error) || t("live.error.network");
  }
  paintLive();
}

/* What moved since the last reply, per player, for the "+6.0" beside his number. */
function gdNote(before, after){
  GD_PULSE = {};
  if (!before) return;
  for (const lg of GD.leagues) for (const tm of Object.values(lg.teams)) for (const r of tm.lineup){
    if (!r.sid || GD_PULSE[r.sid] !== undefined) continue;
    const a = gdPts(lg.rules, r, before.stats[r.sid]), b = gdPts(lg.rules, r, after.stats[r.sid]);
    if (b !== null && Math.abs((b || 0) - (a || 0)) >= 0.05) GD_PULSE[r.sid] = Math.round((b - (a || 0)) * 10) / 10;
  }
  clearTimeout(GD_PULSE_T);
  if (Object.keys(GD_PULSE).length) GD_PULSE_T = setTimeout(() => { GD_PULSE = {}; paintLive(); }, GD_PULSE_MS);
}

function gdEnsure(){
  const now = Date.now();
  if (!GD_STATS || now - GD_AT > (gdPlaying(now) ? GD_POLL_MS : GD_IDLE_MS)) gdFetch();
}

/* ---------------------------------------------------------------- paint */

/* Repaints in place, never through render(): a poll must not rebuild the page under a thumb. */
function paintLive(){
  const host = document.querySelector("[data-gdboard]");
  if (!host) return;
  host.innerHTML = gdBoardHTML();
  wireLive(host);
}

function liveHTML(){
  gdEnsure();
  return `<div class="wrap"><section class="gd" data-gdboard>${gdBoardHTML()}</section></div>`;
}

function wireLive(host){
  host.querySelectorAll("[data-gdleague]").forEach(b => b.addEventListener("click", () => {
    gdSetLeague(b.dataset.gdleague); paintLive();
  }));
  host.querySelectorAll("[data-gdgame]").forEach(b => b.addEventListener("click", () => {
    GD_PICK = b.dataset.gdgame.split(","); paintLive();
    host.querySelector(".gd-head")?.scrollIntoView({block: "start", behavior: "smooth"});
  }));
  /* An NFL game opens the game sheet (gamesheet.js). */
  host.querySelectorAll("[data-gdnfl]").forEach(b => b.addEventListener("click", () => {
    const [event, away, home] = b.dataset.gdnfl.split(",");
    gsOpen({event, away, home}, b);
  }));
  /* A player opens his profile, the view search and the Digest open (surface/profile/panel.js). */
  host.querySelectorAll("[data-gdslug]").forEach(b => b.addEventListener("click", () => {
    openProfile({n: b.dataset.gdn, pos: b.dataset.gdpos, team: b.dataset.gdteam, slug: b.dataset.gdslug}, b);
  }));
}

/* One timer for the life of the page, inert unless Live is on screen. */
function buildLive(){
  setInterval(() => { if (gdOnScreen() && gdPlaying(Date.now())) gdFetch(); }, GD_POLL_MS);
  document.addEventListener("visibilitychange", () => { if (gdOnScreen()) gdEnsure(); });
}
