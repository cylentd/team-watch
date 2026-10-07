/* ============================== STATS' POSITION STRIP ==============================
   2026-10-06 (David picked "A Slide", storyboard https://claude.ai/artifact/G93YHzFMaUAHo1fvmMx3h7). On a
   phone the open Stats view's positions are one pill fixed above the bottom bar (#statspos, shell.html),
   where the thumb is, instead of chips at the view's top. A tap picks; a press that slides along the pill
   picks the segment under the finger as it moves, and the list redraws live (the feel prototype's mode
   "as"). One highlight slides between the segments. A desktop draws no strip: each view keeps its chips.

   Which positions a view has and which one it shows: data/statspos.js. The strip sits outside #view, so a
   render() mid-slide never rebuilds it under the finger; it is painted only when the view or its list
   changed, and otherwise only its pressed segment moves. DESIGN.md "Stats position strip". */

/* The views' top chips are a desktop's; a phone has the strip. */
const spChipsOn = () => !NAV_PHONE.matches;

/* A pick from the strip or from a view's own chip: Stats' one position. The next render draws it. */
function statsPick(pos){ STATS_POS = statsPosPick(STATS_POS, pos); }

/* Every render, before the view draws: the open view takes the position it shows for the shared one,
   then the strip is painted for it (or hidden, off Stats, on Highlights and on a desktop). */
function statsPosSync(){
  const d = STATS_VIEWS[SURFACE];
  const list = d ? statsPosList(SURFACE, d.opts ? d.opts() : {}) : [];
  const pos = statsPosShown(list, STATS_POS);
  if (pos) d.use(pos);
  spPaint(d, list, pos);
}

let SP_KEY = null;
function spPaint(d, list, pos){
  const el = document.getElementById("statspos"), on = NAV_PHONE.matches && list.length > 1;
  el.hidden = !on;
  document.body.classList.toggle("has-sp", on);
  const key = on ? `${SURFACE}|${list.join()}` : "";
  if (key !== SP_KEY){
    SP_KEY = key;
    el.innerHTML = on ? spHTML(d, list) : "";
    el.style.setProperty("--n", list.length);
  }
  if (!on) return;
  el.style.setProperty("--i", Math.max(0, list.indexOf(pos)));
  el.querySelectorAll("[data-spseg]").forEach(b => b.setAttribute("aria-pressed", b.dataset.spseg === pos));
}

/* One highlight under the segments, moved by --i; each segment carries its view's own attribute too
   (data-rkpos on Ranks), so a selector for the view's chip finds the segment on a phone. */
function spHTML(d, list){
  return `<i class="sp-hl" data-testid="stats-pos-hl" aria-hidden="true"></i>${list.map(p =>
    `<button type="button" class="sp-seg" data-testid="stats-pos-seg" data-spseg="${esc(p)}" data-${d.attr}="${esc(p)}" aria-pressed="false">${d.label(p)}</button>`).join("")}`;
}

/* The segment under a finger at x: the segments' own extent, so the pill's padding counts as its end segment. */
function spSegUnder(el, x){
  const segs = [...el.querySelectorAll("[data-spseg]")];
  if (!segs.length) return null;
  const a = segs[0].getBoundingClientRect(), z = segs[segs.length - 1].getBoundingClientRect();
  return segs[statsSegAt(x, a.left, z.right - a.left, segs.length)].dataset.spseg;
}

/* A new position is a new list, read from its top. The pressed one again does nothing. */
function spPick(pos){
  const on = document.querySelector("#statspos [aria-pressed='true']");
  if (!pos || (on && on.dataset.spseg === pos)) return;
  statsPick(pos);
  window.scrollTo(0, 0);
  render();
}

/* Bound once, at load: #statspos is in the shell, above the script. A press captures the pointer, so the
   slide keeps reporting to the strip wherever the finger goes; the click a tap ends with finds the segment
   already pressed and does nothing. A keyboard's Enter is a click on the segment. */
function wireStatsPos(){
  const el = document.getElementById("statspos");
  el.addEventListener("click", e => { const b = e.target.closest("[data-spseg]"); if (b) spPick(b.dataset.spseg); });
  el.addEventListener("pointerdown", e => {
    if (!e.isPrimary || e.button > 0 || !e.target.closest("[data-spseg]")) return;
    el.setPointerCapture(e.pointerId);
    spPick(spSegUnder(el, e.clientX));
  });
  el.addEventListener("pointermove", e => { if (el.hasPointerCapture(e.pointerId)) spPick(spSegUnder(el, e.clientX)); });
  // Crossing 760px swaps the strip and the views' top chips.
  NAV_PHONE.addEventListener("change", () => { if (STATS_VIEWS[SURFACE]) render(); });
}
wireStatsPos();
