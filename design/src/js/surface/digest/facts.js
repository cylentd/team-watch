/* ============================== DIGEST: WORTH KNOWING ==============================
   2026-09-29, storyboard https://claude.ai/artifact/96B1dMss6vfyhhsQLUSK4x (option B, David: "doing the
   legwork for casuals who don't want to dive into the research in Players"). Four tiles, one fact each
   from a Players view, and a tap opens that view. They replaced Results' four tiles, which only
   restated the first row of the lists under them (Achane three times in week 3).

   Every number is the view's own: Role's gap (descriptive only, METHODOLOGY 12.41, so no tile says
   buy or sell), the Grid's target share, Takes' call against the experts. A player shows once, never the banner's; a
   fact with no one to name drops, and Role's workload leader fills the fourth slot when Takes has
   no calls yet (Takes' calls land Tuesday). */

const dgFactTile = (tone, label, r, big, sub, leaf) => `<button type="button" class="dg-tile dg-fact${tone ? " " + tone : ""}" data-dggo="${leaf}" data-dgfact="${esc(r.slug)}">
    <span class="dg-tile-k">${label}</span>
    <span class="dg-tile-top"><span class="dg-hd">${dgResFace(r)}</span><b class="dg-tile-v">${big}</b></span>
    <span class="dg-tile-n">${esc(dgShort(r.n))}</span><span class="dg-tile-s">${sub}</span>
    <span class="dg-fact-go">${navLabel(leaf)}${DG_ARROW}</span></button>`;

const dgRoleSub = r => t("digest.fact.roleSub", {pts: r.pts.toFixed(1), xfp: r.xfp.toFixed(1)});

/* The Grid's biggest rise in target share, WR and TE, from the week before to its newest full week.
   Only a qualified row counts, and the new share must be a real role (20%+), not 2% to 9%. */
const DG_JUMP_MIN = 20;
function dgJump(){
  if (!USAGE_LIVE) return null;
  const wk = usageDefaultWeek(), rows = USAGE.rows || [];
  const was = new Map(rows.filter(r => r.wk === wk - 1).map(r => [r.slug, r.v.tgt_pct]));
  return rows.filter(r => r.wk === wk && r.q && (r.pos === "WR" || r.pos === "TE")
      && r.v.tgt_pct >= DG_JUMP_MIN && was.get(r.slug) != null)
    .map(r => ({...r, was: was.get(r.slug), now: r.v.tgt_pct, rise: r.v.tgt_pct - was.get(r.slug)}))
    .sort((a, b) => b.rise - a.rise)[0] || null;
}

/* The banner's player (lead.js): the week's top score, or the hurt player it leads with. */
function dgLeadSlug(d){
  const L = d.lead;
  if (!L) return null;
  if (L.rule === "results") return ([...d.stars].sort((a, b) => b.actual - a.actual)[0] || {}).slug || null;
  if (L.rule === "hurt") return (d.hurt[L.index] || {}).slug || null;
  return null;
}

/* From Highlights (2026-09-29, David: "yes"): one tile per Players view, its first line, or its second
   when the first names the banner's player. One producer feeds both, so the Digest and the tab can
   never disagree; a foot leads to the tab. Without the packet the Digest keeps its own picks below. */
function dgFactsFromHighlights(d){
  const H = typeof LIVE_HIGHLIGHTS !== "undefined" ? LIVE_HIGHLIGHTS : null;
  if (!H) return "";
  const used = new Set([dgLeadSlug(d)].filter(Boolean));
  const tiles = H.views.map(v => {
    const r = v.rows.find(x => !used.has(x.slug));
    if (!r) return "";
    used.add(r.slug);
    return dgFactTile("", hlViewName(v.view), r, esc(r.num || ""), esc(r.line), v.leaf);
  }).filter(Boolean);
  if (!tiles.length) return "";
  return `<section class="dg-facts" aria-labelledby="dg-facts-h">
    <h3 class="dg-sec" id="dg-facts-h">${t("digest.fact.title")}</h3><div class="dg-tiles">${tiles.join("")}</div>
    ${dgFootHTML("", "highlights", t("digest.fact.more"))}</section>`;
}

function dgFactsHTML(d){
  const fromHl = dgFactsFromHighlights(d);
  if (fromHl) return fromHl;
  const used = new Set([dgLeadSlug(d)].filter(Boolean));
  const free = list => list.find(r => !used.has(r.slug)) || null;
  const take = r => { if (r) used.add(r.slug); return r; };
  const role = LIVE_ROLE ? [...LIVE_ROLE.rows] : [];
  const over = take(free([...role].sort((a, b) => b.gap - a.gap).filter(r => r.gap > 0)));
  const under = take(free([...role].sort((a, b) => a.gap - b.gap).filter(r => r.gap < 0)));
  const j = dgJump(), jump = j && !used.has(j.slug) ? take(j) : null;
  const call = take(free(muCalls("start").filter(r => r.ecr != null && r.ecr > r.rank)));
  const work = call ? null : take(free([...role].sort((a, b) => b.xfp - a.xfp)));
  const tiles = [
    over && dgFactTile("up", t("digest.fact.over"), over, dgSigned(over.gap, 1), dgRoleSub(over), "movers"),
    under && dgFactTile("dn", t("digest.fact.under"), under, dgSigned(under.gap, 1), dgRoleSub(under), "movers"),
    jump && dgFactTile("", t("digest.fact.jump"), jump, `${Math.round(jump.now)}%`,
      t("digest.fact.jumpSub", {was: Math.round(jump.was), now: Math.round(jump.now), wk: jump.wk}), "usage"),
    call && dgFactTile("", t("digest.fact.take"), call, `+${call.ecr - call.rank}`,
      t("digest.fact.takeSub", {pos: esc(call.pos), rank: call.rank, ecr: call.ecr}), "matchups"),
    work && dgFactTile("", t("digest.fact.work"), work, work.xfp.toFixed(1), t("digest.fact.workSub"), "movers"),
  ].filter(Boolean);
  if (!tiles.length) return "";
  return `<section class="dg-facts" aria-labelledby="dg-facts-h">
    <h3 class="dg-sec" id="dg-facts-h">${t("digest.fact.title")}</h3><div class="dg-tiles">${tiles.join("")}</div></section>`;
}
