/* ------------------------------------------------------------------
   LIVE — gameday scoreboard: my starting lineup against my opponent's, scored live.

   ESPN league only. Yahoo's fantasy API is gated behind an approval that has not come, and its
   website is a cookie-and-regex scrape; reading it from a datacenter address every 90 seconds is
   how you lose the cookie. The ESPN half is an authenticated API read of my own league, so it is
   the half that can poll honestly. Yahoo is a later decision, not an oversight.

   The second surface that talks to a server, and unlike Chat it asks for no passphrase. What
   was worth protecting was never the board -- it is a fantasy lineup, and the opponent can see
   it anyway -- it was the ESPN cookies behind it, and a 60-second edge cache protects those
   better than a secret would: repeats are served by the CDN, so ESPN sees at most one read per
   window however many callers there are. A passphrase would make the reply uncacheable.

   Nothing is stored anywhere. Each reply replaces the last, so there is no merge, no history and
   no cache to invalidate -- ask, draw, forget. Deltas, if they are ever wanted, belong in this
   browser, not on the server.
------------------------------------------------------------------ */

/* 90 seconds is the cadence while something is actually being played. Three guards keep it from
   being 90 seconds all week: the Live tab has to be the one on screen, the browser tab has to be
   visible, and a game involving somebody in this matchup has to be underway. Reading another
   surface, a phone in a pocket, or a Tuesday all cost nothing. */
const GD_POLL_MS = 90000;
/* Outside a game window the board still refreshes, just rarely -- a lineup can change, and the
   first load has to come from somewhere. Four reads an hour rather than forty. */
const GD_IDLE_MS = 900000;
/* How long after kickoff a game might still be scoring. Sixty minutes of play runs a bit over
   three hours; the padding is for overtime and for a clock that started late. Erring long costs
   a few reads at the end of a window, erring short misses the finish of a close game. */
const GD_GAME_MS = 13500000;
/* A repaint within this window reuses what is already drawn rather than asking again -- which is
   what makes switching to Live and back cheap, and matches the server's own 20s memo. */
const GD_STALE_MS = 60000;

/* How long a delta chip stays beside a score before it fades. Long enough to catch on a glance
   back at the phone, short enough that the board is mostly numbers rather than mostly news. */
const GD_PULSE_MS = 9000;

let GD_DATA = null;      /* the whole last reply, or null before the first one lands */
let GD_ERR = "";         /* the server's own message, preferred over anything invented here */
let GD_BUSY = false;
let GD_AT = 0;           /* epoch ms of the last good reply, for GD_STALE_MS */
let GD_WP = [];          /* [[epoch ms, winPct]] this week, as far as this browser has watched */
let GD_PULSE = {};       /* name -> what he just scored, for the few seconds it is worth saying */
let GD_PULSE_T = 0;
let GD_CATCHUP = null;   /* {movers, swing} after time away, until it is dismissed */

const gdOnScreen = () => SURFACE === "live" && document.visibilityState === "visible";

/* ---------------------------------------------------------------- the gate */

/* Kickoffs, injected at build time by design/schedule.py. Null when that log was not readable,
   and then there is no gate at all -- the idle cadence below is the only thing holding the line,
   which is the right way round: a missing schedule should slow the board, never silence it. */
const GD_GAMES = (LIVE_SCHEDULE && LIVE_SCHEDULE.games) || [];

/* Both lineups, not just mine: the score moves when his players play too. Null before the first
   reply lands, because there is no lineup yet to check a game against -- and every game counting
   is exactly what lets that first reply happen. */
function gdClubs(){
  if (!GD_DATA) return null;
  const out = new Set();
  for (const r of [...GD_DATA.me.lineup, ...GD_DATA.opponent.lineup]) if (r.team) out.add(r.team);
  return out;
}

function gdKicks(){
  const clubs = gdClubs(), out = [];
  for (const g of GD_GAMES){
    if (clubs && !clubs.has(g.home) && !clubs.has(g.away)) continue;
    const t = Date.parse(g.kickoff);
    if (!isNaN(t)) out.push(t);
  }
  return out.sort((a, b) => a - b);
}

/* When this club's game started. The season ships, so "nearest to now" is how this week's game
   is picked out of eighteen of them -- a club plays once a week, so nothing else is close. */
function gdKickOf(club){
  const now = Date.now();
  let best;
  for (const g of GD_GAMES){
    if (g.home !== club && g.away !== club) continue;
    const at = Date.parse(g.kickoff);
    if (isNaN(at)) continue;
    if (best === undefined || Math.abs(at - now) < Math.abs(best - now)) best = at;
  }
  return best;
}

/* Somebody in this matchup is on the field right now. */
const gdPlaying = now => gdKicks().some(k => k <= now && now < k + GD_GAME_MS);
/* ... and when the next one starts, for the line the board shows while nothing is being played. */
const gdNextKick = now => gdKicks().find(k => k > now);

/* ---------------------------------------------------------------- fetching */

