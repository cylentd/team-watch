/* ============================== DIGEST: WHAT'S AHEAD ==============================
   Top 5 and Weather, the two topics that look forward, each reading the view that owns it
   (2026-09-29, storyboard https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz, 5A and 6A). Neither waits
   on the week's digest any more: the page already carries next week's projections and forecasts.
   data/digest.js dgTop5 and dgWxMoves pick the rows. */

/* One ranked row: place, name over his game, an injury tag, the tier, the projection. FLEX names the
   position before the game. Opens the profile. */
function dgT5Row(r, i, flex){
  const inj = r.inj ? `<span class="dg-rk-inj ${r.inj === "Q" ? "q" : "d"}">${r.inj === "Q" ? t("digest.t5.q") : t("digest.t5.d")}</span>` : "";
  const tier = r.tier ? `<span class="dg-rk-tier">${t("digest.t5.tier", {n: r.tier})}</span>` : "";
  return `<button type="button" class="dg-rk" data-dgslug="${esc(r.slug)}"><span class="dg-rk-n">${i + 1}</span>
    <span class="dg-rk-t"><b>${esc(nameInitial(r.n))}${inj}</b><span>${flex ? esc(r.pos) + " · " : ""}${dgVs(r)}</span></span>
    ${tier}<span class="dg-rk-p">${r.pts.toFixed(1)}</span></button>`;
}

function dgTop5Body(d){
  const tabs = DG_T5_POS.map(pos => {
    const rows = dgTop5(d, pos);
    return rows.length ? {key: pos, label: pos === "FLEX" ? t("digest.t5.flex") : pos,
      body: `<div class="dg-rks">${rows.map((r, i) => dgT5Row(r, i, pos === "FLEX")).join("")}</div>`} : null;
  }).filter(Boolean);
  const week = typeof LIVE_RANKS !== "undefined" && LIVE_RANKS && LIVE_RANKS.week;
  return dgTabsHTML("t5", tabs)
    + dgFootHTML(week ? t("digest.foot.t5Week", {week}) : t("digest.foot.t5"), "ranks", t("digest.go.ranks"));
}

/* One game whose weather moves scoring: the matchup over its kickoff, the reading at the right. */
function dgWxRow(r){
  const c = dgWxCond(r), fc = r.fc || {};
  const num = c === "wind" ? t("digest.wx.mph", {n: Math.round(r.mph)}) : c === "precip" ? t("digest.wx.pct", {n: fc.precip_pct})
    : t("digest.lead.wx.temp", {f: fc.temp_f});
  return `<div class="dg-wx">${c === "wind" ? DG_WIND : DG_RAIN}
    <span class="dg-ln-t"><b>${esc(r.g.away)} @ ${esc(r.g.home)}</b><span>${wtKick(r.g.kickoff)}</span></span>
    <span class="dg-ln-r">${num}</span></div>`;
}

function dgWxBody(){
  return dgWxMoves().map(dgWxRow).join("") + dgFootHTML(t("digest.foot.wxProven"), "weather", t("digest.go.weather"));
}
