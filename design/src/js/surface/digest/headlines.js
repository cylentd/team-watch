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

/* How long a left-hurt player is out, as a rank for the injury tile: the season first, then IR, then
   the most weeks, then anything open-ended. The same phrases results.js turns into its pills. */
function dgOutRank(text){
  if (!text) return 0;
  if (/season-ending|for the season|rest of the season/i.test(text)) return 100;
  if (/injured reserve|\bIR\b/.test(text)) return 90;
  const m = text.match(/\b(\d+|one|two|three|four|five|six|seven|eight)(?:[- ]to[- ]\w+)? weeks?\b/i);
  if (m) return 10 * (DG_WORD_N[m[1].toLowerCase()] || Number(m[1]) || 1);
  return /extended time|multiple weeks|several weeks/i.test(text) ? 50 : /week-to-week/i.test(text) ? 5 : 0;
}

/* One tile: what it is, the face beside the number, the name, one line of why. Opens the profile. */
const dgTile = (tone, label, r, big, sub) => `<button type="button" class="dg-tile${tone ? " " + tone : ""}" data-dgslug="${esc(r.slug)}">
    <span class="dg-tile-k">${label}</span>
    <span class="dg-tile-top"><span class="dg-hd">${dgResFace(r)}</span><b class="dg-tile-v">${big}</b></span>
    <span class="dg-tile-n">${esc(dgShort(r.n))}</span>${sub ? `<span class="dg-tile-s">${sub}</span>` : ""}</button>`;

/* The four tiles. A player appears once: when the banner is the week's top score (lead.js,
   dgLeadRes) the first tile is the runner-up (David, 2026-09-29), and a later tile skips whoever an
   earlier one took, so a bust who also left hurt is the dud, not both. A tile with no one left drops. */
function dgTilesHTML(d){
  const used = new Set();
  const take = list => { const r = list.find(x => !used.has(x.slug)); if (r) used.add(r.slug); return r; };
  const byPts = [...d.stars].sort((a, b) => b.actual - a.actual);
  const banner = d.lead && d.lead.rule === "results" && byPts[0];
  if (banner) used.add(banner.slug);
  const top = take(byPts);
  const smash = take([...d.smashed].sort((a, b) => b.diff - a.diff));
  const dud = take([...d.busts].sort((a, b) => a.diff - b.diff));
  const hurt = take([...d.left].sort((a, b) => dgOutRank(b.later) - dgOutRank(a.later) || (b.proj || 0) - (a.proj || 0)));
  const proj = r => [t("digest.tile.proj", {n: r.proj.toFixed(1)}), dgStatLine(r)].filter(Boolean).join(" · ");
  const tiles = [
    top && dgTile("", banner ? t("digest.tile.second") : t("digest.tile.top"), top, top.actual.toFixed(1), dgStatLine(top)),
    smash && dgTile("up", t("digest.tile.smash"), smash, smash.actual.toFixed(1), proj(smash)),
    dud && dgTile("dn", t("digest.tile.dud"), dud, dud.actual.toFixed(1), proj(dud)),
    hurt && dgTile("hurt", t("digest.tile.hurt"), hurt, dgOutPill(hurt.later) || dgPill(t("digest.res.leftEarly")),
      hurt.actual != null && hurt.proj != null
        ? t("digest.tile.hurtSub", {injury: esc(dgCap(hurt.injury || "")), a: hurt.actual.toFixed(1), p: hurt.proj.toFixed(1)})
        : esc(dgCap(hurt.injury || "")))];
  const html = tiles.filter(Boolean).join("");
  return html ? `<div class="dg-tiles">${html}</div>` : "";
}

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
