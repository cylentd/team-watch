/* Trade value, as rows (2026-11-03; David: "you have to think of PAR"). Pure and DOM-free, so Node tests it
   (tests/test_js_tradevalue.py). The numbers are ff-jarvis's (LIVE_TRADE_VALUE via design/trade_value.py): each
   rostered player's points over replacement for the rest of the season, in his league's scoring, already in PAR order.
   This only picks a league, filters it by a chip (everyone, the reader's own team, or a position), caps the long list,
   and words the signed numbers. The page computes no points.

   PAR = (his points a game - the replacement level at his position) x his games left. Two players of equal PAR are a
   fair swap on paper; the trade finder (finder/finder.js) still scores a real package against both rosters. */
const TV_FILTERS = ["all", "mine", "QB", "RB", "WR", "TE"];
const TV_POS = ["QB", "RB", "WR", "TE"];
const TV_CAP = 40;          // rows the All list shows before "Show all": a screenful of starters, and the trade market
const TV_GAP_MIN = 2;       // points a game: a smaller gap between his manager's view and ours is not drawn

const tvBlock = () => {
  const b = typeof LIVE_TRADE_VALUE !== "undefined" && LIVE_TRADE_VALUE;
  return b && b.leagues && Object.keys(b.leagues).length ? b : null;
};
const tvLeague = (block, key) => (block && block.leagues[key]) || null;

/* The chips a league shows: Mine only when the reader's team holds someone in it. */
const tvFilters = (lg, me) => TV_FILTERS.filter(f => f !== "mine" || (!!me && lg.players.some(p => p.holder === me)));
/* A chip the league does not show is everyone. */
const tvFilter = (lg, me, want) => (tvFilters(lg, me).includes(want) ? want : "all");

/* The spans the block can show: the rest of season always, the fantasy playoff weeks when the file names them and
   prices someone over them (2026-11-03). */
const tvSpans = (block, lg) => (block && (block.po_weeks || []).length && lg.players.some(p => p.po_par != null) ? ["ros", "po"] : ["ros"]);

/* The league's players in a span's order, each with what the row draws: `show_par`, `show_games` and `show_rank` (his
   place at his position). The rest of season is the file's PAR order and rank. The playoffs are PAR over those weeks,
   best first, a tie to the name; a player with no playoff number is left out, and the rank is his place in that list. */
function tvOrdered(lg, span){
  if (span !== "po") return lg.players.map(p => ({...p, show_par: p.par, show_games: p.games, show_rank: p.pos_rank}));
  const rows = lg.players.filter(p => p.po_par != null).sort((a, b) => b.po_par - a.po_par || a.n.localeCompare(b.n));
  const at = {};
  return rows.map(p => ({...p, show_par: p.po_par, show_games: p.po_games, show_rank: (at[p.pos] = (at[p.pos] || 0) + 1)}));
}

/* The league's rows under a chip, in the span's order (the rest of season by default). */
function tvRows(lg, filter, me, span){
  const rows = tvOrdered(lg, span || "ros");
  if (filter === "mine") return rows.filter(p => p.holder === me);
  if (TV_POS.includes(filter)) return rows.filter(p => p.pos === filter);
  return rows;
}

/* The rows drawn: the All list stops at TV_CAP until the reader asks for the rest; a chip's list is short. */
const tvShown = (rows, filter, all) => (filter === "all" && !all ? rows.slice(0, TV_CAP) : rows);
const tvMore = (rows, filter, all) => (filter === "all" && !all ? Math.max(0, rows.length - TV_CAP) : 0);

/* One decimal, signed with a true minus: +12.4, −3.0, 0.0. */
function tvSigned(x){
  const r = Math.round(x * 10) / 10;
  return r > 0 ? `+${r.toFixed(1)}` : r < 0 ? `−${(-r).toFixed(1)}` : "0.0";
}

/* How much PAR the what-if adds (healthy games), or null without one. Rest of season only: the what-if counts his
   games to week 17, so the playoff span draws none. */
const tvHealthyAdd = (p, span) => (span === "po" || p.par_healthy == null ? null : Math.round((p.par_healthy - p.par) * 10) / 10);

/* The gap between his manager's view and ours, or null when it is under TV_GAP_MIN or there is none. Above 0 the
   league sees more than our rate; below, less. A number, never a verdict word: nothing tested it as a trading rule. */
const tvGap = p => (p.gap == null || Math.abs(p.gap) < TV_GAP_MIN ? null : Math.round(p.gap * 10) / 10);

/* The replacement levels in position order, for the caption: [[pos, points a game]]. */
const tvReplacement = lg => TV_POS.map(pos => [pos, lg.replacement[pos]]);
