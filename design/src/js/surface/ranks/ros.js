/* ------------------------------------------------------------------
   RANKS > REST OF SEASON (2026-10-06; David picked storyboard option B, https://claude.ai/artifact/CH1bZ7HFWCZQPvUrRGAEAm:
   "A doesn't have enough space and shows a lot of numbers, which seems busy").

   Ranks has two views: This week (today's Ranks) and Rest of season, declared with navModes (data/tabrow.js) so a phone
   opens them in place in the Ranks pill and a desktop draws the bar below (.view-tabs). Rest of season is one chip row
   (QB RB WR TE), a bump chart of the top 10 at the position (rank by week, roschart.js), then a quiet list: rank, name and
   team, ROS points. Nothing else on a row. The numbers are ff-jarvis's (LIVE_ROS, data/ros.js); the page computes none.

   Absent without a file: no tab, and Ranks reads as it did. The position is Ranks' one setting (STYLE.md): FLEX, D/ST
   and K have no rest of season, so the list shows RB while RK_POS is one of them, and This week still has its pick.
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

function rosRowHTML(r, mine){
  return `<button type="button" class="ros-row${mine ? " mine" : ""}" data-testid="ros-row" data-rosopen="${esc(r.slug)}">
    <span class="rk-n" data-testid="ros-rank">${r.rank}</span>
    <span class="ros-nm"><span data-testid="ros-name">${esc(nameInitial(r.n))}</span><small data-testid="ros-team">${esc(r.team || "")}</small>${mine ? `<i class="rk-mine">${t("ranks.row.mine")}</i>` : ""}</span>
    <span class="ros-pts" data-testid="ros-pts">${Math.round(r.pts)}</span>
  </button>`;
}

function rosListHTML(rows, pos){
  const mine = rkMine();
  return `<section class="rk-group ros-group"><div class="ros-lh"><span>#</span><span>${esc(pos)}</span><span>${t("ros.list.pts")}</span></div>
    <div class="ros-rows">${rows.map(r => rosRowHTML(r, mine.has(r.slug))).join("")}</div></section>`;
}

function rosViewHTML(){
  const block = rosBlock(), pos = rosPos(), scoring = rosReaderScoring(block), rows = rosRows(block, pos, scoring);
  const span = {from: block.week, to: block.last_week};
  const sub = scoring === "espn" ? t("ros.head.subEspn", span) : t("ros.head.sub", span);
  // No heading: the tab says where he is, and the chart is the first data (STYLE.md, ~200px). One caption under the chart says
  // what the points are, with the way out to the schedule's strength at its end.
  const cap = `<div class="ros-cap"><p data-testid="ros-sub">${sub}</p>${rkSchedHTML()}</div>`;
  const body = !rows.length
    ? `<div class="state-empty" data-testid="ros-empty" style="min-height:220px"><div><b>${t("ros.empty.title", {pos: esc(pos)})}</b><span>${t("ros.empty.sub")}</span></div></div>`
    : `<div class="ros-bump" data-testid="ros-chart" data-pos="${esc(pos)}">${rosBumpHTML(rosChart(rows), pos, rosBox(window.innerWidth))}</div>
       ${cap}<div class="ros-list">${rosListHTML(rows, pos)}</div>`;
  return `<div class="wrap rk ros">${rkViewsHTML()}${rkChipsHTML(pos, [], ROS_POSITIONS)}${body}</div>`;
}

/* A row or a chart name opens the profile, which carries the Rest of season block. */
function wireRos(v){
  const block = rosBlock(), scoring = rosReaderScoring(block);
  const open = el => {
    const r = rosOne(block, el.dataset.rosopen, scoring);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  };
  v.querySelectorAll("[data-rosopen]").forEach(el => {
    el.addEventListener("click", () => open(el));
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(el); } });
  });
}
