/* THE SLIPS BOARD'S READS (2026-10-03, storyboard "Slips research board", picked A + B). David
   researches here and enters his slips on Underdog, so the board answers "who is getting the work"
   rather than dealing slips: per kickoff, a card per game, its players by work rising. Nothing here
   draws (surface/parlay/board.js does); every read is pure over PROPS, LIVE_REASONS and the logs.

   Shown: every player with a line still to play who is not out and whose line the book has not
   moved far from the model (lineMoved). A WR3 or a backup stays: those were David's wins. */
const REASONS = (typeof LIVE_REASONS !== "undefined" && LIVE_REASONS) || {};
let SL_CHIP = {};      // the chip pressed in each game card, keyed by game; "rise" until changed
let SL_FOCUS = null;   // a game to bring into view after the next render (Preview's hand-off)

/* The kickoff the board shows: the chosen one, or the first window still to come. */
function slWin(){
  return GAL_WINDOWS.find(w => w.k === GAL_WIN) || GAL_WINDOWS.find(w => !w.wins) || null;
}

const slSlug = p => p.slug || slugOf(p.n);
/* Longest reception ships as history only (plan update 2026-10-03: no source sells its line), so a
   LONG row, should one arrive, is not a line on the board; the sheet shows his longest catches. */
const slVisible = p => p.mkt !== "LONG" && upcoming(p) && p.flag !== "out" && !lineMoved(p, PARLAY_BOOK);
/* "SEA @ SF" -> ["SEA", "SF"]; the sample's "DET vs GB" too. */
const slTeams = game => String(game || "").split(/\s+(?:@|vs\.?)\s+/);

/* A player's markets in the order a slip is read: the score, then catches, yards. */
const SL_MKT_ORDER = ["TD", "RECS", "REC", "RUSH", "PASS"];
const slMktRank = m => { const k = SL_MKT_ORDER.indexOf(m); return k < 0 ? SL_MKT_ORDER.length : k; };

/* Every line he has on the board, in that order. */
function slPlayerRows(slug){
  return PROPS.map((p, i) => [p, i]).filter(([p]) => slSlug(p) === slug && slVisible(p))
    .sort((a, b) => slMktRank(a[0].mkt) - slMktRank(b[0].mkt)).map(([, i]) => i);
}

/* His work in his last three games: ff-jarvis's reason when it sent one (targets for a receiver,
   carries for a back, snaps otherwise), else the same cut of the log's per-game usage. */
function slWork(p){
  const r = REASONS[slSlug(p)], w = r && r.work;
  const nums = a => (a || []).filter(v => typeof v === "number");
  if (w && nums(w.last).length){
    const last = nums(w.last);
    return {key: w.key, last, trend: typeof w.trend === "number" ? w.trend : last[last.length - 1] - last[0]};
  }
  const log = LIVE_MARKET && LIVE_MARKET.logs && LIVE_MARKET.logs[slSlug(p)];
  const key = p.pos === "WR" || p.pos === "TE" ? "tgt" : p.pos === "RB" ? "car" : "snap";
  const last = log && log.u ? nums(log.u[key]).slice(-3) : [];
  return last.length ? {key, last, trend: last[last.length - 1] - last[0]} : null;
}

/* His snap share in his latest game, from the log's usage; null without it. */
function slSnapNow(p){
  const log = LIVE_MARKET && LIVE_MARKET.logs && LIVE_MARKET.logs[slSlug(p)];
  const s = log && log.u && (log.u.snap || []).filter(v => typeof v === "number");
  return s && s.length ? Math.round(s[s.length - 1]) : null;
}

function slPlayer(slug, rows){
  const p = PROPS[rows[0]], r = REASONS[slug] || null;
  return {slug, p, reason: !!r, rows: slPlayerRows(slug), tags: (r && r.tags) || [], vacated: (r && r.vacated) || [], work: slWork(p)};
}

/* His most confident line, or null: among his lines the model gave a pick (tier not "none", never a
   touchdown), the highest chance of its side, ties to the higher tier. {i, side, tier, mkt}. */
const SL_TIER_RANK = {slight: 1, confident: 2, very: 3};
function slBestLine(x){
  let best = null;
  x.rows.forEach(i => {
    const p = PROPS[i], m = p.mkt === "TD" ? null : slModel(p);
    if (!m || !m.tier || m.tier === "none") return;
    if (!best || m.q > best.q || (m.q === best.q && SL_TIER_RANK[m.tier] > SL_TIER_RANK[best.tier])) best = {i, side: m.side, tier: m.tier, q: m.q, mkt: p.mkt};
  });
  return best;
}

