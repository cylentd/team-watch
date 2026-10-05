/* ============================== DIGEST: RESULTS HEADLINES ==============================
   2026-09-29, storyboard https://claude.ai/artifact/FYQES3vMxJ8ukZm7gLNNih (option B, David's pick).
   The week in four tiles (the top score, the one nobody saw coming, the dud, the injury), then each
   position's top three: on a phone one line per position, on the wall a column each with a face and
   the player's day. Smashed, Busts and Left hurt stay in results.js, folded under them. */

/* A player's day in one short line: a passer's yards and TDs, a back's rushing and receiving yards,
   a receiver's catches for yards. Every word is a copy key, spelled out for assemble.py --check. */
function dgStatLine(r){
  const b = r.line;
  if (!b) return "";
  const td = n => n ? t("digest.stat.td", {n}) : "";
  const parts = b.att >= 10
    ? [t("digest.stat.pass", {y: b.pass_yd}), td(b.pass_td), b.int ? t("digest.stat.int", {n: b.int}) : "",
       b.rush_yd >= 20 ? t("digest.stat.rush", {y: b.rush_yd}) : ""]
    : b.car >= 5
      ? [t("digest.stat.rush", {y: b.rush_yd}), b.rec_yd > 0 ? t("digest.stat.recYd", {y: b.rec_yd}) : "", td(b.td)]
      : [b.rec ? t("digest.stat.catches", {n: b.rec, y: b.rec_yd}) : "", b.car ? t("digest.stat.rush", {y: b.rush_yd}) : "", td(b.td)];
  return parts.filter(Boolean).join(" · ");
}

/* The four tiles (the runner-up, out of nowhere, the dud, carted off) left on 2026-09-29, storyboard
   https://claude.ai/artifact/96B1dMss6vfyhhsQLUSK4x: each was the first row of Smashed, Busts or Left
   hurt right under it. Their shape went on to Worth knowing, which left the Digest on 2026-10-04. */

/* Each position's top three, as a table: the position as a heading, then name over his day, points at
   the right (2026-09-29, storyboard https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz, 1B; David: "should
   the categories be bigger? Should we consider not using headshots?"). No faces: the tiles above keep
   them, where one player is the subject, and a list scans by name. It is also the shape a kicker or a
   defense can take, which has no face to show. Two positions a row on a phone, four on the wall. */
function dgBoardHTML(d){
  const pos = DG_POS.map(p => {
    const rows = d.stars.filter(r => r.pos === p);
    return rows.length ? `<div class="dg-bd-pos"><h4 class="dg-bd-p">${p}</h4><span class="dg-bd-ns">${rows.map(r =>
      `<button type="button" class="dg-bd-r" data-dgslug="${esc(r.slug)}">
        <b>${esc(dgShort(r.n))}</b><span class="dg-bd-s">${dgStatLine(r)}</span><i>${r.actual.toFixed(1)}</i></button>`).join("")}</span></div>` : "";
  }).join("");
  return pos ? `<div class="dg-bd">${pos}</div>` : "";
}
