/* THE RECORD LINE at the top of Slips (2026-10-05; one "Our picks" record since 2026-10-08, ledger #33).
   One button: RECORD, then how our picks have done ("Our picks 58% · 7-5"), or before a graded game, the week
   the numbers start; under it the note that our pick is unproven until ff-jarvis's test (METHODOLOGY 12.84,
   restarted week 6). Our pick is a line where Claude and the model took the same side, so its record is
   ff-jarvis's `agree` tally (LIVE_CLAUDE_RECORD). A tap opens the detail: our picks' tile, then how each of
   the model's tier words has hit (LIVE_PROPS_RECORD), the record behind the word a pick wears. Before
   2026-10-08 the line was the three tiers and a second Claude row, "agrees" and "alone". No Claude block
   draws nothing. */
const SL_REC_TIERS = ["slight", "confident", "very"];
const slRecName = k => k === "very" ? t("slips.record.very") : k === "confident" ? t("slips.record.confident") : t("slips.record.slight");
let SL_REC_OPEN = false;   // the detail under the line is open

/* Hit rate in whole percent, pushes and voids out; null before a graded pick. */
const slHitPct = c => c.w + c.l ? Math.round(100 * c.w / (c.w + c.l)) : null;
const slRecOurs = () => typeof LIVE_CLAUDE_RECORD !== "undefined" ? LIVE_CLAUDE_RECORD : null;
const slRecGraded = c => !!c && !!c.agree && c.agree.w + c.agree.l > 0;

function slRecTileHTML(k, c, name){
  const pct = slHitPct(c);
  return `<div class="pr-rt ${k}"><b>${c.w}-${c.l}</b><span>${name}</span><small>${pct === null ? "" : pct + "%"}</small></div>`;
}

/* "Our picks 58% · 7-5", or "Our picks from week 6" before a graded game. */
function slRecLineHTML(c, more){
  const body = slRecGraded(c)
    ? `<b data-testid="parlay-record-pct">${slHitPct(c.agree)}%</b><span class="pr-rec-dot" aria-hidden="true">·</span><b>${c.agree.w}-${c.agree.l}</b>`
    : `<span class="pr-rec-from">${t("slips.record.from", {n: c.week + 1})}</span>`;
  return `<span class="pr-rec-r"><span class="pr-rec-l">${t("slips.record.label")}</span><span class="pr-oq"><i>${t("slips.record.ours")}</i>${body}</span>${more ? `<span class="pr-rec-c" aria-hidden="true"></span>` : ""}</span>`;
}

function slRecMoreHTML(c){
  const r = typeof LIVE_PROPS_RECORD !== "undefined" ? LIVE_PROPS_RECORD : null;
  const tiers = r && SL_REC_TIERS.some(k => r.tiers[k].w + r.tiers[k].l > 0);
  const ours = slRecGraded(c) ? `<span class="pr-rec-s">${t("slips.record.through", {n: c.through_week})}</span>
      <div class="pr-ots">${slRecTileHTML("ours", c.agree, t("slips.record.ours"))}</div>` : "";
  const byTier = tiers ? `<span class="pr-rec-s">${t("slips.record.tiers", {n: r.through_week})}</span>
      <div class="pr-rts">${SL_REC_TIERS.map(k => slRecTileHTML(k, r.tiers[k], slRecName(k))).join("")}</div>` : "";
  return ours + byTier;
}

function slRecordHTML(){
  const c = slRecOurs();
  if (!c) return "";
  const more = slRecMoreHTML(c);
  return `<section class="pr-rec" data-testid="parlay-record" aria-label="${t("slips.record.aria")}">
    <button type="button" class="pr-rec-b" data-slrec aria-expanded="${SL_REC_OPEN}" aria-controls="pr-rec-more"${more ? "" : " disabled"}>
      ${slRecLineHTML(c, !!more)}
      <span class="pr-rec-r pr-rec-note" data-testid="parlay-record-note">${t("slips.record.note")}</span>
    </button>
    ${more ? `<div class="pr-rec-more" id="pr-rec-more" ${SL_REC_OPEN ? "" : "hidden"}>${more}</div>` : ""}
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
