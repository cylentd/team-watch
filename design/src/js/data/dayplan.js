/* The Digest's day plan (split from data/digest.js 2026-10-06, which hit its line budget): which job each Pacific
   weekday does, and the pickers that choose the subject the day's banner is about. surface/digest/day.js and the
   cards read it; nothing here draws. */

/* ---------------------------------------------------------------- the day plan
   2026-10-06 (storyboard "Digest by Day", option B): each Pacific weekday is one job, superseding the
   ticker of seven rows and DG_DAY. `banner`: the kind surface/digest/day.js leads with; `cards`: card ids
   in order ("need", "now" are Need to know and Right now); `strip`: nav leaves. Pacific, not the reader's
   clock: the league's week turns on Pacific time, and a Tuesday is waiver day everywhere.
   2026-10-07 (David: two cards was too thin): the day's job first, then the cards with data that day, five at most;
   a strip chip that a card now links (its "more") left the strip.
   2026-10-08 (Home draft B, ledger #52): the week tier sheet ("tiers") follows the day's job card every day; Thursday's
   and Monday's game is one Tonight card ("tonight": Vegas beside Claude and the game's starts), superseding Claude vs
   Vegas plus Start in this game; Sunday's Right now takes Weather's place (DG_TAKES_PLACE). Ranks left the strips,
   since the tier sheet links it. */
const DG_PLAN = {
  2: {key: "tue", banner: "adds",    cards: ["adds", "tiers", "gains", "usage"],                     strip: ["weekrecap", "schedule", "weather", "news"]},
  3: {key: "wed", banner: "usage",   cards: ["usage", "tiers", "gains", "defenses", "adds", "calls"], strip: ["preview", "matchups", "weekrecap", "news"]},
  4: {key: "thu", banner: "tnf",     cards: ["tonight", "tiers", "status", "calls"],                strip: ["usage", "schedule", "news"]},
  5: {key: "fri", banner: "status",  cards: ["status", "tiers", "gains", "smash", "weather"],       strip: ["preview", "parlay", "news"]},
  6: {key: "sat", banner: "smash",   cards: ["smash", "tiers", "bold", "calls", "weather"],         strip: ["preview", "news"]},
  0: {key: "sun", banner: "kickoff", cards: ["need", "tiers", "now", "weather", "calls"],           strip: ["live", "usage", "news"]},
  1: {key: "mon", banner: "tonight", cards: ["tonight", "tiers", "gains", "calls"],                 strip: ["weekrecap", "waivers"]},
};

/* A moment as the league's clock reads it: the weekday (0 Sunday) and the date, Pacific. */
const DG_PT = new Intl.DateTimeFormat("en-US", {timeZone: "America/Los_Angeles", weekday: "short",
  year: "numeric", month: "2-digit", day: "2-digit"});
const DG_WD = {Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6};
function dgPacific(ms){
  const p = Object.fromEntries(DG_PT.formatToParts(new Date(ms)).map(x => [x.type, x.value]));
  return {day: DG_WD[p.weekday], date: `${p.year}-${p.month}-${p.day}`};
}
const dgDayPlan = ms => DG_PLAN[dgPacific(ms).day];

/* The cards to draw, from what each drew (`drawn`: id -> HTML or ""); none at all: Need to know stands in. */
function dgDayCards(plan, drawn){
  const cards = plan.cards.filter(id => drawn[id]);
  return cards.length ? cards : ["need"];
}

/* ---------------------------------------------------------------- the night-game card (2026-10-07)
   One preview card, two days: Wednesday previews Thursday night's game, Sunday previews Sunday night's. It is not in
   DG_PLAN's lists: it takes the second place on those two days (dgCardOrder), after the day's job card (usage movers,
   Need to know). `slot` is the league's kickoff window from design/preview.py; the card goes at the kickoff. */
const DG_NIGHT_SLOT = {wed: "thu", sun: "sunnight"};
const DG_MAX_CARDS = 5;   // David, 2026-10-07: a day holds five cards at most

/* {i, game}: the night game still to kick off, `i` its index in preview.games (what Preview opens on), or null.
   Sunday's must be today's (a Sunday night game of another week is not tonight's). */
