/* One icon per group, not per view. The `scouting` group has read "Stats" since 2026-10-05 ("Players"
   from 2026-09-25; the id stays, so nothing keyed on it moves). It keeps the old Pool chart mark: the
   scatter is the Board's Movers mode since 2026-09-25. Bets is a banknote (2026-09-25): the three slider
   knobs it used to wear read as settings. The Teams group's two-people mark left with the group (2026-10-05). */
const NAV_ICON = {
  week: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/><path d="M7.5 14h4" opacity=".55"/></svg>`,
  scouting: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v16h16"/><circle cx="9" cy="14" r="1.6" fill="currentColor" stroke="none"/><circle cx="14" cy="9" r="1.6" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1.6" fill="currentColor" stroke="none"/></svg>`,
  bets: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="6" width="19" height="12" rx="2"/><circle cx="12" cy="12" r="2.8"/><path d="M6 9.5v5M18 9.5v5"/></svg>`,
  league: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10v4a5 5 0 0 1-10 0z"/><path d="M7 5.5H4.5a2.5 2.5 0 0 0 2.8 3.4M17 5.5h2.5a2.5 2.5 0 0 1-2.8 3.4"/><path d="M12 13v3.5M8.5 20h7M9.5 16.5h5"/></svg>`,
};
/* Four groups, each holding the views that answer one question: the table is data/navmap.js (NAV, its
   aliases, the leaves a league shows), pure so Node tests it. Seven flat tabs fitted no phone and,
   worse, implied seven peers: Board and Grid are two readings of the same usage data, and Roster and
   Waivers were already a pair hidden inside the hero. Grouping says which is which.
   Each leaf's label is its own key (navLabel), so a rename here never silently changes a heading elsewhere.
   History of the table, newest first (bookmarks outlive labels, so every leaf id and hash below stayed):
   2026-10-05 Teams and League merged into one League group (David; decided in plan U8). "League" was a
     group and a leaf under Teams, "Teams" a group and a leaf under League, and the league was picked in
     two places, the team switch and the Madden Curse / AYO chips. Now Week . League . Stats . Bets, and
     League holds Roster, Waivers, Teams, Trades, Recap, Records: six leaves, the most a 360px phone
     holds (six take 324px of its 332px sub-row at 360px, a seventh does not fit; data/navmap.js). The league is the one chip, the team
     switch (surface/league/switch.js): pick your team and every leaf follows its league. `myrecap` (Yahoo
     My recap) and `league` (ESPN League) are NAV_ALIAS entries for Recap; a league without a record
     book or graded trades (ESPN, AYO's trades) shows fewer leaves (navLeavesFor).
   2026-10-05 Players is labelled Stats (David: option A + C; the group id `scouting` stays). Its views are
     named by what they hold (Leaders, Work vs points, Usage; the draft's "Stat leaders" and "Usage grid" took
     408px of the 332px row at 360px) with one line each, and a player
     elsewhere reaches his row in 1 tap: navGoRow(leaf, slug), below.
   2026-10-05 Recap (leaf `weekrecap`, storyboard https://claude.ai/artifact/HVdkEL4YbiBKUJ3QbLH9gf) joined
     This week, the week's results; it took Weather's room in the sub-row (NAV_HIDDEN).
   2026-09-29 News moved from Players to This week (storyboard 96B1dMss6vfyhhsQLUSK4x), then Takes (leaf
     `matchups`, Start / Sit since 2026-10-03). Highlights (storyboard W5ty9RzT4XWSRfSjtdKEAk, option A)
     leads Players: two lines from each view below it.
   2026-09-28 League became a group of its own (storyboard https://claude.ai/artifact/EhbDwDUZ7ERb2iNfAqaKjn):
     the Yahoo league's recap, record book and trades left This week. Live joined This week.
   2026-09-26 "This week" leads: the Digest, what changed league-wide this week, is the front page.
   2026-09-25 Movers left the Board as a mode and came back as a view: a mode switch was a fifth row of
     controls on a phone, and Leaders and Movers answer different questions. "Board" reads Leaders; its leaf
     and hash stay `board`. Parlay split the same way: Slips (leaf `parlay`) and Build.

   navGoRow(leaf, slug) -> boolean. Opens Grid (leaf "usage") or Role (leaf "movers") on one player's row:
   sets the position and week (Grid) or the filter and Show all (Role) so the row is drawn, scrolls it to
   the middle and marks it (.nav-hit). False when the view has no row for him; the view still opens.
   Called by the Digest's usage rows; the profile and Start/Sit call it too (plan U3). The plan for where
   the view must stand is data/navrow.js navRowPlan. */

