/* ------------------------------------------------------------------
   HIGHLIGHTS — Players > Highlights (leaf `highlights`, 2026-09-29; storyboard
   https://claude.ai/artifact/W5ty9RzT4XWSRfSjtdKEAk, option A). David: doing "the legwork for casuals
   who dont want to dive into the research in Players".

   Two lines from each Players view, in the tabs' order: Ranks, Leaders, Role, Grid. ff-jarvis's code
   finds the candidates in each view's own data, Claude words the two worth telling, and every number
   in a line is checked against its own candidate (model.season.highlights). One card per view; its
   heading is the way into the full view. A line opens the player's profile. The page computes nothing.
------------------------------------------------------------------ */

/* Every heading spelled out: assemble.py --check finds a copy key only as a literal lookup. */
const hlViewName = view => ({ranks: t("highlights.view.ranks"), leaders: t("highlights.view.leaders"),
  role: t("highlights.view.role"), grid: t("highlights.view.grid")})[view] || view;

/* Its own arrow: the Digest's DG_ARROW is styled in the Digest's fenced ticker.css. */
const HL_ARROW = `<svg class="hl-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5"/></svg>`;

/* The number's unit, from the line's kind (ff-jarvis's candidate id, `view.kind`). Every key spelled
   out for the same reason as above; an unknown kind draws no unit rather than a wrong one. */
const hlUnit = r => ({
  "ranks.jump": t("highlights.unit.jump"), "ranks.clear": t("highlights.unit.clear"), "ranks.top": t("highlights.unit.top"),
  "leaders.multi": t("highlights.unit.multi"), "leaders.axis": t("highlights.unit.axis", {pos: r.pos}),
  "role.over": t("highlights.unit.over"), "role.under": t("highlights.unit.under"), "role.work": t("highlights.unit.work"),
  "grid.tgt": t("highlights.unit.tgt"), "grid.snap": t("highlights.unit.snap"),
})[r.kind] || "";

/* Up is green and down is red, as everywhere on the page; a number with no sign is plain ink. */
const hlTone = num => /^\+/.test(num) ? " up" : /^[-−]/.test(num) ? " down" : "";

/* The Reel (storyboard https://claude.ai/artifact/Adzka79DUskrYurWBzhuvB, option A, David 2026-09-30):
   one card per line. The number is the headline beside the player on his club's colour, and the
   sentence runs the card's full width underneath. The whole card opens the profile. */
function hlLineHTML(r){
  const art = HEADS[r.slug] ? headImgHTML(HEADS[r.slug], initials(r.n), r.slug, 170) : `<div class="fallback">${esc(initials(r.n))}</div>`;
  const unit = hlUnit(r);
  return `<button type="button" class="hl-ln" data-hlopen="${esc(r.slug)}" ${teamColourStyle(r.team)}>
    <span class="hl-txt"><b class="hl-n${hlTone(r.num || "")}">${esc(r.num || "")}</b>${unit ? `<span class="hl-u">${esc(unit)}</span>` : ""}
    <span class="hl-nm">${esc(r.n)} <span class="hl-u">${esc(r.pos)} · ${esc(r.team)}</span></span></span>
    <span class="hl-art">${art}</span>
    <span class="hl-t">${esc(r.line)}</span></button>`;
}

function hlViewHTML(){
  const H = typeof LIVE_HIGHLIGHTS !== "undefined" ? LIVE_HIGHLIGHTS : null;
  const sub = `<p>${t("highlights.head.sub")}</p>`;
  // No packet, or one written for another week (schedIsPageWeek): the heading and what the tab is, then the wait.
  if (!H || !H.views.length || !schedIsPageWeek(H.week)) return `<div class="wrap hl">
    <div class="hl-head"><h2>${t("nav.tab.highlights")}</h2>${sub}</div>
    <div class="state-empty" style="min-height:220px;margin-top:16px">
    <div><b>${t("highlights.empty.title")}</b><span>${t("highlights.empty.sub")}</span></div></div></div>`;
  // One column of cards per view: stacked on a phone, side by side on a desktop.
  const cards = H.views.map(v => `<section class="hl-v" aria-labelledby="hl-h-${v.view}">
    <h3 id="hl-h-${v.view}"><button type="button" class="hl-go" data-hlgo="${v.leaf}">${hlViewName(v.view)}${HL_ARROW}</button></h3>
    ${v.rows.map(hlLineHTML).join("")}</section>`).join("");
  return `<div class="wrap hl">
    <div class="hl-head"><h2>${t("highlights.head.title", {week: H.week})}</h2>${sub}</div>
    <div class="hl-grid">${cards}</div>
  </div>`;
}

function wireHl(v){
  v.querySelectorAll("[data-hlgo]").forEach(b => b.addEventListener("click", () => {
    morphLogo(); navGo(b.dataset.hlgo); window.scrollTo({top: 0});
  }));
  v.querySelectorAll("[data-hlopen]").forEach(el => el.addEventListener("click", () => {
    const r = LIVE_HIGHLIGHTS.views.flatMap(x => x.rows).find(x => x.slug === el.dataset.hlopen);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
