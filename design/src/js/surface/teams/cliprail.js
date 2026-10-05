/* ============================== THE CLIP RAIL, SHARED ==============================
   The card, the header and the drag of the clip rail, for the two views that draw one: the Roster's
   Week plays (reel.js) and Live > TDs' TD clips (surface/live/tdclips.js, 2026-10-05). The card must stay
   identical in both, so it lives here once; each view decides which clips, in what order, and what the
   card's second line says.

   An item is {c: a clip, p: a player, ps: every player credited}; the rail's index is the theater's.
   A clip that plays here wears a lime disc and opens the theater (clipsheet.js); one YouTube refuses on
   other sites wears a YouTube chip and is a plain link. The header's "Play n" starts the theater on the
   first clip that plays; ‹ › exist from 1100px, where the rail overflows.

   From clipsheet.js and clipplayer.js: clipTheaterOpen(items, i, el), clipThumbOf, clipCan, clipDur,
   clipYtUrl, clipYtChipHTML, clipWarm, clipNames. */

const REEL_DRAG = 5;                              // px a mouse moves before it is a drag and not a click
const REEL_PLAY = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5l12 7-12 7z"/></svg>`;

/* A thumbnail is an external image in a box that has its shape already, so a slow or failed load
   moves nothing, and a failed one just shows the box. */
const reelImg = c => `<img src="${clipThumbOf(c)}" alt="" loading="lazy" decoding="async" draggable="false" onerror="this.hidden=true">`;

/* One card. `cap` is its second line (default: the clip's own title); the first names who is in it.
   The card carries its clip's id (data-clipid): Live's rail finds a card again by it after a repaint, and
   the theater gives focus back to it on close (clipsheet.js). */
function clipCardHTML(x, i, cap){
  const c = x.c, attrs = ` data-clipid="${esc(c.id)}"`;
  const can = clipCan(c);
  const thumb = `<span class="reel-thumb">${reelImg(c)}${can ? `<span class="reel-disc">${REEL_PLAY}</span>` : `<span class="reel-mark">${clipYtChipHTML()}</span>`}`
    + `${Number.isFinite(c.secs) ? `<b class="reel-dur">${clipDur(c.secs)}</b>` : ""}</span>`;
  const text = `<span class="reel-nm">${esc(clipNames(x))}</span><span class="reel-cap">${esc(cap === undefined ? c.title || "" : cap)}</span>`;
  return can
    ? `<button type="button" class="reel-card" data-reelplay="${i}"${attrs}>${thumb}${text}</button>`
    : `<a class="reel-card" href="${esc(clipYtUrl(c))}" target="_blank" rel="noopener" draggable="false"${attrs}
        aria-label="${esc(t("teams.clips.opensYouTube", {title: c.title || ""}))}">${thumb}${text}</a>`;
}

/* The header: title and count, the Play n pill when anything plays here, and the two arrows. */
function clipRailHeadHTML(title, count, play){
  return `<div class="reel-h">
      <div class="reel-ti"><h2>${esc(title)}</h2><small>${t("teams.clips.count", {n: count, s: count === 1 ? "" : "s"})}</small></div>
      ${play ? `<button type="button" class="reel-all" data-reelall>${REEL_PLAY}${t("teams.clips.playN", {n: play})}</button>` : ""}
      <button type="button" class="reel-arr" data-reelstep="-1" aria-label="${esc(t("teams.clips.prev"))}">&lsaquo;</button>
      <button type="button" class="reel-arr" data-reelstep="1" aria-label="${esc(t("teams.clips.next"))}">&rsaquo;</button>
    </div>`;
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

/* Wire one rail: a card opens the theater on its place in `items`, Play n on the first that plays
   (`first`), the arrows step, the drag works, and the first touch or scroll warms the player. Nothing
   is cued ahead of the tap: on real YouTube the cue swallows the loadVideoById the click sends, and
   the clip stays cued. Returns the track.
   A view whose card is not one clip passes `open(i, el)` for a card's tap (the Roster's card is a
   player and opens his clips only) and `step(track, dir)` for the arrows (the Roster turns a page). */
function clipRailWire(box, items, first, {open, step = reelStep} = {}){
  const track = box.querySelector(".reel-track");
  const play = (i, el) => clipTheaterOpen(items, i, el), card = open || play;
  track.addEventListener("click", e => {
    const b = e.target.closest("[data-reelplay]");
    if (b) card(+b.dataset.reelplay, b);
  });
  box.querySelector("[data-reelall]")?.addEventListener("click", e => play(first, e.currentTarget));
  box.querySelectorAll("[data-reelstep]").forEach(b => b.addEventListener("click", () => step(track, +b.dataset.reelstep)));
  let warm = false;
  const wake = () => { if (!warm){ warm = true; clipWarm(); } };
  ["pointerdown", "touchstart", "scroll"].forEach(k => track.addEventListener(k, wake, {passive: true}));
  track.addEventListener("scroll", () => reelFit(box), {passive: true});
  reelDrag(track);
  reelFit(box);
  return track;
}
window.addEventListener("resize", () => reelFit(document.querySelector("#view [data-reel]")));
