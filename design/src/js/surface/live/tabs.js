/* ============================== LIVE: THE TABS ==============================
   Matchup, Games, TDs, League (2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV,
   option A). One segmented control at the top; the choice is `tw-live-tab` in localStorage, never the
   hash, so another view sends the reader to a tab by setting it and then opening #live. Switching
   repaints in place (paintLive), never through render().

   Games carries a small lime count of the NFL games on now. */

const GD_TAB_KEY = "tw-live-tab";
const GD_TABS = ["matchup", "games", "tds", "league"];
let GD_TAB_MEM = null;     /* the tab when localStorage will not answer (private window, blocked data) */
let GD_BENCHES = false;    /* the Benches row, open or closed: memory only, closed on every visit */

function gdTab(){
  let v = GD_TAB_MEM;
  /* A store that answers but has lost the key (cleared mid-visit) does not overrule memory. */
  try { v = localStorage.getItem(GD_TAB_KEY) || v; } catch (e) {}
  return GD_TABS.includes(v) ? v : "matchup";
}
function gdSetTab(v){
  if (!GD_TABS.includes(v)) return;
  GD_TAB_MEM = v;
  try { localStorage.setItem(GD_TAB_KEY, v); } catch (e) {}
}

/* Every key spelled out: assemble.py --check finds unused copy by scanning for literal lookups. */
const gdTabName = k => ({matchup: t("live.tab.matchup"), games: t("live.tab.games"), tds: t("live.tab.tds"), league: t("live.tab.league")})[k];

function gdTabsHTML(){
  const on = gdTab(), live = gdLiveCount();
  const btn = k => `<button type="button" data-gdtab="${k}" aria-pressed="${k === on}">${gdTabName(k)}${k === "games" && live
    ? `<em class="gd-n" aria-label="${live === 1 ? t("live.tab.liveNow1") : t("live.tab.liveNow", {n: live})}">${live}</em>` : ""}</button>`;
  return `<div class="gd-tabs" role="group" aria-label="${t("live.tab.label")}">${GD_TABS.map(btn).join("")}</div>`;
}
