/* Kickoff windows: build.py splits each time-of-day bucket by calendar date so a window never
   mixes two different days (the old "evening" spanned Thursday/Sunday/Monday night at once).
   Ordered chronologically; empty on the sample data (PROPS_SAMPLE carries no `win` field). */
const WINDOWS = (LIVE_MARKET && LIVE_MARKET.windows) || [];
/* Whole-day groupings (a Sunday's morning + afternoon + night), same date by construction. */
const DAYS = (LIVE_MARKET && LIVE_MARKET.days) || [];
const winGames = k => new Set(PROPS.filter(p => !k || p.win === k).map(p => p.game)).size;
/* The page is a static build that can be days old when it is opened, so "has this game started"
   is asked of the viewer's clock, once at load. A started game is no longer a bet. */
const NOW = Date.now();
const upcoming = p => !p.commence || Date.parse(p.commence.replace(" ", "T") + "Z") > NOW;
const inWin = (p, w) => !w || (w.wins ? w.wins.includes(p.win) : p.win === w.k);
/* The gallery's kickoff choices: every day, then every window, that still has a game to come. */
const GAL_WINDOWS = [...DAYS, ...WINDOWS].filter(w => PROPS.some(p => inWin(p, w) && upcoming(p)));

/* Gallery presets. "Best" is the largest positive edges the model will stand behind: a rate
   resting on at least 8 of his own games, a model chance between 25% and 85% so a thin sample
   or a novelty price cannot top the list, one leg per player. One card per kickoff window
   (never mixed dates) crossed with a scope -- yards (rush/rec/receptions/pass), TDs, or mix
   (both, each leg still gated by its own market's band). "Mine" is three of my players in
   three games, no model involved. Any tap on a leg turns the slip custom. */
const SLIP_LEGS = 3;
/* Sportsbook legs: a DraftKings price between -300 and +200 (edge in points rewards a +750 long
   shot far more than it deserves), a model chance of 35-85%, a rate on 8+ games, positive edge. */
/* A slip leg has to be on the field, in a starter's role, and priced at a line that agrees with
   the role the model knows about; a backup, a questionable, or a line the book has moved far
   from last season's rate is news, not edge. */
const playing = p => p.flag !== "out" && p.flag !== "q" && p.flag !== "backup" && !p.stale && !p.moved;
/* Scope, parameterized so the gallery can evaluate all three independently of any UI toggle.
   Touchdown legs are priced longer and land less often, so the floor is 30% and the price
   window runs to +600; mix needs no new band since each leg is still gated by its own market. */
const scopeOK = (p, s) => s === "tds" ? p.mkt === "TD" : s === "mix" ? true : p.mkt !== "TD";
/* Underdog is pick'em: higher or lower at their line, paid by a fixed multiplier. UD_MIN is the
   line list's "weak" shading, not the gallery gate (HIT_RECS / HIT_TD below). Underdog sells no
   anytime-TD line, so udPick() derives one from the model's raw P(score), tagged MODEL. */
const UD_MIN = 58;
/* The Underdog gallery ranks for the chance a slip hits, and only uses the two kinds of leg that
   held up against 2025's closing lines (ff-jarvis METHODOLOGY 12.31, 12.34, 12.51): anytime TDs
   where the model's P(score) is 50%+ (honest in every week bucket: stated ~54, scored 48-71), and
   receptions at a 2.5+ Underdog line -- but only the LOWER side, at 65%+.

   The side is the split that matters, not the calendar (12.51, graded 2026-09-19 on all 18 weeks
   of 2025 under this exact filter): lower picks hit 56.3% (n 567), higher picks 42.3% (n 71), and
   lower at 65%+ hits 57.3% (n 281, CI 51-63) against a 57.7% break-even on a 2-leg 3x board and
   55.0% on a 3-leg 6x. The old rule gated on week 5 instead, which let the losing side through
   from week 5 on and blocked the winning side before it. In-sample: the split was found in the
   same 2025 data, and no other season's closing lines are on disk to check it against. */