function dgPickNight(preview, key, ms){
  const slot = DG_NIGHT_SLOT[key], games = (preview && preview.games) || [];
  if (!slot) return null;
  const hits = games.map((game, i) => ({i, game})).filter(x => x.game.slot === slot && Date.parse(x.game.kickoff) > ms
    && (key !== "sun" || dgToday(x.game.kickoff, ms)));
  return hits.sort((a, b) => Date.parse(a.game.kickoff) - Date.parse(b.game.kickoff))[0] || null;
}

/* The plan's card ids with the night card second on the days that have one. */
const dgCardOrder = plan => DG_NIGHT_SLOT[plan.key] ? [plan.cards[0], "night", ...plan.cards.slice(1)] : plan.cards;

/* A card that, when it draws, takes another's place (2026-10-08, Home draft B): from the first kickoff Right now
   stands where Weather was, so the day keeps its last card. */
const DG_TAKES_PLACE = {now: "weather"};

/* The cards to draw from what each drew: the plan's, empty ones skipped, five at most, Need to know when none. */
function dgCardList(plan, drawn){
  const gone = Object.entries(DG_TAKES_PLACE).filter(([id]) => drawn[id]).map(([, was]) => was);
  return dgDayCards({cards: dgCardOrder(plan).filter(id => !gone.includes(id))}, drawn).slice(0, DG_MAX_CARDS);
}

/* The strip's views: Recap only while its week is fresh (dgRecap), as the Recap row was. */
const dgStripLeaves = (plan, facts) => plan.strip.filter(leaf => leaf !== "weekrecap" || facts.recap);

/* ---------------------------------------------------------------- the banner's subject, per day
   Each takes its block and returns the row the banner is about, or null (the packet's lead then leads). */
const dgPickAdd = d => (d && d.adds && d.adds[0]) || null;

/* Friday: the hurt player with the highest healthy projection (2026-10-06; the packet's hurt list is sorted by rank
   within a position, so its first row is a QB or a WR by the sorting, not by who matters more). The points are the
   page's own list (LIVE_RANKS, `ranks`): his row if he has one, else the points the list puts at his position and
   rank, because a player who is Out has no row (the ranking leaves him out). With no points for anyone, the lowest
   rank number across positions; with no rank either, the packet's first. */
/* The hurt rows ranked the same way, best first: the ones with points by their points, then the rest by rank. */
function dgHurtRanked(hurt, ranks){
  const rows = (ranks && ranks.rows) || [];
  const pts = r => { const at = rows.find(x => x.slug === r.slug) || rows.find(x => r.rank != null && x.pos === r.pos && x.rank === r.rank); return at ? at.pts : null; };
  const all = (hurt || []).map(r => ({r, p: pts(r)}));
  const scored = all.filter(x => x.p != null).sort((a, b) => b.p - a.p);
  const rest = all.filter(x => x.p == null).sort((a, b) => (a.r.rank ?? Infinity) - (b.r.rank ?? Infinity));
  return [...scored, ...rest].map(x => x.r);
}
const dgPickStatus = (d, ranks) => dgHurtRanked(d && d.hurt, ranks)[0] || null;

/* Thursday's Injury watch (2026-10-08, Home draft B): the questionable players ranked highest league-wide, the
   storyboard's three of twelve, and how many are questionable in all. The Out are decided; the Q are the watch. */
const DG_WATCH_N = 3;
function dgWatchRows(d, ranks){
  const q = ((d && d.hurt) || []).filter(r => r.status === "Questionable");
  return {rows: dgHurtRanked(q, ranks).slice(0, DG_WATCH_N), of: q.length};
}

/* "WR2": his rank in Ranks' own list, the one rank Home shows (the storyboard found a back RB17 on one card and RB22
   in Ranks); "" when Ranks has no row for him. */
function dgRankOf(r, ranks){
  const at = ((ranks && ranks.rows) || []).find(x => x.slug === r.slug);
  return at && at.rank != null ? `${at.pos}${at.rank}` : "";
}

