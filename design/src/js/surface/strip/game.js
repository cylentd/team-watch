/* ------------------------------------------------------------------
   STRIP GAME — one game, fetched. The only file in the strip that talks to a server.

   /api/game?event= shapes an ESPN summary into the drives the strip draws (api/game.py says how,
   and why field position must come from yardsToEndzone rather than the number painted on the
   grass). A live game and one from a month ago come back in the same shape, so the two ways into
   the strip -- Gameday, and a week in a player's game log -- are the same call with a different id.

   Two caches, for two different problems. The edge cache (30s, set by the endpoint) is what keeps
   ESPN seeing one read per window however many people are watching. The map below is what keeps
   re-opening the same game from asking again at all.
------------------------------------------------------------------ */

const ST_GAMES = new Map();      /* event -> {at, data} */
const ST_FRESH_MS = 20000;       /* under the endpoint's own 30s window, so a repeat is free */

/* Two sources, tried in that order, for reasons that have nothing to do with preference:

     games/<id>.json   nflverse, written at build time. Every finished game. A static file off the
                       CDN, 8 KB gzipped, no server, and richer than the alternative -- nflverse
                       states air yards, the tackler and the fumble recovery as columns where ESPN
                       states them inside a sentence.
     /api/game         ESPN, the only source that has a drive while it is still being played --
                       and the one behind a bot wall that answers this client with 403.

   So a finished game never depends on ESPN, and a live one is the only thing that does. */
async function stGame(g){
  const key = g.id || g.espn;
  const hit = ST_GAMES.get(key);
  if (hit && Date.now() - hit.at < ST_FRESH_MS) return hit.data;
  const payload = (g.id && await stStatic(g.id)) || await stLive(g.espn);
  ST_GAMES.set(key, {at: Date.now(), data: payload});
  return payload;
}

/* A miss here is the ordinary case for a game being played right now, so it is not an error:
   nflverse publishes about one overnight behind, and until it does there is no file. */
async function stStatic(id){
  try {
    const res = await fetch(`/games/${encodeURIComponent(id)}.json`, {headers: {Accept: "application/json"}});
    if (!res.ok) return null;
    const payload = await res.json();
    return payload && payload.drives ? payload : null;
  } catch (e) {
    return null;
  }
}

async function stLive(event){
  if (!event) throw new Error(t("strip.error.notPlayed"));
  const res = await fetch(`/api/game?event=${encodeURIComponent(event)}`, {headers: {Accept: "application/json"}});
  const payload = await res.json().catch(() => null);
  if (!res.ok || !payload || !payload.drives){
    /* the endpoint's own sentence, always preferred: "ESPN would not serve this game to the
       server" is actionable in a way a generic retry line is not */
    throw new Error((payload && payload.error) || t("strip.error.network"));
  }
  return payload;
}

/* Draw one game into `host`, with `name` (his full name as this page spells it) as the player the
   reel can narrow to. `data.names` supplies the play texts' spelling of him ("J. Allen"); the
   page never reduces a name itself. Returns the mounted controller, or null when the game could
   not be had -- the host then holds the reason, in the endpoint's own words. */
async function stripOpenGame(host, game, name){
  host.classList.add("stpanel");
  host.innerHTML = `<p class="stwait">${t("strip.loading")}</p>`;
  /* From a file:// page there is no origin to ask, and every caller would hit it again on the
     next click. Say so once, in the same place every other failure is said. */
  if (!PAGE_SERVED()){
    host.innerHTML = `<p class="sterr">${t("strip.error.notServed")}</p>`;
    return null;
  }
  try {
    const data = await stGame(game);
    return stripMount(host, data, null, (data.names || {})[name]);
  } catch (e) {
    host.innerHTML = `<p class="sterr">${esc(e.message || t("strip.error.network"))}</p>`;
    return null;
  }
}

/* Which NFL game a club played in `week`, or is playing now when no week is given. The schedule
   block is the same one Live's poll gate reads (GD_GAMES); a game whose history row predates
   ff-jarvis carrying the ESPN id has no `espn`, and is no game at all as far as this is
   concerned -- better no link than a link to the wrong game. */
function stGameFor(club, week){
  /* The two callers speak different dialects. The Live board's club codes come from /api/live and
     are ESPN's (LAR, WSH); the profile's game log carries nflverse's, off ff-jarvis's box score
     (LA, WAS). The schedule block ships the translation rather than this file repeating it. */
  const alias = (typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE && LIVE_SCHEDULE.alias) || {};
  club = alias[club] || club;
  const mine = GD_GAMES.filter(g => g.espn && (g.home === club || g.away === club));
  if (week !== null && week !== undefined) return mine.find(g => g.week === week) || null;
  /* a club plays once a week, so "nearest kickoff to now" picks this week's out of eighteen */
  const now = Date.now();
  let best = null, gap = Infinity;
  for (const g of mine){
    const at = Date.parse(g.kickoff);
    if (isNaN(at) || Math.abs(at - now) >= gap) continue;
    best = g; gap = Math.abs(at - now);
  }
  return best;
}

/* The strip as a dialog, stacked over the player profile so opening it from a game log does not
   throw the profile away. `name` is the player to open at, `originEl` the element tapped. */
function openStrip(game, name, originEl){
  const d = document.getElementById("stripmodal");
  const title = `${esc(game.away)} ${t("strip.title.at")} ${esc(game.home)}`;
  d.innerHTML = `<div class="dr-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <h3 id="st-title">${title}</h3>
      <div class="lbl">${esc(name || "")}${name ? " · " : ""}${t("strip.title.week", {n: game.week})}</div>
    </div><div class="dr-body stbody"></div>`;
  showModal(d, originEl, "st-title");
  stripOpenGame(d.querySelector(".stbody"), game, name);
}
