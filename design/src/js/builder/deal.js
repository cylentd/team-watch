/* Deal me 3 (2026-09-25): three slips dealt from one kickoff's approved picks. Two are random --
   a 3-pick at 6x and a 5-pick at 20x -- and the third is the model's pick: the top-confidence
   picks that share no player with the kickoff's best slip, so a second bet spreads the risk
   instead of doubling it. Every qualifying receptions pick is graded at the same 57.3% (the side's
   2025 hit rate, slips.js HIT_RECS), so a random slip grades exactly as well as the best one: the
   deal costs nothing. A 2-pick at 3x is not dealt: it grades 32.8% against the 33.3% it needs.
   Underdog only; a kickoff needs 4+ games in its pool, since one game (Thursday, Monday) has
   exactly one slip, already the best slip under its heading. */
const DEAL_MIN_GAMES = 4;
const DEAL_TIERS = [["medium", 3], ["hard", 5]];
/* win key -> {medium, hard, model}: leg index lists, or null where the pool is too small. This
   tab only; a reload starts fresh. */
let DEALS = {};
/* The deal to animate after the next render: {k, model}. `model` is false on a redeal, since the
   model's pick stays where it is. */
let DEAL_FRESH = null;

/* Function declarations, not consts: the render test widens the pool on fixtures that have no
   approved pick (tests/test_parlay_grid.py). */
function dealPool(w){
  return PROPS.map((p, i) => [p, i]).filter(([p]) => legOKInBook(p, "mix", "underdog") && inWin(p, w)).map(([, i]) => i);
}
function dealOK(w){ return !w.wins && new Set(dealPool(w).map(i => PROPS[i].game)).size >= DEAL_MIN_GAMES; }

/* One pick per game and per player, like every gallery slip. */
function dealFill(order, n){
  const games = new Set(), players = new Set(), legs = [];
  order.forEach(i => {
    const p = PROPS[i];
    if (legs.length < n && !games.has(p.game) && !players.has(p.n)){ games.add(p.game); players.add(p.n); legs.push(i); }
  });
  return legs.length === n ? legs : null;
}
function dealShuffle(pool){
  const a = pool.slice();
  for (let k = a.length - 1; k > 0; k--){ const j = Math.floor(Math.random() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; }
  return a;
}
function dealModel(w){
  const best = bestCard(GALLERIES.underdog.filter(c => c.win === w));
  const taken = new Set(best ? best.legs.map(i => PROPS[i].n) : []);
  const metric = legMetric("underdog");
  return dealFill(dealPool(w).filter(i => !taken.has(PROPS[i].n)).sort((a, b) => metric(PROPS[b]) - metric(PROPS[a])), SLIP_LEGS);
}
function dealFor(w){
  const pool = dealPool(w), was = DEALS[w.k];
  DEALS[w.k] = Object.fromEntries(DEAL_TIERS.map(([tier, n]) => [tier, dealFill(dealShuffle(pool), n)]));
  DEALS[w.k].model = was ? was.model : dealModel(w);
  DEAL_FRESH = {k: w.k, model: !was};
}
