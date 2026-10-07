/* ------------------------------------------------------------------
   RANKS > REST OF SEASON (2026-10-06; David picked storyboard option B, https://claude.ai/artifact/CH1bZ7HFWCZQPvUrRGAEAm:
   "A doesn't have enough space and shows a lot of numbers, which seems busy").

   Ranks has two views: This week (today's Ranks) and Rest of season, declared with navModes (data/tabrow.js) so a phone
   opens them in place in the Ranks pill and a desktop draws the bar below (.view-tabs). Rest of season is one chip row
   (QB RB WR TE), a bump chart of the top 10 at the position (rank by week, roschart.js), then a quiet list: rank, name and
   team, ROS points. Nothing else on a row. The numbers are ff-jarvis's (LIVE_ROS, data/ros.js); the page computes none.

   Absent without a file: no tab, and Ranks reads as it did. The position is Stats' one setting (data/statspos.js, since
   2026-10-06): FLEX, D/ST and K have no rest of season, so the list shows the last of QB to TE the reader picked (RB
   before any) while the shared one is one of them, and This week still has its pick.
------------------------------------------------------------------ */
let RK_VIEW = "week";

const rkViews = () => rosBlock() ? ["week", "ros"] : ["week"];
const rkView = () => RK_VIEW === "ros" && rosBlock() ? "ros" : "week";
const rkViewName = id => id === "ros" ? t("ranks.view.ros") : t("ranks.view.week");
const rosPos = () => ROS_POSITIONS.includes(RK_POS) ? RK_POS : "RB";
/* ESPN's numbers for a team picked in the ESPN league, half-PPR for everyone else (data/ros.js rosScoring). */
const rosReaderScoring = block => rosScoring(!!lgMine(), lgFocusKey(), block);

function rkSelectView(id){
  if (id === rkView() || !rkViews().includes(id)) return;
  RK_VIEW = id;
  render();
  window.scrollTo({top: 0});
}
navModes("ranks", () => ({ids: rkViews(), cur: rkView(), attr: "rkview", name: t("ranks.views.label"), label: rkViewName, select: rkSelectView}));

/* The desktop's bar; "" with one view, and hidden on a phone, whose tab row holds the views. */
const rkViewsHTML = () => rkViews().length < 2 ? "" : `<div class="setrow rk-views view-tabs" role="group" aria-label="${t("ranks.views.label")}">${
  rkViews().map(id => `<button type="button" class="chip" data-testid="ranks-view-tab" data-rkview="${id}" aria-pressed="${id === rkView()}">${rkViewName(id)}</button>`).join("")}</div>`;

/* The span: the whole rest of season, or the fantasy playoff weeks (2026-10-07). Only a file with playoff numbers has the toggle. */
let ROS_SPAN = "ros";
const rosSpan = block => ROS_SPAN === "po" && rosHasPlayoffs(block) ? "po" : "ros";
const rosSpans = block => rosHasPlayoffs(block) ? ["ros", "po"] : ["ros"];
const rosSpanName = (id, block) => id === "po" ? t("ros.span.po", {from: block.po_weeks[0], to: block.po_weeks[block.po_weeks.length - 1]}) : t("ros.span.ros");

function rosSpanHTML(block){
  const ids = rosSpans(block), cur = rosSpan(block);
  return ids.length < 2 ? "" : `<div class="setrow ros-spans" role="group" aria-label="${t("ros.span.label")}">${
    ids.map(id => `<button type="button" class="chip" data-testid="ros-span" data-rosspan="${id}" aria-pressed="${id === cur}">${rosSpanName(id, block)}</button>`).join("")}</div>`;
}

/* FantasyPros' ROS position rank and the gap (theirs less ours; + = they have him lower), or an empty cell. */
function rosFpHTML(fp){
  if (!fp) return `<span class="ros-fp" data-testid="ros-fp"></span>`;
  const gap = fp.gap > 0 ? `+${fp.gap}` : fp.gap < 0 ? `−${-fp.gap}` : "0";
  const arg = {rank: fp.rank, n: Math.abs(fp.gap)};
  const tip = fp.gap > 0 ? t("ros.fp.below", arg) : fp.gap < 0 ? t("ros.fp.above", arg) : t("ros.fp.same", arg);
  return `<span class="ros-fp" data-testid="ros-fp" title="${esc(tip)}" aria-label="${esc(tip)}"><b>${fp.rank}</b><i>${gap}</i></span>`;
}

