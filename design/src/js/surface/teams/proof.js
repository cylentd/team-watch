/* A waiver card's evidence: three usage stats chosen by position, each with his rank at the
   position that week and an arrow against the week before.

   Everything reads the Grid (USAGE, data/usage.js): the stat's label and format come from the
   grid's own `cols`, the rank is the profile sheet's rankAmong/rankText (surface/profile/facts.js),
   so a card and the sheet never disagree on how a rank or a tie is written. Each slot lists the
   stats it would like, best first; the first one the grid carries for that position is used. A
   route share lands here the week the producer adds one to the weekly grid, with no edit. */
const WV_PROOF = {
  RB: [["snap"], ["car_share", "car"], ["rz"]],
  WR: [["route_pct", "routes", "snap"], ["tgt_pct"], ["adot"]],
  TE: [["route_pct", "routes", "snap"], ["tgt_pct"], ["rz_tgt"]],
  QB: [["dropbacks", "att"], ["rush"], ["rz_att"]],
};

function wvCol(pos, want){
  const cols = (USAGE.cols && USAGE.cols[pos]) || [];
  for (const id of want){ const c = cols.find(x => x.id === id); if (c) return c; }
  return null;
}

/* The latest week the grid has, and the one before it: "this week" is the league's week, not
   his, so a player who sat out reads as no number rather than an older one passed off as new. */
function wvWeeks(){
  const w = (USAGE.weeks || []).slice().sort((a, b) => a - b);
  const now = USAGE.through || w[w.length - 1];
  return [now, w.filter(x => x < now).pop()];
}

function wvWeekValue(slug, id, wk){
  const r = USAGE.rows.find(x => x.slug === slug && x.wk === wk);
  const v = r ? r.v[id] : null;
  return v === undefined ? null : v;
}

/* His rank on one stat among his position that week, as the sheet writes it: "TE5", "TE5*". */
function wvWeekRank(pos, id, slug, wk){
  const by = {};
  USAGE.rows.forEach(r => {
    if (r.pos === pos && r.wk === wk && r.v[id] !== null && r.v[id] !== undefined) by[r.slug] = r.v[id];
  });
  const rk = rankAmong(by, slug);
  return rk ? rankText(pos, rk) : null;
}

function wvTrendHTML(now, before){
  if (now === null || before === null || before === undefined) return "";
  const d = now - before;
  if (Math.abs(d) < 0.05) return `<i class="wvp-t flat" title="${t("waiver.proof.flatTip")}">${t("waiver.proof.flat")}</i>`;
  return d > 0
    ? `<i class="wvp-t up" title="${t("waiver.proof.upTip")}">${t("waiver.proof.up")}</i>`
    : `<i class="wvp-t down" title="${t("waiver.proof.downTip")}">${t("waiver.proof.down")}</i>`;
}

/* The line under his name: where he ranks on the stat his position is sorted by in the Grid. */
function wvUsageRankHTML(r){
  if (typeof USAGE === "undefined" || !USAGE) return "";
  const id = USAGE.rankBy && USAGE.rankBy[r.pos];
  const col = id && wvCol(r.pos, [id]);
  const [wk] = wvWeeks();
  const rank = col && wvWeekRank(r.pos, col.id, r.slug, wk);
  return rank ? `<span class="wvc-urank">${t("waiver.card.usageRank", {rank, stat: esc(col.label), wk})}</span>` : "";
}

function wvProofHTML(r){
  if (typeof USAGE === "undefined" || !USAGE || !WV_PROOF[r.pos]) return "";
  const [wk, prev] = wvWeeks();
  const cells = WV_PROOF[r.pos].map(want => wvCol(r.pos, want)).filter(Boolean).map(c => {
    const now = wvWeekValue(r.slug, c.id, wk);
    const rank = now === null ? null : wvWeekRank(r.pos, c.id, r.slug, wk);
    return `<div class="wvp"><span class="wvp-l">${esc(c.label)}</span>
      <b>${usageFmt(now, c.fmt)}</b>
      <span class="wvp-r">${rank || t("waiver.proof.noRank")}${wvTrendHTML(now, prev === undefined ? null : wvWeekValue(r.slug, c.id, prev))}</span></div>`;
  });
  return cells.length ? `<div class="wvc-proof">${cells.join("")}</div>` : "";
}
