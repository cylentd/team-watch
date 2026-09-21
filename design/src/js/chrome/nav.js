const NEWS_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v11H9l-4 4V16H4z"/></svg>`;
/* One icon per group, not per view. Scouting keeps the old Pool chart mark because the scatter
   is still the first thing behind that tab; Bets keeps the parlay ticket for the same reason. */
const NAV_ICON = {
  teams: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><circle cx="17" cy="7" r="2.4" opacity=".55"/><path d="M15.5 14.2c2.6.4 4.5 2.2 4.5 5.3" opacity=".55"/></svg>`,
  scouting: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v16h16"/><circle cx="9" cy="14" r="1.6" fill="currentColor" stroke="none"/><circle cx="14" cy="9" r="1.6" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1.6" fill="currentColor" stroke="none"/></svg>`,
  bets: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="7" x2="20" y2="7"/><circle cx="9" cy="7" r="2" fill="var(--panel)"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="15" cy="12" r="2" fill="var(--panel)"/><line x1="4" y1="17" x2="20" y2="17"/><circle cx="11" cy="17" r="2" fill="var(--panel)"/></svg>`,
  gameday: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2.4" fill="currentColor" stroke="none"/><path d="M8.1 8.1a5.5 5.5 0 0 0 0 7.8"/><path d="M15.9 15.9a5.5 5.5 0 0 0 0-7.8"/><path d="M5.2 5.2a9.6 9.6 0 0 0 0 13.6" opacity=".55"/><path d="M18.8 18.8a9.6 9.6 0 0 0 0-13.6" opacity=".55"/></svg>`,
};
/* Four groups, each holding the views that answer one question. Seven flat tabs fitted no phone
   and, worse, implied seven peers: Movers and Grid are two readings of the same usage data, and
   Roster and Waivers were already a pair hidden inside the hero. Grouping says which is which.
   Gameday holds one view today and exists as a group because that is where a live surface grows.
   Each leaf's label is its own key, so a rename here never silently changes a heading elsewhere. */
const NAV = [
  ["teams",    ["roster", "waivers"]],
  ["scouting", ["pool", "usage", "news"]],
  ["bets",     ["parlay", "dfs"]],
  ["gameday",  ["live"]],
];

/* Every key spelled out, never built from a variable. assemble.py --check proves no copy key is
   orphaned by scanning for literal lookups, and a key assembled from a template is invisible to
   it -- the build would pass while the label rendered blank. */
const navLabel = leaf => ({
  roster: t("nav.tab.roster"), waivers: t("nav.tab.waivers"), pool: t("nav.tab.movers"),
  usage: t("nav.tab.grid"), news: t("nav.tab.news"), parlay: t("nav.tab.parlay"),
  dfs: t("nav.tab.dfs"), live: t("nav.tab.live"),
}[leaf] || leaf);

const navGroupLabel = (group, short) => (short ? {
  teams: t("nav.group.teams.short"), scouting: t("nav.group.scouting.short"),
  bets: t("nav.group.bets.short"), gameday: t("nav.group.gameday.short"),
} : {
  teams: t("nav.group.teams.full"), scouting: t("nav.group.scouting.full"),
  bets: t("nav.group.bets.full"), gameday: t("nav.group.gameday.full"),
})[group] || group;

const navGroupOf = leaf => (NAV.find(([, tabs]) => tabs.includes(leaf)) || NAV[0])[0];
const navTabsOf = group => (NAV.find(([g]) => g === group) || NAV[0])[1];

/* Waivers is the one leaf whose label carries a number: how many players are on the wire. It is
   the only count that changes what you would do next, so it is the only one worth a badge. */
function navCount(leaf){
  if (leaf !== "waivers") return "";
  const lg = waiverFor(VIEW);
  return lg ? ` <span class="tabcount">${lg.wire.length}</span>` : "";
}

