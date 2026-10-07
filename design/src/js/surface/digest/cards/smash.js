/* DIGEST CARD: SMASH (Saturday). The top SMASH play at each of QB, RB, WR and TE (LIVE_SS3), his projected
   points on the right. A tap opens what the opponent allows to his position (LIVE_DEFENSE, "Nth most" of the
   league: rank 1 allows the fewest), the book's main line and the anytime-TD price. The foot links to the rest of
   the list in Matchups and carries Start/Sit's record with its marks (dgCardRecord); the title word carries
   SMASH's own mark. Interface: card.js; returns "" without a SMASH play. */

/* The opponent's points allowed to his position, as a research pair, or null when the page has no row for the club. */
function dgSmashAllows(ctx, r){
  const a = dgAllowed(ctx.def, r.opp, r.pos);   // data/dayplan.js: the rank the banner picked by
  if (!a || a.cur.pts_pg == null) return null;
  return [t("digest.card.smash.allows", {opp: r.opp}),
    t("digest.card.smash.allowsVal", {pts: a.cur.pts_pg.toFixed(1), nth: ordinal(a.most), of: a.of})];
}

function dgSmashRowHTML(ctx, r){
  const allows = dgSmashAllows(ctx, r), l = r.line;
  return dgRowHTML("smash", {slug: r.slug, n: dgShort(r.name),
    meta: t("digest.card.smash.meta", {rank: r.rank, pos: esc(r.pos), game: muVs(r)}),
    answer: {num: r.pts == null ? "" : r.pts.toFixed(1), change: t("digest.card.smash.pts"), dir: "flat"},
    research: [[t("digest.card.smash.rank"), dgSsRank(r.pos, r.rank)], ...(allows ? [allows] : []),
      ...(l ? [[t("digest.card.smash.line"), `${l.value.toFixed(1)} ${MU_STAT()[l.stat] || l.stat}`]] : []),
      ...(r.td_price == null ? [] : [[t("digest.card.smash.td"), fmtAm(r.td_price)]])]});
}

function dgCardSmash(ctx){
  const smash = (ctx.ss3 && ctx.ss3.smash) || [];
  const top = DG_POS.map(pos => smash.filter(r => r.pos === pos).sort((a, b) => a.rank - b.rank)[0]).filter(Boolean);
  if (!top.length) return "";
  const rest = smash.length - top.length;
  const more = rest > 0 ? `<button type="button" class="dg-sm-more" data-testid="digest-smash-more" data-dggo="matchups">${t("digest.card.smash.more", {n: rest})}${DG_ARROW}</button>` : "";
  return dgCardHTML({id: "smash", title: `<span title="${esc(t("matchups.takes.markSmash"))}">${t("digest.card.smash.title")}</span>`,
    body: top.map(r => dgSmashRowHTML(ctx, r)).join(""), foot: [more, dgRecordFoot(ctx, "smash")].filter(Boolean).join(" ")});
}
