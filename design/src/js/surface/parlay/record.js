/* THE PROP RECORD, the line at the top of Slips (2026-10-05, storyboard "Prop Picks" record strip; slimmed
   to one line the same day: the card was 117px tall and pushed the first game to 289px, over the 200px
   budget in design/STYLE.md). How each tier of the model's picks has done since week 1, graded every
   Tuesday by ff-jarvis (LIVE_PROPS_RECORD): "RECORD  Slight 55%  Confident 53%  Very 57%" in one button.
   A tap opens the detail under it: wins and losses big, the tier's name small, the hit rate small, and the
   weeks counted. It is closed until tapped. The same question as Start/Sit's record: does a tier hit more
   often than the tier below it? Absent (no file yet, or nothing graded) it draws nothing. */
const SL_REC_TIERS = ["slight", "confident", "very"];
const slRecName = k => k === "very" ? t("slips.record.very") : k === "confident" ? t("slips.record.confident") : t("slips.record.slight");
let SL_REC_OPEN = false;   // the detail under the line is open

/* Hit rate in whole percent, pushes and voids out; null before a graded pick. */
const slHitPct = c => c.w + c.l ? Math.round(100 * c.w / (c.w + c.l)) : null;

/* One tier in the line: its word, then its hit rate. */
function slRecItemHTML(k, c){
  const pct = slHitPct(c);
  return `<span class="pr-rq ${k}"><i>${slRecName(k)}</i>${pct === null ? "" : `<b>${pct}%</b>`}</span>`;
}

function slRecTileHTML(k, c){
  const pct = slHitPct(c);
  return `<div class="pr-rt ${k}"><b>${c.w}-${c.l}</b><span>${slRecName(k)}</span><small>${pct === null ? "" : pct + "%"}</small></div>`;
}

function slRecordHTML(){
  const r = typeof LIVE_PROPS_RECORD !== "undefined" ? LIVE_PROPS_RECORD : null;
  if (!r || !SL_REC_TIERS.some(k => r.tiers[k].w + r.tiers[k].l > 0)) return "";
  const wk = r.through_week;
  const line = SL_REC_TIERS.map(k => slRecItemHTML(k, r.tiers[k])).join(`<span class="pr-rec-d" aria-hidden="true">·</span>`);
  return `<section class="pr-rec" aria-label="${t("slips.record.aria", {n: wk})}">
    <button type="button" class="pr-rec-b" data-slrec aria-expanded="${SL_REC_OPEN}" aria-controls="pr-rec-more">
      <span class="pr-rec-l">${t("slips.record.label")}</span>${line}<span class="pr-rec-c" aria-hidden="true"></span>
    </button>
    <div class="pr-rec-more" id="pr-rec-more" ${SL_REC_OPEN ? "" : "hidden"}>
      <span class="pr-rec-s">${wk === 1 ? t("slips.record.week1") : t("slips.record.weeks", {n: wk})}</span>
      <div class="pr-rts">${SL_REC_TIERS.map(k => slRecTileHTML(k, r.tiers[k])).join("")}</div>
    </div>
  </section>`;
}

/* The line is a toggle. It flips the detail in place, so the page does not re-render under the reader. */
function wireSlRecord(v){
  v.querySelectorAll("[data-slrec]").forEach(b => b.addEventListener("click", () => {
    SL_REC_OPEN = !SL_REC_OPEN;
    b.setAttribute("aria-expanded", String(SL_REC_OPEN));
    const more = document.getElementById("pr-rec-more");
    if (more) more.hidden = !SL_REC_OPEN;
  }));
}
