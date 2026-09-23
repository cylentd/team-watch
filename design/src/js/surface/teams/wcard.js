/* One waiver card, in the order a phone reads it: tier and position, who he is, where he ranks,
   the swap he makes, why (two sentences), the proof, then one row per league he can be had in.
   The whole card is the tap target for the profile (panel.js wireProfiles, via data-wire).
   His name in the heading is full; every other name on the card is "B. Allen" (nameInitial). */
const wvSigned = v => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1);
/* Literal keys, so assemble.py's copy check sees every one. */
const WV_TIER = {
  must: () => t("waiver.tier.must"), worth: () => t("waiver.tier.worth"), watch: () => t("waiver.tier.watch"),
  spec: () => t("waiver.tier.spec"), stash: () => t("waiver.tier.stash"),
};
const WV_INJURY = {
  Q: () => t("waiver.injury.q"), D: () => t("waiver.injury.d"), O: () => t("waiver.injury.o"), IR: () => t("waiver.injury.ir"),
};
const WV_PRACTICE = {
  DNP: () => t("waiver.practice.dnp"), LP: () => t("waiver.practice.lp"), FP: () => t("waiver.practice.fp"),
};

const wvMarginHTML = m => `<b class="wvc-m ${m >= 0 ? "up" : "down"}">${t("waiver.unit.perWeek", {m: wvSigned(m)})}</b>`;

/* The headline: the best swap across his open leagues, else the need he fills, else nothing --
   a watch-list name has no swap yet, and a sentence saying so would be filler. */
function wvSwapHTML(r){
  const v = waiverBestVerdict(r);
  if (v && v.kind === "start")
    return t("waiver.swap.start", {over: esc(nameInitial(v.over)), slot: esc(v.slot), margin: wvMarginHTML(v.margin)});
  if (v) return t("waiver.swap.bench", {over: esc(nameInitial(v.over)), margin: wvMarginHTML(v.margin)});
  return waiverLeagues(r).some(([, lg]) => waiverOpen(lg) && lg.need) ? t("waiver.swap.need", {pos: esc(r.pos)}) : "";
}

function wvSummaryHTML(r){
  const s = r.summary;
  if (!s || !s.text) return "";
  const mark = s.src === "rule"
    ? ` <span class="wvc-rule" title="${t("waiver.summary.ruleTip")}">${t("waiver.summary.rule")}</span>` : "";
  return `<p class="wvc-sum">${esc(s.text)}${mark}</p>`;
}

function wvVerdictText(r, lg){
  const v = lg.verdict;
  if (v && v.kind === "start") return t("waiver.league.start", {over: esc(nameInitial(v.over)), slot: esc(v.slot)});
  if (v) return t("waiver.league.bench", {over: esc(nameInitial(v.over))});
  return lg.need ? t("waiver.league.need", {pos: esc(r.pos)}) : t("waiver.league.none");
}

function wvLeagueHTML(r, key, lg){
  const meta = waiverMeta()[key];
  const status = lg.status === "waiver"
    ? t("waiver.league.waiver", {when: waiverWhen(lg.clears || meta.clears) || ""}) : t("waiver.league.fa");
  const drop = lg.drop
    ? `<span class="wvl-drop">${t("waiver.league.drop", {name: esc(nameInitial(lg.drop.name)), pos: esc(lg.drop.pos)})}</span>` : "";
  return `<div class="wvl">
    <span class="wvl-lg"><i class="wvl-mark lg-${esc(key)}"></i><b>${esc(meta.label)}</b><span class="wvl-st">${status}</span></span>
    <span class="wvl-m">${lg.verdict ? wvMarginHTML(lg.verdict.margin) : ""}</span>
    <span class="wvl-v">${wvVerdictText(r, lg)}${drop}</span>
  </div>`;
}

/* Leagues where he is already on a roster fold into one grey line, mine named apart. */
function wvRosteredHTML(r){
  const all = waiverLeagues(r), meta = waiverMeta();
  const mine = all.filter(([, lg]) => lg.status === "mine").map(([k]) => esc(meta[k].label));
  const gone = all.filter(([, lg]) => lg.status === "rostered").map(([k]) => esc(meta[k].label));
  const parts = [gone.length ? t("waiver.league.rostered", {leagues: gone.join(", ")}) : "",
                 mine.length ? t("waiver.league.mine", {leagues: mine.join(", ")}) : ""].filter(Boolean);
  return parts.length ? `<p class="wvc-note">${parts.join(" · ")}</p>` : "";
}

/* Injury, practice and news on one line, only when there is any of it. */
function wvNewsHTML(r){
  const inj = WV_INJURY[r.injury];
  const hurt = inj ? inj() + (r.injury_note ? ` (${esc(r.injury_note)})` : "") : "";
  const prac = WV_PRACTICE[r.practice] ? WV_PRACTICE[r.practice]() : "";
  const news = r.news_count ? t("waiver.card.news", {n: r.news_count}) : "";
  const parts = [hurt, prac, news].filter(Boolean);
  if (!parts.length) return "";
  const tone = r.injury === "Q" ? "q" : r.injury ? "o" : "";
  const title = r.news_latest ? ` title="${esc(r.news_latest.headline)}"` : "";
  return `<p class="wvc-news ${tone}"${title}>${parts.join(" · ")}</p>`;
}

function wvCardHTML(r, i, n){
  const opp = !r.opp ? "" : r.home ? t("waiver.card.vs", {opp: esc(r.opp)}) : t("waiver.card.at", {opp: esc(r.opp)});
  const open = waiverLeagues(r).filter(([, lg]) => waiverOpen(lg));
  const swap = wvSwapHTML(r);
  return `<article class="wvc tier-${esc(r.tier)}" style="animation-delay:${60 + n * 55}ms" data-wire="${i}" role="button" tabindex="0">
    <div class="wvc-top"><span class="wvc-tier">${(WV_TIER[r.tier] || WV_TIER.watch)()}</span><span class="wvc-pos">${esc(r.pos)}</span></div>
    <div class="wvc-id"><div class="head">${headHTML(r)}</div>
      <div class="wvc-who"><b>${esc(r.n)}</b><span class="wvc-team">${esc(r.team)} ${opp}</span>${wvUsageRankHTML(r)}</div></div>
    ${swap ? `<p class="wvc-swap">${swap}</p>` : ""}
    ${wvSummaryHTML(r)}
    ${wvProofHTML(r)}
    ${open.length ? `<div class="wvc-leagues">${open.map(([k, lg]) => wvLeagueHTML(r, k, lg)).join("")}</div>` : ""}
    ${wvRosteredHTML(r)}
    ${wvNewsHTML(r)}
  </article>`;
}
