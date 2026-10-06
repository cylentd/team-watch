/* The strip under the head: what do we expect, is he good, and how much does he play. Up to five numbers,
   one row (cells are data/lede.js ledeCells): this week's projection first, then, from LIVE_POOL (every
   player who logged a snap, watch's own numbers), his points per game, his rank at his position by them,
   his role share and his snap share.

   It replaced the three-number lede on 2026-09-28, which had the projection; that left for the Season
   table's lime row and the strip opened on "WR3 / 26.2 PPG", which the audit of 2026-10-05 found readers
   took for the projection. The projection is the headline again (plan U3), points per game second.

   Numbers, never a word (DESIGN.md's market rule: the page prices nothing in verdicts). A cell with
   no source is left out, not dashed; the row is gone when none survives. */
function ledeCellHTML(value, label, id, range){
  const rng = range ? `<small class="pf-lede-r" title="${t("range.tip", {floor: range.floor.toFixed(1), ceil: range.ceil.toFixed(1)})}">${range.text}</small>` : "";
  return `<div class="pf-lede-c${id === "proj" ? " proj" : ""}"><b>${value}</b><span class="pf-lede-l">${label}</span>${rng}</div>`;
}

function poolRow(slug){
  return typeof LIVE_POOL !== "undefined" && LIVE_POOL ? LIVE_POOL.players.find(r => r.slug === slug) || null : null;
}

/* The share is the one pool.py plots for his position: carries for a back, targets for a
   receiver, and for a passer his snaps -- which the snap cell already says, so he gets no share. */
function ledeShareId(pos){
  return pos === "RB" ? "carries" : pos === "WR" || pos === "TE" ? "targets" : null;
}

const ledePct = v => v === null || v === undefined ? null : Math.round(v) + "%";

function ledeHTML(p, prof){
  const pos = prof ? prof.pos : p.pos;
  const row = poolRow(p.slug);
  const rk = ppgRank({slug: p.slug, pos});
  const pts = projFor(p), out = projOut(p), done = projDone(p);
  const range = rangeFor(p);
  const cells = ledeCells({
    proj: pts === null && !out && !done ? null : {pts, out, done},
    ppg: row && row.ppg !== null && row.ppg !== undefined ? Number(row.ppg) : null,
    rank: rk ? rankText(pos, rk) : null,
    share: row && ledeShareId(pos) && ledePct(row.share) ? {id: ledeShareId(pos), pct: ledePct(row.share)} : null,
    snaps: row ? ledePct(row.snaps) : null,
    range,
  });
  const html = cells.map(c => ledeCellHTML(esc(c.value), c.label, c.id, c.range ? range : null)).join("");
  // The band is said in words once, under the strip, and only when a cell draws one (plan U5).
  const note = cells.some(c => c.range) ? `<p class="pf-lede-note">${t("range.note")}</p>` : "";
  return html ? `<div class="pf-lede">${html}</div>${note}` : "";
}
