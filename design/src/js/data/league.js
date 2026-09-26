/* My teams > League (2026-09-26; storyboard https://claude.ai/artifact/Lf17QZYMoNJvmVHCT45xUJ): the
   ESPN league's weekly recap, the rivalry with this week's opponent, and its history since 2014.
   LIVE_LEAGUE is design/league_recap.py's: every award, record and head-to-head is computed there,
   so the page only picks which team is on screen. ESPN only: Yahoo's API is still unapproved.
   Nothing here helps anyone beat anyone; it is what the league already knows about itself. */
const LG = (typeof LIVE_LEAGUE !== "undefined" && LIVE_LEAGUE) ? LIVE_LEAGUE : null;

/* Every ESPN team's record in the hero, from ESPN's own standings: this league adds a win for a
   top-half score each week, so 1-1 head to head can be 2-2. It replaced a hard-coded "0–0". */
if (LG) LG.teams.forEach(x => {
  if (TEAMS[x.key]) TEAMS[x.key].record = x.t ? `${x.w}–${x.l}–${x.t}` : `${x.w}–${x.l}`;
});

/* The week the recap shows: null until the reader taps a chip, and then the newest decided week. */
let LG_WEEK = null;

/* A team in the ESPN league: David's own (key "espn") or a leaguemate's there. A connected league
   and every Yahoo team have no League tab. */
const hasLeague = team => !!(LG && team && (team.key === "espn" || (team.mate && team.league === "espn")));

/* The ESPN team id of the team on screen, matched by the key the team switch uses. */
const lgIdOf = team => ((LG && team && LG.teams.find(x => x.key === team.key)) || {}).id;

/* Today's name for an id. A team that has left the league has no name on the page: early seasons
   carry ESPN's default "Team <surname>", and the page is public. */
const lgName = id => { const x = LG && LG.teams.find(tm => tm.id === id); return x ? esc(x.name) : t("league.former"); };

const lgWeek = () => (LG && LG.weeks.find(w => w.week === LG_WEEK)) || (LG && LG.weeks[LG.weeks.length - 1]) || null;

/* 137.35 -> "137.35", 58.7 -> "58.70": ESPN scores to two places, so every score reads the same width. */
const lgPts = v => Number(v).toFixed(2);

/* This week's opponent for an id, or null on a bye or with no schedule. */
function lgOpp(id){
  const g = LG && LG.now.find(x => x.a === id || x.b === id);
  return g ? (g.a === id ? g.b : g.a) : null;
}

/* a's all-time record against b, or null when they have never met. */
const lgH2H = (a, b) => (LG && LG.h2h[String(a)] && LG.h2h[String(a)][String(b)]) || null;
