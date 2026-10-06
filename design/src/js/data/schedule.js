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

/* ONE PAGE WEEK (David, 2026-10-05; supersedes the same day's rule that took the projections' week
   over the schedule's): the whole site turns week at the first rebuild after the week's last game is
   final. Until then every forward view (Ranks, Teams, Start/Sit, Bets, the pack) says schedWeek(), and
   Monday night is still its game to play. A backward view whose week is behind the page and whose
   stats have not landed says "final tomorrow" (recapKicker, recapChip). */
const schedFinalSoon = d => {
  const sw = schedWeek();
  return !!d && sw !== null && Number.isInteger(d.week) && d.week < sw && !d.complete;
};
const recapKicker = d => schedFinalSoon(d) ? t("weekrecap.banner.kFinal", {week: d.week})
  : d.complete ? t("weekrecap.banner.k", {week: d.week}) : t("weekrecap.banner.kSoFar", {week: d.week});
/* The Digest's recap row: the chip stays "Wk 4" (at 360px a longer one squeezes the row's text to nothing);
   the note is the first words of the row's text, which wraps. */
const recapChip = r => t("digest.recapRow.wk", {n: r.week});
const recapNote = r => schedFinalSoon(r) ? t("digest.recapRow.final") : "";

/* Is a forward block (Highlights, D/ST and K, Preview) written for the page week? Its producer runs on its
   own schedule, so for a few hours after the turn it still holds last week's rows, and a page that said
   "Week 5" over week 4's numbers would be wrong. False means: show that view's not-posted state. A block
   that names no week, or a page with no week, is not judged. (2026-10-05) */
const schedIsPageWeek = w => {
  const sw = schedWeek();
  return sw === null || !Number.isInteger(w) || w === sw;
};

/* Every game of a week, in kickoff order. */
const schedGamesOf = wk => !schedOk() || wk === null ? [] : LIVE_SCHEDULE.games
  .filter(g => g.week === wk).sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff));

/* The week's games still to play: no final score and not kicked off. */
const schedGamesLeft = (wk, now = Date.now()) => schedGamesOf(wk).filter(g => !g.final && Date.parse(g.kickoff) > now);

/* Ranks' line about the teams left off its lists (already played or on a bye). Up to SCHED_OFF_MAX codes it
   names them; past that the list is most of the league, so it names what is left instead: "Only ATL @ NO
   left in week 4" (a count past four games). With no schedule to say, or nothing left, it names the teams. */
const SCHED_OFF_MAX = 8, SCHED_LEFT_MAX = 4;
function schedOffLine(off, now = Date.now()){
  if (!off.length) return "";
  const teams = t("ranks.head.off", {teams: off.map(esc).join(", ")});
  const wk = schedWeek(), left = off.length > SCHED_OFF_MAX && wk !== null ? schedGamesLeft(wk, now) : [];
  if (!left.length) return teams;
  return left.length > SCHED_LEFT_MAX ? t("ranks.head.leftMany", {n: left.length, week: wk})
    : t("ranks.head.left", {games: left.map(g => `${esc(g.away)} @ ${esc(g.home)}`).join(", "), week: wk});
}
