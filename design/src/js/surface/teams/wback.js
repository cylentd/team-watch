/* The back of a waiver card: the evidence behind the front's call. Each proof stat week by week,
   the full summary, the injury and the latest headline, one line for every other league, and the
   way into the full profile. Starts inert: wvFlip (wvmotion.js) swaps which face is live. */

function wvSummaryHTML(r){
  const s = r.summary;
  if (!s || !s.text) return "";
  const mark = s.src === "rule"
    ? ` <span class="wvc-rule" title="${t("waiver.summary.ruleTip")}">${t("waiver.summary.rule")}</span>` : "";
  return `<p class="wvc-sum">${esc(s.text)}${mark}</p>`;
}

/* Injury and practice on one line, the latest headline under it, only when there is any. */
function wvNewsHTML(r){
  const inj = WV_INJURY[r.injury];
  const hurt = inj ? inj() + (r.injury_note ? ` (${esc(r.injury_note)})` : "") : "";
  const prac = WV_PRACTICE[r.practice] ? WV_PRACTICE[r.practice]() : "";
  const status = [hurt, prac].filter(Boolean).join(" · ");
  const head = r.news_latest && r.news_latest.headline ? `<span class="wvc-hl">${esc(r.news_latest.headline)}</span>` : "";
  if (!status && !head) return "";
  const tone = r.injury === "Q" ? "q" : r.injury ? "o" : "";
  return `<p class="wvc-news">${status ? `<b class="${tone}">${status}</b>` : ""}${head}</p>`;
}

/* One other league in a few words: "Yahoo: rostered", "Yahoo: FA, bench over B. Allen +5.6". */
function wvOtherText(r, key, lg){
  const label = esc(waiverMeta()[key].label);
  if (lg.status === "mine") return t("waiver.other.mine", {league: label});
  if (lg.status === "rostered") return t("waiver.other.rostered", {league: label});
  if (!waiverOpen(lg)) return t("waiver.other.unknown", {league: label});
  const v = lg.verdict;
  const what = v && v.kind === "start" ? t("waiver.other.start", {over: esc(nameInitial(v.over)), slot: esc(v.slot), margin: wvMarginHTML(v.margin)})
    : v ? t("waiver.other.bench", {over: esc(nameInitial(v.over)), margin: wvMarginHTML(v.margin)})
    : lg.need ? t("waiver.other.need", {pos: esc(r.pos)}) : "";
  return (lg.status === "waiver" ? t("waiver.other.waiver", {league: label}) : t("waiver.other.fa", {league: label})) + what;
}

function wvOthersHTML(r, key){
  const rows = waiverLeagues(r).filter(([k]) => k !== key).map(([k, lg]) => wvOtherText(r, k, lg));
  return rows.length ? `<p class="wvc-other">${rows.join(" · ")}</p>` : "";
}

function wvBackHTML(r, i, key){
  return `<div class="wvc-face wvc-back" inert aria-hidden="true">
    <div class="wvc-top"><span class="wvc-bname">${esc(nameInitial(r.n))}</span>
      <span class="wvc-st">${t("waiver.card.backTitle")}</span></div>
    ${wvTrendsHTML(r)}
    ${wvSummaryHTML(r)}
    ${wvNewsHTML(r)}
    ${wvOthersHTML(r, key)}
    <div class="wvc-foot"><button type="button" class="btn ghost wvc-profile" data-wire="${i}">${t("waiver.card.profile")}</button>
      <span class="wvc-turn" aria-hidden="true">${t("waiver.card.turnBack")}</span></div>
  </div>`;
}
