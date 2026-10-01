/* ============================== TAKES: RECORD AND EVIDENCE ==============================
   The record strip comes first because it is the trust question: two thin bars, Pitcher List's
   and ours, through the last graded week, the higher score lime. The best-spot lead that stood
   under it went on 2026-09-29: a matchup is a tag on the Ranks row now, not a page's headline. */

/* "DAL vs BAL" / "LAC @ BUF", the call's own club first. Pitcher List's rows sometimes carry no
   opponent (their column names no game); the team alone, never "vs null". */
const muVs = r => !r.opp ? esc(r.team) : r.home ? t("matchups.vs.home", {team: esc(r.team), opp: esc(r.opp)})
  : t("matchups.vs.away", {team: esc(r.team), opp: esc(r.opp)});

/* One source's bar: its label, a track filled to the score (0 to 1), the score with its own
   call count ("0.67 · 12 calls") so each bar says whose count it is. */
function muBarHTML(label, side, lead){
  const w = side.score == null ? 0 : Math.max(0, Math.min(1, side.score)) * 100;
  return `<span class="mu-rb${lead ? " lead" : ""}"><span>${label}</span><span class="mu-tr"><i style="--w:${w.toFixed(1)}%"></i></span
    ><em>${t("matchups.record.line", {score: muScore(side.score), n: side.n})}</em></span>`;
}

/* From week 4 the bars are v2's (METHODOLOGY 12.64): our takes and FantasyPros' other side, each
   on the clean set (a take an injury decided is left out: David, "that's just bad luck"), beside
   Pitcher List's own calls. Before a v2 week is graded the strip is v1's. No line says which
   (2026-09-30): the version is bookkeeping, not something a reader acts on. */
function muRecordHTML(){
  const r = LIVE_STARTSIT.record;
  if (!r) return `<div class="mu-rec none"><span class="mu-rec-l">${t("matchups.record.label")}</span>
    <span class="mu-rec-none">${t("matchups.record.none")}</span></div>`;
  const v = r.v2;
  const bars = v ? {pl: r.pl, fp: v.fp.clean, ours: v.ours.clean} : {pl: r.pl, fp: r.fp, ours: r.ours};
  const weeks = v ? r.weeks.filter(w => w >= 4) : r.weeks;
  // The best score is lime, ties to ours. FantasyPros is graded on our takes, the other side of each;
  // its bar is drawn only once ff-jarvis has graded that side.
  const sides = [["pl", t("matchups.record.pl")], ["fp", t("matchups.record.fp")], ["ours", t("matchups.record.ours")]]
    .filter(([k]) => bars[k]);
  const top = Math.max(...sides.map(([k]) => bars[k].score ?? -1));
  const lead = k => bars[k].score != null && bars[k].score === top && (k === "ours" || bars.ours.score !== top);
  return `<div class="mu-rec" role="group" aria-label="${t("matchups.record.aria", {wk: r.through})}">
    <span class="mu-rec-l">${t("matchups.record.label")}<small>${t("matchups.record.weeks", {wk: muWeeks(weeks.length ? weeks : r.weeks)})}</small></span>
    <span class="mu-rec-bars">${sides.map(([k, label]) => muBarHTML(label, bars[k], lead(k))).join("")}</span>
    <div class="mu-rec-f">${muSplitsToggle(r)}${muSplitsHTML(r)}</div>
  </div>`;
}

/* Claude's read of the graded week (ff-jarvis startsit_review, opus): a note, up to three patterns
   named with their counts, and up to three take types to watch with their own split numbers. Words
   about what happened, labelled as Claude's; it moves no rule. Absent draws nothing. */
function muReadHTML(v){
  const d = v.read;
  if (!d) return "";
  const pats = d.patterns.length ? `<ul class="mu-read-p">${d.patterns.map(p => `<li>${esc(p)}</li>`).join("")}</ul>` : "";
  const watch = d.watch.length ? `<p class="mu-read-h">${t("matchups.read.watch")}</p><ul class="mu-read-w">${d.watch.map(w => `<li>
      <span class="mu-read-t">${muTag(w.tag)} ${esc(w.pos)}${w.status === "paused" ? ` · ${t("matchups.read.paused")}` : ""}</span>
      <span class="mu-read-x">${esc(w.text)}</span>
      ${w.n ? `<em>${t("matchups.read.nums", {ours: muScore(w.ours), fp: muScore(w.fp), n: w.n})}</em>` : ""}</li>`).join("")}</ul>` : "";
  // Two groups, so a desktop pairs them side by side instead of stretching the note 1,000px wide.
  return `<div class="mu-read"><p class="mu-read-l">${t("matchups.read.label", {week: v.week})}</p>
    <div class="mu-read-a"><p class="mu-read-n">${esc(d.note)}</p>${pats}</div>${watch ? `<div class="mu-read-b">${watch}</div>` : ""}</div>`;
}

/* Last graded v2 week, take by take: the result, and for a miss its cause in plain words. A miss an
   injury decided says so and is marked as left out of the score. */
const MU_CAUSE = () => ({injury: t("matchups.review.injury"), role: t("matchups.review.role"),
  td: t("matchups.review.td"), read: t("matchups.review.read")});
function muReviewHTML(){
  const v = LIVE_STARTSIT.review;
  if (!v || !v.rows.length) return "";
  const res = s => s === 1 ? ["hit", t("matchups.review.hit")] : s === .5 ? ["close", t("matchups.review.close")] : ["miss", t("matchups.review.miss")];
  const rows = v.rows.map(r => {
    const [cls, word] = res(r.score), why = r.score === 1 ? "" : (MU_CAUSE()[r.cause] || "");
    return `<li class="mu-rv ${cls}${r.cause === "injury" ? " out" : ""}"><span class="mu-rv-r">${word}</span>
      <span class="mu-rv-n"><b>${esc(nameInitial(r.n))}</b> <i>${esc(r.pos)} · ${esc(muTag(r.call))}${r.backed ? "" : ` · ${t("matchups.row.gut")}`}</i></span>
      <span class="mu-rv-w">${why}${r.note ? ` <small>${esc(r.note)}</small>` : ""}</span></li>`;
  }).join("");
  return `<section class="mu-review"><h3 class="mu-grp">${t("matchups.review.title", {week: v.week})}</h3>${muReadHTML(v)}<ul class="mu-rvs">${rows}</ul></section>`;
}

/* Up to `max` chips: what argues the take (green), then what argues against it (amber, "but ..."). */
function muEvidence(r, max){
  const pro = r.why.map(w => `<span class="mu-ev pro">${esc(w.t)}</span>`);
  const con = r.but.map(w => `<span class="mu-ev con">${t("matchups.row.but", {why: esc(w.charAt(0).toLowerCase() + w.slice(1))})}</span>`);
  return [...pro, ...con].slice(0, max).join("");
}
