/* ============================== DIGEST ==============================
   This week, the front page. Since 2026-10-06 (storyboard "Digest by Day", option B; STYLE.md "Answer
   first, research one tap away") each Pacific weekday is one job: the banner says the day's answer
   (lead.js, day.js), the day's cards hold the decision (card.js, row.js, cards/), and "Rest of the week"
   links the views that are not today's job (strip.js). Which cards and links a day has is data
   (data/digest.js DG_PLAN). Game-day state still wins once a game is on, as before: Right now (now.js),
   Tonight's card (tonight.js) and the last game's block (mnf.js).
   Superseded: the ticker of seven rows and the wall of open panels (2026-09-26 to 2026-10-06).
   The packet is ff-jarvis's (data/weekly_digest.json); the page computes nothing. */

const DG_ARROW = `<svg class="dg-arrow" data-testid="digest-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5"/></svg>`;
const DG_WIND = `<svg class="dg-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8h11a3 3 0 1 0-3-3M3 12h15a3 3 0 1 1-3 3M3 16h7"/></svg>`;
const DG_RAIN = `<svg class="dg-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 15a4 4 0 0 1 .5-8 5.5 5.5 0 0 1 10.3 1.5A3.5 3.5 0 0 1 17.5 15H7zM9 18l-1 3M13 18l-1 3M17 18l-1 3"/></svg>`;

/* The day's cards, in the plan's order, skipping the empty ones; Need to know when every one is empty.
   Right now leads them on a day whose plan does not place it (a Thursday or Monday game on). */
function dgCardsHTML(d, plan, now){
  const ctx = dgCardCtx(d, plan, now);
  const drawn = Object.fromEntries(dgCardOrder(plan).map(id => [id, dgCardDraw(id, ctx)]));
  const ids = dgCardList(plan, drawn);
  if (!(ids[0] in drawn)) drawn[ids[0]] = dgCardDraw(ids[0], ctx);
  const live = plan.cards.includes("now") ? "" : dgNowHTML();
  return live + ids.map(id => drawn[id]).join("");
}

function digestHTML(){
  // After the week's first kickoff the Digest shares Live's poll (now.js); before it, nothing is asked.
  // Asked after this render, not during it: the reply repaints the Digest, which must not render inside a render.
  if (dgKicked()) queueMicrotask(gdEnsure);
  const d = dgD(), now = Date.now(), plan = dgDayPlan(now);
  const lead = dgLeadHTML(), strip = dgStripHTML(plan);
  if (!d){
    DG_LAST = {lead, now: "", mnf: ""};
    DG_DRAWN = dgPhaseKey();
    return `<div class="dg" data-testid="digest-root">${lead}<p class="dg-none">${t("digest.empty.ticker")}</p>${strip}</div>`;
  }
  const mnf = dgMnfHTML();
  // The body's classes name which game-day parts it holds: tonight's card (or the last game's, mnf.js),
  // and Need to know left out once games are on and nothing in it is left to say.
  const cls = [d.tn.length || mnf ? "has-tn" : "", dgNeedEmpty(d) ? "no-need" : ""].filter(Boolean).join(" ");
  const cards = dgCardsHTML(d, plan, now);
  DG_LAST = {lead, now: dgNowHTML(), mnf};
  DG_DRAWN = dgPhaseKey();
  return `<div class="dg" data-testid="digest-root">${lead}
    <section class="dg-main${cls ? " " + cls : ""}" data-testid="digest-ticker" aria-label="${t("digest.ticker.label")}">${dgTonightHTML(d, mnf)}${cards}</section>${strip}</div>`;
}

function wireDigest(v){
  v.querySelectorAll("[data-dgneedall]").forEach(b => b.addEventListener("click", () => {
    const y = window.scrollY; DG_NEED_ALL = true; render(); window.scrollTo(0, y);
  }));
  // A foot's link, a card's "more" and the strip's chips: the view they name.
  v.querySelectorAll("[data-dggo]").forEach(b => b.addEventListener("click", () => {
    morphLogo(); navGo(b.dataset.dggo); window.scrollTo({top: 0});
  }));
  // The night game's card and its link: Preview, open on that game.
  v.querySelectorAll("[data-dgpv]").forEach(b => b.addEventListener("click", () => dgPreviewOpen(+b.dataset.dgpv)));
  // A row with research opens it in place, one at a time (row.js).
  const root = v.querySelector(".dg");
  v.querySelectorAll(".dg-r-b[data-dgr]").forEach(b => b.addEventListener("click", () => dgRowToggle(b, root)));
  // A live scorer, the touchdown count and the last game's link: one listener, so the parts a poll
  // repaints in place need no wiring (now.js).
  root?.addEventListener("click", dgLiveClick);
  const d = dgD();
  v.querySelectorAll("[data-dgslug]").forEach(el => el.addEventListener("click", () => {
    const slug = el.dataset.dgslug;
    const p = d && [...d.hurt, ...d.starters, ...d.best, ...d.adds].find(x => x.slug === slug);
    if (p) return openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, el);
    // A player need not be in any list above: search's index knows everyone on the page.
    const e = searchIndex().find(x => x.slug === slug);
    if (e) openProfile(searchPlayer(e), el);
  }));
}
