/* DIGEST CARD: Top calls (Saturday). The model's strongest prop lines in games still to play: the same list
   Slips opens with (data/topcalls.js topCalls, the same book and the same filters), the top three. The meta
   line is the side and the line ("under 218.5 pass yds"), the answer the chance of that side with its tier word.
   The tier has failed its test, so the mark rides on every row (Slips' own, slips.tier.mark) and the foot gives
   the top tier's record. A tap opens his game, the kickoff and his own average. More to Slips. Interface: card.js;
   returns "" without a line to call. */
const DG_CALLS_N = 3;

/* The foot: the top call's tier word, its graded record through the week the grader reached, then the mark. */
function dgCallsFoot(tier){
  const r = typeof LIVE_PROPS_RECORD !== "undefined" ? LIVE_PROPS_RECORD : null, c = r && r.tiers && r.tiers[tier];
  const pct = c ? slHitPct(c) : null;
  const rec = pct === null ? "" : t("digest.card.calls.foot", {tier: slTierWord(tier), wk: r.through_week, w: c.w, l: c.l, pct}) + " ";
  return rec + t("slips.tier.mark");
}

function dgCallsRowHTML(c){
  const p = PROPS[c.i], mkt = SL_MKT_WORD()[c.mkt] || c.mkt;
  const avg = p.mu != null && p.games ? [[t("digest.card.calls.avg"),
    t("digest.card.calls.avgVal", {mu: Math.round(p.mu * 10) / 10, stat: mkt, n: p.games})]] : [];
  return dgRowHTML("calls", {slug: c.slug, n: dgShort(c.n),
    meta: t("digest.card.calls.meta", {team: esc(c.team), side: c.side === "lower" ? t("digest.card.calls.under") : t("digest.card.calls.over"),
      line: c.line, mkt: esc(mkt)}),
    answer: {num: `${c.pct}%`, change: slTierWord(c.tier), dir: "flat"},
    research: [[t("digest.card.calls.game"), c.game], [t("digest.card.calls.kick"), c.kick], ...avg], foot: t("slips.tier.mark")});
}

function dgCardCalls(ctx){
  const calls = topCalls(PROPS, {now: ctx.now, book: PARLAY_BOOK, limit: DG_CALLS_N});
  if (!calls.length) return "";
  return dgCardHTML({id: "calls", title: t("digest.card.calls.title"), more: {leaf: "parlay"},
    body: calls.map(dgCallsRowHTML).join(""), foot: dgCallsFoot(calls[0].tier)});
}
