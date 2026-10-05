/* ============================== ROSTER: THE WEEK PLAYS RAIL ==============================
   One card per clip (LIVE_CLIPS, design/clips.py) of the starters who have any, in a rail the reader
   drags: native touch scroll, a mouse drag on a desktop, the next card showing past the edge so the
   rail says it goes on (STYLE.md allows this one sideways row, "Roster clips, 2026-10-05"). Best
   scorer first, each player's clips in data order. A clip that plays here wears a lime disc with a
   play triangle and opens the theater on it; one YouTube refuses on other sites wears a YouTube chip
   and is a plain link. A last card names the starters with no clip and opens their game's highlights.
   The header's "Play n" starts the theater on the first clip that plays.

   It sits above the "This week" list on a phone, and the list folds to its one row while the rail
   shows (brief.js, reelFolds) so the first starter does not drop. From 1100px the list is a column
   beside the rows and keeps its place, and the rail gets ‹ › when it overflows.

   From clipsheet.js and clipplayer.js: clipData, clipsOf, clipGameOf,
   clipWeekRow, clipCan, clipDur, clipTheaterOpen(items, i, el), clipYtUrl, clipYtChipHTML,
   clipThumbOf, clipWarm, clipNames. */

let REEL = {unfold: false};                       // the list shown anyway after "Show"
const REEL_DRAG = 5;                              // px a mouse moves before it is a drag and not a click
const REEL_PLAY = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5l12 7-12 7z"/></svg>`;
const reelDesk = () => window.matchMedia("(min-width:1100px)").matches;

/* The week the clips are of, from the data: schedWeek() is the week coming up. */
function reelWeek(){
  const wk = clipData().week;
  return Number.isInteger(wk) ? wk : null;
}

/* The starters with clips, best scorer first (a tie, or no points, keeps roster order). */
function reelCards(team){
  const cards = team.roster.filter(p => p.start && p.slug).map(p => ({p, clips: clipsOf(p.slug)}))
    .filter(c => c.clips.length)
    .map(c => ({...c, pts: clipWeekRow(c.p).pts}));
  return cards.sort((a, b) => (b.pts ?? -999) - (a.pts ?? -999));
}

/* One item per clip: [{c, p, ps}] in rail order, the theater's queue, so a card's index is its place.
   A clip credited to two starters (a touchdown pass) is one item at the first's place; `p` is that
   first player and `ps` every starter credited. */
function reelItems(cards){
  const by = new Map(), items = [];
  cards.forEach(card => card.clips.forEach(c => {
    const had = by.get(c.id);
    if (!had){ const it = {c, p: card.p, ps: [card.p]}; by.set(c.id, it); items.push(it); }
    else if (!had.ps.includes(card.p)) had.ps.push(card.p);
  }));
  return items;
}

/* null when nothing is on show. `ends` are the starters with no clip but a game video. */
function reelModel(team){
  const wk = reelWeek(), cards = wk === null ? [] : reelCards(team);
  if (!cards.length) return null;
  const items = reelItems(cards);
  const had = new Set(cards.map(c => c.p));
  const ends = team.roster.filter(p => p.start && !had.has(p) && clipGameOf(p.team));
  const play = items.filter(it => clipCan(it.c)).length;
  return {wk, items, ends, play, first: items.findIndex(it => clipCan(it.c))};
}

const reelShows = team => !!reelModel(team);
const reelFolds = team => !REEL.unfold && !reelDesk() && reelShows(team);
function reelUnfold(){ REEL.unfold = true; render(); }

/* The list's folded form, in brief.js's own done row: what is left to check, and the way to open it. */
function reelFoldHTML(team, open){
  return `<section class="brief done" aria-label="${t("teams.brief.title")}" data-bteam="${team.key}">
    <div class="brief-h"><h2>${t("teams.brief.title")}</h2><small>${t("teams.brief.count", {n: open, s: open === 1 ? "" : "s"})}</small>
    <button type="button" class="brief-act" data-briefunfold>${t("teams.brief.show")}</button></div></section>`;
}

/* A thumbnail is an external image in a box that has its shape already, so a slow or failed load
   moves nothing, and a failed one just shows the box. */
const reelImg = c => `<img src="${clipThumbOf(c)}" alt="" loading="lazy" decoding="async" draggable="false" onerror="this.hidden=true">`;

function reelCardHTML(x, i){
  const c = x.c;
  const can = clipCan(c);
  const thumb = `<span class="reel-thumb">${reelImg(c)}${can ? `<span class="reel-disc">${REEL_PLAY}</span>` : `<span class="reel-mark">${clipYtChipHTML()}</span>`}`
    + `${Number.isFinite(c.secs) ? `<b class="reel-dur">${clipDur(c.secs)}</b>` : ""}</span>`;
  const text = `<span class="reel-nm">${esc(clipNames(x))}</span><span class="reel-cap">${esc(c.title || "")}</span>`;
  return can
    ? `<button type="button" class="reel-card" data-reelplay="${i}">${thumb}${text}</button>`
    : `<a class="reel-card" href="${esc(clipYtUrl(c))}" target="_blank" rel="noopener" draggable="false"
        aria-label="${esc(t("teams.clips.opensYouTube", {title: c.title || ""}))}">${thumb}${text}</a>`;
}

