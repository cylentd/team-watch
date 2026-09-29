/* ============================== TAKES: SPLITS AND THE PAUSE RULE ==============================
   ff-jarvis METHODOLOGY 12.64 Amendment 2 (2026-09-29). David: "keep track of our track record and
   try to improve it week to week". The record splits by call, position and confidence, each ours
   beside FantasyPros on the same takes; the rule that pauses a take type trailing them; and, in the
   list, one line where a paused type's takes would be. The page computes nothing: every number is
   ff-jarvis's (design/startsit.py). */

const MU_CHEV = `<svg class="mu-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>`;
const MU_SPLIT_LABEL = () => ({START: t("matchups.call.start"), SIT: t("matchups.call.sit"),
  QB: "QB", RB: "RB", WR: "WR", TE: "TE",
  lean: t("matchups.tier.lean"), solid: t("matchups.tier.solid"), strong: t("matchups.tier.strong")});

/* One row: the label, ours, FantasyPros', the count. The higher score is lime, as on the bars above
   (one meaning: which side scored better); a tie or an empty cell is plain. */
function muSplitRow(c){
  const has = c.n && c.ours != null && c.fp != null;
  const win = has && c.ours > c.fp ? "ours" : has && c.fp > c.ours ? "fp" : "";
  return `<tr${has ? "" : ` class="none"`}><th scope="row">${MU_SPLIT_LABEL()[c.k] || esc(c.k)}</th>
    <td${win === "ours" ? ` class="mu-lead"` : ""}>${has ? muScore(c.ours) : "—"}</td>
    <td${win === "fp" ? ` class="mu-lead"` : ""}>${has ? muScore(c.fp) : "—"}</td><td>${c.n || 0}</td></tr>`;
}

function muSplitGroup(title, rows){
  return `<tbody><tr class="mu-spg"><th scope="rowgroup" colspan="4">${title}</th></tr>${rows.map(muSplitRow).join("")}</tbody>`;
}

/* The rule, said once. While nothing is paused and the season is young it adds when the first
   pause could come: 40 graded takes of one type take until about week 11. */
function muRuleHTML(){
  const rule = LIVE_STARTSIT.rule;
  if (!rule || rule.min_n == null) return "";
  const soon = !rule.paused.length && LIVE_STARTSIT.week < 11 ? ` ${t("matchups.rule.soon")}` : "";
  return `<p class="mu-rule">${t("matchups.rule.text", {n: rule.min_n})}${soon}</p>`;
}

/* The button that sits on the record's last line, and the panel it opens in place. Reference
   detail, so it may wait behind a tap; the bars above stay the answer. */
function muSplitsToggle(r){
  if (!r.splits) return "";
  return `<button type="button" class="mu-sp-t" data-musplits aria-expanded="${MU_SPLITS}" aria-controls="mu-sp"
    >${t("matchups.splits.open")}${MU_CHEV}</button>`;
}

function muSplitsHTML(r){
  const s = r.splits;
  if (!s) return "";
  const weeks = s.set === "v2" ? r.weeks.filter(w => w >= 4) : r.weeks.filter(w => w < 4);
  const cap = s.set === "v2" ? t("matchups.splits.capV2", {wk: muWeeks(weeks.length ? weeks : r.weeks)})
    : t("matchups.splits.capV1", {wk: muWeeks(weeks.length ? weeks : r.weeks)});
  return `<div class="mu-sp" id="mu-sp"${MU_SPLITS ? " data-open" : ""}><div class="mu-sp-in"${MU_SPLITS ? "" : " inert"}><div class="mu-sp-pad">
    <table class="mu-spt"><caption>${cap}</caption>
      <thead><tr><td></td><th scope="col">${t("matchups.record.ours")}</th><th scope="col">${t("matchups.record.fp")}</th><th scope="col">${t("matchups.splits.n")}</th></tr></thead>
      ${muSplitGroup(t("matchups.splits.call"), s.by_call)}${muSplitGroup(t("matchups.splits.pos"), s.by_pos)}${muSplitGroup(t("matchups.splits.tier"), s.by_tier)}
    </table>${muRuleHTML()}</div></div></div>`;
}

/* Where a paused type's takes would be: one line with the numbers that paused it, and a tap that
   shows this week's shadow takes in place when there are any. */
function muPausedHTML(tag){
  return muPaused(tag).map(p => {
    const rows = muShadow(p.tag, p.pos), on = MU_SHADOW === p.type;
    const line = t("matchups.paused.line", {call: muTag(p.tag), pos: esc(p.pos), ours: muScore(p.ours), fp: muScore(p.fp), n: p.n ?? 0});
    if (!rows.length) return `<div class="mu-ps"><p class="mu-ps-h">${line}</p></div>`;
    const id = "mu-ps-" + p.type.replace(/[^\w-]/g, "");
    return `<div class="mu-ps" data-mups="${esc(p.type)}"${on ? " data-open" : ""}>
      <button type="button" class="mu-ps-h" aria-expanded="${on}" aria-controls="${id}"><span>${line}</span
        ><span class="mu-ps-n">${t("matchups.paused.see", {n: rows.length})}${MU_CHEV}</span></button>
      <div class="mu-ps-b" id="${id}"${on ? "" : " inert"}><div class="mu-ps-in">${rows.map(r => muCallHTML(r, "s:")).join("")}</div></div>
    </div>`;
  }).join("");
}

/* Both open in place on the house spring; the list is never redrawn under the reader. */
function wireMuSplits(v){
  const b = v.querySelector("[data-musplits]");
  if (b) b.addEventListener("click", () => {
    MU_SPLITS = !MU_SPLITS;
    b.setAttribute("aria-expanded", MU_SPLITS);
    const p = v.querySelector(".mu-sp");
    p.toggleAttribute("data-open", MU_SPLITS);
    p.querySelector(".mu-sp-in").inert = !MU_SPLITS;
  });
  v.querySelectorAll("[data-mups] > .mu-ps-h").forEach(h => h.addEventListener("click", () => {
    const type = h.parentElement.dataset.mups;
    MU_SHADOW = MU_SHADOW === type ? "" : type;
    v.querySelectorAll("[data-mups]").forEach(el => {
      const on = el.dataset.mups === MU_SHADOW;
      el.toggleAttribute("data-open", on);
      el.querySelector(".mu-ps-h").setAttribute("aria-expanded", on);
      el.querySelector(".mu-ps-b").inert = !on;
    });
  }));
}
