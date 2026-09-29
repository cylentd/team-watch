/* ------------------------------------------------------------------
   ROLE — Players > Role (leaf `movers`, 2026-09-29; storyboard
   https://claude.ai/artifact/DQK7e9SEqgdmLL8joh1fYu, option A). It replaced Movers' share cards:
   David, "target share is just half the story".

   One list, RB/WR/TE together, ranked by what each player's work is worth a game: an average
   player at his position with the same targets and carries (ff-jarvis role_board, the recap's own
   expected points). Beside it, what he scored, on one shared scale; under it, the work itself with
   his touchdowns next to his scoring chances; and last season's gap, which is what separates a
   player who is simply good (JSN) from a hot month.

   Descriptive only. METHODOLOGY 12.41 and 12.44: the gap does not beat our projection, so no row
   says buy or sell, and the rank -- the workload -- is the part that carries forward.
------------------------------------------------------------------ */
const RV_POSITIONS = ["ALL", "RB", "WR", "TE"];
let RV_POS = "ALL";
let RV_ALL = false;          // past the first RV_FIRST rows, on a tap
const RV_FIRST = 20;

const rvRows = () => !LIVE_ROLE ? [] : RV_POS === "ALL" ? LIVE_ROLE.rows : LIVE_ROLE.rows.filter(r => r.pos === RV_POS);
const rvNum = v => v == null ? "—" : Number(v).toFixed(1);
const rvSigned = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1);

/* The work, in the order a reader weighs it: a back's carries, a receiver's targets and how deep,
   then the scoring chances, then the touchdowns beside them -- so six touchdowns on 0.7 carries
   inside the 5 reads differently from six on 3. A null is left out, never printed as 0. */
function rvWork(r){
  const w = r.work || {}, n = (v, d = 1) => Number(v).toFixed(d), out = [];
  if (w.car_g != null && w.car_g >= 1) out.push(t("role.work.car", {n: n(w.car_g)}));
  if (w.tgt_g != null && w.tgt_g >= .5) out.push(t("role.work.tgt", {n: n(w.tgt_g)}));
  if (r.pos !== "RB" && w.air_g != null) out.push(t("role.work.air", {n: n(w.air_g, 0)}));
  if (w.gl_g != null && w.gl_g > 0) out.push(t("role.work.gl", {n: n(w.gl_g)}));
  else if (w.rz_g != null && w.rz_g > 0) out.push(t("role.work.rz", {n: n(w.rz_g)}));
  out.push(r.td === 1 ? t("role.work.tdOne") : t("role.work.td", {n: r.td}));
  return out.join(" · ");
}

/* Last season's same gap: the one number that says whether this season's is his normal. */
function rvPrev(r){
  if (!r.prev) return `<span class="rv-prev none">${t("role.prev.none", {season: (LIVE_ROLE.season || 0) - 1})}</span>`;
  const g = r.prev.gap;
  const s = r.prev.season, n = rvSigned(g);
  const say = Math.abs(g) < .5 ? t("role.prev.even", {season: s})
    : g > 0 ? t("role.prev.over", {season: s, n}) : t("role.prev.under", {season: s, n});
  return `<span class="rv-prev">${say}</span>`;
}

function rvRowHTML(r, top){
  const pct = v => (100 * Math.max(0, Math.min(v, top)) / top).toFixed(1) + "%";
  const dir = r.pts >= r.xfp ? "up" : "dn";
  const lo = Math.min(r.xfp, r.pts), hi = Math.max(r.xfp, r.pts);
  return `<button type="button" class="rv-row" data-rvopen="${esc(r.slug)}">
    <span class="rv-top"><span class="xf-head rv-face">${avatarHTML(r)}</span>
      <span class="rv-nm"><b>${esc(nameInitial(r.n))}</b><span class="rv-pos ${esc(r.pos.toLowerCase())}">${esc(r.pos)}</span></span>
      <span class="rv-v" aria-label="${t("role.row.aria", {x: rvNum(r.xfp), p: rvNum(r.pts)})}">${rvNum(r.xfp)}<small>→ ${rvNum(r.pts)}</small></span></span>
    <span class="rv-db ${dir}" aria-hidden="true" style="--lo:${pct(lo)};--hi:${pct(hi)};--x:${pct(r.xfp)};--p:${pct(r.pts)}"><i class="seg"></i><i class="x"></i><i class="p"></i></span>
    <span class="rv-work">${rvWork(r)}</span>
    ${rvPrev(r)}
  </button>`;
}

function rvViewHTML(){
  const chips = `<div class="setrow" role="group" aria-label="${t("role.filter.label")}">
    ${RV_POSITIONS.map(p => `<button class="chip" data-rvpos="${p}" aria-pressed="${RV_POS === p}">${p === "ALL" ? t("role.filter.all") : p}</button>`).join("")}
  </div>`;
  const rows = rvRows();
  if (!rows.length) return `<div class="wrap">${chips}<div class="state-empty" style="min-height:220px">
    <div><b>${t("role.empty.title")}</b><span>${t("role.empty.sub")}</span></div></div></div>`;
  // One scale for every row on screen, rounded up to 5 points, so two rows' dots compare.
  const top = Math.ceil(Math.max(...rows.map(r => Math.max(r.xfp, r.pts))) / 5) * 5;
  const shown = RV_ALL ? rows : rows.slice(0, RV_FIRST);
  const more = rows.length > shown.length
    ? `<button type="button" class="chip rv-more" data-rvmore>${t("role.more", {n: rows.length})}</button>` : "";
  return `<div class="wrap rv">
    ${chips}
    <div class="rv-head"><h2>${t("role.head.title", {wk: LIVE_ROLE.through})}</h2><p>${t("role.head.sub")}</p>
      <p class="rv-key"><span><i class="x"></i>${t("role.key.worth")}</span><span><i class="p"></i>${t("role.key.scored")}</span><span>${t("role.key.unit")}</span></p></div>
    <div class="rv-list">${shown.map(r => rvRowHTML(r, top)).join("")}</div>
    ${more}
    <p class="note rv-foot">${t("role.foot", {g: LIVE_ROLE.min_games})}</p>
  </div>`;
}

function wireRv(v){
  v.querySelectorAll("[data-rvpos]").forEach(b => b.addEventListener("click", () => {
    if (RV_POS === b.dataset.rvpos) return;
    RV_POS = b.dataset.rvpos; RV_ALL = false; render();
  }));
  v.querySelectorAll("[data-rvmore]").forEach(b => b.addEventListener("click", () => {
    const y = window.scrollY; RV_ALL = true; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-rvopen]").forEach(el => el.addEventListener("click", () => {
    const r = LIVE_ROLE.rows.find(x => x.slug === el.dataset.rvopen);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
