/* The Takes view's state and its one cut of LIVE_STARTSIT (design/startsit.py). The calls are
   ff-jarvis's, frozen there before each kickoff and graded there; the page only shows them.
   One list across positions since 2026-09-29 (it was a QB/RB/WR/TE chip row): a take is ordered by
   how far we sit from the experts, in units of that position's own threshold (`gap`, ff-jarvis's
   gap_n), so a 3-spot QB take and a 6-spot RB take weigh the same. */

/* The one open row, across both lists ("c:<slug>" ours, "p:<slug>" Pitcher List's), "" for none. */
let MU_OPEN = "";

const muGap = r => r.gap == null ? -Infinity : r.gap;
const muCalls = tag => (LIVE_STARTSIT ? LIVE_STARTSIT.calls : []).filter(r => r.tag === tag)
  .sort((a, b) => muGap(b) - muGap(a) || b.pts - a.pts);
const muPl = () => LIVE_STARTSIT ? LIVE_STARTSIT.pl : [];
const muScore = x => x == null ? "—" : x.toFixed(2);

/* The kickoff, from the season schedule (LIVE_SCHEDULE, ESPN's club codes), matched on the call's
   week and either club: the calls carry the props feed's raw codes (JAC), so the side that is
   spelled the same finds the game. Pacific wall-clock words, "Sun 1:25 PM", as the Digest writes
   them. Null when the schedule does not hold the game; the row then names the matchup alone. */
const MU_KICK_FMT = new Intl.DateTimeFormat("en-US", {timeZone: "America/Los_Angeles", weekday: "short",
  hour: "numeric", minute: "2-digit"});
function muKick(r){
  if (typeof LIVE_SCHEDULE === "undefined" || !LIVE_SCHEDULE || !LIVE_STARTSIT) return null;
  const alias = LIVE_SCHEDULE.alias || {}, code = c => alias[c] || c;
  const clubs = [code(r.team), code(r.opp)];
  const g = LIVE_SCHEDULE.games.find(x => x.week === LIVE_STARTSIT.week
    && (clubs.includes(x.home) || clubs.includes(x.away)));
  return g ? MU_KICK_FMT.format(new Date(g.kickoff)).replace(",", "") : null;
}

/* "wk 1–2", or "wk 1" after one graded week. */
const muWeeks = w => w.length > 1 ? `${Math.min(...w)}–${Math.max(...w)}` : String(w[0]);

/* Amendment 2 (2026-09-29). The splits panel under the record, and the one paused take type whose
   shadow takes are showing ("" for none); both open in place, never by re-render. */
let MU_SPLITS = false;
let MU_SHADOW = "";
const muShadow = (tag, pos) => (LIVE_STARTSIT && LIVE_STARTSIT.shadow || []).filter(r => r.tag === tag && r.pos === pos)
  .sort((a, b) => muGap(b) - muGap(a) || b.pts - a.pts);
const muPaused = tag => ((LIVE_STARTSIT && LIVE_STARTSIT.rule || {}).paused || []).filter(p => p.tag === tag);
