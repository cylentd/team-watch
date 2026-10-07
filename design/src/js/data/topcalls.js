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

/* The model's strongest lines in games that have not kicked off, strongest first: tier, then the chance of
   its side. One line per player (his strongest). Each is {i, slug, n, pos, team, game, kick, mkt, line, side,
   tier, pct}: `pct` the chance of the model's side. No edge over the book's price since 2026-10-06 (METHODOLOGY
   12.31: the model's +EV overs lost at the close, ROI -17.9% in weeks 1-4), so the price neither prints nor
   picks the list. Nothing for a touchdown (no side), Longest reception, an Out player, a line the book moved
   far from the model, or a line with no pick. opts: {now (ms), book ("underdog"|"dk"), limit}. */
function topCalls(props, opts){
  const {now, book, limit} = opts, best = new Map();
  props.forEach((p, i) => {
    if (p.mkt === "TD" || p.mkt === "LONG" || p.flag === "out" || lineMoved(p, book) || kickPast(p.commence, now)) return;
    const s = ptSrc(p, book);
    if (!PT_RANK[s.tier] || typeof s.model !== "number") return;
    const side = s.side === "lower" ? "lower" : "higher", pct = Math.round(Math.max(s.model, 100 - s.model));
    const row = {i, slug: p.slug || p.n, n: p.n, pos: p.pos, team: p.team, game: p.game, kick: p.kick, mkt: p.mkt,
      line: s.line, side, tier: s.tier, pct};
    const had = best.get(row.slug);
    if (!had || ptOrder(row, had) < 0) best.set(row.slug, row);
  });
  const out = [...best.values()].sort(ptOrder);
  return limit ? out.slice(0, limit) : out;
}

const ptOrder = (a, b) => PT_RANK[b.tier] - PT_RANK[a.tier] || b.pct - a.pct || a.n.localeCompare(b.n);

/* The game two legs of a slip share, or null. `rest` is the game of every leg outside a whole stack and
   `stack` the stack's game (or null): a stack's three legs are one unit because ff-jarvis measured their
   joint chance (12.32, 23.1%); two legs of one game outside a stack have no measured joint, so the slip
   shows no combined chance and says why (slips.joint.note). */
function slipSameGame(rest, stack){
  const units = stack ? [...rest, stack] : rest;
  return units.find((g, k) => units.indexOf(g) !== k) ?? null;
}
