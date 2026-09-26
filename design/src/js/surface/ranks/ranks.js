/* ------------------------------------------------------------------
   RANKS — this week's ranking at a position, in tiers (2026-09-26, the storyboard's frame 3).

   A glance page, not a research page: most readers come here and to Matchups and nowhere else.
   So a row carries only what moves a start/sit call -- the face, the game and when it kicks off,
   an injury tag, the projected points -- and the profile is one tap away for the rest. A desktop
   adds one column, what the points are made of, because it has the width and nothing else on the
   row says it.

   Data: LIVE_RANKS (design/ranks.py), one week only; a team whose next game is a later week is
   named in the heading instead of ranked on a number for a game outside it. Tiers are natural
   breaks in the points, each drawn as its own panel, so the list needs no rule between tiers.
------------------------------------------------------------------ */
const RK_POSITIONS = ["QB", "RB", "WR", "TE", "FLEX"];
let RK_POS = "RB";

const rkList = pos => !LIVE_RANKS ? [] : pos === "FLEX" ? LIVE_RANKS.flex : LIVE_RANKS.rows.filter(r => r.pos === pos);

/* The reader's own players: his teams and a league he connected, never a leaguemate's roster
   (data/mates.js), which would mark most of the league as his. */
function rkMine(){
  const s = new Set();
  Object.values(TEAMS).filter(tm => !tm.mate).forEach(tm => (tm.roster || []).forEach(p => p.slug && s.add(p.slug)));
  return s;
}

const rkKick = iso => iso ? new Date(iso).toLocaleString([], {weekday: "short", hour: "numeric", minute: "2-digit"}) : "";
function rkGame(r){
  const vs = r.opp ? `${esc(r.team)} ${r.home === false ? "@" : "vs"} ${esc(r.opp)}` : esc(r.team || "");
  const when = rkKick(r.kick);
  return when ? `${vs} · ${when}` : vs;
}

/* The producer's own means, in the order a reader says them. */
function rkMakeup(r){
  const mu = r.mu || {}, n = (v, d) => v.toFixed(d);
  return [
    mu.PASS !== undefined ? t("ranks.mu.pass", {n: n(mu.PASS, 0)}) : "",
    mu.RUSH !== undefined && mu.RUSH >= 1 ? t("ranks.mu.rush", {n: n(mu.RUSH, 0)}) : "",
    mu.REC !== undefined && mu.REC >= 1 ? t("ranks.mu.rec", {n: n(mu.REC, 0)}) : "",
    mu.RECS !== undefined && mu.RECS >= .5 ? t("ranks.mu.recs", {n: n(mu.RECS, 1)}) : "",
    mu.TD !== undefined && r.pos !== "QB" ? t("ranks.mu.td", {n: n(mu.TD, 1)}) : "",
  ].filter(Boolean).join(" · ");
}

function rkRowHTML(r, place, mine, flex){
  const inj = r.inj ? `<span class="rk-inj ${r.inj.toLowerCase()}">${r.inj === "Q" ? t("ranks.inj.q") : t("ranks.inj.d")}</span>` : "";
  // On FLEX the position and its own rank lead the game line, the card's "RB3".
  const pos = flex ? `<b class="rk-pos">${esc(r.pos)}${r.rank}</b>` : "";
  return `<button type="button" class="rk-row${mine ? " mine" : ""}" data-rkopen="${esc(r.slug)}">
    <span class="rk-n">${place}</span>
    <span class="rk-face">${avatarHTML(r)}</span>
    <span class="rk-who"><span class="rk-nm">${esc(nameInitial(r.n))}${mine ? `<i class="rk-mine">${t("ranks.row.mine")}</i>` : ""}</span>
      <span class="rk-game">${pos}<span>${rkGame(r)}</span>${inj}</span></span>
    <span class="rk-mu">${rkMakeup(r)}</span>
    <span class="rk-pts">${r.pts.toFixed(1)}</span>
  </button>`;
}

/* Each tier is its own panel with its label and its points range; the label's fill steps down
   from lime at Tier 1, so how high a tier sits reads before its number does. */
function rkTiersHTML(list, flex){
  const mine = rkMine(), last = list[list.length - 1].tier || 1, groups = [];
  list.forEach((r, i) => {
    if (!groups.length || groups[groups.length - 1].tier !== r.tier) groups.push({tier: r.tier, rows: []});
    groups[groups.length - 1].rows.push([r, i + 1]);
  });
  return groups.map(g => {
    const hi = g.rows[0][0].pts.toFixed(1), lo = g.rows[g.rows.length - 1][0].pts.toFixed(1);
    const k = last > 1 ? ((g.tier - 1) / (last - 1)).toFixed(2) : "0";
    return `<section class="rk-group" style="--k:${k}">
      <div class="rk-tier"><b>${t("ranks.tier", {n: g.tier})}</b><span>${hi === lo ? t("ranks.tier.one", {pts: hi}) : t("ranks.tier.range", {hi, lo})}</span></div>
      ${g.rows.map(([r, place]) => rkRowHTML(r, place, mine.has(r.slug), flex)).join("")}
    </section>`;
  }).join("");
}

function ranksHTML(){
  const chips = `<div class="setrow" role="group" aria-label="${t("ranks.filter.position")}">
    ${RK_POSITIONS.map(p => `<button class="chip" data-rkpos="${p}" aria-pressed="${RK_POS === p}">${p === "FLEX" ? t("ranks.filter.flex") : p}</button>`).join("")}
  </div>`;
  const list = rkList(RK_POS);
  if (!list.length) return `<div class="wrap">${chips}<div class="state-empty" style="min-height:220px">
    <div><b>${t("ranks.empty.title")}</b><span>${t("ranks.empty.sub")}</span></div></div></div>`;
  const pos = RK_POS === "FLEX" ? t("ranks.filter.flex") : RK_POS;
  const title = LIVE_RANKS.week ? t("ranks.head.title", {week: LIVE_RANKS.week, pos}) : t("ranks.head.titleNoWeek", {pos});
  const off = (LIVE_RANKS.off || []).length ? " " + t("ranks.head.off", {teams: LIVE_RANKS.off.map(esc).join(", ")}) : "";
  return `<div class="wrap rk">
    ${chips}
    <div class="rk-headline"><h2>${title}</h2><p>${t("ranks.head.sub", {scoring: esc(LIVE_RANKS.scoring || "")})}${off}</p></div>
    <div class="rk-list">${rkTiersHTML(list, RK_POS === "FLEX")}</div>
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