function rosRowHTML(r, mine, withFp){
  return `<button type="button" class="ros-row${mine ? " mine" : ""}${withFp ? " has-fp" : ""}" data-testid="ros-row" data-rosopen="${esc(r.slug)}">
    <span class="rk-n" data-testid="ros-rank">${r.rank ?? ""}</span>
    <span class="ros-nm"><span data-testid="ros-name">${esc(nameInitial(r.n))}</span><small data-testid="ros-team">${esc(r.team || "")}</small>${mine ? `<i class="rk-mine">${t("ranks.row.mine")}</i>` : ""}</span>
    ${withFp ? rosFpHTML(r.fp) : ""}<span class="ros-pts" data-testid="ros-pts">${r.pts == null ? "" : Math.round(r.pts)}</span>
  </button>`;
}

function rosListHTML(rows, pos, po){
  const mine = rkMine(), withFp = rows.some(r => r.fp);
  return `<section class="rk-group ros-group"><div class="ros-lh${withFp ? " has-fp" : ""}"><span>#</span><span>${esc(pos)}</span>${withFp ? `<span>${t("ros.list.fp")}</span>` : ""}<span>${po ? t("ros.list.ptsPo") : t("ros.list.pts")}</span></div>
    <div class="ros-rows">${rows.map(r => rosRowHTML(r, mine.has(r.slug), withFp)).join("")}</div></section>`;
}

function rosViewHTML(){
  const block = rosBlock(), pos = rosPos(), span = rosSpan(block), po = span === "po";
  const scoring = po ? "half" : rosReaderScoring(block), rows = rosRows(block, pos, scoring, span);
  const weeks = {from: block.week, to: block.last_week};
  const sub = po ? t("ros.cap.po", {from: block.po_weeks[0], to: block.po_weeks[block.po_weeks.length - 1]})
    : scoring === "espn" ? t("ros.head.subEspn", weeks) : t("ros.head.sub", weeks);
  const fpNote = !po && block.fp && rows.some(r => r.fp) ? `<p data-testid="ros-fp-note">${t("ros.cap.fp", {n: block.fp.experts})}</p>` : "";
  // No heading: the tab says where he is, and the chart is the first data (STYLE.md, ~200px). One caption under the chart says
  // what the points are, with the way out to the schedule's strength at its end. The playoff weeks have no chart: it is
  // rank by week of the whole rest of season.
  const cap = `<div class="ros-cap"><div><p data-testid="ros-sub">${sub}</p>${fpNote}</div>${rkSchedHTML()}</div>`;
  const chart = po ? "" : `<div class="ros-bump" data-testid="ros-chart" data-pos="${esc(pos)}">${rosBumpHTML(rosChart(rows), pos, rosBox(window.innerWidth))}</div>`;
  const body = !rows.length
    ? `<div class="state-empty" data-testid="ros-empty" style="min-height:220px"><div><b>${t("ros.empty.title", {pos: esc(pos)})}</b><span>${t("ros.empty.sub")}</span></div></div>`
    : `${chart}${cap}<div class="ros-list">${rosListHTML(rows, pos, po)}</div>`;
  return `<div class="wrap rk ros">${rkViewsHTML()}${rkChipsHTML(pos, [], ROS_POSITIONS)}${rosSpanHTML(block)}${body}</div>`;
}

/* A row or a chart name opens the profile, which carries the Rest of season block. */
function wireRos(v){
  const block = rosBlock(), scoring = rosReaderScoring(block);
  v.querySelectorAll("[data-rosspan]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.rosspan === rosSpan(block)) return;
    ROS_SPAN = b.dataset.rosspan;
    render();
  }));
  const open = el => {
    const r = rosOne(block, el.dataset.rosopen, scoring);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  };
  v.querySelectorAll("[data-rosopen]").forEach(el => {
    el.addEventListener("click", () => open(el));
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(el); } });
  });
}