/* Claims are placed Tuesday and clear midweek, so on a Tuesday (the reader's local day) the wire
   is the question: an empty hash opens Waivers and Waivers leads its group. A hash still wins.
   The day comes from Date.now(), which the render suite pins, so a test picks the weekday. Any
   other day the Digest opens (2026-09-26): the week league-wide in one screen. It was Ranks for
   part of that day, and Board (who leads each stat) before; Highlights is Stats' first view (Ranks second). */
const navWaiverDay = () => new Date(Date.now()).getDay() === 2;
const navDefaultLeaf = () => navWaiverDay() ? "waivers" : "digest";

/* What the league on screen has, as plain booleans for navLeavesFor. A connected league has no Waivers:
   ff-jarvis builds the packet for David's leagues only. A leaguemate's team has its league's rail
   (data/mates.js hasWaivers). Recap is every league with a League block, ESPN's too; Records only a
   league with a record book (Yahoo's), whose Trade history tab is a league with graded trades; Teams (2026-10-05)
   and Trades (the trade finder, 2026-10-06) are for all three leagues, and a league with no rosters says so on the
   page. */
function navFacts(){
  const f = lgFocusKey(), L = f && LGS[f], rosters = lbKeys().length > 0;
  return {waivers: hasWaivers(TEAMS[VIEW]), teams: rosters, recap: !!L, records: !!(L && L.book), trades: rosters};
}
const navTabsOf = group => navLeavesFor(group, navFacts(), navWaiverDay());

/* Waivers is the one leaf whose label carries a number: how many players are on the wire in the
   league on screen. It is the only count that changes what you would do next, so it is the only
   one worth a badge. A team switch repaints it (teamswitch.js). */
function navCount(leaf){
  // A leaguemate's count would be David's claim list, so theirs has none, nor a reader yet to pick.
  if (leaf !== "waivers" || !WAIVER || notMine(TEAMS[VIEW]) || needsPick() || !isOwner()) return "";
  return ` <span class="tabcount">${waiverIn(VIEW).filter(([r]) => waiverTier(r, VIEW) !== "stash").length}</span>`;
}

/* The phone layout (2026-10-05, chrome/phonenav.css): a header bar, one tab row, a bottom tab bar. */
const NAV_PHONE = matchMedia("(max-width:760px)");

/* The open pill opened in place into its view's own tabs (data/tabrow.js); a view declares them with
   navModes. Each segment carries the view's own attribute too (data-gdtab on Live's), so a selector
   for the view's tab finds the one on screen. */
function navPillHTML(p, m){
  const btn = `<button class="mode-sub" data-leaf="${p.leaf}" aria-pressed="${p.on}">${navLabel(p.leaf)}${navCount(p.leaf)}</button>`;
  if (!p.segs) return btn;
  const seg = s => { const c = m.count && m.count(s.id);
    return `<button type="button" class="tr-seg" data-tseg="${esc(s.id)}" data-${m.attr}="${esc(s.id)}" aria-pressed="${s.on}">${
      m.label(s.id)}${c ? `<em class="tr-n" aria-label="${esc(c.label)}">${c.n}</em>` : ""}</button>`; };
  return `<span class="tr-x" role="group" aria-label="${esc(m.name)}">${btn}${p.segs.map(seg).join("")}</span>`;
}

