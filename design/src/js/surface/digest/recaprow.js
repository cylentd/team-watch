/* ============================== DIGEST: THE RECAP ROW ==============================
   2026-10-05 (David: "we probably need a recap section for the week instead of dumping it into the
   Digest. The Digest should be a curated list of content for readers to enjoy and not just a results
   section that stays there for the whole week and quickly become stale"). The Results row, its banner
   and the Waiting card left the Digest; this one row stands in for them and links to This week > Recap
   (#weekrecap), where the week's results are. One 52px ticker row in the other rows' shape: label, week,
   the week's top scorer and Claude's record on its Preview picks, an arrow. It opens nothing in place.

   No fantasy points on it (David, 2026-10-05: Digest headlines show yards and TDs, never points, since
   every league scores differently): the top scorer's day is the first two parts of his box line (dgStatLine, parts.js), or just
   his name when the recap has none. Claude's part is its straight-up picks, "5-3" read as 5 of 8, left
   out when the recap has no Preview record. When the row shows is data/digest.js dgRecap. */

/* "5-3" (or "5-3-0") as {w: 5, n: 8}: wins of games picked; null for anything else. */
function dgRecapPicks(su){
  const m = /^(\d+)-(\d+)/.exec(su || "");
  return m ? {w: +m[1], n: +m[1] + +m[2]} : null;
}

function dgRecapRowHTML(){
  const r = dgRecap();
  if (!r) return "";
  const top = r.top, picks = dgRecapPicks(r.preview_record && r.preview_record.su);
  // The first two parts of his line ("285 yds · 3 TD"): the whole line ran past 360px and cut off.
  const day = top ? dgStatLine(top).split(" · ").slice(0, 2).join(" · ") : "";
  const who = top ? `<span class="dg-s-w"><b>${esc(dgShort(top.n))}</b>${day ? " " + esc(day) : ""}</span>` : "";
  const claude = picks ? `<span class="dg-s-c">${t("digest.recapRow.claude", picks)}</span>` : "";
  return `<div class="dg-row link" data-dgrow="recap">
    <a class="dg-head" href="#weekrecap">
      <span class="dg-l">${dgIcon("recap")}${dgLabel("recap")}</span><span class="dg-n go">${t("digest.recapRow.wk", {n: r.week})}</span>
      <span class="dg-s">${who}${claude}</span>${DG_ARROW}</a>
  </div>`;
}
