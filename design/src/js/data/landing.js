/* WHICH VIEW A GROUP CLICK OPENS (2026-10-09, ledger #91; David: "every tab opens the same view every time",
   "currently it takes you to where you were last at. this is confusing").
   Pure over (group, now, schedule, leaves): chrome/nav.js asks, this answers. The row a reader sees keeps its
   order (Live first in Matchup's); only the view a click opens is decided here.

   Matchup opens on Preview, except while a game is on: then Live (David: "maybe it's live on Sunday or during
   live games"). "On" is any game inside its window, plus Sunday from its first kickoff to its last game's end,
   so the gap between the 1 pm and the 4:25 pm slates is still Live. Players opens on Ranks. Every other group
   opens its row's first view. */

/* How long a game stays "in progress" after its kickoff: four hours, the page's own grace (SCHED_GRACE_MS in
   data/schedule.js). An NFL game runs about 3 h 10 min on the clock; overtime and a weather delay still fit. */
const LANDING_GAME_MS = 4 * 3600e3;
const LANDING_OPEN = {week: "preview", scouting: "ranks"};   // groups that do not open on the first leaf of their row
const LANDING_LIVE_LEAF = "live";
const LANDING_SUNDAY = "Sun";

/* The league's day for a kickoff is Eastern (design/preview.py `_slot`, surface/recap/state.js `wrSlot`). */
const LANDING_ET = new Intl.DateTimeFormat("en-US", {timeZone: "America/New_York", weekday: "short", year: "numeric",
  month: "numeric", day: "numeric"});
const landingDay = ms => LANDING_ET.format(new Date(ms));
const landingWeekday = ms => LANDING_ET.formatToParts(new Date(ms)).find(p => p.type === "weekday").value;

const landingKicks = games => (games || []).map(g => Date.parse((g || {}).kickoff || "")).filter(k => !isNaN(k));

/* A game is on, or it is Sunday between the day's first kickoff and the end of its last game. */
function landingLive(now, games){
  const kicks = landingKicks(games);
  if (kicks.some(k => k <= now && now < k + LANDING_GAME_MS)) return true;
  if (landingWeekday(now) !== LANDING_SUNDAY) return false;
  const today = kicks.filter(k => landingDay(k) === landingDay(now));
  return Math.min(...today) <= now && now < Math.max(...today) + LANDING_GAME_MS;   // nomutate: <= vs <: at the first kickoff the test above has answered; no Sunday game: min() is Infinity
}

/* The leaf a group click opens. `leaves` is the row as the reader sees it (navLeavesFor), so a leaf the league
   lacks falls to the row's first. */
function landingLeaf(group, now, games, leaves){
  const want = group === "week" ? (landingLive(now, games) ? LANDING_LIVE_LEAF : LANDING_OPEN.week) : LANDING_OPEN[group];
  return leaves.includes(want) ? want : leaves[0];
}
