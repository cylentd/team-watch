/* The nav's table, as data (chrome/nav.js draws it). Pure and DOM-free, so Node tests it
   (tests/test_js_nav.py). `NAV` is the whole table: a group in the bar, the leaves under it.
   `SURFACE` is always the leaf; the group is derived from it, never stored.

   The history of the table (what moved when, and why every leaf id stayed) is the header of chrome/nav.js. */
/* Team · Matchup · Players · League · Bets since 2026-10-08 (David, storyboard nav draft B, ledger #32): the
   sections Yahoo, ESPN and Sleeper readers already know. A renamed group keeps its id (`week` reads Matchup,
   `scouting` Players), so nothing keyed on it moves; `team` is new, split from League. Highlights was dropped
   2026-10-08 (David: "the information is not useful"); #highlights opens Ranks.
   Home · Team · Matchup · Players · League since 2026-10-08 (David, storyboard home draft B, ledger #52): Home is
   its own group of one view, today's Digest (leaf `digest`), so it draws no tab row; Bets' three views moved under
   Matchup with their leaf ids and hashes, and the `bets` group is gone. */
const NAV = [
  ["home",     ["digest"]],
  ["team",     ["roster", "waivers", "trades"]],
  ["week",     ["live", "matchups", "preview", "weekrecap", "parlay", "build", "dfs", "weather"]],
  ["scouting", ["news", "ranks", "board", "movers", "usage", "schedule"]],
  ["league",   ["recap", "teams", "records", "tradehist"]],   // Trade history left Records' mode row for its own leaf 2026-10-08 (David, ledger #74)
];

/* The most leaves a sub-row holds on a 360 px phone. The row is 332 px (360 less the page's 14 px a side);
   measured in the browser at 360 px, 2026-10-05: This week's six take 316 px at the phone's 16 px gap and
   seven take 383 px; League's six take 324 px at the dense 8 px gap with Waivers' two-digit count (366 px
   at 16); Stats' five took 312 px at 8 px (344 at 16), and its sixth, Schedule, came back 2026-10-06, so
   the row scrolls sideways inside itself as one row (STYLE.md "Controls"; chrome/phonenav.css). A seventh does not fit. */
const NAV_SUBROW_MAX = 6;

/* Groups whose words take the tighter 8px gap on a desktop (navrow.css .dense): Players names its views by
   what they hold. League held six leaves until 2026-10-08 and was dense too; it holds three now. Matchup is dense
   since it took Bets' three views (2026-10-08): eight words in one row. */
const NAV_DENSE = ["week", "scouting"];

/* Weather left the sub-row on 2026-10-05 to make room for Recap. It stays in NAV, so #weather,
   navGo("weather") and navGroupOf still work; the Digest's Weather row and every Preview dossier link
   to it. While it is open no sub button is pressed.
   Schedule (leaf `schedule`, plan U7) was hidden the same way from 2026-10-05, because Stats' five tabs took 312 of
   the 332 px a phone's sub-row holds; David put it back in the Stats row on 2026-10-06 (plan dbd T4), where a
   link in Ranks still opens it too. */
const NAV_HIDDEN = ["weather"];

/* Old names that still land. Movers was the `pool` view until 2026-09-25. Takes kept Matchups' leaf
   `matchups` (2026-09-29), so #takes is the new name's way in; Start/Sit (2026-10-03) was the same leaf, #startsit
   its name; it reads Matchups again since 2026-10-06 (the picker moved behind "Compare two"), and every name
   still lands. `myrecap` and `league` merged into Recap on 2026-10-05. `highlights` opens Ranks since the view was dropped 2026-10-08. */
const NAV_ALIAS = {pool: "movers", takes: "matchups", startsit: "matchups", myrecap: "recap", league: "recap", highlights: "ranks"};

/* A hash or a name -> the leaf it opens, or null when no view has it. */
const navLeafOf = name => {
  const leaf = NAV_ALIAS[name] || name;
  return NAV.some(([, tabs]) => tabs.includes(leaf)) ? leaf : null;
};

// A name no group holds belongs to the default view's group: Home since 2026-10-08 (Matchup before; NAV[0] while This week led the bar).
const navGroupOf = leaf => (NAV.find(([, tabs]) => tabs.includes(leaf)) || NAV.find(([, tabs]) => tabs.includes("digest")))[0];