/* A group with one leaf gets no row, unless its view opens into tabs: a sub-nav of one is a label
   pretending to be a choice. Repainted only when it changed (Live's poll asks every 30 s), and the row
   keeps where the reader scrolled it unless the pressed pill is off screen. */
let NAV_ROW = null;
function paintSubnav(){
  paintHdrTeam();
  const el = document.getElementById("subnav"), m = navModesOf(SURFACE);
  const tabs = navTabsOf(navGroupOf(SURFACE)).filter(k => !NAV_HIDDEN.includes(k));
  const plan = tabRowPlan(tabs, SURFACE, m, NAV_PHONE.matches);
  el.hidden = !plan.shown;
  const html = el.hidden ? "" : `<div class="modes-sub${NAV_DENSE.includes(navGroupOf(SURFACE)) ? " dense" : ""}" role="group" aria-label="${t("nav.sub.label")}">
      ${plan.pills.map(p => navPillHTML(p, m)).join("")}</div>`;
  const inner = el.querySelector(".subnav-in"), was = inner.querySelector(".modes-sub")?.scrollLeft || 0;
  if (html === NAV_ROW) return;
  NAV_ROW = html;
  inner.innerHTML = html;
  el.querySelectorAll("[data-leaf]").forEach(b => b.addEventListener("click", () => {
    if (SURFACE === b.dataset.leaf) return;
    morphLogo();
    navGo(b.dataset.leaf);
  }));
  el.querySelectorAll("[data-tseg]").forEach(b => b.addEventListener("click", () => {
    const now = navModesOf(SURFACE);
    if (now) now.select(b.dataset.tseg);
    paintSubnav();
  }));
  const row = inner.querySelector(".modes-sub"), on = row && row.querySelector(".tr-x, .mode-sub[aria-pressed='true']");
  if (!on) return;
  const r = row.getBoundingClientRect(), o = on.getBoundingClientRect();
  row.scrollLeft = tabRowScroll(o.left - r.left, o.width, was, r.width, 16);   // the new row starts at 0
}

/* The phone's header bar: the reader's team as the team switch, or "Pick your team" until there is one
   (the same menu either way). Drawn on a phone only, so a desktop has one switch per screen, and only
   when the team changed, so a repaint never shuts the menu under a finger. */
let NAV_HDR = null;
function paintHdrTeam(){
  const el = document.getElementById("hdrteam");
  const key = NAV_PHONE.matches ? `${VIEW}|${needsPick()}|${TEAMS[VIEW] ? TEAMS[VIEW].name : ""}` : "";
  if (!el || key === NAV_HDR) return;
  NAV_HDR = key;
  const pick = needsPick();
  el.innerHTML = key ? teamSwitchHTML(pick ? t("nav.header.pick") : "", pick ? "hdr ts-pick" : "hdr", "hdrswitch") : "";
  if (!key) return;
  el.querySelector("[data-tsmenu]").innerHTML = "";   // drawn when opened (wireTeamSwitch), so a view's menu is the only one in the page until then
  wireTeamSwitch(el, "hdrswitch");
}

/* The view lives in the hash, so a reload lands where you were reading rather than back on the
   roster -- which matters more now that there are eight views instead of one. Only the view: the
   grid's position and week reset, and that is a deliberate line, because every control that
   learns the URL is another thing to keep in step with it. Old names land too (NAV_ALIAS), and a
   leaf the league on screen lacks lands on its nearest (navFallback). */
