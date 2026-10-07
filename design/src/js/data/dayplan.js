/* The Digest's day plan (split from data/digest.js 2026-10-06, which hit its line budget): which job each Pacific
   weekday does, and the pickers that choose the subject the day's banner is about. surface/digest/day.js and the
   cards read it; nothing here draws. */

/* ---------------------------------------------------------------- the day plan
   2026-10-06 (storyboard "Digest by Day", option B): each Pacific weekday is one job, superseding the
   ticker of seven rows and DG_DAY. `banner`: the kind surface/digest/day.js leads with; `cards`: card ids
   in order ("need", "now" are Need to know and Right now); `strip`: nav leaves. Pacific, not the reader's
   clock: the league's week turns on Pacific time, and a Tuesday is waiver day everywhere. */
const DG_PLAN = {
  2: {key: "tue", banner: "adds",    cards: ["adds", "gains"],                     strip: ["weekrecap", "usage", "schedule", "weather"]},
  3: {key: "wed", banner: "usage",   cards: ["usage", "defenses"],                 strip: ["waivers", "preview", "matchups", "weekrecap"]},
  4: {key: "thu", banner: "tnf",     cards: ["vegas", "game", "status"],           strip: ["usage", "schedule", "waivers", "news"]},
  5: {key: "fri", banner: "status",  cards: ["status", "gains"],                   strip: ["matchups", "weather", "parlay", "news"]},
  6: {key: "sat", banner: "smash",   cards: ["smash", "bold", "calls", "weather"], strip: ["preview", "news"]},
  0: {key: "sun", banner: "kickoff", cards: ["need", "now", "weather"],            strip: ["live", "parlay"]},
  1: {key: "mon", banner: "tonight", cards: ["game", "gains"],                     strip: ["weekrecap", "waivers"]},
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
function dgPickStatus(d, ranks){
  const hurt = (d && d.hurt) || [], rows = (ranks && ranks.rows) || [];
  const pts = r => { const at = rows.find(x => x.slug === r.slug) || rows.find(x => r.rank != null && x.pos === r.pos && x.rank === r.rank); return at ? at.pts : null; };
  const scored = hurt.map(r => ({r, p: pts(r)})).filter(x => x.p != null).sort((a, b) => b.p - a.p);
  if (scored.length) return scored[0].r;
  return hurt.slice().sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity))[0] || null;
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
