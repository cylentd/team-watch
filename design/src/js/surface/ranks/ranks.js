/* ------------------------------------------------------------------
   RANKS — this week's ranking at a position, in tiers (2026-09-26, the storyboard's frame 3).

   A glance page, not a research page: most readers come here and to Matchups and nowhere else.
   So a row carries only what moves a start/sit call -- the face, the game and when it kicks off,
   an injury tag, the projected points -- and the profile is one tap away for the rest. A desktop
   adds one column, what the points are made of, because it has the width and nothing else on the
   row says it.

   Data: LIVE_RANKS (design/ranks.py), one week only; a team whose next game is a later week is
   named in the heading instead of ranked on a number for a game outside it. Order, rank and tier are
   ff-jarvis's week_ranks lists (since 2026-10-08; `from` "week_ranks"), each tier drawn as its own panel,
   so the list needs no rule between tiers. With no such file (`from` "projections") the build cuts them
   itself, as before, and the back list keeps its "No line" tag and its note on the books' order.
------------------------------------------------------------------ */
const RK_POSITIONS = statsPosList("ranks");   // QB RB WR TE FLEX; D/ST and K are the league's (dst.js)
let RK_POS = "RB";

const rkList = pos => !LIVE_RANKS ? [] : pos === "FLEX" ? LIVE_RANKS.flex : LIVE_RANKS.rows.filter(r => r.pos === pos);

/* The reader's own players (2026-10-06, David: "Unselecting your team doesn't remove them from the MINE
   designation"): the rosters of the teams the switch lists as followed, and a league they connected
   (tsFollowed). It was every roster on the page but a leaguemate's, which marked David's three teams for
   every reader and never changed when one unfollowed or picked another. */
const rkMine = () => rosterSlugs(TEAMS, tsFollowed());

const rkKick = iso => kickFmt(iso);   // the page's one kickoff format (lib/kick.js)
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

/* The matchup, under the points (2026-09-29; it was the Matchups view): what this defense adds or
   takes against an average one, ff-jarvis's calibrated number. Part of it is already in the
   projection (`mxp`), and the tooltip says how much; ff-jarvis kept its own pricing because the
   full effect made the projection's error worse (METHODOLOGY 12.61). Beside the game it pushed the
   kickoff off a 360px row. Shown from half a point: 27 of 104 QB/RB/TE in week 4. Never on a WR. */
const RK_MX_MIN = .5;
const rkSigned = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1);
function rkMatchupHTML(r){
  if (r.mx == null || Math.abs(r.mx) < RK_MX_MIN) return "";
  const n = rkSigned(r.mx);
  const say = r.mxp == null ? t("ranks.row.mx", {n, opp: esc(r.opp || "")})
    : t("ranks.row.mxPriced", {n, opp: esc(r.opp || ""), p: rkSigned(r.mxp)});
  const tip = `${say} ${t("ranks.row.mxMark")}`;   // the failed test, in the tap text (2026-10-06)
  return `<span class="rk-mx ${r.mx > 0 ? "up" : "dn"}" data-testid="ranks-mx" title="${tip}" aria-label="${tip}">${n}</span>`;
}

/* Floor and ceiling under the projection (plan U5): ff-jarvis's band, from the row's own fields (the
   same two numbers LIVE_PROJECTIONS holds for him). Nothing for a row with no band. */
function rkRangeHTML(r){
  const g = rangeFrom(r);
  return g ? `<small class="rk-rng" title="${t("range.tip", {floor: g.floor.toFixed(1), ceil: g.ceil.toFixed(1)})}">${g.text}</small>` : "";
}