const navHash = () => (location.hash || "").replace(/^#\/?/, "");
const navFromHash = () => {
  const leaf = navLeafOf(navHash());
  return leaf && navFallback(leaf, navTabsOf(navGroupOf(leaf)));
};

function navGo(leaf, fromHash){
  leaf = navLeafOf(leaf) || leaf;      // an old name (`myrecap`, `pool`) opens its successor
  LAST_LEAF[navGroupOf(leaf)] = leaf;
  if (leaf !== "trades" && TB_EDIT) tfLeft();   // the trade finder's edit page left open by a tap on another view (finder/page.js)
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

/* One player's row in Grid or Role (see the header). navRowPlan says where each view must stand; this
   sets it, opens the view, and puts the row in the middle of the screen, marked until the next draw. */
function navGoRow(leaf, slug){
  const role = typeof LIVE_ROLE !== "undefined" && LIVE_ROLE;
  const plan = navRowPlan(leaf, slug, leaf === "usage" ? USAGE.rows : role && role.rows, {week: USAGE_WEEK, pos: RV_POS, first: RV_FIRST});
  if (plan && leaf === "usage"){ USAGE_POS = plan.pos; USAGE_WEEK = plan.week; USAGE_MINE = false; }
  if (plan && leaf === "movers"){ RV_POS = plan.pos; if (plan.all) RV_ALL = true; }
  navGo(leaf);
  const row = plan && document.querySelector(`[data-${leaf === "usage" ? "usage" : "rvopen"}="${CSS.escape(slug)}"]`);
  if (!row) return false;
  row.classList.add("nav-hit");
  row.scrollIntoView({block: "center"});
  return true;
}

/* The mark before TEAM//WATCH is Smug Blip (2026-09-29, per David), the one drawing in lib/blip.js.
   The shell is static markup and the drawing lives in JS, so it is painted here, once. Decoration:
   the wordmark beside it carries the name. */
function paintBrand(){
  const m = document.querySelector(".navbar .brand-mark");
  if (m) m.innerHTML = blipSVG("", "smug");
}

function buildNav(){
  paintBrand();
  const n = document.getElementById("nav");
  // Two labels per group, same pattern as the topbar pills' full/abbr swap: four fit a phone
  // where seven did not. A group with no view to show draws no button.
  n.innerHTML = NAV.filter(([g]) => navTabsOf(g).length).map(([g]) =>
    `<button class="navitem" data-s="${g}" aria-current="${navGroupOf(SURFACE) === g}">
      <span class="ix">${NAV_ICON[g]}</span><span class="full">${navGroupLabel(g, false)}</span
      ><span class="abbr">${navGroupLabel(g, true)}</span></button>`).join("");
  n.querySelectorAll(".navitem").forEach(b => b.addEventListener("click", () => {
    const g = b.dataset.s;
    if (navGroupOf(SURFACE) !== g) morphLogo();
    // Back to where you were in that group, not to its first tab.
    const tabs = navTabsOf(g);
    navGo(navFallback(LAST_LEAF[g] || tabs[0], tabs));
    window.scrollTo({top: 0, behavior: "smooth"});
  }));

  /* Back and forward move between views, which is what a browser's own buttons are for and what
     everyone tries first. The guard keeps a hash we just wrote from re-rendering the same view. */
  window.addEventListener("hashchange", () => {
    const leaf = navFromHash();
    if (leaf && leaf !== SURFACE) navGo(leaf, true);
  });
  // Crossing 760px swaps the layouts: the header's switch and the row's opened tabs are a phone's only.
  NAV_PHONE.addEventListener("change", paintSubnav);
  paintSubnav();
}

/* One global listener, registered once, rather than one per render -- render() rebuilds a view's
   #switch from scratch every time (see teamSwitchHTML/wireTeamSwitch), so a listener attached inside
   render() would stack a new copy on every re-render. It closes every open switch menu: the view's and
   the phone header's (#hdrswitch). */
document.addEventListener("click", e=>{
  document.querySelectorAll(".teamswitch").forEach(sw => {
    const menu = sw.querySelector("[data-tsmenu]"), btn = sw.querySelector("[data-tsbtn]");
    if (menu && !menu.hidden && !sw.contains(e.target)){
      menu.hidden = true; btn.setAttribute("aria-expanded","false");
    }
  });
});
