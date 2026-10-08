/* OUR PICK, ONE PER LINE (2026-10-08, David, ledger #33: "our model is claude + model. users dont need to
   understand if claude or model is better"). Pure functions from given sides to what Slips draws; the page
   computes no model number here, it only compares two sides it was sent.

   A line is our pick when Claude (ff-jarvis claude_props) and the model (props_model, its tier) take the same
   side of it; the model's tier and chance ride along, the one confidence vocabulary (data/topcalls.js). When
   they take opposite sides the line is a split and shows no side. A line Claude has not called yet, or one the
   model gave no pick, is neither. */

/* The tiers whose agreed lines lead a window (David, 2026-10-08): Confident and up. */
const OP_LEAD = ["confident", "very"];

/* m: the model's call on the line shown ({side, tier, q} or a touchdown's {td}); c: Claude's ({side}) or null.
   {kind: "ours", side, tier, pct} | {kind: "split"} | null. */
function opCall(m, c){
  if (!m || m.td || !PT_RANK[m.tier] || !c) return null;
  return m.side === c.side ? {kind: "ours", side: m.side, tier: m.tier, pct: Math.round(m.q)} : {kind: "split"};
}

/* A game's lines, each {i, slug, n, pos, team, mkt, line, call, called} (`call` from opCall, `called` Claude
   has a call on it). Its picks strongest first, its splits as given, whether Claude has called the game at all,
   and whether its best pick leads the window. */
function opGame(lines){
  const picks = lines.filter(l => l.call && l.call.kind === "ours")
    .map(l => ({...l, side: l.call.side, tier: l.call.tier, pct: l.call.pct})).sort(ptOrder);
  return {picks, split: lines.filter(l => l.call && l.call.kind === "split"), called: lines.some(l => l.called),
    lead: picks.length > 0 && OP_LEAD.includes(picks[0].tier)};
}

/* A window's games ({..., op}), in kickoff order on the way in: the games whose best pick leads go first,
   strongest first; the rest keep their order. */
function opOrder(games){
  const lead = games.filter(g => g.op.lead).sort((a, b) => ptOrder(a.op.picks[0], b.op.picks[0]));
  return [...lead, ...games.filter(g => !g.op.lead)];
}