/* Eight softest and eight toughest defences against his position, from LIVE_DEFENSE (rank 1 allows the
   fewest points, so seasonDefRank counts from the easy end): "easy", "tough" or "". */
const SL_DEF_EDGE = 8;
function slMatchup(p){
  const opp = legOpp(p), d = opp ? seasonDefRank(opp, p.pos) : null;
  return !d ? "" : d[0] <= SL_DEF_EDGE ? "easy" : d[0] > d[1] - SL_DEF_EDGE ? "tough" : "";
}
/* One step of work, per kind: two targets, two carries, ten snap points. A bigger move than that is
   a rise; snaps wobble too much to call a rise without ff-jarvis's tag. */
const SL_UNIT = {tgt: 2, car: 2, snap: 10};
const slLatest = x => x.work ? x.work.last[x.work.last.length - 1] : -1;
const slSteps = (x, n) => x.work ? n / SL_UNIT[x.work.key] : -99;
const slRising = x => !!x.work && (x.reason ? x.tags.includes("work_up")
  : x.work.key !== "snap" && x.work.trend >= SL_UNIT[x.work.key]);
/* Rising work first, the biggest rise on top (in steps, so targets and snaps compare); then the most work. */
const slOrder = (a, b) => slRising(b) - slRising(a) || slSteps(b, (b.work || {}).trend) - slSteps(a, (a.work || {}).trend)
  || slSteps(b, slLatest(b)) - slSteps(a, slLatest(a)) || a.p.n.localeCompare(b.p.n);

/* The kickoff's games in kickoff order, each with its players in board order. */
function slGames(w){
  const by = new Map();
  PROPS.forEach((p, i) => {
    if (!inWin(p, w) || !slVisible(p)) return;
    const g = by.get(p.game) || by.set(p.game, {game: p.game, kick: p.kick, at: p.commence || "", players: new Map()}).get(p.game);
    const s = slSlug(p);
    (g.players.get(s) || g.players.set(s, []).get(s)).push(i);
  });
  return [...by.values()].sort((a, b) => a.at.localeCompare(b.at) || a.game.localeCompare(b.game))
    .map(g => ({...g, players: [...g.players.entries()].map(([s, rows]) => slPlayer(s, rows)).sort(slOrder)}));
}

/* The four chips inside a game card: Work rising (the default), TE, Role guys (a WR2 or deeper, a
   backup back), and All N. A game where nobody's work rose opens on All, never on an empty card. */
const SL_CHIPS = ["rise", "te", "role", "all"];
const slChip = g => SL_CHIP[g.game] || (g.players.some(slRising) ? "rise" : "all");
function slChipPlayers(g, k){
  if (k === "te") return g.players.filter(x => x.p.pos === "TE");
  if (k === "role") return g.players.filter(x => (x.p.depth || 1) >= 2 || x.p.flag === "backup");
  if (k === "rise") return g.players.filter(slRising);
  return g.players;
}

/* Preview's game for these two clubs, or null. */
function slPreviewGame(teams){
  const want = new Set(teams.map(schedCode));
  return pvGames().find(g => want.has(schedCode(g.away)) && want.has(schedCode(g.home))) || null;
}

/* The game's numbers: each side's implied points, and the spread and total. LIVE_LINES first (the
   DFS lobby, a team's own spread below 0 when it gives points), Preview's line second. */
function slGameLine(teams, pv){
  const L = typeof LIVE_LINES !== "undefined" ? LIVE_LINES : null;
  const rows = teams.map(c => schedTeamRow(L, c));
  if (rows.every(r => r && typeof r.implied === "number")){
    const s = rows[0].spread;
    return {imp: rows.map(r => r.implied), fav: s < 0 ? teams[0] : s > 0 ? teams[1] : null, by: Math.abs(s || 0), total: rows[0].total};
  }
  const l = pv && pv.line;
  if (!l) return null;
  const imp = l.implied ? teams.map(c => l.implied[schedCode(c)] ?? l.implied[c]) : null;
  return {imp: imp && imp.every(v => typeof v === "number") ? imp : null, fav: l.fav, by: l.by, total: l.total};
}
