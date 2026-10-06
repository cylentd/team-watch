/* ============================== LIVE: THE GAME SHEET ==============================
   One NFL game, for following it without watching (2026-09-28, storyboard
   https://claude.ai/artifact/7dtFfrweZG7mYE6oWSjmFb). A game tile on Live opens it as a centred
   modal (U9, 2026-10-05; STYLE.md "Overlays": it is for reading, so not a bottom sheet); the X, Back,
   Escape, the scrim and a pull down from the top close it (chrome/layers.js), and a sideways swipe
   walks the week's games inside it. It lives outside #view (shell.html), so a render() never rebuilds it.

   When it asks, and why:
     open                         ESPN's summary (the reader's browser, espn.js) and /api/stats for
                                  the two clubs, at once: two hosts, one request each.
     open, the game on, visible   both again every 30 s, one of each in flight at most.
     closed, tab hidden, final    never. */

let GS = null;            /* {event, away, home, slug?} on screen, ESPN's codes; slug = the player the reader came from; null = closed */
let GS_GAME = null;       /* gsShape of the last good ESPN summary */
let GS_BOX = null;        /* the last good /api/stats?teams= reply */
let GS_ERR = "";          /* why ESPN did not answer, above the plays */
let GS_BOX_ERR = "";
let GS_BUSY = false;
let GS_TEAM = null;       /* the club the box score shows */
let GS_OPEN = new Map();  /* drive key -> open, as the reader left it */
let GS_RETURN = null;
/* The pane the reader last chose, kept for the session in memory: Plays, Box score, Top scorers. */
const GS_TABS = ["plays", "box", "top"];
let GS_TAB = "box";
/* Players followed this week: id (his Sleeper id, else his slug) -> {id, sid, slug, n, pos, team}. */
let GS_FOLLOW = {};
const GS_WIDE = window.matchMedia("(min-width:960px)");
/* What can scroll: on a phone the whole body (.gs-main) and nothing inside it; from 960px the cards and
   the pinned list (data-gsscroll). The scroll of each is put back after a repaint. */
const GS_SCROLLERS = ".gs-main, [data-gsscroll]";
const gsEl = () => document.getElementById("gamesheet");

function gsOpen(game, origin){
  const d = gsEl();
  if (!d) return;
  GS = game; GS_GAME = null; GS_BOX = null; GS_ERR = ""; GS_BOX_ERR = ""; GS_TEAM = null; GS_OPEN = new Map();
  GS_FOLLOW = gsFollowLoad();
  GS_RETURN = origin || document.activeElement;
  gsPaint(true);
  d.scrollTop = 0;
  d.classList.add("on");
  d.setAttribute("aria-hidden", "false");
  document.getElementById("gamesheet-scrim").classList.add("on");
  d.querySelector("[data-gsclose]").focus({preventScroll: true});
  layerPush("gamesheet", gsShut);
  gsPoll();
}

/* The close itself; gsClose also takes back the history entry (layers.js). */
function gsShut(){
  const d = gsEl();
  if (!d || !GS) return;
  GS = null;
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  document.getElementById("gamesheet-scrim").classList.remove("on");
  const back = GS_RETURN;
  GS_RETURN = null;
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}
function gsClose(){ gsShut(); layerDone("gamesheet"); }

/* A repaint replaces the panes, so the scroll the reader is at is put back; `top` starts at the top. */
function gsPaint(top){
  const d = gsEl();
  if (!d || !GS) return;
  const at = [...d.querySelectorAll(GS_SCROLLERS)].map(el => el.scrollTop);
  d.innerHTML = gsSheetHTML();
  d.querySelectorAll(GS_SCROLLERS).forEach((el, i) => { el.scrollTop = top ? 0 : at[i] || 0; });
}

/* ---- followed players: this week only, on this device (not tw-follow, which is the team switch) ---- */
const gsFollowKey = () => `tw-gs-follow.${(GD.leagues[0] || {}).week}`;
function gsFollowLoad(){
  try {
    /* One key per week: the ones of other weeks are dead, so they go. */
    for (let i = localStorage.length - 1; i >= 0; i--){
      const k = localStorage.key(i);
      if (k && k.startsWith("tw-gs-follow.") && k !== gsFollowKey()) localStorage.removeItem(k);
    }
    const v = JSON.parse(localStorage.getItem(gsFollowKey()) || "{}");
    return v && typeof v === "object" && !Array.isArray(v) ? v : {};
  } catch (e) { return {}; }
}
function gsFollowToggle(rec){
  if (GS_FOLLOW[rec.id]) delete GS_FOLLOW[rec.id]; else GS_FOLLOW[rec.id] = rec;
  try { localStorage.setItem(gsFollowKey(), JSON.stringify(GS_FOLLOW)); } catch (e) { /* kept for this open only */ }
}

/* A sideways swipe, or the step row's buttons, walks the week's games in the Games tab's order (live,
   still to play, final; 2026-10-04, was kickoff order, so a swipe from the list jumped about), the
   sheet staying up: every NFL game. The step row names the game on each side. It stops at either end. */
function gsNeighbours(){
  const games = gdGamesSorted().map(x => x.g);
  const i = games.findIndex(g => (GS.event && g.espn === GS.event) || (g.away === GS.away && g.home === GS.home));
  return i < 0 ? [null, null] : [games[i - 1] || null, games[i + 1] || null];
}
function gsStep(step){
  if (!GS) return;
  const g = gsNeighbours()[step > 0 ? 1 : 0];
  if (!g) return;
  gsOpen({event: g.espn || "", away: g.away, home: g.home}, GS_RETURN);   // layerPush keeps the one entry
  const d = gsEl();
  if (d && !REDUCED()){
    d.classList.remove("turn-r", "turn-l"); void d.offsetWidth;
    d.classList.add(step > 0 ? "turn-r" : "turn-l");
  }
}

