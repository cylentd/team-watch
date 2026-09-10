/* American odds arithmetic. Implied probability keeps the vig, so a two-way market sums past 100. */
const amToDec  = a => a > 0 ? 1 + a/100 : 1 + 100/(-a);
const amToProb = a => a > 0 ? 100/(a+100) : (-a)/((-a)+100);
const decToAm  = d => d >= 2 ? Math.round((d-1)*100) : Math.round(-100/(d-1));
const fmtAm    = a => a === null || a === undefined ? "—" : (a > 0 ? `+${a}` : `${a}`);
const overPrice = p => p.book ? (p.books ? p.books[p.book].over : Number(p.book)) : null;
/* One line per book, "DK o63.5 -112 · UD o60.5 -107". The sample rows only carry one price. */
const ABBR = {DraftKings:"DK", Underdog:"UD"};
const bookLine = p => !p.books ? t("parlay.bookline.book", {price: p.book})
  : Object.entries(p.books).map(([b,x]) => `${ABBR[b]||b} ${x.line == null ? "" : `o${x.line} `}${fmtAm(x.over)}`
      + (x.pick ? ` → ${x.pick.toUpperCase()} ${x.conf}%` : "")).join(" · ")
    + (p.games ? ` · ${t("parlay.bookline.games", {n: p.games})}` : "")
    + (p.opp_f ? ` · ${t("parlay.bookline.opp", {team: esc(p.opp), pct: Math.round(Math.abs(p.opp_f - 1) * 100) === 0 ? "±0" : (p.opp_f >= 1 ? "+" : "−") + Math.round(Math.abs(p.opp_f - 1) * 100)})}` : "");
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

