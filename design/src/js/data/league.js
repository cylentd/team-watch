/* League > Recap (it was My teams > League, 2026-09-26; storyboard https://claude.ai/artifact/Lf17QZYMoNJvmVHCT45xUJ): each
   league's weekly recap, the rivalry with this week's opponent, and its history. LIVE_LEAGUE (ESPN,
   since 2014) and LIVE_LEAGUE_YAHOO (since 2018, champions only) are design/league_recap.py's: every
   award, record and head-to-head is computed there, so the page only picks the team on screen.
   Nothing here helps anyone beat anyone; it is what the league already knows about itself. */
const LGS = {
  espn: (typeof LIVE_LEAGUE !== "undefined" && LIVE_LEAGUE) || null,
  yahoo: (typeof LIVE_LEAGUE_YAHOO !== "undefined" && LIVE_LEAGUE_YAHOO) || null,
  ayo: (typeof LIVE_LEAGUE_AYO !== "undefined" && LIVE_LEAGUE_AYO) || null,   // the third league, 2026-09-29
};
/* Each Yahoo league's Trades block (design/league_trades.py), by the same keys: AYO has none until
   ff-jarvis grades its trades, and Trades says so. */
const LG_TRADES = {
  yahoo: (typeof LIVE_TRADES !== "undefined" && LIVE_TRADES) || null,
  ayo: (typeof LIVE_TRADES_AYO !== "undefined" && LIVE_TRADES_AYO) || null,
};

/* The League group's league (2026-10-05, David: one chip, "pick your team, the league follows"): the
   league of the reader's team, whichever of David's three it is; a leaguemate's is his league's.
   Until 2026-10-05 Recap, Records and Trades had a Madden Curse / AYO switch of their own (2026-09-29,
   kept in `tw-league`), and the Teams board a third with ESPN: two ways to say one thing. The team is
   the one pick now (data/mates.js myTeamSave), so a reload keeps it. */
const lgFocusKey = () => navFocusKey(lgSeat(), lbKeys());
/* The reader's own team: the one they picked, else David's on a page with no leaguemates, else none (the
   chip then says "Pick your team"). Recap puts this team's game first. The team on screen (VIEW) can be
   another's, reached from a profile; the League group is about the reader's. */
function lgMine(){
  const k = myTeamLoad();
  return k ? TEAMS[k] : needsPick() ? null : TEAMS[VIEW] || null;
}
/* The team whose league the League group shows: the reader's, else the one on screen (David's yahoo by default). */
const lgSeat = () => lgMine() || TEAMS[VIEW];
/* The Yahoo leagues with a League block: the ones Records and Trades are about. */
const lgLeagueKeys = () => myLeagueKeys().filter(k => TEAMS[k].site === "yahoo" && LGS[k]);
/* The Yahoo league Recap's back page, Records and Trades draw: the focus league when it is one, else the
   first (an ESPN team on a stale #records link). */
function lgLeagueKey(){
  const ks = lgLeagueKeys(), f = lgFocusKey();
  return ks.includes(f) ? f : ks[0] || null;
}

/* The league of a team: David's own two by key, a leaguemate's by its league. A connected league has
   none. */
const lgOf = team => !team || team.connected ? null : LGS[team.mate ? team.league : team.key] || null;

/* The league on screen. Recap (lgUsePicked, leagueHTML) sets it before drawing, so every helper below reads one league. */
let LG = null;

/* Every team's record in the hero, from its site's own standings: ESPN's adds a win for a top-half
   score each week, so 1-1 head to head can be 2-2. It replaced a hard-coded "0–0". */
Object.values(LGS).forEach(L => L && L.teams.forEach(x => {
  if (TEAMS[x.key]) TEAMS[x.key].record = x.t ? `${x.w}–${x.l}–${x.t}` : `${x.w}–${x.l}`;
}));

/* The week the recap shows: null until the reader taps a chip, and then the newest decided week.
   Reset when the league on screen changes, since the other league's weeks are its own. */
let LG_WEEK = null;

/* Whether Records is a leaf is `(LGS[focus] || {}).book` (chrome/nav.js navFacts): a league whose block
   carries a record book (Yahoo's back page, design/league_back.py). */

/* The team id of the team on screen, matched by the key the team switch uses. */
const lgIdOf = team => ((LG && team && LG.teams.find(x => x.key === team.key)) || {}).id;

/* Today's name for an id. A team that has left the league has no name on the page: ESPN's early
   seasons carry its default "Team <surname>", and the page is public. */
const lgName = id => { const x = LG && LG.teams.find(tm => tm.id === id); return x ? esc(x.name) : t("league.former"); };
/* The manager's first name where the league has one (Yahoo, since 2026-09-27), else the team's name. */
const lgMgr = id => { const x = LG && LG.teams.find(tm => tm.id === id); return x ? esc(x.mgr || x.name) : t("league.former"); };

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
