/* ============================== MATCHUPS: RECORD AND LEAD ==============================
   The record strip comes first because it is the trust question: two thin bars, Pitcher List's
   and ours, through the last graded week, the higher score lime. Then the lead, the Digest's panel
   (component/lead.css) with the best spot at the position in it. Unlike the Digest's, this lead
   keeps its facts line: our rank beside the experts' is what the page is for. */

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
  const us = r.ours.score != null && r.pl.score != null && r.ours.score >= r.pl.score;
  const them = r.pl.score != null && !us;
  return `<div class="mu-rec" role="group" aria-label="${t("matchups.record.aria", {wk: r.through})}">
    <span class="mu-rec-l">${t("matchups.record.label")}<small>${t("matchups.record.weeks", {wk: muWeeks(r.weeks)})}</small></span>
    <span class="mu-rec-bars">${muBarHTML(t("matchups.record.pl"), r.pl, them)}${muBarHTML(t("matchups.record.ours"), r.ours, us)}</span>
  </div>`;
}

/* Up to `max` chips: what argues the call (green; the defense-vs-position one dashed, because the
   backtest found no such effect), then what argues against it (amber, "but ..."). */
function muEvidence(r, max){
  const pro = r.why.map(w => `<span class="mu-ev pro${w.k === "mx" ? " mx" : ""}">${esc(w.t)}</span>`);
  const con = r.but.map(w => `<span class="mu-ev con">${t("matchups.row.but", {why: esc(w.charAt(0).toLowerCase() + w.slice(1))})}</span>`);
  return [...pro, ...con].slice(0, max).join("");
}

/* "Start Jahmyr Gibbs": ours, the experts', the projection, the evidence, the photo, and a foot
   that says why this one leads. A position with no best spot says so and the calls follow. */
function muLeadHTML(pos){
  const b = muCalls(pos, "best")[0];
  if (!b) return `<article class="dg-lead mu-lead quiet"><div class="dg-lead-txt">
    <h2 class="dg-lead-h long">${t("matchups.lead.none", {pos})}</h2>
    <p class="dg-lead-fact">${t("matchups.lead.noneSub")}</p></div></article>`;
  const photo = dgPhotoHTML(b.slug), kick = muKick(b), chips = muEvidence(b, 3);
  const game = kick ? `${muVs(b)}, ${esc(kick)}` : muVs(b);
  return `<article class="dg-lead go mu-lead${photo ? " has-photo" : ""}">
    <div class="dg-lead-txt">
      <h2 class="dg-lead-h">${t("matchups.lead.head", {name: `<em class="dg-em go">${esc(b.n)}</em>`})}</h2>
      <p class="mu-facts"><span>${esc(pos)}${b.rank}<i>${t("matchups.lead.ours")}</i></span
        ><span>${b.ecr == null ? "—" : esc(pos) + b.ecr}<i>${t("matchups.lead.experts")}</i></span
        ><span>${b.pts.toFixed(1)}<i>${t("matchups.lead.pts")}</i></span></p>
      ${chips ? `<div class="mu-evs">${chips}</div>` : ""}
    </div>
    ${photo}
    <p class="mu-lead-why">${t("matchups.lead.why", {pos, game})}</p>
  </article>`;
}
