/* Kickoff windows: build.py splits each time-of-day bucket by calendar date so a window never
   mixes two different days (the old "evening" spanned Thursday/Sunday/Monday night at once).
   Ordered chronologically; empty on the sample data (PROPS_SAMPLE carries no `win` field). */
const WINDOWS = (LIVE_MARKET && LIVE_MARKET.windows) || [];
const winGames = k => new Set(PROPS.filter(p => !k || p.win === k).map(p => p.game)).size;

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
/* Underdog is pick'em: higher or lower at their line, paid by a fixed multiplier, so a
   yards/receptions pick needs the model above 58% (a 3-pick entry needs each leg near 55% to
   break even at 6x) to clear the "confidence for free" floor. A touchdown pick skips that floor
   on purpose -- Underdog sells no anytime-TD line, so udPick() derives one from the model's raw
   P(score) (tagged MODEL) and a real slate mostly runs under 50%: TDs are long shots by nature,
   and a gallery card that only ever showed the rare 58%+ read would misrepresent what "the
   model's best TD card" actually looks like. Ranked by confidence either way, so a card still
   leads with its strongest read; a low number here is the risk, not a mistake. */
const UD_MIN = 58;
const legOKInBook = (p, s, book) => {
  if (book !== "underdog")
    return typeof p.edge === "number" && p.edge > 0 && (p.games||0) >= 8 && playing(p)
      && scopeOK(p, s) && p.book === "DraftKings"
      && (p.mkt === "TD" ? (p.model >= 30 && overPrice(p) >= -300 && overPrice(p) <= 600)
                         : (p.model >= 35 && p.model <= 85 && overPrice(p) >= -300 && overPrice(p) <= 200));
  const u = udPick(p);
  // A real yardage/receptions pick has to be at Underdog's own line (!synthetic) and clear the
  // confidence floor; a touchdown pick is always synthetic and skips that floor (see above).
  return u && (p.mkt === "TD" || (!u.synthetic && u.conf >= UD_MIN)) && (p.games||0) >= 8 && playing(p) && !u.stale && scopeOK(p, s)
    // The line-size floor (a 0.5-reception or 12.5-yard line is confidence for free) only means
    // anything for a real yardage/receptions line; a TD pick has no line to be thin, it is
    // whichever side the model favors.
    && (p.mkt === "TD" ? true : p.mkt === "RECS" ? u.line >= 2.5 : u.line >= 15);
};
const legMetric = (book) => book === "underdog" ? (p => udPick(p).conf) : (p => p.edge);
function pickLegs(cands, key, allowSameGame){
  const seenG = new Set(), seenP = new Set(), out = [];
  cands.sort((a,b) => key(b[0]) - key(a[0])).forEach(([p,i]) => {
    if (out.length < SLIP_LEGS && (allowSameGame || !seenG.has(p.game)) && !seenP.has(p.n)){
      seenG.add(p.game); seenP.add(p.n); out.push(i);
    }
  });
  return out;
}
function bestSlipIn(scope, winKey, book){
  const cands = PROPS.map((p,i)=>[p,i]).filter(([p]) => legOKInBook(p, scope, book) && (!winKey || p.win === winKey));
  const games = new Set(cands.map(([p]) => p.game)).size;
  // A single-game window (a Thu/Sun/Mon night with one game on the slate) can never fill three
  // legs under the one-leg-per-game rule -- allow it there; the `.corr` warning already tells
  // the reader it is a same-game parlay and to price it as one.
  return pickLegs(cands, legMetric(book), games > 0 && games < SLIP_LEGS);
}
function mineSlip(book){
  if (!LIVE_MARKET) return [1,2,5];
  const seen = new Set(), out = [];
  const ok = book === "underdog" ? p => !!udPick(p) : p => p.mkt !== "TD";
  PROPS.forEach((p,i) => { if (p.mine && ok(p) && !seen.has(p.game) && out.length < SLIP_LEGS){ seen.add(p.game); out.push(i); } });
  return out;
}
const PRESETS = [["mine","My players"],["blank","Clear"]];
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
   tds exactly). No whole-slate card -- that would reintroduce the cross-date bug this fixes.
   Computed once per book: PROPS never mutates, and toggling the cart must not re-roll the
   gallery. Both books' galleries are built up front so switching PARLAY_BOOK is instant. */
function buildGallery(book){
  const scopes = [["yards","Yards"],["tds","TDs"],["mix","Mix"]];
  const metric = legMetric(book);
  const out = [], seen = new Set();
  for (const w of WINDOWS) for (const [s, label] of scopes){
    const legs = bestSlipIn(s, w.k, book);
    if (legs.length < 2) continue;
    const sig = legs.slice().sort((a,b)=>a-b).join(",");
    if (seen.has(sig)) continue;
    seen.add(sig);
    out.push({i: out.length, book, scope: s, scopeLabel: label, win: w, legs,
               metric: legs.reduce((a,i)=>a+metric(PROPS[i]), 0) / legs.length});
  }
  return out;
}
const GALLERIES = {dk: buildGallery("dk"), underdog: buildGallery("underdog")};
const GALLERY_BEST = {
  dk: GALLERIES.dk.reduce((a,c) => !a || c.metric > a.metric ? c : a, null),
  underdog: GALLERIES.underdog.reduce((a,c) => !a || c.metric > a.metric ? c : a, null),
};
/* The gallery's own filter -- not fed into legOKInBook/bestSlipIn, which already ran once above. */
let SLIP_SCOPE = "all";
let GAL_WIN = "ALL";

