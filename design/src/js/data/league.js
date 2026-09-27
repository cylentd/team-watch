/* My teams > League (2026-09-26; storyboard https://claude.ai/artifact/Lf17QZYMoNJvmVHCT45xUJ): each
   league's weekly recap, the rivalry with this week's opponent, and its history. LIVE_LEAGUE (ESPN,
   since 2014) and LIVE_LEAGUE_YAHOO (since 2018, champions only) are design/league_recap.py's: every
   award, record and head-to-head is computed there, so the page only picks the team on screen.
   Nothing here helps anyone beat anyone; it is what the league already knows about itself. */
const LGS = {
  espn: (typeof LIVE_LEAGUE !== "undefined" && LIVE_LEAGUE) || null,
  yahoo: (typeof LIVE_LEAGUE_YAHOO !== "undefined" && LIVE_LEAGUE_YAHOO) || null,
};

/* The league of a team: David's own two by key, a leaguemate's by its league. A connected league has
   none. */
const lgOf = team => !team || team.connected ? null : LGS[team.mate ? team.league : team.key] || null;

/* The league on screen. renderLeague sets it before drawing, so every helper below reads one league. */
let LG = null;

/* Every team's record in the hero, from its site's own standings: ESPN's adds a win for a top-half
   score each week, so 1-1 head to head can be 2-2. It replaced a hard-coded "0–0". */
Object.values(LGS).forEach(L => L && L.teams.forEach(x => {
  if (TEAMS[x.key]) TEAMS[x.key].record = x.t ? `${x.w}–${x.l}–${x.t}` : `${x.w}–${x.l}`;
}));

/* The week the recap shows: null until the reader taps a chip, and then the newest decided week.
   Reset when the league on screen changes, since the other league's weeks are its own. */
let LG_WEEK = null;

const hasLeague = team => !!lgOf(team);

/* The Records tab: a league whose block carries a record book (Yahoo's back page, design/league_back.py). */
const hasRecords = team => !!(lgOf(team) || {}).book;

/* The team id of the team on screen, matched by the key the team switch uses. */
const lgIdOf = team => ((LG && team && LG.teams.find(x => x.key === team.key)) || {}).id;

/* Today's name for an id. A team that has left the league has no name on the page: ESPN's early
   seasons carry its default "Team <surname>", and the page is public. */
const lgName = id => { const x = LG && LG.teams.find(tm => tm.id === id); return x ? esc(x.name) : t("league.former"); };

const lgWeek = () => (LG && LG.weeks.find(w => w.week === LG_WEEK)) || (LG && LG.weeks[LG.weeks.length - 1]) || null;

/* 137.35 -> "137.35", 58.7 -> "58.70": both sites score to two places, so every score reads the same width. */
const lgPts = v => Number(v).toFixed(2);

/* This week's opponent for an id, or null on a bye or with no schedule. */
function lgOpp(id){
  const g = LG && LG.now.find(x => x.a === id || x.b === id);
  return g ? (g.a === id ? g.b : g.a) : null;
}

/* a's record against b (all-time on ESPN, this season on Yahoo: LG.scope), or null when they have
   never met. */
const lgH2H = (a, b) => (LG && LG.h2h[String(a)] && LG.h2h[String(a)][String(b)]) || null;
