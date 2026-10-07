/* DIGEST CARD: Top adds (Tuesday). The wire's five adds (LIVE_DIGEST.adds), each with the number that earned it;
   more to Waivers. The answer is the role behind the add where Usage movers has him (his share now and its change,
   red when it fell), else Sleeper's add count, else ESPN's % rostered and its change. The meta line says why when
   the data does: a teammate out, or the teammate whose work he took. Research: the numbers above, plus his targets
   and carries. A number from Usage movers is descriptive and untested, and its row says so. Interface: card.js. */

const DG_ADDS_MAX = 5;

const dgAddsMover = (ctx, slug) => ((ctx.usage && ctx.usage.rows) || []).find(r => r.slug === slug) || null;

/* Why he was added, in a few words, or "": the starter he replaces, which is the gains row whose next man he is, else
   one out at his own position on his team (never any out starter on the team: a back's injury is no receiver's
   reason); else the teammate who lost work. */
function dgAddsReason(ctx, a, mv){
  const gains = ((ctx.d && ctx.d.gains) || []).filter(g => g && g.out);
  const g = gains.find(x => x.next && x.next.slug === a.slug)
    || gains.find(x => a.pos && x.out.team === a.team && x.out.pos === a.pos && x.out.slug !== a.slug);
  if (g) return t("digest.card.adds.reasonOut", {name: esc(dgShort(g.out.name)), word: esc(dgStatusWord(g.out.status))});
  return mv && mv.teammate ? t("digest.card.adds.reasonFell", {name: esc(dgShort(mv.teammate.name))}) : "";
}

/* The number behind the add, or null. */
function dgAddsAnswer(d, a, mv){
  if (mv) return dgUsageAnswer(mv);
  if (d.adds_source === "sleeper" && a.count != null) return {num: dgBig(a.count), change: t("digest.card.adds.chAdds"), dir: "flat"};
  if (a.now == null) return null;
  const delta = a.delta != null ? a.delta : a.was != null ? a.now - a.was : null;
  return {num: `${dgPct(a.now)}%`, dir: delta == null ? "flat" : dgUsageDir(delta),
    change: delta == null ? "" : t("digest.card.adds.chRostered", {n: dgSigned(delta, 0)})};
}

function dgAddsResearch(d, a, mv){
  const share = mv && mv.metric === "snap" ? t("digest.card.usage.snapShare") : t("digest.card.usage.tgtShare");
  return [a.count != null ? [t("digest.card.adds.sleeper", {h: d.adds_hours}), t("digest.card.adds.sleeperN", {n: dgBig(a.count)})] : null,
    a.was != null && a.now != null ? [t("digest.card.adds.rostered"), `${dgPct(a.was)}% → ${dgPct(a.now)}%`] : null,
    mv ? [share, (mv.spark || []).map(x => `${dgPct(x)}%`).join(" · ")] : null,
    mv && mv.targets != null ? [t("digest.card.usage.targets"), mv.targets] : null,
    mv && mv.carries != null ? [t("digest.card.usage.carries"), mv.carries] : null].filter(Boolean);
}

function dgAddRow(ctx, a){
  const mv = dgAddsMover(ctx, a.slug), reason = dgAddsReason(ctx, a, mv);
  return dgRowHTML("adds", {slug: a.slug, n: dgShort(a.n),
    meta: reason ? t("digest.card.adds.meta", {team: esc(a.team), reason}) : esc(a.team),
    answer: dgAddsAnswer(ctx.d, a, mv), research: dgAddsResearch(ctx.d, a, mv), foot: mv ? t("digest.card.usage.mark") : ""});
}

function dgCardAdds(ctx){
  const adds = ((ctx.d && ctx.d.adds) || []).slice(0, DG_ADDS_MAX);
  if (!adds.length) return "";
  return dgCardHTML({id: "adds", title: t("digest.card.adds.title"), more: {leaf: "waivers"}, body: adds.map(a => dgAddRow(ctx, a)).join("")});
}
