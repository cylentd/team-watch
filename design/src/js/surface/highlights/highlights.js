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

/* A face cropped to the head, drawn at 150% as the Digest's are (the files are chest-up). */
const hlLineHTML = r => `<button type="button" class="hl-ln" data-hlopen="${esc(r.slug)}">
    <span class="hl-hd">${avatarHTML(r)}</span>
    <b class="hl-n">${esc(r.num || "")}</b>
    <span class="hl-t">${esc(r.line)}</span></button>`;

function hlViewHTML(){
  const H = typeof LIVE_HIGHLIGHTS !== "undefined" ? LIVE_HIGHLIGHTS : null;
  const sub = `<p>${t("highlights.head.sub")}</p>`;
  // No packet: the heading and what the tab is, then the wait, in the site's own empty state.
  if (!H || !H.views.length) return `<div class="wrap hl">
    <div class="hl-head"><h2>${t("nav.tab.highlights")}</h2>${sub}</div>
    <div class="state-empty" style="min-height:220px;margin-top:16px">
    <div><b>${t("highlights.empty.title")}</b><span>${t("highlights.empty.sub")}</span></div></div></div>`;
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
