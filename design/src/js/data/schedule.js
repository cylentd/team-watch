/* The season schedule (LIVE_SCHEDULE, design/schedule.py) as the page asks it: which week is this
   week, and which club is which. Shared by the roster cards, the week's pack and This week > Weather;
   moved here from teams/cards.js and teams/pack.js on 2026-09-26, when Weather became the third
   reader. Every function is pure over the injected block and the clock. */

/* A game still counts as this week's for four hours after it kicks off. */
const SCHED_GRACE_MS = 4 * 3600e3;
const schedOk = () => typeof LIVE_SCHEDULE !== "undefined" && !!LIVE_SCHEDULE;

/* The schedule speaks ESPN's club codes; rosters and ff-jarvis blocks may say nflverse's (LA, WAS).
   `alias` maps the second to the first, so one table serves both directions. */
const schedCode = team => (schedOk() && LIVE_SCHEDULE.alias || {})[team] || team;

/* A row of a team-keyed block (LIVE_WEATHER, LIVE_LINES) under either spelling of the club. */
function schedTeamRow(block, team){
  if (!block) return null;
  const alias = (schedOk() && LIVE_SCHEDULE.alias) || {};
  const plain = Object.keys(alias).find(k => alias[k] === team);
  return block.teams[team] || block.teams[alias[team]] || (plain ? block.teams[plain] : null) || null;
}

/* The page's week, decided by the build from the scores in its data (design/schedule.py page_week),
   never by the reader's clock: since 2026-09-28 the pack, the brief and Weather turn the week at the
   same build as the recap and the projections, not the moment Monday night kicks off. */
const schedWeek = () => schedOk() ? LIVE_SCHEDULE.week ?? null : null;

/* Every game of a week, in kickoff order. */
const schedGamesOf = wk => !schedOk() || wk === null ? [] : LIVE_SCHEDULE.games
  .filter(g => g.week === wk).sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff));
