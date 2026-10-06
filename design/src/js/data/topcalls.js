/* TOP CALLS AND THE SLIP'S GAMES (2026-10-05, plan "Bets UX" changes 1 and 5). Pure functions from rows to
   rows; surface/parlay/topcalls.js only draws them, and builder/board.js, lineitem.js and the tray read the
   one tier vocabulary and the one same-game test from here.

   The tier words are ff-jarvis's (model/market/prop_tiers.py, METHODOLOGY 12.82): the page never cuts a tier
   from a chance, it only orders by the one that was sent. */
const PT_TIERS = ["none", "slight", "confident", "very"];
const PT_RANK = {slight: 1, confident: 2, very: 3};

/* The row, or Underdog's own entry when the reader is on Underdog and it posts a line: the line shown is
   the one a tier belongs to (the same choice lineitem.js slSrc makes). */
const ptSrc = (p, book) => book === "underdog" && ud(p) && typeof ud(p).line === "number" ? ud(p) : p;

/* The price the model's side would be bet at, in the source's own book: Underdog's entry carries its prices,
   a DraftKings row its primary book's. */
function ptPrice(p, s, side){
  const e = s === p ? (p.books && p.books[p.book]) || null : s;
  const v = e ? (side === "lower" ? e.under : e.over) : null;
  return typeof v === "number" ? v : null;
}

/* The model's strongest lines in games that have not kicked off, strongest first: tier, then the chance of
   its side, then the edge. One line per player (his strongest). Each is {i, slug, n, pos, team, game, kick,
   mkt, line, side, tier, pct, be, edge}: `pct` the chance of the model's side, `be` the book's break-even at
   that side's price (null when the book sent none), `edge` their difference, both whole numbers so the reader
   can subtract what is printed. Nothing for a touchdown (no side), Longest reception, an Out player, a line
   the book moved far from the model, a line with no pick, or a call priced worse than its break-even (edge
   under 0; a call with no price sent stays, with no edge). opts: {now (ms), book ("underdog"|"dk"), limit}. */
function topCalls(props, opts){
  const {now, book, limit} = opts, best = new Map();
  props.forEach((p, i) => {
    if (p.mkt === "TD" || p.mkt === "LONG" || p.flag === "out" || lineMoved(p, book) || kickPast(p.commence, now)) return;
    const s = ptSrc(p, book);
    if (!PT_RANK[s.tier] || typeof s.model !== "number") return;
    const side = s.side === "lower" ? "lower" : "higher", pct = Math.round(Math.max(s.model, 100 - s.model));
    const price = ptPrice(p, s, side), be = price === null ? null : Math.round(amToProb(price) * 100);
    const row = {i, slug: p.slug || p.n, n: p.n, pos: p.pos, team: p.team, game: p.game, kick: p.kick, mkt: p.mkt,
      line: s.line, side, tier: s.tier, pct, be, edge: be === null ? null : pct - be};
    if (row.edge !== null && row.edge < 0) return;   // priced worse than its break-even: no edge to lead with
    const had = best.get(row.slug);
    if (!had || ptOrder(row, had) < 0) best.set(row.slug, row);
  });
  const out = [...best.values()].sort(ptOrder);
  return limit ? out.slice(0, limit) : out;
}

const ptOrder = (a, b) => PT_RANK[b.tier] - PT_RANK[a.tier] || b.pct - a.pct
  || (b.edge === null ? -Infinity : b.edge) - (a.edge === null ? -Infinity : a.edge) || a.n.localeCompare(b.n);

/* The game two legs of a slip share, or null. `rest` is the game of every leg outside a whole stack and
   `stack` the stack's game (or null): a stack's three legs are one unit because ff-jarvis measured their
   joint chance (12.32, 23.1%); two legs of one game outside a stack have no measured joint, so the slip
   shows no combined chance and says why (slips.joint.note). */
function slipSameGame(rest, stack){
  const units = stack ? [...rest, stack] : rest;
  return units.find((g, k) => units.indexOf(g) !== k) ?? null;
}
