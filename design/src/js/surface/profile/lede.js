/* The strip under the head: is he good, and how much does he play. Four numbers, one row, from
   LIVE_POOL (every player who logged a snap, watch's own numbers): his rank at his position by
   points per game, the points per game, his role share and his snap share.

   It replaced the three-number lede on 2026-09-28. The lede's projection and matchup now sit on the
   Season table's lime row, where they belong to a week, and its usage rank sits under the sphere
   in the head. What the lede never answered -- how good he has been -- is the first cell here.

   Numbers, never a word (DESIGN.md's market rule: the page prices nothing in verdicts). A cell with
   no source is left out, not dashed; the row is gone when none survives. */
function ledeCellHTML(value, label){
  return `<div class="pf-lede-c"><b>${value}</b><span class="pf-lede-l">${label}</span></div>`;
}

function poolRow(slug){
  return typeof LIVE_POOL !== "undefined" && LIVE_POOL ? LIVE_POOL.players.find(r => r.slug === slug) || null : null;
}

/* The share is the one pool.py plots for his position: carries for a back, targets for a
   receiver, and for a passer his snaps -- which the snap cell already says, so he gets no share. */
function ledeShareLabel(pos){
  return pos === "RB" ? t("profile.lede.carries") : pos === "WR" || pos === "TE" ? t("profile.lede.targets") : null;
}

const ledePct = v => v === null || v === undefined ? null : Math.round(v) + "%";

function ledeHTML(p, prof){
  const pos = prof ? prof.pos : p.pos;
  const row = poolRow(p.slug);
  const rk = ppgRank({slug: p.slug, pos});
  const share = ledeShareLabel(pos);
  const cells = [
    rk ? ledeCellHTML(rankText(pos, rk), t("profile.lede.rank")) : "",
    row && row.ppg !== null && row.ppg !== undefined ? ledeCellHTML(Number(row.ppg).toFixed(1), t("profile.lede.ppg")) : "",
    row && share && ledePct(row.share) ? ledeCellHTML(ledePct(row.share), share) : "",
    row && ledePct(row.snaps) ? ledeCellHTML(ledePct(row.snaps), t("profile.lede.snaps")) : "",
  ].join("");
  return cells ? `<div class="pf-lede">${cells}</div>` : "";
}
