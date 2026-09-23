/* One waiver card, a trading card with two faces, for the league on screen (VIEW).
   Front decides: tier stamp, who he is, the swap and the drop in one line, the first sentence of
   the summary, three proof stats. Back is the evidence (wback.js). The flip button lies under the
   faces and covers the whole card; the faces let taps through (pointer-events), so a tap anywhere
   flips it, and only the back's "Full profile" button takes its own taps.
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

/* Why this league's screen listed him (`leagues[VIEW].lane`), as a tag under his name with the
   reason as its tooltip. No lane in this league, or an unknown one, draws nothing. Literal keys, so the copy check sees every one. */
const WV_LANE = {
  hole: () => [t("waiver.lane.hole"), t("waiver.lane.holeTip")],
  starter: () => [t("waiver.lane.starter"), t("waiver.lane.starterTip")],
  open: () => [t("waiver.lane.open"), t("waiver.lane.openTip")],
  usage: () => [t("waiver.lane.usage"), t("waiver.lane.usageTip")],
  role: () => [t("waiver.lane.role"), t("waiver.lane.roleTip")],
  insure: () => [t("waiver.lane.insure"), t("waiver.lane.insureTip")],
  injured: () => [t("waiver.lane.injured"), t("waiver.lane.injuredTip")],
};
function wvLaneHTML(lane){
  if (!WV_LANE[lane]) return "";
  const [word, tip] = WV_LANE[lane]();
  return `<span class="wvc-lane lane-${esc(lane)}" title="${esc(tip)}">${word}</span>`;
}

/* A section header's count, "Must claim · 1": a plain count, never zero-padded, so it cannot be
   read as a section number. */
const wvCountHTML = n => `<span class="count wv-count">${t("waiver.section.count", {n})}</span>`;

const wvMarginHTML = m => `<b class="wvc-m ${m >= 0 ? "up" : "down"}">${t("waiver.unit.perWeek", {m: wvSigned(m)})}</b>`;

/* What he does for this league's roster, then who goes: "Bench over H. Henry, +1.2/wk · drop
   K. Raymond". Nothing at all for a name with no swap yet; a sentence saying so is filler. */
function wvSwapHTML(r, lg){
  const v = lg.verdict;
  const swap = v && v.kind === "start"
    ? t("waiver.swap.start", {over: esc(nameInitial(v.over)), slot: esc(v.slot), margin: wvMarginHTML(v.margin)})
    : v ? t("waiver.swap.bench", {over: esc(nameInitial(v.over)), margin: wvMarginHTML(v.margin)})
    : lg.need ? t("waiver.swap.need", {pos: esc(r.pos)}) : "";
  if (!swap) return "";
  const drop = lg.drop ? `<span class="wvc-drop">${t("waiver.swap.drop", {name: esc(nameInitial(lg.drop.name))})}</span>` : "";
  return `<p class="wvc-swap">${swap}${drop}</p>`;
}

/* FA, or on waivers with the clear time: the one fact that says whether a claim is a bid. Also
   read by the rail for a drop. Anything but fa/waiver is unknown, and says so: never "FA". */
function wvStatusText(lg, key){
  if (lg.status === "fa") return t("waiver.card.fa");
  if (lg.status !== "waiver") return t("waiver.card.unknown");
  const when = waiverWhen(lg.clears || (waiverMeta()[key] || {}).clears);
  return when ? t("waiver.card.waiver", {when}) : t("waiver.card.waiverNoWhen");
}

/* The summary's first sentence. A period after a short word ("St.", "Jr.") is not an end. */
function wvFirstSentence(text){
  const m = /^(.+?(?:\b\w{3,}|\d|%|\))[.!?])\s+(?=[A-Z])/.exec(text || "");
  return m ? m[1] : text || "";
}

function wvFrontHTML(r, key, tier){
  const lg = r.leagues[key];
  const opp = !r.opp ? "" : r.home ? t("waiver.card.vs", {opp: esc(r.opp)}) : t("waiver.card.at", {opp: esc(r.opp)});
  const first = r.summary && r.summary.text ? `<p class="wvc-lede">${esc(wvFirstSentence(r.summary.text))}</p>` : "";
  return `<div class="wvc-face wvc-front">
    <div class="wvc-top"><span class="wvc-stamp">${(WV_TIER[tier] || WV_TIER.watch)()}</span>
      <span class="wvc-st">${esc(r.pos)} · ${wvStatusText(lg, key)}</span></div>
    <div class="wvc-id"><div class="head">${headHTML(r)}</div>
      <div class="wvc-who"><h3>${esc(r.n)}</h3><span class="wvc-team">${esc(r.team)} ${opp}</span>${wvUsageRankHTML(r)}${wvLaneHTML(lg.lane)}</div></div>
    ${wvSwapHTML(r, lg)}
    ${first}
    ${wvProofHTML(r)}
    <div class="wvc-foot" aria-hidden="true"><span></span><span class="wvc-turn">${t("waiver.card.turnFront")}</span></div>
  </div>`;
}

/* `n` is the card's place in the deal, so the cards land in rank order. */
function wvCardHTML(r, i, n, key){
  const tier = waiverTier(r, key);
  return `<article class="wvc tier-${esc(tier)}" style="--i:${n}">
    <button type="button" class="wvc-flip" aria-pressed="false" aria-label="${esc(t("waiver.card.flipLabel", {name: r.n}))}"></button>
    <div class="wvc-in">
      ${wvFrontHTML(r, key, tier)}
      ${wvBackHTML(r, i, key)}
    </div>
  </article>`;
}
