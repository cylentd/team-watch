/* DIGEST CARD: Bold calls (Saturday). The widest START and the widest SIT from LIVE_SS3: the two of each where our
   rank and his season average disagree by the most spots (METHODOLOGY 12.75). The answer is the pick word, which
   carries its model's mark (row.js); the meta line puts our rank beside his season average ("WR · Our rank 15 · his
   season 44"); a tap opens both ranks and the reasons the call carries. The foot is Start/Sit's record (dgCardRecord);
   more to Matchups. Interface: card.js; returns "" without a bold call. */
const DG_BOLD_EACH = 2;

function dgBoldRowHTML(r){
  const ours = dgSsRank(r.pos, r.rank), avg = dgSsRank(r.pos, r.avg_rank);
  return dgRowHTML("bold", {slug: r.slug, n: dgShort(r.name),
    meta: avg ? t("digest.card.bold.meta", {team: esc(r.team), pos: esc(r.pos), ours: r.rank, avg: r.avg_rank})
      : t("digest.card.bold.metaNone", {team: esc(r.team), pos: esc(r.pos), ours: r.rank}),
    answer: {pill: r.call},
    research: [[t("digest.card.bold.rank"), ours], ...(avg ? [[t("digest.card.bold.avg"), avg]] : []),
      ...(r.reasons || []).map(w => [t("digest.card.bold.why"), w.t])]});
}

function dgCardBold(ctx){
  const takes = (ctx.ss3 && ctx.ss3.takes) || [];
  const widest = call => takes.filter(r => r.call === call).sort((a, b) => b.margin_spots - a.margin_spots).slice(0, DG_BOLD_EACH);
  const rows = [...widest("START"), ...widest("SIT")];
  if (!rows.length) return "";
  const rec = dgRecordFoot(ctx, "bold");
  return dgCardHTML({id: "bold", title: t("digest.card.bold.title"), more: {leaf: "matchups"},
    body: rows.map(dgBoldRowHTML).join(""), foot: rec, footTip: rec ? DG_RECORD_TIP() : ""});
}
