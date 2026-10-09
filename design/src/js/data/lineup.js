/* Start/Sit's lineup card and paged calls (ledger #94, draft A, David 2026-10-09): pure functions of data, Node-tested
   (tests/test_js_lineup.py). The card leads the view with the reader's own starters and bench, our one swap on top;
   the calls under it page one kind at a time. Nothing here makes a number: points are the Ranks rows' (the picker's
   own, ssPts), the calls are ff-jarvis's (LIVE_SS3.calls, cut by design/startsit_v3.py), and the swap is the
   picker's own verdict on the pair the roster brief names (briefPairs, rbVerdict). */

/* Calls drawn on one page of the calls card: six 53px rows, with the card's head and its kind switch, end
   above the bottom tab bar on a 360x800 phone, so the switch stays in the thumb's reach (STYLE.md). */
const MU_PAGE_ROWS = 6;
/* One call row's height, 52px and its 1px rule (rows.css): from 960px the calls card sits beside the lineup and
   holds as many rows as end it level with the lineup (calls.js muFitCalls, measured in the reader's browser,
   STYLE.md "Measure, never guess"), never fewer than MU_PAGE_ROWS. */
const MU_ROW_H = 53;

/* Rows a page that end a card of `restH` px (everything but its rows) level with a `targetH` px neighbour. */
const muFitRows = (targetH, restH) => Math.max(MU_PAGE_ROWS, Math.floor((targetH - restH) / MU_ROW_H));

/* The positions a lineup call is about: the ones Ranks projects and ff-jarvis calls. K and DST have neither. */
const MU_SKILL = ["QB", "RB", "WR", "TE"];

/* His lineup: the skill starters, then the healthy bench, each {slug, n, pos, team, slot, pts, call, bye}.
   `pts` is {slug: points or null}, `calls` LIVE_SS3.calls, `off` the clubs on a bye (LIVE_RANKS.off). The
   injured list (slot OUT) is no lineup call. */
function muLineup(roster, pts, calls, off){
  const skill = roster.filter(p => MU_SKILL.includes(p.pos) && p.slot !== "OUT");
  const row = p => ({slug: p.slug, n: p.n, pos: p.pos, team: p.team, slot: p.slot,
    pts: typeof pts[p.slug] === "number" ? pts[p.slug] : null, call: calls[p.slug] || "", bye: off.includes(p.team)});
  return {starters: skill.filter(p => p.start).map(row), bench: skill.filter(p => !p.start).map(row)};
}

/* Our call on the pair [bench, starter]: `verdict` is the picker's (rbVerdict, `win` a lane {p: {slug}}).
   {kind, in, out, gap}: "swap" when the bench player wins (we'd start him), "keep" when the starter does,
   "flip" inside the coin flip; `in` is the one we'd start. Null with no pair or no verdict. */
function muSwap(pair, verdict){
  if (!pair || pair.length < 2 || !verdict) return null;
  const [bench, starter] = pair;
  if (verdict.flip) return {kind: "flip", in: bench, out: starter, gap: verdict.gap};
  const benchWins = verdict.win.p.slug === bench;
  return {kind: benchWins ? "swap" : "keep", in: benchWins ? bench : starter, out: benchWins ? starter : bench, gap: verdict.gap};
}

/* One kind's calls ("smash", "start", "sit"), in the order the build cut them (design/startsit_v3.py). */
function muCallRows(ss3, kind){
  if (kind === "smash") return ss3.smash;
  const call = kind.toUpperCase();
  return ss3.takes.filter(r => r.call === call);
}

/* Page `page` of `n` rows, `per` a page, clamped to the list: {from, to, page, pages}. */
function muPage(n, page, per){
  const pages = Math.max(1, Math.ceil(n / per));
  const at = Math.min(Math.max(page, 0), pages - 1);
  return {from: at * per, to: Math.min(n, at * per + per), page: at, pages};
}