const HIT_RECS = 65, HIT_TD = 50;
/* A leg's graded chance, the payout board and stacks live in builder/grade.js. */
const legOKInBook = (p, s, book) => {
  if (!upcoming(p)) return false;
  if (book !== "underdog")
    return typeof p.edge === "number" && p.edge > 0 && (p.games||0) >= 8 && playing(p)
      && scopeOK(p, s) && p.book === "DraftKings"
      && (p.mkt === "TD" ? (p.model >= 30 && overPrice(p) >= -300 && overPrice(p) <= 600)
                         : (p.model >= 35 && p.model <= 85 && overPrice(p) >= -300 && overPrice(p) <= 200));
  const u = udPick(p);
  // A receptions pick has to be at Underdog's own line (!synthetic), at 2.5+ (a 1.5-catch line is
  // priced as a heavy favourite), on the lower side, and at the HIT_RECS floor; a touchdown pick
  // is always synthetic and needs its P(score) at HIT_TD.
  return u && (p.mkt === "TD" ? u.conf >= HIT_TD
    : p.mkt === "RECS" && !u.synthetic && u.pick === "lower" && u.conf >= HIT_RECS && u.line >= 2.5)
    && (p.games||0) >= 8 && playing(p) && !u.stale && scopeOK(p, s);
};
/* The non-TD scope is "yards" inside (scopeOK), but on Underdog it only ever holds receptions. */
/* Underdog adds Long (4-5 picks, 2026-09-25: a long slip is worth it when every leg is, and the
   payout grows faster than the chance falls) and Stacks (a QB with his receivers, grade.js). */
const galleryScopes = book => [["all",t("parlay.scope.all")],
  ["yards", book === "underdog" ? t("parlay.scope.recs") : t("parlay.scope.yards")],
  ["tds",t("parlay.scope.tds")],["mix",t("parlay.scope.mix")],
  ...(book === "underdog" ? [["long",t("parlay.scope.long")],["stack",t("parlay.scope.stack")]] : [])];
const LONG_LEGS = 5;
/* Underdog legs rank by graded chance, the model's confidence breaking ties. */
const legMetric = (book) => book === "underdog" ? (p => legHit(p) + udPick(p).conf / 1000) : (p => p.edge);
function pickLegs(cands, key, allowSameGame, n = SLIP_LEGS){
  const seenG = new Set(), seenP = new Set(), out = [];
  cands.sort((a,b) => key(b[0]) - key(a[0])).forEach(([p,i]) => {
    if (out.length < n && (allowSameGame || !seenG.has(p.game)) && !seenP.has(p.n)){
      seenG.add(p.game); seenP.add(p.n); out.push(i);
    }
  });
  return out;
}
/* The fallback when no slip at a kickoff clears the gates above: the best of what is on the
   board, so every window and scope still shows a card. The gates that say "this number is wrong"
   stay (started, out, backup, stale or moved line, no model number, a synthetic Underdog yards
   line); the gates that say "this number is too low" go (edge, chance floors, price bands, the
   8-game floor, the Underdog side and confidence floors). The card is tagged so it never reads
   as a pick. */
const legLowInBook = (p, s, book) => {
  if (!upcoming(p) || !playing(p) || !scopeOK(p, s) || typeof p.model !== "number") return false;
  if (book !== "underdog") return p.book === "DraftKings" && overPrice(p) !== null && typeof p.edge === "number";
  const u = udPick(p);
  // Non-TD stays receptions-only: the Underdog scope chip is labelled receptions.
  return !!u && !u.stale && (p.mkt === "TD" || (p.mkt === "RECS" && !u.synthetic));
};
function slipFrom(ok, scope, win, book){
  // A long card draws from the mix pool, five picks, one per game, never a same-game fallback.
  const long = scope === "long";
  const cands = PROPS.map((p,i)=>[p,i]).filter(([p]) => ok(p, long ? "mix" : scope, book) && inWin(p, win));
  const games = new Set(cands.map(([p]) => p.game)).size;
  // A single-game window (a Thu/Sun/Mon night with one game on the slate) can never fill three
  // legs under the one-leg-per-game rule -- allow it there; the `.corr` warning already tells
  // the reader it is a same-game parlay and to price it as one.
  return pickLegs(cands, legMetric(book), !long && games > 0 && games < SLIP_LEGS, long ? LONG_LEGS : SLIP_LEGS);
}
const bestSlipIn = (scope, win, book) => slipFrom(legOKInBook, scope, win, book);
function mineSlip(book){
  if (!LIVE_MARKET) return [1,2,5];
  const seen = new Set(), out = [];
  const ok = book === "underdog" ? p => !!udPick(p) : p => p.mkt !== "TD";
  PROPS.forEach((p,i) => { if (p.mine && ok(p) && !seen.has(p.game) && out.length < SLIP_LEGS){ seen.add(p.game); out.push(i); } });
  return out;
}
const PRESETS = [["mine",t("parlay.preset.mine")],["blank",t("parlay.preset.blank")]];
function presetSlip(k, book){
  if (k === "mine") return mineSlip(book);
  return [];
}
/* The cart starts empty -- the gallery below answers "what does the model like", the cart is
   the user's own, built one leg at a time, cart-style. */