function rkRowHTML(r, place, mine, flex){
  const inj = r.inj ? `<span class="rk-inj ${r.inj.toLowerCase()}">${r.inj === "Q" ? t("ranks.inj.q") : t("ranks.inj.d")}</span>` : "";
  // On FLEX the position and its own rank lead the game line, the card's "RB3".
  const pos = flex ? `<b class="rk-pos" data-testid="ranks-row-pos">${esc(r.pos)}${r.rank}</b>` : "";
  return `<button type="button" class="rk-row${mine ? " mine" : ""}" data-testid="ranks-row" data-rkopen="${esc(r.slug)}">
    <span class="rk-n">${place}</span>
    <span class="rk-face">${avatarHTML(r)}</span>
    <span class="rk-who"><span class="rk-nm">${esc(nameInitial(r.n))}${mine ? `<i class="rk-mine">${t("ranks.row.mine")}</i>` : ""}</span>
      <span class="rk-game">${pos}<span>${rkGame(r)}</span>${inj}${rbNoLineHTML(r, "rk-noline")}</span></span>
    <span class="rk-mu">${rkMakeup(r)}</span>
    <span class="rk-pts" data-testid="ranks-pts">${r.pts.toFixed(1)}${rkRangeHTML(r)}${rkMatchupHTML(r)}</span>
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
    const {hi, lo} = rbTierSpan(g.rows.map(([r]) => r));   // a back's tier follows the books, so its edge rows need not hold its extremes
    const k = last > 1 ? ((g.tier - 1) / (last - 1)).toFixed(2) : "0";
    return `<section class="rk-group" style="--k:${k}">
      <div class="rk-tier"><b data-testid="ranks-tier">${t("ranks.tier", {n: g.tier})}</b><span>${hi === lo ? t("ranks.tier.one", {pts: hi}) : t("ranks.tier.range", {hi, lo})}</span></div>
      ${g.rows.map(([r, place]) => rkRowHTML(r, place, mine.has(r.slug), flex)).join("")}
    </section>`;
  }).join("");
}

/* RK_POS is what the list draws: Stats' one position as Ranks shows it (data/statspos.js, 2026-10-06). */
const rkPosLabel = p => p === "FLEX" ? t("ranks.filter.flex") : p === "DST" ? t("ranks.filter.dst") : p;
statsPosView("ranks", {attr: "rkpos", label: rkPosLabel, use: p => { RK_POS = p; },
  opts: () => ({ros: rkView() === "ros", extra: dstTabs(rkDstBlock(), rkLeague())})});

/* The position row: QB RB WR TE FLEX, then D/ST and, in a Yahoo league, K (surface/ranks/dst.js, 2026-10-05).
   A desktop's only: a phone picks from the strip above the bottom bar (chrome/statspos.js, 2026-10-06). */
function rkChipsHTML(pos, extra, base = RK_POSITIONS){
  if (!spChipsOn()) return "";
  return `<div class="setrow" data-testid="ranks-pos-row" role="group" aria-label="${t("ranks.filter.position")}">
    ${[...base, ...extra].map(p => `<button class="chip" data-testid="ranks-pos-tab" data-rkpos="${p}" aria-pressed="${pos === p}">${rkPosLabel(p)}</button>`).join("")}
  </div>`;
}

/* Running backs only (2026-10-05, ff-jarvis METHODOLOGY 12.86 and 12.87), each said once per list and only when
   it shows on screen: why a back can sit above one with more points (the list follows the books), and what a
   "No line" tag means. */
function rkRbNotes(pos, list){
  // Only on the old cut (no week_ranks file): ff-jarvis's lists already hold the books' order and the reader sees one rank (2026-10-08).
  if (pos !== "RB" || LIVE_RANKS.from !== "projections") return "";
  const order = rbReordered(list) ? " " + t("ranks.rb.note") : "";
  const row = list.find(r => rbNoLine(r));
  return order + (row ? ` ${rbNoLineHTML(row, "rk-noline")} ${rbNoLine(row).tip}` : "");
}

function ranksHTML(){
  if (rkView() === "ros") return rosViewHTML();   // Rest of season (surface/ranks/ros.js)
  const block = rkDstBlock(), lg = rkLeague(), pos = dstPos(RK_POS, block, lg), extra = dstTabs(block, lg);
  const chips = rkViewsHTML() + rkChipsHTML(pos, extra);
  if (pos === "DST" || pos === "K") return rkDstHTML(chips, dstBoard(block, lg, pos, dstHeld(TEAMS, tsFollowed(), lg, pos)));
  const list = rkList(pos);
  if (!list.length) return `<div class="wrap">${chips}<div class="state-empty" style="min-height:220px">
    <div><b>${t("ranks.empty.title")}</b><span>${t("ranks.empty.sub")}</span></div></div></div>`;
  const posName = pos === "FLEX" ? t("ranks.filter.flex") : pos;
  const wk = schedWeek();
  const title = wk ? t("ranks.head.title", {week: wk, pos: posName}) : t("ranks.head.titleNoWeek", {pos: posName});
  const offLine = schedOffLine(LIVE_RANKS.off || []), off = offLine ? " " + offLine : "";
  // The band is said in words once per list, only when a row draws one (plan U5).
  const band = list.some(rangeFrom) ? " " + t("range.note") : "";
  const rb = rkRbNotes(pos, list);
  return `<div class="wrap rk">
    ${chips}
    <div class="rk-headline"><div><h2>${title}</h2><p data-testid="ranks-sub">${t("ranks.head.sub", {scoring: esc(LIVE_RANKS.scoring || "")})}${band}${rb}${off}</p></div>${rkSchedHTML()}</div>
    <div class="rk-list">${rkTiersHTML(list, pos === "FLEX")}</div>
  </div>`;
}

function wireRanks(v){
  v.querySelectorAll("[data-rkview]").forEach(b => b.addEventListener("click", () => rkSelectView(b.dataset.rkview)));
  if (rkView() === "ros") wireRos(v);
  v.querySelectorAll("[data-rkpos]").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.rkpos === RK_POS) return;
    statsPick(b.dataset.rkpos); render();
  }));
  v.querySelectorAll("[data-rkgo]").forEach(b => b.addEventListener("click", () => navGo(b.dataset.rkgo)));
  v.querySelectorAll("[data-rkopen]").forEach(el => el.addEventListener("click", () => {
    const r = rkList(RK_POS).find(x => x.slug === el.dataset.rkopen);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