/* The starters with no clip, and their game's highlights on YouTube (the first such game's). */
function reelEndHTML(ends){
  const names = ends.map(p => nameInitial(p.n)).join(", ");
  return `<a class="reel-card reel-end" href="${esc(clipYtUrl(clipGameOf(ends[0].team)))}" target="_blank" rel="noopener" draggable="false">
    <span class="reel-thumb"><b class="reel-no">${t("teams.clips.noClip")}</b>
    <span class="reel-endline">${esc(t("teams.clips.noClipLine", {names}))}</span><span class="reel-mark">${clipYtChipHTML()}</span></span></a>`;
}

function reelHTML(team){
  const m = reelModel(team);
  if (!m) return "";
  const n = m.items.length;
  return `<section class="reel" data-reel aria-label="${esc(t("teams.clips.title", {week: m.wk}))}">
    <div class="reel-h">
      <div class="reel-ti"><h2>${t("teams.clips.title", {week: m.wk})}</h2><small>${t("teams.clips.count", {n, s: n === 1 ? "" : "s"})}</small></div>
      ${m.play ? `<button type="button" class="reel-all" data-reelall>${REEL_PLAY}${t("teams.clips.playN", {n: m.play})}</button>` : ""}
      <button type="button" class="reel-arr" data-reelstep="-1" aria-label="${esc(t("teams.clips.prev"))}">&lsaquo;</button>
      <button type="button" class="reel-arr" data-reelstep="1" aria-label="${esc(t("teams.clips.next"))}">&rsaquo;</button>
    </div>
    <div class="reel-track">${m.items.map(reelCardHTML).join("")}${m.ends.length ? reelEndHTML(m.ends) : ""}</div>
  </section>`;
}

/* Whether the rail overflows (the arrows exist only then), and which arrows lead somewhere. */
function reelFit(box){
  if (!box) return;
  const track = box.querySelector(".reel-track"), room = track.scrollWidth - track.clientWidth;
  box.classList.toggle("fits", room <= 1);
  box.querySelector("[data-reelstep='-1']").disabled = track.scrollLeft <= 1;
  box.querySelector("[data-reelstep='1']").disabled = track.scrollLeft >= room - 1;
}

/* One card's width and a gap: what an arrow scrolls by. */
function reelStep(track, dir){
  const card = track.querySelector(".reel-card"), gap = parseFloat(getComputedStyle(track).columnGap) || 0;
  track.scrollBy({left: dir * (card.offsetWidth + gap), behavior: REDUCED() ? "auto" : "smooth"});
}

/* A mouse drags the rail like a finger does. Past REEL_DRAG px it is a drag, and the click that ends
   it opens nothing. */
function reelDrag(track){
  let x0 = null, s0 = 0, moved = false, ended = 0;
  track.addEventListener("pointerdown", e => {
    if (e.pointerType !== "mouse" || e.button) return;
    x0 = e.clientX; s0 = track.scrollLeft; moved = false;
  });
  track.addEventListener("pointermove", e => {
    if (x0 === null) return;
    const dx = e.clientX - x0;
    if (!moved){
      if (Math.abs(dx) < REEL_DRAG) return;
      moved = true;
      track.classList.add("drag");
      track.setPointerCapture(e.pointerId);
    }
    track.scrollLeft = s0 - dx;
  });
  const end = () => {
    if (x0 === null) return;
    x0 = null; track.classList.remove("drag");
    if (moved) ended = performance.now();
  };
  track.addEventListener("pointerup", end);
  track.addEventListener("pointercancel", end);
  track.addEventListener("click", e => {
    if (moved && performance.now() - ended < 400){ e.preventDefault(); e.stopPropagation(); }
  }, true);
}

function wireReel(v, team){
  const box = v.querySelector("[data-reel]"), m = reelModel(team);
  if (!box || !m) return;
  const track = box.querySelector(".reel-track");
  const open = (i, el) => clipTheaterOpen(m.items, i, el);
  track.addEventListener("click", e => {
    const b = e.target.closest("[data-reelplay]");
    if (b) open(+b.dataset.reelplay, b);
  });
  box.querySelector("[data-reelall]")?.addEventListener("click", e => open(m.first, e.currentTarget));
  box.querySelectorAll("[data-reelstep]").forEach(b => b.addEventListener("click", () => reelStep(track, +b.dataset.reelstep)));
  /* The first touch of the rail, or its first scroll, warms the player. Nothing is cued ahead of the tap:
     on real YouTube the cue swallows the loadVideoById the click sends, and the clip stays cued. */
  let warm = false;
  const wake = () => { if (!warm){ warm = true; clipWarm(); } };
  ["pointerdown", "touchstart", "scroll"].forEach(k => track.addEventListener(k, wake, {passive: true}));
  track.addEventListener("scroll", () => reelFit(box), {passive: true});
  reelDrag(track);
  reelFit(box);
}
window.addEventListener("resize", () => reelFit(document.querySelector("#view [data-reel]")));