let SLIP_MODE = "blank";
let SLIP = [];
/* DraftKings (over/price) or Underdog (higher/lower + confidence) -- a page-level toggle, same
   pattern as DFS_SITE, because the two books need different rows, a different gallery, and a
   different cart payout entirely, not just a different price column. */
let PARLAY_BOOK = "underdog";

/* One card per window x scope with at least two legs, deduped (mix often reproduces yards or
   tds exactly). Days are built first, so a window card that repeats a whole-day card's legs is
   the one dropped; display order is by kickoff (below). No whole-slate card -- that would reintroduce the
   cross-date bug this fixes.
   Computed once per book: PROPS never mutates, and toggling the cart must not re-roll the
   gallery. Both books' galleries are built up front so switching PARLAY_BOOK is instant. */
function buildGallery(book){
  const scopes = galleryScopes(book).filter(([k]) => k !== "all");
  const metric = legMetric(book);
  const out = [], seen = new Set();
  /* A near copy is a copy (2026-09-25): Sunday morning's 3 receptions slip reused 2 of the whole
     day's 3, and its 5-pick long card 4 of 5. A slip of 3 or more that shares all but one leg with
     a kept slip of its own kind is dropped (a 3-pick inside a 5-pick is a different bet: 6x, not
     20x); days are built first, so the whole-day card stays. */
  const nearCopy = (s, legs) => legs.length >= 3 && out.some(c =>
    c.scope === s && legs.filter(i => c.legs.includes(i)).length >= legs.length - 1);
  const add = (s, label, w, legs, low) => {
    const sig = legs.slice().sort((a,b)=>a-b).join(",");
    if (seen.has(sig) || (s !== "stack" && nearCopy(s, legs))) return;
    seen.add(sig);
    // The star goes to the best return, not the safest slip: on Underdog the graded chance times
    // the payout (David, 2026-09-25: the point is the edge, not the hit rate). A stack's payout is
    // unknown until the app quotes it, so a stack is never the star.
    const ps = legs.map(i => PROPS[i]), x = s === "stack" ? null : udPayout(ps.length);
    out.push({book, scope: s, scopeLabel: label, win: w, legs, low,
               metric: book !== "underdog" ? ps.reduce((a,p)=>a+metric(p), 0) / ps.length
                 : x ? udChance(ps) * x : -1});
  };
  for (const w of GAL_WINDOWS) for (const [s, label] of scopes){
    // One card per stack: the whole day is built first, so a window repeating its QB is dropped.
    if (s === "stack"){
      stackCards(w).filter(legs => !seen.has(`qb:${legs[0]}`))
        .forEach(legs => { seen.add(`qb:${legs[0]}`); add(s, label, w, legs, false); });
      continue;
    }
    let legs = bestSlipIn(s, w, book), low = false;
    if (s === "long"){ if (legs.length >= 4) add(s, label, w, legs, false); continue; }
    if (legs.length < 2){ legs = slipFrom(legLowInBook, s, w, book); low = true; }
    if (legs.length < 2) continue;
    add(s, label, w, legs, low);
  }
  // The next game first (David, 2026-09-16: "the upcoming game slip should be first"): by the
  // earliest kickoff among a card's legs, a single-window card ahead of the whole day it sits in,
  // then build order. `i` is assigned after, because data-loadslip indexes this sorted array.
  const kick = c => Math.min(...c.legs.map(i => PROPS[i].commence ? Date.parse(PROPS[i].commence.replace(" ", "T") + "Z") : Infinity));
  return out.map((c, n) => ({c, n, k: kick(c)}))
    .sort((a, b) => a.k - b.k || (a.c.win.wins ? 1 : 0) - (b.c.win.wins ? 1 : 0) || a.n - b.n)
    .map(({c}, i) => ({...c, i}));
}
const GALLERIES = {dk: buildGallery("dk"), underdog: buildGallery("underdog")};
/* A below-the-bar card is never the star. */
const bestCard = cards => cards.reduce((a,c) => !c.low && (!a || c.metric > a.metric) ? c : a, null);
const GALLERY_BEST = {dk: bestCard(GALLERIES.dk), underdog: bestCard(GALLERIES.underdog)};
/* The gallery's own filter -- not fed into legOKInBook/bestSlipIn, which already ran once above. */
let SLIP_SCOPE = "all";
/* The one kickoff filter for both Bets views (2026-09-25): Slips filters its cards by it, Build its
   lines. Two selects used to set two variables, so a reader who picked Sunday for the slips saw
   Thursday's lines under them. */
let GAL_WIN = "ALL";
let BETS_PANEL = false;   // the settings panel under the bar is open
let BETS_SHEET = false;   // the slip sheet is up

