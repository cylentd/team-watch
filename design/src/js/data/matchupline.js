/* The matchup line (2026-10-07, David's pick "B . Row + back"): who a roster player faces this week, as
   one model both the Sheet row and the card back draw ("vs BUF 5th", a roof mark, the kickoff under it).
   Pure over the injected blocks; nothing here prints.

   The rank is ff-jarvis's own matchup number for the player (LIVE_PROFILES `next.factor.rank`: 1 = the
   toughest defense for his position, 32 = the easiest), the number his projection prices, so the line
   agrees with the points beside it. A player without one takes the opponent's form rank from LIVE_DEFENSE
   (this season, same direction); one with neither still names the opponent. Colour is the band of the
   rank, 1-8 hard, 9-24 middle, 25-32 easy: it explains the projection, it does not claim an edge. */
const ML_BAND = 8, ML_FIELD = 32;

/* "hard" | "mid" | "easy" for a rank of `of` (1 = toughest), "" with none. */
function mlTone(rank, of = ML_FIELD){
  if (!rank) return "";
  return rank <= ML_BAND ? "hard" : rank > of - ML_BAND ? "easy" : "mid";
}

/* The stadium's roof from its LIVE_WEATHER row: "dome", "retractable", or "" for open air or no row. */
const mlRoof = row => row && (row.roof === "dome" || row.roof === "retractable") ? row.roof : "";

/* His club's game in the page's week (schedWeek), kickoff order. With no week it is the next kickoff, as
   the cards' own lookup. null when the schedule is absent or the club has no game that week. */
function mlGameOf(team){
  if (!schedOk()) return null;
  const code = schedCode(team), wk = schedWeek(), floor = Date.now() - SCHED_GRACE_MS;
  return LIVE_SCHEDULE.games
    .filter(g => (g.home === code || g.away === code) && (wk !== null ? g.week === wk : Date.parse(g.kickoff) > floor))
    .sort((a, b) => Date.parse(a.kickoff) - Date.parse(b.kickoff))[0] || null;
}

/* The opponent's rank against his position from LIVE_DEFENSE: 1 allows the fewest points. `of` is the
   highest rank anyone holds, not the count of teams in the block. */
function mlFormRank(opp, pos){
  if (typeof LIVE_DEFENSE === "undefined" || !LIVE_DEFENSE || !LIVE_DEFENSE.form) return null;
  const row = schedTeamRow({teams: LIVE_DEFENSE.form}, opp), cur = row && row.current && row.current[pos];
  if (!cur || !cur.rank) return null;
  const of = Math.max(...Object.values(LIVE_DEFENSE.form).map(x => (x.current && x.current[pos] && x.current[pos].rank) || 0));
  return cur.rank <= of ? {rank: cur.rank, of} : null;
}

/* {rank, of, src} for a player against `opp` (the club the schedule says he faces), or null. His profile's
   number counts only when it was made against that club: last week's profile names last week's opponent. */
function mlRankFor(p, opp){
  const prof = profileFor(p), nx = prof && prof.next, f = nx && nx.factor;
  if (f && f.rank && f.of && nx.opp && schedCode(nx.opp) === schedCode(opp)) return {rank: f.rank, of: f.of, src: "factor"};
  const form = mlFormRank(opp, p.pos);
  return form ? {...form, src: "form"} : null;
}

/* null with no schedule, {bye: true} when his club has no game this week, else
   {opp, home, rank, of, tone, roof, kickoff, src}. */
function matchupLine(p){
  if (!schedOk() || !p) return null;
  const g = mlGameOf(p.team);
  if (!g) return {bye: true};
  const code = schedCode(p.team), home = g.home === code, opp = home ? g.away : g.home;
  const r = mlRankFor(p, opp);
  const w = schedTeamRow(typeof LIVE_WEATHER !== "undefined" ? LIVE_WEATHER : null, g.home);
  return {opp, home, rank: r ? r.rank : null, of: r ? r.of : null, tone: r ? mlTone(r.rank, r.of) : "",
    roof: mlRoof(w), kickoff: g.kickoff, src: r ? r.src : null};
}

/* A lineup slot as the sheet prints it: RB1 and FLX2 lose their number, every flex spelling is FLX,
   and ESPN's D/ST is DST. (Moved here from surface/teams/board.js, 2026-10-07, so the model can read it.) */
function slotLabel(slot){
  const s = String(slot || "").replace(/\d+$/, "");
  return {FLEX: "FLX", "D/ST": "DST", DEF: "DST"}[s] || s;
}

/* Does the line need to say his position? A starter in his own slot already shows it in the slot column;
   a bench player and a flex starter do not. */
const mlSaysPos = p => !p.start || slotLabel(p.slot) !== p.pos;

