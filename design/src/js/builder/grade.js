/* What an Underdog slip is worth (2026-09-25): its graded chance to hit, against the payout the
   app quotes for it. The model's receptions confidence runs ~8 points high, so every number here
   comes from grading it against 2025's closing lines (ff-jarvis METHODOLOGY 12.51, 12.32), and
   the payout is whatever the reader types, since Underdog changes it slip by slip. */

/* A leg's graded chance. A receptions pick counts at its side's graded rate (12.51: lower stated
   65.4, hit 56.3; lower at 65%+ hit 57.3; higher stated 61.9, hit 42.3), never above its own
   confidence; a touchdown at its P(score), which grading found honest. */
const GRADED = {lowerAtFloor: 57.3, lower: 56.3, higher: 42.3};
function legHit(p){
  const u = udPick(p);
  if (p.mkt === "TD" || u.synthetic) return u.conf;
  const g = u.pick === "higher" ? GRADED.higher : u.conf >= HIT_RECS ? GRADED.lowerAtFloor : GRADED.lower;
  return Math.min(u.conf, g);
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
const isLower = p => { const u = udPick(p); return !!u && !u.synthetic && u.pick === "lower"; };
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
function udChance(legs){
  const st = stackIn(legs);
  return legs.filter(l => !st || !st.includes(l)).reduce((a, l) => a * legHit(l) / 100, st ? STACK_HIT / 100 : 1);
}
/* What the slip pays: the app's number when the reader typed one for this exact slip, else the
   standard board, and nothing for a stack, whose discount only the app knows. */
let BETS_PAY = null;   // {sig, x}
const slipSig = () => SLIP.join(",");
function betsPayout(legs){
  if (BETS_PAY && BETS_PAY.sig === slipSig()) return BETS_PAY.x;
  return stackIn(legs) ? null : udPayout(legs.length);
}

/* The gallery's stack cards: per kickoff window, each team whose QB and top two receivers are all
   called lower by the model and pass the leg gates, plus the best other-game leg, since an entry
   needs two teams. */
function stackCards(win){
  const ok = p => upcoming(p) && playing(p) && (p.games||0) >= 8 && isLower(p) && inWin(p, win);
  const out = [];
  PROPS.filter(p => p.mkt === "PASS" && ok(p)).forEach(qb => {
    const s = stackOf(qb);
    if (!s || !s.every(ok)) return;
    const other = PROPS.map((p, i) => [p, i]).filter(([p]) => p.game !== qb.game && legOKInBook(p, "mix", "underdog") && inWin(p, win))
      .sort((a, b) => legHit(b[0]) - legHit(a[0]))[0];
    if (other) out.push([...s.map(l => PROPS.indexOf(l)), other[1]]);
  });
  return out;
}
