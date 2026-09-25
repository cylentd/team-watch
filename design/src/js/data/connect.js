/* Leagues a visitor connected themselves, read at runtime from api/league.py.

   David's two leagues are baked into the page (TEAMS.yahoo, TEAMS.espn) and stay the default. A
   connected league joins TEAMS under its own key ("espn-1534545") with `connected: true`, so the
   team switch lists it and the roster view draws it like any other. Waivers stay David's leagues'
   only: ff-jarvis builds the waiver packet and the Breaking rail for those two, nobody else's.

   The connection itself is an HttpOnly cookie the function sets; this file never sees a
   credential after the one POST that hands it over. */
const LEAGUE_API = "api/league";
let CONNECT_ERRORS = [];      // [{key, error}] from the last GET: an expired or unreachable league

function connectedTeam(card){
  return {
    key: card.key, plat: t("connect.plat.espn"), tint: "var(--espn)", slot: "",
    name: card.name, record: card.record, meta: [card.league],
    roster: espnRows(card.roster), connected: true, leagueId: card.league_id,
  };
}

function connectAdd(card){
  TEAMS[card.key] = connectedTeam(card);
}

/* On load, once. Nothing to ask from disk, and nothing to do when no league is connected: the
   function answers {leagues: []} without touching ESPN. */
async function connectLoad(){
  if (!PAGE_SERVED()) return;
  try {
    const r = await fetch(LEAGUE_API, {credentials: "same-origin"});
    if (!r.ok) return;
    const {leagues} = await r.json();
    CONNECT_ERRORS = (leagues || []).filter(l => l.error);
    (leagues || []).filter(l => !l.error).forEach(connectAdd);
    if ((leagues || []).length) render();
  } catch (e) {
    /* Offline or the function is not deployed: the baked leagues still draw. */
  }
}

/* POST one league. Resolves to {league} on success, {pick: [...]} when the visitor has to say
   which team is theirs, or {error} with a sentence the sheet can show as it is. */
async function connectPost(body){
  try {
    const r = await fetch(LEAGUE_API, {method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    const got = await r.json().catch(() => ({}));
    if (r.status === 409) return got.private
      ? {error: t("connect.error.private"), private: true} : {error: t("connect.error.expired")};
    if (!r.ok) return {error: got.error || t("connect.error.generic")};
    if (got.league) connectAdd(got.league);
    return got;
  } catch (e) {
    return {error: t("connect.error.offline")};
  }
}

async function connectRemove(key){
  try { await fetch(`${LEAGUE_API}?key=${encodeURIComponent(key)}`, {method: "DELETE", credentials: "same-origin"}); }
  catch (e) { return; }
  delete TEAMS[key];
  if (VIEW === key) VIEW = "yahoo";
}

const connectedKeys = () => Object.keys(TEAMS).filter(k => TEAMS[k].connected);