async function gdFetch(){
  if (GD_BUSY) return;
  /* No origin to ask. From disk this resolved to file:///api/live, which the browser refuses and
     logs; every one of gdFetch's callers would hit it again on the next tick. Say so once, in the
     same place every other failure of this endpoint is said, and stop. */
  if (!PAGE_SERVED()){ GD_ERR = t("live.error.notServed"); paintLive(); return; }
  GD_BUSY = true;

  const asked = gdTeamKey();
  let payload = null, ok = false;
  try {
    /* A plain GET, so the CDN can cache it. Anything clever here -- a POST, a header, a query
       string that changes per call -- would make every request its own ESPN read again. The
       ?team= of a leaguemate's board is the same string on every call, so it caches per team. */
    const team = gdTeamName();
    const res = await fetch(team ? `/api/live?team=${encodeURIComponent(team)}` : "/api/live",
      {headers: {"Accept": "application/json"}});
    payload = await res.json().catch(() => null);
    ok = res.ok;
  } catch (e) {
    /* fetch itself threw: no response, so there is no server message to prefer. */
    GD_ERR = t("live.error.network");
  }

  GD_BUSY = false;
  // The team on screen changed while this was in flight: its reply belongs to a board no longer
  // shown. gdFollow already reset the board; the next ensure asks for the right team.
  if (asked !== gdTeamKey()){ paintLive(); return; }
  if (ok && payload && payload.me){
    GD_DATA = payload; GD_ERR = ""; GD_AT = Date.now();
    gdNote(payload);
  } else if (!GD_ERR){
    /* Every failure this endpoint has -- not configured, expired cookies, ESPN unreachable --
       already arrives as one sentence worth showing. A 409 saying to re-copy the cookies is
       actionable in a way no generic retry line would be. */
    GD_ERR = (payload && payload.error) || t("live.error.network");
  }
  paintLive();
}

/* What this reply changed, as against the last one this reader was shown (memory.js).

   Away and present are answered differently on purpose. Coming back to twelve rows each wearing
   a chip is not news, it is noise, so time away is summed up in one line instead; while you are
   watching, the chip beside the score IS the news and there are rarely more than one or two. */
function gdNote(d){
  const change = gdRemember(d);
  GD_WP = change.wp;
  GD_PULSE = {};
  if (change.away && change.movers.length){
    GD_CATCHUP = {movers: change.movers.slice(0, 3), swing: change.swing};
  } else {
    for (const m of change.movers) GD_PULSE[m.name] = m.delta;
  }
  clearTimeout(GD_PULSE_T);
  if (Object.keys(GD_PULSE).length){
    GD_PULSE_T = setTimeout(() => { GD_PULSE = {}; paintLive(); }, GD_PULSE_MS);
  }
}

/* Called on every paint of the surface. A fetch already in flight, or a reply still young
   enough, means there is nothing to do -- and what counts as young enough depends on whether
   anything is being played. */
function gdEnsure(){
  const now = Date.now();
  if (!GD_DATA || now - GD_AT > (gdPlaying(now) ? GD_STALE_MS : GD_IDLE_MS)) gdFetch();
}

/* ---------------------------------------------------------------- paint */

/* Repaints the board in place. Never calls render(): that rebuilds all of #view, and a poll
   landing every 90 seconds must not rebuild the page under someone's thumb. */
function paintLive(){
  const host = document.querySelector("[data-gdboard]");
  if (!host) return;              /* a different surface is showing; nothing to draw into */
  host.innerHTML = gdBoardHTML();
  wireLive(host);
}

function liveHTML(){
  if (gdYahooMate()) return `<div class="wrap"><div class="state-empty"><div><b>—</b><span>${t("live.yahooMate")}</span></div></div></div>`;
  gdFollow();
  gdEnsure();
  return `<div class="wrap">
    <section class="gdboard" data-gdboard>${gdBoardHTML()}</section>
  </div>`;
}

/* ---------------------------------------------------------------- wiring */

/* Re-run after every paint, because the board's markup is rebuilt each time. Safe to repeat:
   the elements it binds to are new ones, so nothing stacks. */
function wireLive(host){
  host.querySelector("[data-gdrefresh]")?.addEventListener("click", () => {
    GD_AT = 0;                    /* force the next ensure past GD_STALE_MS */
    gdFetch();
  });
  host.querySelector("[data-gdseen]")?.addEventListener("click", () => {
    GD_CATCHUP = null;
    paintLive();
  });
  /* A name opens his club's game as a drive strip, at the drive he was last on the field for.
     Bound here rather than once at load, because paintLive() rebuilds these cells on every poll. */
  host.querySelectorAll("[data-gdopen]").forEach(el => {
    const open = () => {
      const g = stGameFor(el.dataset.gdopen);
      if (g) openStrip(g, el.dataset.gdname, el);
    };
    el.addEventListener("click", open);
    el.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(); }
    });
  });
}

/* Registered once, at load, exactly like buildChat(): one interval for the life of the page,
   inert unless the Live tab is on screen. Starting a timer inside render() would stack a new
   one on every surface change, and they would all keep firing. */
function buildLive(){
  /* Paint from memory before anything is clicked. GD_AT stays 0 on purpose, so the first paint
     of the surface still asks for a fresh reply immediately -- this shows the board at once, it
     does not stand in for fetching one. */
  const last = gdBoardLoad();
  if (last){
    GD_DATA = last;
    GD_WP = (gdMemLoad(last.week) || {}).wp || [];
  }
  /* And when a game is actually being played, fetch once now rather than on the click, so the
     numbers are already current by the time the tab is opened. Outside a game window this does
     nothing at all, which is the whole point of the gate. */
  if (gdPlaying(Date.now())) gdFetch();

  setInterval(() => {
    if (!gdOnScreen()) return;
    const now = Date.now();
    /* Full cadence only while a game with one of these players in it is being played. Outside
       that, a slow refresh -- enough to catch a lineup change, and to load the board at all. */
    if (gdPlaying(now) || now - GD_AT > GD_IDLE_MS) gdFetch();
  }, GD_POLL_MS);
  /* Coming back to the tab should not wait out the rest of an interval. */
  document.addEventListener("visibilitychange", () => { if (gdOnScreen()) gdEnsure(); });
}
