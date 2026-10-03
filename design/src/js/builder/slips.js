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
   from week 5 on and blocked the winning side before it. The split was found in 2025; on 2024's
   closing lines (12.56, 2026-09-27, weeks 1-13) the same rule hit 55.9% (n 202, CI 49-63) and TDs
   at 50%+ hit 58.8% (n 51): enough for a 3-leg 6x, not a 2-leg 3x. */
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
  // priced as a heavy favourite), and at the HIT_RECS floor; a touchdown pick is always synthetic
  // and needs its P(score) at HIT_TD. No side gate since 2026-10-03: David bets Higher, and the
  // graded rate per side (grade.js legHit) already prices a higher pick down.
  return u && (p.mkt === "TD" ? u.conf >= HIT_TD
    : p.mkt === "RECS" && !u.synthetic && u.conf >= HIT_RECS && u.line >= 2.5)
    && (p.games||0) >= 8 && playing(p) && !u.stale && scopeOK(p, s);
};
function mineSlip(book){
  if (!LIVE_MARKET) return [1,2,5];
  const seen = new Set(), out = [];
  // Longest reception has no line to pick from (2026-10-03), so it is never a leg.
  const ok = book === "underdog" ? p => !!udPick(p) && p.mkt !== "LONG" : p => p.mkt !== "TD" && p.mkt !== "LONG";
  PROPS.forEach((p,i) => { if (p.mine && ok(p) && !seen.has(p.game) && out.length < SLIP_LEGS){ seen.add(p.game); out.push(i); } });
  return out;
}
const PRESETS = [["mine",t("parlay.preset.mine")],["blank",t("parlay.preset.blank")]];
function presetSlip(k, book){
  if (k === "mine") return mineSlip(book);
  return [];
}
/* The cart starts empty: the reader builds it one leg at a time from the board's player sheet,
   Build's lines or Preview, or loads a saved slip (builder/saved.js). SLIP holds PROPS indexes;
   SLIP_SIDE the side the reader picked for each (2026-10-03, "higher" or "lower"; a touchdown is
   "higher", shown as Yes). A leg with no side picked (a Build tap) takes the model's call. */
let SLIP_MODE = "blank";
let SLIP = [];
let SLIP_SIDE = {};
function slipSide(i){
  if (SLIP_SIDE[i]) return SLIP_SIDE[i];
  const u = PROPS[i] ? udPick(PROPS[i]) : null;
  return u && u.pick ? u.pick : "higher";
}
/* The side of a leg named by its row, for the grading in grade.js; a row off the slip reads the
   model's call, as before sides were picked. */
const slipSideOf = p => { const i = PROPS.indexOf(p); return i >= 0 ? slipSide(i) : ((udPick(p) || {}).pick || "higher"); };
/* Put leg i on the slip at `side`; the same side again takes it off. Returns whether it is on. */
function slipSet(i, side){
  if (SLIP.includes(i) && slipSide(i) === side){
    SLIP = SLIP.filter(x => x !== i); delete SLIP_SIDE[i];
  } else {
    if (!SLIP.includes(i)) SLIP = SLIP.concat(i);
    SLIP_SIDE[i] = side;
  }
  SLIP_MODE = "custom";
  return SLIP.includes(i);
}
/* DraftKings (over/price) or Underdog (higher/lower + confidence) -- a page-level toggle, same
   pattern as DFS_SITE, because the two books need different rows, a different gallery, and a
   different cart payout entirely, not just a different price column. */
let PARLAY_BOOK = "underdog";

/* Kickoff groups for Build's headings (lines.js): windows in kickoff order, a day just ahead of
   its first window. Slips picks one kickoff at a time from the bar instead (bar.js KICK_CHIPS). */
const GAL_GROUPS = (() => {
  const out = [], days = new Set();
  WINDOWS.filter(w => GAL_WINDOWS.includes(w)).forEach(w => {
    const day = DAYS.find(d => d.wins.includes(w.k) && GAL_WINDOWS.includes(d));
    if (day && !days.has(day.k)){ days.add(day.k); out.push(day); }
    out.push(w);
  });
  return out;
})();
/* "Sunday morning", "Thursday Night", "All Sunday": a window labelled only by the hour
   ("Morning") takes its weekday, since the heading is what the reader scrolls to. */
function galGroupName(w){
  const day = new Date(`${w.date}T12:00:00`).toLocaleDateString("en-US", {weekday: "long"});
  const name = w.wins || w.label.startsWith(day) ? w.label : `${day} ${w.label}`;
  // Sentence case, weekdays kept: "Thursday Night" reads "Thursday night".
  return name.split(" ").map((s, i) => i && !/day$/.test(s) ? s.toLowerCase() : s).join(" ");
}

/* The one kickoff filter for both Bets views (2026-09-25): Slips filters its cards by it, Build its
   lines. Two selects used to set two variables, so a reader who picked Sunday for the slips saw
   Thursday's lines under them. */
let GAL_WIN = "ALL";
let BETS_PANEL = false;   // the settings panel under the bar is open
let BETS_SHEET = false;   // the slip sheet is up

