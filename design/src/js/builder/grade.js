/* What an Underdog slip is worth (2026-09-25): its graded chance to hit, against the payout the
   app quotes for it. The model's receptions confidence runs ~8 points high, so every number here
   comes from grading it against 2025's closing lines (ff-jarvis METHODOLOGY 12.51, 12.32), and
   the payout is whatever the reader types, since Underdog changes it slip by slip. */

/* A leg's graded chance. A receptions pick counts at its side's graded rate (12.51: lower stated
   65.4, hit 56.3; lower at 65%+ hit 57.3; higher stated 61.9, hit 42.3), never above its own
   confidence; a touchdown at its P(score), which grading found honest. The side is the one on the
   slip (slipSide, 2026-10-03): against the model's call the chance is what the model leaves for it.
   A market the model does not price (Longest reception) has no chance: null. */
const GRADED = {lowerAtFloor: 57.3, lower: 56.3, higher: 42.3};
function legHit(p){
  const u = udPick(p);
  if (!u) return null;
  if (p.mkt === "TD" || u.synthetic) return u.conf;
  const side = slipSideOf(p), conf = side === u.pick ? u.conf : 100 - u.conf;
  const g = side === "higher" ? GRADED.higher : u.conf >= HIT_RECS && side === u.pick ? GRADED.lowerAtFloor : GRADED.lower;
  return Math.min(conf, g);
}

/* Underdog's standard board. 3x, 6x and 10x were seen in the app; 20x for five is the published
   board and unverified. A discounted favourite or a same-team pick pays less, which is why the
   sheet takes the app's own number. */
const UD_BOARD = {2: 3, 3: 6, 4: 10, 5: 20};
const udPayout = n => UD_BOARD[n] || null;

/* A same-team stack: his QB's passing yards and the team's two biggest receiving-yards lines, all
   lower. A bad passing day sinks all three at once, so together they hit 23.1% (12.32, n 481, CI
   19.5-27.0) where three independent legs would hit 13.3%. Underdog pays less for it (8.18x for a
   4-pick on 2026-09-14), so a stack never gets the standard board. */
const STACK_HIT = 23.1;
const isLower = p => { const u = udPick(p); return !!u && !u.synthetic && slipSideOf(p) === "lower"; };
function stackOf(qb){
  const recs = PROPS.filter(p => p.mkt === "REC" && p.team === qb.team && p.game === qb.game && ud(p))
    .sort((a, b) => ud(b).line - ud(a).line).slice(0, 2);
  return recs.length === 2 ? [qb, ...recs] : null;
}
/* The stack inside a slip, if it holds one whole, every leg on the lower side. */
function stackIn(legs){
  for (const qb of legs.filter(l => l.mkt === "PASS" && isLower(l))){
    const s = stackOf(qb);
    if (s && s.every(l => legs.includes(l) && isLower(l))) return s;
  }
  return null;
}
/* Null when any leg has no chance (an unpriced market). */
function udChance(legs){
  const st = stackIn(legs), rest = legs.filter(l => !st || !st.includes(l));
  if (rest.some(l => legHit(l) === null)) return null;
  return rest.reduce((a, l) => a * legHit(l) / 100, st ? STACK_HIT / 100 : 1);
}
/* What the slip pays: the app's number when the reader typed one for this exact slip, else the
   standard board, and nothing for a stack, whose discount only the app knows. */
let BETS_PAY = null;   // {sig, x}
const slipSig = () => SLIP.map(i => `${i}${slipSide(i)}`).join(",");
function betsPayout(legs){
  if (BETS_PAY && BETS_PAY.sig === slipSig()) return BETS_PAY.x;
  return stackIn(legs) ? null : udPayout(legs.length);
}
