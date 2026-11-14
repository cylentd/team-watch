/* ------------------------------------------------------------------
   RANKS > BOOM AND BUST (2026-11-13; density redo the same day, STYLE.md "Density": David turned down a third
   line of odds on every row as "super compact and clutter").

   A chip row sorts the QB/RB/WR/TE list: Projection (the build's order, in tiers), Upside (boom high to low) or Safe
   (bust low to high). A row shows only the number its sort is about: Projection draws the row as it always was;
   Upside and Safe put the boom or bust percent where the points sit, and the points small under it, with no range and
   no matchup delta. Tiers are cut on points, so a sorted list is one panel with no tier labels.

   The explainer above the list is one line; its ⓘ opens the full definition in place. The numbers are ff-jarvis's
   (data/outcome.js); a list with none draws no chip row, and Projection's explainer stays. D/ST and K never reach
   here (dst.js). The sort and the open ⓘ are not kept between visits (navForget, 2026-10-09 ledger #91).
------------------------------------------------------------------ */
let RK_SORT = "pts", RK_MORE = false;
navForget("ranks", () => { RK_SORT = "pts"; RK_MORE = false; });

const rkSortOf = list => outcomeSorts(list).includes(RK_SORT) ? RK_SORT : "pts";
const rkSortName = id => id === "boom" ? t("ranks.sort.boom") : id === "bust" ? t("ranks.sort.bust") : t("ranks.sort.pts");

function rkSortsHTML(list){
  const ids = outcomeSorts(list), cur = rkSortOf(list);
  return ids.length < 2 ? "" : `<div class="setrow rk-sorts" data-testid="ranks-sort-row" role="group" aria-label="${t("ranks.sort.label")}">${
    ids.map(id => `<button type="button" class="chip" data-testid="ranks-sort" data-rksort="${id}" aria-pressed="${id === cur}">${rkSortName(id)}</button>`).join("")}</div>`;
}

/* Upside and Safe: the row's answer, "44% boom", with the projection small under it. A row without odds sorts last
   and keeps its points as the answer. */
function rkAnswerHTML(r, sort){
  const o = outcomeOf(r), pts = rkShown(r).toFixed(1);
  if (!o) return `<span class="rk-pts" data-testid="ranks-pts">${pts}</span>`;
  const word = sort === "boom" ? t("ranks.odds.boom") : t("ranks.odds.bust");
  return `<span class="rk-pts rk-ans" data-testid="ranks-pts"><span data-testid="ranks-${sort}">${t("ranks.odds.pct", {n: o[sort]})}</span><small class="rk-answ">${word}</small>
    <small class="rk-rng" data-testid="ranks-ans-pts">${t("ranks.odds.pts", {n: pts})}</small></span>`;
}

/* The bars for the position in view, the most common pair first (FLEX: RB and WR, then TE). Null without bars. */
function rkBars(list, pos){
  return outcomeBars(LIVE_RANKS.bars, pos === "FLEX" ? [...new Set(list.map(r => r.pos))] : [pos]);
}

/* The one line above the list: what the open sort puts first, with its bar ("Most likely to score 20+"). */
function rkShortLine(list, pos, sort, scoring){
  if (sort === "pts") return t("ranks.head.subShort", {scoring});
  const groups = rkBars(list, pos);
  if (!groups) return sort === "boom" ? t("ranks.head.subBoomBare") : t("ranks.head.subBustBare");
  const [main, ...rest] = groups;
  const line = sort === "boom" ? t("ranks.head.subBoom", {n: main.boom}) : t("ranks.head.subBust", {n: main.bust});
  if (!rest.length) return line;
  const others = rest.map(g => sort === "boom" ? t("ranks.head.otherBoom", {pos: g.pos.join(", "), n: g.boom})
    : t("ranks.head.otherBust", {pos: g.pos.join(", "), n: g.bust})).join(", ");
  return t("ranks.head.withOthers", {line, rest: others});
}

/* The full definition behind the ⓘ: Boom is his chance of 20+ points, bust of under 8. */
function rkOddsNote(list, pos){
  if (!list.some(outcomeHas)) return "";
  const groups = rkBars(list, pos);
  if (!groups) return "";
  const [main, ...rest] = groups;
  if (!rest.length) return t("ranks.odds.note", {boom: main.boom, bust: main.bust});
  const others = rest.map(g => t("ranks.odds.other", {pos: g.pos.join(", "), boom: g.boom, bust: g.bust})).join("; ");
  return t("ranks.odds.noteFlex", {boom: main.boom, bust: main.bust, rest: others});
}

/* The explainer: one line and its ⓘ, then the full definition, shown when the ⓘ is open. */
function rkExplainHTML(list, pos, sort, scoring, off){
  // Projection: the scoring, the tiers and the band. Upside and Safe: the bars, which name what a boom and a bust are.
  const head = sort === "pts" ? [t("ranks.head.sub", {scoring}), list.some(rangeFrom) ? t("range.note") : ""] : [rkOddsNote(list, pos)];
  const more = [...head, off].filter(Boolean).join(" "), line = rkShortLine(list, pos, sort, scoring);
  if (!more) return `<p class="rk-sub" data-testid="ranks-sub">${line}</p>`;
  return `<p class="rk-sub" data-testid="ranks-sub">${line}<button type="button" class="rk-info"
      data-testid="ranks-info" aria-expanded="${RK_MORE}" aria-controls="rk-more" aria-label="${t("ranks.head.info")}">ⓘ</button></p>
    <p class="rk-more" id="rk-more" data-testid="ranks-more"${RK_MORE ? "" : " hidden"}>${more}</p>`;
}

/* Upside and Safe: one panel, numbered by place in the sort. */
function rkSortedHTML(list, flex, sort){
  const mine = rkMine();
  return `<section class="rk-group rk-sorted" data-testid="ranks-sorted">${
    outcomeSort(list, sort).map((r, i) => rkRowHTML(r, i + 1, mine.has(r.slug), flex, sort)).join("")}</section>`;
}

function wireRkSorts(v){
  v.querySelectorAll("[data-rksort]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.rksort === RK_SORT) return;
    RK_SORT = b.dataset.rksort;
    render();
  }));
  v.querySelectorAll("[data-testid='ranks-info']").forEach(b => b.addEventListener("click", () => {
    RK_MORE = !RK_MORE;
    b.setAttribute("aria-expanded", String(RK_MORE));
    v.querySelector("#rk-more").hidden = !RK_MORE;
  }));
}