/* The two clubs in every spelling, sorted, so every reader of one game shares one cached reply. */
function gsBoxUrl(at){
  const week = (GD.leagues[0] || {}).week, codes = new Set([...gdCodes(at.away), ...gdCodes(at.home)]);
  return `/api/stats?week=${week}&teams=${[...codes].sort().join(",")}`;
}

/* Sleeper directly when our endpoint cannot answer, cut the way api/stats.py box() cuts it. */
async function gsBoxDirect(at){
  const week = (GD.leagues[0] || {}).week, rows = await fetch(`https://api.sleeper.com/stats/nfl/${GD.season}/${week}?season_type=regular`).then(r => r.ok ? r.json() : null);
  if (!rows) return null;
  const box = {};
  for (const r of rows){
    const p = r.player || {}, s = r.stats || {};
    if (!["QB", "RB", "WR", "TE", "K"].includes(p.position) || !(gdSameClub(at.away, r.team) || gdSameClub(at.home, r.team))) continue;
    if (Object.values(s).some(Boolean)) box[String(r.player_id)] = {n: `${p.first_name || ""} ${p.last_name || ""}`.trim(), pos: p.position, team: r.team, s};
  }
  return {box};
}

/* Both fetches are for game `at`, and write nothing if the reader has swiped to another meanwhile. */
async function gsBoxFetch(at){
  let reply = null;
  try {
    const res = await fetch(gsBoxUrl(at), {headers: {"Accept": "application/json"}});
    reply = res.ok ? await res.json() : null;
  } catch (e) { /* Sleeper directly, below */ }
  if (!(reply && reply.box)) { try { reply = await gsBoxDirect(at); } catch (e) { reply = null; } }
  if (GS !== at) return;
  if (reply && reply.box){ GS_BOX = reply; GS_BOX_ERR = ""; } else GS_BOX_ERR = t("live.sheet.noSleeper");
}

async function gsEspnFetch(at){
  if (!at.event) return;
  let shaped = null;
  try { shaped = gsShape(await gsFetchSummary(at.event)); } catch (e) { shaped = null; }
  if (GS !== at) return;
  if (shaped){ GS_GAME = shaped; GS_ERR = ""; } else GS_ERR = t("live.sheet.espnDown");
}

async function gsPoll(){
  if (!GS || GS_BUSY) return;
  if (!PAGE_SERVED()){ GS_ERR = t("live.error.notServed"); gsPaint(); return; }
  GS_BUSY = true;
  const at = GS;
  await Promise.all([gsEspnFetch(at), gsBoxFetch(at)]);
  GS_BUSY = false;
  if (GS === at) gsPaint(); else if (GS) gsPoll();   // swiped to another game mid-fetch: fetch that one
}

const gsLive = () => GS && document.visibilityState === "visible" && (GS_GAME ? GS_GAME.state !== "post" : gsSleeperState() !== "post");

/* Bound once: the sheet's markup is replaced on every paint, its listeners are not. */
(() => {
  const d = gsEl();
  if (!d) return;
  d.addEventListener("click", e => {
    if (e.target.closest("[data-gsclose]")) return gsClose();
    const step = e.target.closest("[data-gsstep]");
    if (step){
      const k = step.dataset.gsstep;
      gsStep(+k);
      /* gsOpen focused the close; a keyboard reader stepping on stays on the step (if there is one). */
      d.querySelector(`[data-gsstep="${k}"]`)?.focus({preventScroll: true});
      return;
    }
    const team = e.target.closest("[data-gsteam]");
    if (team){ GS_TEAM = team.dataset.gsteam; gsPaint(); return; }
    const tab = e.target.closest("[data-gstab]");
    if (tab){
      GS_TAB = tab.dataset.gstab; gsPaint(true);
      d.querySelector(`[data-gstab="${GS_TAB}"]`)?.focus({preventScroll: true});
      return;
    }
    const star = e.target.closest("[data-gsfollow]");
    if (star){
      const k = star.dataset;
      gsFollowToggle({id: k.gsfollow, sid: k.sid, slug: k.slug, n: k.n, pos: k.pos, team: k.team});
      gsPaint();
      d.querySelector(`[data-gsfollow="${CSS.escape(k.gsfollow)}"]`)?.focus({preventScroll: true});
    }
  });
  /* A drive the reader opened or closed stays that way through the next poll. */
  d.addEventListener("toggle", e => {
    const drv = e.target.closest && e.target.closest("[data-gsdrive]");
    if (drv) GS_OPEN.set(drv.dataset.gsdrive, drv.open);
  }, true);
  d.addEventListener("keydown", e => {
    if (e.key !== "Tab") return;
    const f = [...d.querySelectorAll("button, summary")];
    if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]){ e.preventDefault(); f[0].focus(); }
  });
  document.getElementById("gamesheet-scrim").addEventListener("click", gsClose);
  /* Bound on the sheet itself, which a paint never replaces: sideways walks the games, down closes. */
  onSwipeX(d, gsStep);
  /* The body scrolls, not the sheet: a pull closes it only from the top of everything that scrolls. */
  onPullDown(d, () => d.scrollTop <= 0 && [...d.querySelectorAll(GS_SCROLLERS)].every(el => el.scrollTop <= 0), () => !!GS, gsClose);
  GS_WIDE.addEventListener("change", () => gsPaint());
  document.addEventListener("keydown", e => { if (e.key === "Escape" && GS) gsClose(); });
  setInterval(() => { if (gsLive()) gsPoll(); }, GD_POLL_MS);
  document.addEventListener("visibilitychange", () => { if (gsLive()) gsPoll(); });
})();