/* LIVE_USAGE_MOVERS (ff-jarvis's top five role changes) may not exist yet. The banner is built from his numbers, so
   the first row the card draws (one with a share) is the subject; Claude's line stays in the row. */
const dgPickUsage = b => ((b && b.rows) || []).find(r => r && r.now != null) || null;
const dgToday = (iso, ms) => !!iso && dgPacific(Date.parse(iso)).date === dgPacific(ms).date;

/* Today's game with Claude's take (LIVE_PREVIEW), first by kickoff: Thursday night's. */
const dgPickTnf = (preview, ms) => ((preview && preview.games) || [])
  .filter(g => g.take && g.take.head && dgToday(g.kickoff, ms))
  .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff))[0] || null;

/* Claude's pick as the banner says it: "DAL 28–21", or the winner alone without a score. */
function dgTakePick(take){
  const p = take && take.pick, w = p && p.winner;
  if (!w) return "";
  const s = p.score || {}, other = Object.keys(s).find(k => k !== w);
  return other && s[w] != null ? `${w} ${s[w]}–${s[other]}` : w;
}

/* Today's first game still to kick off (Sunday), and today's game not yet final (Monday night). */
const dgByKick = games => games.slice().sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff));
const dgPickKickoff = (games, ms) => dgByKick(games || []).find(g => dgToday(g.kickoff, ms) && Date.parse(g.kickoff) > ms) || null;
const dgPickTonight = (games, ms) => dgByKick(games || []).find(g => dgToday(g.kickoff, ms) && !g.final) || null;

/* What `opp`'s defense has allowed `pos` this season (LIVE_DEFENSE `def`, rank 1 allows the fewest): {cur, of, most},
   or null with no row for the club. `cur` is its {pts_pg, rank}; it allows the `most`-th most of the `of` clubs ranked
   at the position (1 = the most). The one place this rank is worked out: the SMASH banner picks by it and its card
   words it. */
function dgAllowed(def, opp, pos){
  const form = def && def.form, f = form && opp ? schedTeamRow({teams: form}, opp) : null;
  const cur = f && f.current && f.current[pos];
  if (!cur || cur.rank == null) return null;
  const of = Math.max(0, ...Object.values(form).map(x => (x.current && x.current[pos] && x.current[pos].rank) || 0));
  return {cur, of, most: of - cur.rank + 1};
}

/* The defense allowing `pos` the most this season: {team, pts, of}, or null. `of` is the clubs ranked at it. */
const DG_DEF_POS = ["QB", "RB", "WR", "TE"];
function dgDefenseTop(form, pos){
  const rows = Object.entries(form || {}).map(([team, f]) => ({team, s: f && f.current && f.current[pos]})).filter(x => x.s && x.s.pts_pg != null);
  if (!rows.length) return null;
  rows.sort((a, b) => b.s.pts_pg - a.s.pts_pg || (a.team < b.team ? -1 : 1));
  return {team: rows[0].team, pts: rows[0].s.pts_pg, of: Math.max(rows.length, ...rows.map(x => x.s.rank || 0))};
}

/* Wednesday with no usage mover: the Defenses card's top row, the first position it draws, {pos, team, pts, of}. */
function dgPickDefense(def){
  for (const pos of DG_DEF_POS){
    const top = dgDefenseTop(def && def.form, pos);
    if (top) return {pos, ...top};
  }
  return null;
}

/* Saturday: the SMASH (LIVE_SS3) whose opponent allows his position the most this season (`most` 1 of `of`
   allows the most). LIVE_SOS ranks a schedule over weeks, not one opponent. */
function dgPickSmash(ss3, def){
  const rows = (ss3 && ss3.smash) || [];
  if (!rows.length) return null;
  const best = rows.map(row => ({row, a: dgAllowed(def, row.opp, row.pos)})).filter(x => x.a)
    .sort((x, y) => x.a.most - y.a.most || x.row.rank - y.row.rank)[0];
  return best ? {row: best.row, allow: best.a.cur, most: best.a.most, of: best.a.of} : {row: rows[0], allow: null, most: null, of: null};
}
