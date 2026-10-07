/* DIGEST CARD: Out, and who gains (Tuesday); Out tonight and who's next (Monday). A starter who is Out, Doubtful or on IR (ctx.d.gains,
   ff-jarvis weekly_digest_gains) and the man behind him on the depth chart. The row is the NEXT man: his face and
   name, who is out and why under it, his last snap share at the right; his targets and carries last week and his
   depth in the research. Facts only, no verdict word: the model that priced the vacated work failed its backtest.
   A starter with nobody behind him shows himself, "No clear backup", and his status. Interface: card.js. */

/* The next man's row. */
function dgGainRow(g){
  const o = g.out, n = g.next, short = esc(dgShort(o.name));
  const v = {team: esc(o.team), name: short, word: esc(dgStatusWord(o.status)), injury: esc(dgInjury(o.injury))};
  const meta = o.injury ? t("digest.card.gains.meta", v) : t("digest.card.gains.metaNoInjury", v);
  const share = n.tgt_pct_last;
  const research = [n.targets_last != null ? [t("digest.card.gains.targets"), n.targets_last] : null,
    n.carries_last != null ? [t("digest.card.gains.carries"), n.carries_last] : null,
    share != null ? [t("digest.card.gains.share"), `${dgPct(share)}%`] : null,
    n.depth != null ? [t("digest.card.gains.depth"), `${n.pos}${n.depth}`] : null].filter(Boolean);
  const snaps = n.snap_last;
  return dgRowHTML("gains", {slug: n.slug, n: dgShort(n.name), meta,
    answer: {num: snaps != null ? `${dgPct(snaps)}%` : "–", change: t("digest.card.gains.snaps"), dir: "flat"}, research});
}

/* A starter with nobody behind him: the starter, his status at the right. */
function dgNoBackupRow(g){
  const o = g.out;
  return dgStatusRowHTML(o.status, "gains", {slug: o.slug, n: dgShort(o.name), meta: t("digest.card.gains.noBackup", {team: esc(o.team)}),
    research: [[t("digest.card.gains.status"), o.status], o.injury ? [t("digest.card.gains.injury"), o.injury] : null].filter(Boolean)});
}

function dgCardGains(ctx){
  const gains = ((ctx.d && ctx.d.gains) || []).filter(g => g && g.out);
  if (!gains.length) return "";
  // Monday's list holds only the teams whose game has not started (the packet drops the rest): tonight's.
  return dgCardHTML({id: "gains", title: ctx.day === "mon" ? t("digest.card.gains.titleMon") : t("digest.card.gains.title"),
    body: gains.map(g => g.next ? dgGainRow(g) : dgNoBackupRow(g)).join("")});
}
