/* ============================== LIVE: THE TABS ==============================
   My league, NFL, TDs (2026-10-05, storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP,
   option 2A; four tabs from 2026-10-04 until Matchup and League merged into My league). One segmented
   control at the top; the choice is `tw-live-tab` in localStorage, never the hash, so another view
   sends the reader to a tab by setting it and then opening #live. Switching repaints in place
   (paintLive), never through render(). The ids stay "league" and "games" so a stored value and every
   link from another view keep working; a stored "matchup" maps to My league (data/gameday/strip.js).

   NFL carries a small lime count of the NFL games on now. */

const GD_TAB_KEY = "tw-live-tab";
const GD_TABS = ["league", "games", "tds"];
let GD_TAB_MEM = null;     /* the tab when localStorage will not answer (private window, blocked data) */
let GD_BENCHES = false;    /* the Benches row, open or closed: memory only, closed on every visit */

function gdTab(){
  let v = GD_TAB_MEM;
  /* A store that answers but has lost the key (cleared mid-visit) does not overrule memory. */
  try { v = localStorage.getItem(GD_TAB_KEY) || v; } catch (e) {}
  return gdTabOf(v);
}
function gdSetTab(v){
  v = gdTabOf(v);
  GD_TAB_MEM = v;
  try { localStorage.setItem(GD_TAB_KEY, v); } catch (e) {}
}

/* Every key spelled out: assemble.py --check finds unused copy by scanning for literal lookups. */
const gdTabName = k => ({league: t("live.tab.myleague"), games: t("live.tab.nfl"), tds: t("live.tab.tds")})[k];

const gdLiveLabel = n => (n === 1 ? t("live.tab.liveNow1") : t("live.tab.liveNow", {n}));

/* A desktop draws this bar; a phone draws the same three tabs as the Live pill's segments in the tab
   row (2026-10-05, data/tabrow.js, declared below), and hides this one (.view-tabs, chrome/phonenav.css). */
function gdTabsHTML(){
  const on = gdTab(), live = gdLiveCount();
  const btn = k => `<button type="button" data-testid="live-tab" data-gdtab="${k}" aria-pressed="${k === on}">${gdTabName(k)}${k === "games" && live
    ? `<em class="gd-n" aria-label="${gdLiveLabel(live)}">${live}</em>` : ""}</button>`;
  return `<div class="gd-tabs view-tabs" data-testid="live-tabbar" role="group" aria-label="${t("live.tab.label")}">${GD_TABS.map(btn).join("")}</div>`;
}
/* Every tab button in the board, the bar's and any link to a tab, repaints in place. */
function wireGdTabs(host){
  host.querySelectorAll("[data-gdtab]").forEach(b => b.addEventListener("click", () => { gdSetTab(b.dataset.gdtab); paintLive(); }));
}
navModes("live", () => ({ids: GD_TABS, cur: gdTab(), attr: "gdtab", name: t("live.tab.label"), label: gdTabName,
  count: k => { const n = k === "games" ? gdLiveCount() : 0; return n ? {n, label: gdLiveLabel(n)} : null; },
  select: k => { gdSetTab(k); paintLive(); }}));
