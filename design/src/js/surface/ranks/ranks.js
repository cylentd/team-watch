/* ------------------------------------------------------------------
   RANKS — this week's ranking at a position, in tiers (2026-09-26, the storyboard's frame 3).

   The rank is the roster card's (LIVE_RANKS, design/ranks.py): projected half-PPR points, a player
   out this week left off. Tier lines are natural breaks in those points, so a line means the
   biggest drops in the list, not a round number. The row says who, the game, the points; a
   player on one of your rosters is marked, and a tap opens his profile.

   One row of controls, the positions and FLEX, so the list starts high on a phone. It scrolls:
   a ranking read top down is the one list here a reader expects to scroll.
------------------------------------------------------------------ */
const RK_POSITIONS = ["QB", "RB", "WR", "TE", "FLEX"];
let RK_POS = "RB";

const rkList = pos => !LIVE_RANKS ? [] : pos === "FLEX" ? LIVE_RANKS.flex : LIVE_RANKS.rows.filter(r => r.pos === pos);

/* Every player on the page's rosters, both leagues and a connected one. */
function rkMine(){
  const s = new Set();
  Object.values(TEAMS).forEach(tm => (tm.roster || []).forEach(p => p.slug && s.add(p.slug)));
  return s;
}

const rkGame = r => r.opp ? `${esc(r.team)} ${r.home === false ? "@" : "vs"} ${esc(r.opp)}` : esc(r.team || "");

function rkRowHTML(r, place, mine, flex){
  const inj = injFor({slug: r.slug});
  const tag = inj ? `<span class="rk-inj ${inj.s.toLowerCase()}" title="${injLabel(inj)}">${inj.s === "Q" ? t("teams.inj.q") : INJ_WORD[inj.s]()}</span>` : "";
  // On FLEX the position and its own rank lead the game line, the card's "RB3".
  const pos = flex ? `<b class="rk-pos">${esc(r.pos)}${r.rank}</b>` : "";
  return `<button type="button" class="rk-row${mine ? " mine" : ""}" data-rkopen="${esc(r.slug)}">
    <span class="rk-n">${place}</span>
    <span class="rk-who"><span class="rk-nm">${esc(nameInitial(r.n))}${mine ? `<i class="rk-mine">${t("ranks.row.mine")}</i>` : ""}</span>
      <span class="rk-game">${pos}${rkGame(r)}${tag}</span></span>
    <span class="rk-pts">${r.pts.toFixed(1)}</span>
  </button>`;
}

function ranksHTML(){
  const chips = `<div class="setrow" role="group" aria-label="${t("ranks.filter.position")}">
    ${RK_POSITIONS.map(p => `<button class="chip" data-rkpos="${p}" aria-pressed="${RK_POS === p}">${p === "FLEX" ? t("ranks.filter.flex") : p}</button>`).join("")}
  </div>`;
  const list = rkList(RK_POS);
  if (!list.length) return `<div class="wrap">${chips}<div class="state-empty" style="min-height:220px">
    <div><b>${t("ranks.empty.title")}</b><span>${t("ranks.empty.sub")}</span></div></div></div>`;
  const mine = rkMine(), flex = RK_POS === "FLEX";
  let tier = 0;
  const body = list.map((r, i) => {
    const head = r.tier !== tier ? `<div class="rk-tier" role="presentation"><span>${t("ranks.tier", {n: r.tier})}</span><i></i></div>` : "";
    tier = r.tier;
    return head + rkRowHTML(r, i + 1, mine.has(r.slug), flex);
  }).join("");
  return `<div class="wrap rk">
    ${chips}
    <div class="rk-list">${body}</div>
    <p class="note rk-foot">${t("ranks.foot", {scoring: esc(LIVE_RANKS.scoring || ""), through: esc(LIVE_RANKS.through || ""), n: list.length})}</p>
  </div>`;
}

function wireRanks(v){
  v.querySelectorAll("[data-rkpos]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.rkpos === RK_POS) return;
    RK_POS = b.dataset.rkpos; render();
  }));
  v.querySelectorAll("[data-rkopen]").forEach(el => el.addEventListener("click", () => {
    const r = rkList(RK_POS).find(x => x.slug === el.dataset.rkopen);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