/* The leaves a group shows, given what the league on screen has. `facts` is plain booleans:
   waivers (a league with a packet; a connected one has none), teams (any league has rosters),
   recap (the league has a recap block), records (a record book: Yahoo's), trades (the trade finder: any league
   with rosters, like teams; the graded trade history moved to Records > Trade history, 2026-10-06), tradehist
   (the league has graded trades: its own leaf since 2026-10-08, was Records' second tab).
   On a Tuesday, claims day, Waivers leads. */
function navLeavesFor(group, facts, waiverDay){
  const all = (NAV.find(([g]) => g === group) || NAV[0])[1];
  const has = {waivers: facts.waivers, teams: facts.teams, recap: facts.recap, records: facts.records, trades: facts.trades, tradehist: facts.tradehist};
  const tabs = all.filter(k => !(k in has) || has[k]);
  return waiverDay && tabs.includes("waivers") ? ["waivers", ...tabs.filter(k => k !== "waivers")] : tabs;
}

/* A leaf the league on screen has no view for (a #records link on an ESPN team, #waivers on a connected
   league) lands on its nearest: Waivers on the roster, the league's book and trades on Recap. A leaf
   hidden from the sub-row on purpose (Weather) is left alone. */
const NAV_LEAGUE_GROUPS = ["team", "league"];   // the groups whose leaves depend on what the league has
function navFallback(leaf, tabs){
  if (tabs.includes(leaf) || NAV_HIDDEN.includes(leaf) || !NAV.some(([g, ts]) => NAV_LEAGUE_GROUPS.includes(g) && ts.includes(leaf))) return leaf;
  const next = leaf === "waivers" ? "roster" : "recap";
  return tabs.includes(next) ? next : tabs[0] || leaf;
}

/* The league a team belongs to: one of David's by its own key, a leaguemate's by his league. A connected
   league, or none, has no league the page holds, so the first one does. `keys` are the leagues with data. */
function navFocusKey(team, keys){
  const own = !team || team.connected ? null : team.mate ? team.league : team.key;
  return keys.includes(own) ? own : keys[0] || null;
}

/* Each leaf's label is its own key, so a rename here never silently changes a heading elsewhere.
   Every key spelled out, never built from a variable: assemble.py --check proves no copy key is
   orphaned by scanning for literal lookups, and a key assembled from a template is invisible to it. */
const navLabel = leaf => ({
  digest: t("nav.tab.digest"), weekrecap: t("nav.tab.weekrecap"), roster: t("nav.tab.roster"), waivers: t("nav.tab.waivers"),
  records: t("nav.tab.records"), recap: t("nav.tab.recap"), trades: t("nav.tab.trades"),
  tradehist: t("nav.tab.tradehist"), ranks: t("nav.tab.ranks"),
  board: t("nav.tab.board"), movers: t("nav.tab.movers"),
  matchups: t("nav.tab.matchups"), usage: t("nav.tab.grid"), news: t("nav.tab.news"),
  weather: t("nav.tab.weather"), preview: t("nav.tab.preview"), teams: t("nav.tab.teams"),
  schedule: t("nav.tab.schedule"),
  parlay: t("nav.tab.parlay"), build: t("nav.tab.build"), dfs: t("nav.tab.dfs"), live: t("nav.tab.live"),
}[leaf] || leaf);

/* One line under the sub-row saying what a Stats view holds (2026-10-05, David: A + C). Role's is its own
   head (role.head.sub); Ranks and the rest are named plainly already. */
const navCaptionHTML = leaf => {
  const say = {board: t("nav.caption.board"), usage: t("nav.caption.usage")}[leaf];
  return say ? `<p class="stat-cap">${say}</p>` : "";
};

const navGroupLabel = (group, short) => (short ? {
  home: t("nav.group.home.short"), team: t("nav.group.team.short"), week: t("nav.group.week.short"),
  scouting: t("nav.group.scouting.short"), league: t("nav.group.league.short"),
} : {
  home: t("nav.group.home.full"), team: t("nav.group.team.full"), week: t("nav.group.week.full"),
  scouting: t("nav.group.scouting.full"), league: t("nav.group.league.full"),
})[group] || group;
