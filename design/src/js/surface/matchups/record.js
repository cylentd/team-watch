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

function muRecordHTML(){
  const r = LIVE_STARTSIT.record;
  if (!r) return `<div class="mu-rec none"><span class="mu-rec-l">${t("matchups.record.label")}</span>
    <span class="mu-rec-none">${t("matchups.record.none")}</span></div>`;
  // The best score is lime, ties to ours. FantasyPros' bar (2026-09-29) is graded on our takes, the
  // other side of each; it is drawn only once ff-jarvis has graded that side.
  const sides = [["pl", t("matchups.record.pl")], ["fp", t("matchups.record.fp")], ["ours", t("matchups.record.ours")]]
    .filter(([k]) => r[k]);
  const top = Math.max(...sides.map(([k]) => r[k].score ?? -1));
  const lead = k => r[k].score != null && r[k].score === top && (k === "ours" || r.ours.score !== top);
  return `<div class="mu-rec" role="group" aria-label="${t("matchups.record.aria", {wk: r.through})}">
    <span class="mu-rec-l">${t("matchups.record.label")}<small>${t("matchups.record.weeks", {wk: muWeeks(r.weeks)})}</small></span>
    <span class="mu-rec-bars">${sides.map(([k, label]) => muBarHTML(label, r[k], lead(k))).join("")}</span>
  </div>`;
}

/* Up to `max` chips: what argues the take (green), then what argues against it (amber, "but ..."). */
function muEvidence(r, max){
  const pro = r.why.map(w => `<span class="mu-ev pro">${esc(w.t)}</span>`);
  const con = r.but.map(w => `<span class="mu-ev con">${t("matchups.row.but", {why: esc(w.charAt(0).toLowerCase() + w.slice(1))})}</span>`);
  return [...pro, ...con].slice(0, max).join("");
}