/* A group with one leaf gets no row: a sub-nav of one is a label pretending to be a choice. */
function paintSubnav(){
  const el = document.getElementById("subnav");
  const tabs = navTabsOf(navGroupOf(SURFACE));
  el.hidden = tabs.length < 2;
  // .modes-sub without .dock: the docked variant is fixed to the phone's bottom edge, which is
  // where the Parlay and DFS switchers already live.
  el.querySelector(".subnav-in").innerHTML = el.hidden ? "" :
    `<div class="modes-sub" role="group" aria-label="${t("nav.sub.label")}">
      ${tabs.map(k => `<button class="mode-sub" data-leaf="${k}"
        aria-pressed="${SURFACE === k}">${navLabel(k)}${navCount(k)}</button>`).join("")}
    </div>`;
  el.querySelectorAll("[data-leaf]").forEach(b => b.addEventListener("click", () => {
    if (SURFACE === b.dataset.leaf) return;
    morphLogo();
    navGo(b.dataset.leaf);
  }));
}

/* The view lives in the hash, so a reload lands where you were reading rather than back on the
   roster -- which matters more now that there are eight views instead of one. Only the view: the
   grid's position and week reset, and that is a deliberate line, because every control that
   learns the URL is another thing to keep in step with it. */
const navFromHash = () => {
  const leaf = (location.hash || "").replace(/^#\/?/, "");
  return NAV.some(([, tabs]) => tabs.includes(leaf)) ? leaf : null;
};

function navGo(leaf, fromHash){
  LAST_LEAF[navGroupOf(leaf)] = leaf;
  SURFACE = leaf;
  const active = navGroupOf(leaf);
  document.querySelectorAll("#nav .navitem")
    .forEach(x => x.setAttribute("aria-current", x.dataset.s === active));
  // Writing the hash back during a hashchange would re-enter this and fight the Back button.
  if (!fromHash) location.hash = leaf;
  paintSubnav();
  render();
  // Moving to a view is the moment you are about to read it, so it is the moment to ask whether
  // what you are reading is still what is on main. Debounced in freshCheck, not here.
  if (typeof freshCheck === "function") freshCheck();
}

function buildNav(){
  const n = document.getElementById("nav");
  // Two labels per group, same pattern as the topbar pills' full/abbr swap: four fit a phone
  // where seven did not, but "Scouting" and "Gameday" still need a short form at 430px.
  n.innerHTML = NAV.map(([g]) =>
    `<button class="navitem" data-s="${g}" aria-current="${navGroupOf(SURFACE) === g}">
      <span class="ix">${NAV_ICON[g]}</span><span class="full">${navGroupLabel(g, false)}</span
      ><span class="abbr">${navGroupLabel(g, true)}</span></button>`).join("");
  n.querySelectorAll(".navitem").forEach(b => b.addEventListener("click", () => {
    const g = b.dataset.s;
    if (navGroupOf(SURFACE) !== g) morphLogo();
    // Back to where you were in that group, not to its first tab.
    navGo(LAST_LEAF[g] || navTabsOf(g)[0]);
    window.scrollTo({top: 0, behavior: "smooth"});
  }));

  /* Back and forward move between views, which is what a browser's own buttons are for and what
     everyone tries first. The guard keeps a hash we just wrote from re-rendering the same view. */
  window.addEventListener("hashchange", () => {
    const leaf = navFromHash();
    if (leaf && leaf !== SURFACE) navGo(leaf, true);
  });
  paintSubnav();
}

/* One global listener, registered once, rather than one per render -- render() rebuilds
   #switch's markup from scratch every time (see teamSwitchHTML/wireTeamSwitch above), so a
   listener attached inside render() would stack a new copy on every re-render. */
document.addEventListener("click", e=>{
  const sw = document.getElementById("switch");
  if (!sw) return;
  const menu = sw.querySelector("[data-tsmenu]"), btn = sw.querySelector("[data-tsbtn]");
  if (menu && !menu.hidden && !sw.contains(e.target)){
    menu.hidden = true; btn.setAttribute("aria-expanded","false");
  }
});

