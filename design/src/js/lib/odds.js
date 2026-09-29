/* American odds arithmetic. Implied probability keeps the vig, so a two-way market sums past 100. */
const amToDec  = a => a > 0 ? 1 + a/100 : 1 + 100/(-a);
const amToProb = a => a > 0 ? 100/(a+100) : (-a)/((-a)+100);
const decToAm  = d => d >= 2 ? Math.round((d-1)*100) : Math.round(-100/(d-1));
const fmtAm    = a => a === null || a === undefined ? "—" : (a > 0 ? `+${a}` : `${a}`);
const overPrice = p => p.book ? (p.books ? p.books[p.book].over : Number(p.book)) : null;
const ABBR = {DraftKings:"DK", Underdog:"UD"};
const ud = p => p.books && p.books.Underdog;
/* Underdog carries no anytime-TD line in this feed at all (checked 2026-09-10: 0 of 430 TD rows
   have an Underdog price -- their pick'em board just isn't in what BettingPros scrapes here), so
   a TD row derives its pick from the model's P(score) instead of sitting out of Underdog mode
   entirely. Anytime TD is a yes-only market everywhere it is sold: there is no "lower", no book
   pays you for a player not scoring. So the derived pick is always higher and its confidence is
   P(score) itself -- a 23% higher sorts to the bottom, where a bet you would not place belongs,
   instead of surfacing as a 77% "lower" nobody can buy. `synthetic: true` marks the difference
   everywhere this is shown -- it is a model read, never passed off as an Underdog price. */
function udPick(p){
  const real = ud(p);
  if (real && typeof real.conf === "number") return real;
  if (p.mkt === "TD" && typeof p.model === "number")
    return {pick: "higher", conf: Math.round(p.model), line: null, synthetic: true};
  return null;
}

/* A line the book set far from the model (build.py's `stale`), in the book in force. The model's
   rate still leans on games from another season or role (props_model.py names it a v1 blind
   spot): on 2026-09-29 every Underdog pick at 80%+ was one of these. Build shows no chance for it. */
const lineMoved = (p, book) => !!(book === "underdog" ? ud(p) && ud(p).stale : p.stale);

/* Best odds (2026-09-29): the line pays more than usual on the model's side, or sets an easier
   number than another book. Underdog: a price better than its standard -107, or its line easier
   than DraftKings'. DraftKings, always the over: an easier line or a better price than the
   BettingPros consensus. Returns the reason for the row to print, or null. A moved line never
   counts: its model side is the number Build no longer trusts. */
const UD_STD = -107;
function bestOdds(p, book){
  if (lineMoved(p, book)) return null;
  const num = x => typeof x === "number";
  if (book === "underdog"){
    const u = ud(p);
    if (!u || !u.pick) return null;
    const lo = u.pick === "lower", price = lo ? u.under : u.over, dk = p.books.DraftKings;
    if (num(price) && price > UD_STD) return fmtAm(price);
    const gap = dk && num(dk.line) && num(u.line) ? (lo ? u.line - dk.line : dk.line - u.line) : 0;
    return gap > 0 ? t("parlay.best.easier", {n: +gap.toFixed(1), book: ABBR.DraftKings}) : null;
  }
  const dk = p.books && p.books.DraftKings, r = p.ref;
  if (!dk || !r || !num(dk.over)) return null;
  if (num(dk.line) && num(r.line) && dk.line < r.line) return t("parlay.best.easier", {n: +(r.line - dk.line).toFixed(1), book: t("parlay.best.market")});
  return dk.line === r.line && num(r.over) && dk.over > r.over ? t("parlay.best.beats", {p: fmtAm(r.over)}) : null;
}

