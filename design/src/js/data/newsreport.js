/* Players > News as an injury report (ledger #95, 2026-10-09; DESIGN.md "News"). Who is on it: the reader's
   players, their wire, the starters in their leagues; what each row says: the Sunday word, Wednesday to Friday,
   the newest story, the next man up free in a league of theirs. Every word is the build's (design/news.py
   news_report); this file only picks, groups and orders. surface/news/news.js draws it. */
const NR_TUESDAY = 2;                         // the Pacific weekday the report turns into player rows (dgPacific's 0 = Sunday)
const NR_PAGE = 8;                            // starters on one page of the report
const NR_DAYS = ["Wed", "Thu", "Fri"];        // the practice days before a Sunday game
const NR_GAME = ["out", "doubtful", "questionable", "cleared"];   // the words that say Sunday, not a practice
const NR_GROUPS = ["mine", "wire", "starter"];
/* Worst first: a row's place in its group. A row with no word at all sorts last. */
const NR_SEVERITY = ["out", "doubtful", "questionable", "dnp", "limited", "full", "cleared"];
const NR_DAY_MS = 86400000;
const NR_WEEK_DAYS = 7;
const NR_ISO_DATE = 10;                       // "YYYY-MM-DD", the date part of an ISO timestamp

/* "YYYY-MM-DD": the Tuesday on or before the moment, Pacific; a practice line from before it is last week's. */
function nrWeekStart(ms){
  const p = dgPacific(ms), back = (p.day - NR_TUESDAY + NR_WEEK_DAYS) % NR_WEEK_DAYS;
  const [y, m, d] = p.date.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d) - back * NR_DAY_MS).toISOString().slice(0, NR_ISO_DATE);
}
const nrTuesday = ms => dgPacific(ms).day === NR_TUESDAY;

/* A team's league key, as data/league.js lgOf reads it. */
const nrLeagueOf = team => team.mate ? team.league : team.key;

/* {mine, starters, leagues, rostered: {league: slugs}} for the followed team keys. With none followed: every
   league on the page, and nobody's players as the reader's. */
function nrScope(teams, followed){
  const all = Object.values(teams || {}).filter(t => t && t.roster);
  const own = (followed || []).map(k => teams[k]).filter(t => t && t.roster);
  const leagues = [...new Set((own.length ? own : all).map(nrLeagueOf))];
  const slugs = rows => rows.map(r => r.slug).filter(Boolean);
  const rostered = Object.fromEntries(leagues.map(lg =>
    [lg, [...new Set(all.filter(t => nrLeagueOf(t) === lg).flatMap(t => slugs(t.roster)))]]));
  const starters = [...new Set(all.filter(t => leagues.includes(nrLeagueOf(t)))
    .flatMap(t => slugs(t.roster.filter(r => r.start))))];
  return {mine: [...new Set(own.flatMap(t => slugs(t.roster)))], starters, leagues, rostered};
}

/* The player a story is about: the build's, else the first of its name's slug candidates someone rosters. */
function nrSlugOf(it, known){
  if (it.slug) return it.slug;
  return (it.slugs || []).find(s => known.has(s)) || null;
}
const nrRank = w => { const i = NR_SEVERITY.indexOf(w); return i < 0 ? NR_SEVERITY.length : i; };

/* One row per player on the report, ordered by group (NR_GROUPS), then the worst word, then the newest story.
   `wire`: the slugs the reader's own waiver packets list. `ms`: now. */
function nrRows(news, scope, wire, ms){
  const players = (news && news.players) || {}, mine = new Set(scope.mine), wired = new Set(wire || []);
  const starters = new Set(scope.starters);
  const known = new Set([...mine, ...wired, ...starters, ...Object.keys(players)]);
  const groupOf = s => mine.has(s) ? "mine" : wired.has(s) ? "wire" : starters.has(s) ? "starter" : null;
  const start = nrWeekStart(ms), by = new Map();
  ((news && news.items) || []).forEach(it => {
    const s = nrSlugOf(it, known), group = s && groupOf(s);
    if (!group) return;
    if (!by.has(s)) by.set(s, {slug: s, group, stories: []});
    by.get(s).stories.push(it);
  });
  /* A player ff-jarvis's practice report lists has a row even when no story names him. */
  Object.entries(players).forEach(([s, p]) => {
    const group = p.report && groupOf(s);
    if (group && !by.has(s)) by.set(s, {slug: s, group, stories: []});
  });
  const at = r => (r.newest && Date.parse(r.newest.at)) || 0;
  const rows = [...by.values()].map(g => nrRow(g, players, scope, start));
  return rows.sort((a, b) => NR_GROUPS.indexOf(a.group) - NR_GROUPS.indexOf(b.group)
    || nrRank(a.sunday || a.latest) - nrRank(b.sunday || b.latest) || at(b) - at(a));
}

/* His week: the practice report's marks, then a headline's for a day the report left empty. */
function nrRow(g, players, scope, start){
  const p = players[g.slug] || {};
  const days = {};
  NR_DAYS.forEach(d => { if (p.days && p.days[d]) days[d] = p.days[d]; });
  g.stories.forEach(it => {
    const thisWeek = it.at && dgPacific(Date.parse(it.at)).date >= start;
    if (it.day && NR_DAYS.includes(it.day) && thisWeek && !(it.day in days)) days[it.day] = it.status;
  });
  const said = g.stories.find(it => NR_GAME.includes(it.status));
  const latest = (g.stories.find(it => it.status) || {}).status || null;
  const outStory = g.stories.find(it => it.next && it.next.length);
  const next = (outStory ? outStory.next : []).map(s => ({
    slug: s, n: (players[s] || {}).n || s,
    free: scope.leagues.filter(lg => !(scope.rostered[lg] || []).includes(s)),
  })).filter(x => x.free.length);
  const [newest = null, ...more] = g.stories;
  return {slug: g.slug, n: p.n || g.slug, pos: p.pos || null, team: p.team || null, group: g.group,
          sunday: said ? said.status : (p.injury || null), latest, days, newest, more, next};
}

/* [{key, rows}] in NR_GROUPS order, an empty group left out. */
const nrGroups = rows => NR_GROUPS.map(key => ({key, rows: rows.filter(r => r.group === key)})).filter(g => g.rows.length);

/* The headline without his name and injury tag, for a row that names him already: "Officially ruled out Sunday". */
function nrWhat(title, name){
  const whole = (title || "").trim();
  if (!name || !whole.startsWith(name)) return whole;
  const rest = whole.slice(name.length).trim().replace(/^\([^)]*\)\s*/, "");
  return rest ? rest[0].toUpperCase() + rest.slice(1) : whole;
}

/* One page of a list: {rows, at, pages}, `at` clamped to the pages there are. */
function nrPage(list, at){
  const pages = Math.max(1, Math.ceil(list.length / NR_PAGE));
  const i = Math.min(Math.max(0, at || 0), pages - 1);
  return {rows: list.slice(i * NR_PAGE, (i + 1) * NR_PAGE), at: i, pages};
}
