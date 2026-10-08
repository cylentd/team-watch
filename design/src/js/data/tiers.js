/* The week tier sheet on Home (2026-10-08, ledger #52, storyboard home draft B): one line of names per tier, as
   Boris Chen sets them, from LIVE_RANKS' own tiers. Pure, so Node tests it (tests/test_js_home.py); the card is
   surface/digest/cards/tiers.js. The page counts nothing: the tiers and their order are ff-jarvis's week_ranks. */

const DG_TIER_POSITIONS = ["QB", "RB", "WR", "TE", "FLEX"];

/* How deep the sheet goes: a 12-team league's starters at the position (1 QB, 2 RB, 2 WR, 1 TE a team; David's
   leagues, PRODUCT.md). FLEX: the three positions a team can start there, 12 teams each. The sheet takes whole
   tiers until this many players are in, so a tier is never cut in half. */
const DG_TIER_TEAMS = 12;
const DG_TIER_SLOTS = {QB: 1, RB: 2, WR: 2, TE: 1, FLEX: 3};
const DG_TIER_DEPTH = Object.fromEntries(Object.entries(DG_TIER_SLOTS).map(([p, n]) => [p, n * DG_TIER_TEAMS]));

/* The position the sheet opens on: the reader's pick this visit, else the day's (storyboard: RB on Thursday, WR on
   Sunday, when receivers fill the most lineup spots), else RB. Which one a weekday should open on is an open
   question in the storyboard's README. */
const DG_TIER_DAY = {sun: "WR"};
const DG_TIER_DEFAULT = "RB";
const dgTierPos = (day, picked) => DG_TIER_POSITIONS.includes(picked) ? picked : DG_TIER_DAY[day] || DG_TIER_DEFAULT;

/* {tiers: [{tier, rows}], shown, of}: the list's whole tiers, in its order, until `depth` players are in. */
function dgTierLines(list, depth){
  const all = list || [], tiers = [];
  let shown = 0;
  for (const r of all){
    const last = tiers[tiers.length - 1];
    if (last && last.tier === r.tier){ last.rows.push(r); shown++; continue; }
    if (shown >= depth) break;
    tiers.push({tier: r.tier, rows: [r]});
    shown++;
  }
  return {tiers, shown, of: all.length};
}
