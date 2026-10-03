/* THE LEG SHEET'S NUMBERS (2026-09-27): every read the sheet (legsheet.js) and the TD board
   (tdboard.js) make, and nothing drawn. Three sources, each optional:

     the log     LIVE_MARKET.logs[slug]: the last 12 games' stats (`v`) and, since ff-jarvis sends
                 it, per-game usage (`u`: targets, carries, red-zone looks, the team's own totals).
                 The sheet keeps the last LS_N.
     the grid    LIVE_USAGE rows: this season's weeks, per player (data/usage.js).
     the defense LIVE_DEFENSE: points allowed by position, and starters out (design/defense.py).

   `u` wins where both say the same thing, because it covers the same ten games as the bars; the
   grid is the fallback for a log that has no `u` yet. A number neither source has is null, and
   the caller draws nothing for it. */
const LS_N = 10;

const lsMean = a => { const x = a.filter(v => typeof v === "number"); return x.length ? x.reduce((s, v) => s + v, 0) / x.length : null; };
const lsSum = a => a.reduce((s, v) => s + (typeof v === "number" ? v : 0), 0);

/* The last LS_N games of his log, every series cut the same way, or null. */
function legLog(p){
  const logs = LIVE_MARKET && LIVE_MARKET.logs;
  const log = logs ? logs[p.slug || slugOf(p.n)] : null;
  if (!log || !log.g || !log.g.length) return null;
  const k = Math.max(0, log.g.length - LS_N), cut = o => Object.fromEntries(Object.entries(o).map(([f, a]) => [f, (a || []).slice(k)]));
  return {g: log.g.slice(k), v: cut(log.v || {}), u: log.u ? cut(log.u) : null};
}

/* The bet the sheet is about: the side, the line, the book and its price, the model's chance.
   Underdog's own line when the reader is on Underdog and it has one; a touchdown is priced at
   DraftKings (Underdog sells none, udPick in lib/odds.js); DraftKings' over otherwise. */
function legSide(p){
  const u = PARLAY_BOOK === "underdog" ? udPick(p) : null;
  if (u && !u.synthetic){
    const b = p.books.Underdog;
    return {book: "underdog", pick: u.pick, line: u.line, where: "Underdog", pct: u.conf, price: u.pick === "lower" ? b.under : b.over};
  }
  // A line the model does not price (Longest reception): Underdog's own line, no chance, higher.
  const own = PARLAY_BOOK === "underdog" && !u ? ud(p) : null;
  if (own && typeof own.line === "number")
    return {book: "underdog", pick: "higher", line: own.line, where: "Underdog", pct: null, price: own.over};
  const dk = p.books && p.books.DraftKings;
  const price = p.mkt === "TD" && dk ? dk.over : overPrice(p);
  return {book: u ? "underdog" : "dk", pick: "higher", line: p.mkt === "TD" ? null : p.line, synthetic: !!u,
          where: p.mkt === "TD" && dk ? "DraftKings" : p.books ? p.book : "", pct: u ? u.conf : p.model, price};
}
const legBookPct = s => typeof s.price === "number" ? Math.round(amToProb(s.price) * 100) : null;

/* A game in the bars cleared the pick's side: under the line for a lower, over it for a higher,
   one score for a touchdown. */
const legHitGame = (p, s, v) => p.mkt === "TD" ? v >= 1 : s.line == null ? false : s.pick === "lower" ? v < s.line : v > s.line;

/* The defense he faces: the model's own `opp`, else the other side of "SEA @ CIN". */
function legOpp(p){
  if (p.opp) return p.opp;
  const teams = String(p.game || "").split(/\s+(?:@|vs\.?)\s+/);
  return teams.length === 2 && p.team ? teams.find(x => x !== p.team) || null : null;
}

/* This season's grid rows for him, oldest week first; none when the grid is the sample. */
function legWeeks(p){
  if (!USAGE_LIVE || !p.slug) return [];
  return USAGE.rows.filter(r => r.slug === p.slug).sort((a, b) => a.wk - b.wk);
}
const legGrid = (rows, k) => rows.map(r => r.v[k]);

