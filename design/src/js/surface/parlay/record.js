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

/* CLAUDE's row (2026-10-05, LIVE_CLAUDE_RECORD): how often Claude's frozen call hit where he took the model's
   side ("agrees", with the lime C badge) and where he took the other one ("alone"). Before a game is graded
   it says when the numbers start. No block (no ff-jarvis file) draws no row. It is part of the same button. */
const SL_REC_PAIR = ["agree", "alone"];
const slRecClaude = () => typeof LIVE_CLAUDE_RECORD !== "undefined" ? LIVE_CLAUDE_RECORD : null;
const slRecClaudeGraded = c => !!c && !!c.agree && !!c.alone && SL_REC_PAIR.some(k => c[k].w + c[k].l > 0);
const slRecClaudeName = k => k === "agree" ? t("slips.record.claude.agrees") : t("slips.record.claude.alone");

/* The lime C. Same look as the line sheet's Claude badge (round, display font, 800, on-lime); that CSS
   is not shared yet, so the look is copied in record.css (.pr-cb) -- dedupe once both are on main. */
const slRecClaudeBadge = () => `<em class="pr-cb" aria-hidden="true">${t("slips.record.claude.badge")}</em>`;

function slRecClaudeItemHTML(k, c){
  const pct = slHitPct(c[k]);
  return `<span class="pr-cq ${k}">${k === "agree" ? slRecClaudeBadge() : ""}<i>${slRecClaudeName(k)}</i>${pct === null ? "" : `<b>${pct}%</b>`}</span>`;
}

function slRecClaudeRowHTML(c){
  const body = slRecClaudeGraded(c)
    ? SL_REC_PAIR.map(k => slRecClaudeItemHTML(k, c)).join(`<span class="pr-rec-dot" aria-hidden="true">·</span>`)
    : `<span class="pr-rec-from">${t("slips.record.claude.from", {n: c.week + 1})}</span>`;
  return `<span class="pr-rec-r pr-rec-cl"><span class="pr-rec-l">${t("slips.record.claude.label")}</span>${body}</span>`;
}

function slRecClaudeTileHTML(k, c){
  const pct = slHitPct(c[k]);
  return `<div class="pr-ct ${k}"><b>${c[k].w}-${c[k].l}</b><span>${k === "agree" ? slRecClaudeBadge() : ""}${slRecClaudeName(k)}</span><small>${pct === null ? "" : pct + "%"}</small></div>`;
}

/* The opened detail for Claude: his own weeks line, then the pair of tiles. Nothing before a game is graded. */
function slRecClaudeMoreHTML(c){
  if (!slRecClaudeGraded(c)) return "";
  return `<span class="pr-rec-cs">${t("slips.record.claude.through", {n: c.through_week})}</span>
      <div class="pr-cts">${SL_REC_PAIR.map(k => slRecClaudeTileHTML(k, c)).join("")}</div>`;
}

function slRecordHTML(){
  const r = typeof LIVE_PROPS_RECORD !== "undefined" ? LIVE_PROPS_RECORD : null;
  if (!r || !SL_REC_TIERS.some(k => r.tiers[k].w + r.tiers[k].l > 0)) return "";
  const wk = r.through_week, c = slRecClaude();
  const line = SL_REC_TIERS.map(k => slRecItemHTML(k, r.tiers[k])).join(`<span class="pr-rec-d" aria-hidden="true">·</span>`);
  return `<section class="pr-rec" aria-label="${t("slips.record.aria", {n: wk})}">
    <button type="button" class="pr-rec-b" data-slrec aria-expanded="${SL_REC_OPEN}" aria-controls="pr-rec-more">
      <span class="pr-rec-r"><span class="pr-rec-l">${t("slips.record.label")}</span>${line}<span class="pr-rec-c" aria-hidden="true"></span></span>
      ${c ? slRecClaudeRowHTML(c) : ""}
    </button>
    <div class="pr-rec-more" id="pr-rec-more" ${SL_REC_OPEN ? "" : "hidden"}>
      <span class="pr-rec-s">${wk === 1 ? t("slips.record.week1") : t("slips.record.weeks", {n: wk})}</span>
      <div class="pr-rts">${SL_REC_TIERS.map(k => slRecTileHTML(k, r.tiers[k])).join("")}</div>
      ${c ? slRecClaudeMoreHTML(c) : ""}
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
