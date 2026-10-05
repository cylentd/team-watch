/* THE PROP RECORD, the strip at the top of Slips (2026-10-05, storyboard "Prop Picks" record strip). How
   each tier of the model's picks has done since week 1, graded every Tuesday by ff-jarvis
   (LIVE_PROPS_RECORD): wins and losses big, the tier's name small, the hit rate small. The same shape
   as Start/Sit's record, and for the same question: does a tier hit more often than the tier below
   it? Nothing else on it. Absent (no file yet, or nothing graded) it draws nothing. */
const SL_REC_TIERS = ["slight", "confident", "very"];
const slRecName = k => k === "very" ? t("slips.record.very") : k === "confident" ? t("slips.record.confident") : t("slips.record.slight");

/* Hit rate in whole percent, pushes and voids out; null before a graded pick. */
const slHitPct = c => c.w + c.l ? Math.round(100 * c.w / (c.w + c.l)) : null;

function slRecTileHTML(k, c){
  const pct = slHitPct(c);
  return `<div class="pr-rt ${k}"><b>${c.w}-${c.l}</b><span>${slRecName(k)}</span><small>${pct === null ? "" : pct + "%"}</small></div>`;
}

function slRecordHTML(){
  const r = typeof LIVE_PROPS_RECORD !== "undefined" ? LIVE_PROPS_RECORD : null;
  if (!r || !SL_REC_TIERS.some(k => r.tiers[k].w + r.tiers[k].l > 0)) return "";
  const wk = r.through_week;
  return `<section class="pr-rec" aria-label="${t("slips.record.aria", {n: wk})}">
    <div class="pr-rec-h"><h3 class="pr-rec-l">${t("slips.record.label")}</h3>
      <span class="pr-rec-s">${wk === 1 ? t("slips.record.week1") : t("slips.record.weeks", {n: wk})}</span></div>
    <div class="pr-rts">${SL_REC_TIERS.map(k => slRecTileHTML(k, r.tiers[k])).join("")}</div>
  </section>`;
}