/* His stat from the log in the same weeks the grid covers, for rates the grid cannot make
   alone (catch rate is catches over the grid's targets). */
function legJoin(p, log, rows, stat){
  if (!log) return [];
  return rows.map(r => {
    const k = log.g.findIndex(g => g[0] == USAGE.season && g[1] === r.wk);
    return k < 0 ? null : log.v[stat][k];
  });
}

/* Red-zone touches a game: targets plus carries inside the 20. From `u` over the ten games; the
   grid's RZ touches for a back, RZ targets for a receiver, otherwise. */
function legRzPerGame(p, log){
  if (log && log.u) return lsMean(log.u.rz_tgt.map((t, k) => t == null && log.u.rz_car[k] == null ? null : (t || 0) + (log.u.rz_car[k] || 0)));
  const rows = legWeeks(p);
  return lsMean(legGrid(rows, p.pos === "RB" ? "rz" : "rz_tgt"));
}

/* Of the team's red-zone touches in the ten games, his share. `u` only: the grid has no team total. */
function legRzShare(log){
  if (!log || !log.u) return null;
  const ks = log.u.team_rz.map((v, k) => typeof v === "number" ? k : -1).filter(k => k >= 0);
  const team = lsSum(ks.map(k => log.u.team_rz[k]));
  return team ? lsSum(ks.map(k => (log.u.rz_tgt[k] || 0) + (log.u.rz_car[k] || 0))) / team : null;
}

/* Targets, their share of the team's, and what he did with them. */
function legTargets(p, log){
  const rows = legWeeks(p);
  if (log && log.u && log.u.tgt.some(v => typeof v === "number")){
    const known = log.u.tgt.map((v, k) => typeof v === "number" ? k : -1).filter(k => k >= 0);
    const tgt = lsSum(known.map(k => log.u.tgt[k]));
    const both = known.filter(k => typeof log.u.team_tgt[k] === "number"), team = lsSum(both.map(k => log.u.team_tgt[k]));
    return {pg: tgt / known.length, share: team ? lsSum(both.map(k => log.u.tgt[k])) / team : null,
            recs: lsSum(known.map(k => log.v.RECS[k])), yds: lsSum(known.map(k => log.v.REC[k])), tgt};
  }
  if (!rows.length) return null;
  const tg = legGrid(rows, "tgt"), recs = legJoin(p, log, rows, "RECS"), yds = legJoin(p, log, rows, "REC");
  const paired = tg.map((v, k) => typeof v === "number" && typeof recs[k] === "number" ? k : -1).filter(k => k >= 0);
  const pairedTgt = lsSum(paired.map(k => tg[k]));
  const share = lsMean(legGrid(rows, "tgt_pct"));
  return {pg: lsMean(tg), share: share === null ? null : share / 100,
          recs: paired.length ? lsSum(paired.map(k => recs[k])) : null,
          yds: paired.length ? lsSum(paired.map(k => yds[k])) : null, tgt: paired.length ? pairedTgt : null};
}

/* aDOT over the season, weighted by targets: a 20-yard week on one target is not a deep role. */
function legAdot(p){
  const rows = legWeeks(p).filter(r => typeof r.v.adot === "number" && r.v.tgt);
  const t = lsSum(rows.map(r => r.v.tgt));
  return t ? lsSum(rows.map(r => r.v.adot * r.v.tgt)) / t : null;
}

/* The defense's line: points allowed to his position and its rank, starters out. */
function legDefense(p){
  const D = typeof LIVE_DEFENSE !== "undefined" ? LIVE_DEFENSE : null, opp = legOpp(p);
  if (!D || !opp) return null;
  const f = D.form[opp], cur = f && f.current && f.current[p.pos];
  return {form: cur || null, out: D.out[opp] || []};
}

const lsOrd = n => n + (n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th");
