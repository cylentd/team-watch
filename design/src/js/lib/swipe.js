/* ------------------------------------------------------------------
   SWIPE — the page's two touch gestures, one definition each (2026-09-29).
   A sideways swipe turns to the next thing in a set the reader already pages with buttons: the
   Leaders card's stat, Preview's game, the profile's tab, the game sheet's game. A pull down from
   the top closes a sheet: the profile, search, the game sheet. One meaning per surface: a swipe on the
   view itself turns the top tab row (chrome/tabswipe.js, since 2026-10-06; it was "never a swipe
   between views" until then), and a touch that starts on one of these surfaces stays theirs.
   Board and Preview each carried their own copy of the arithmetic; the third caller made it this file.
------------------------------------------------------------------ */
const SWIPE_MIN = 48;      // px sideways before a drag is a swipe
const SWIPE_RATIO = 1.5;   // and this many times more sideways than down: a mostly-vertical drag is a scroll
const PULL_MIN = 96;       // px down, from the top of the sheet's scroll, before a pull closes it
const PULL_FOLLOW = .6;    // how far the sheet follows the finger: it lags, so it reads as weight

/* step(+1) on a swipe left (the next one), step(-1) on a swipe right. `skip(target, touch)` true means
   the touch began on something with its own drag (the radar, the orb sheet): that touch is left alone.
   `el` is marked data-ownswipe, so the tab swipe on the view around it leaves its touches alone. */
function onSwipeX(el, step, skip){
  let x0 = null, y0 = 0;
  el.dataset.ownswipe = "";
  el.addEventListener("touchstart", e => {
    const ok = e.touches.length === 1 && !(skip && skip(e.target, e.touches[0]));
    x0 = ok ? e.touches[0].clientX : null;
    y0 = ok ? e.touches[0].clientY : 0;
  }, {passive: true});
  el.addEventListener("touchend", e => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    x0 = null;
    if (Math.abs(dx) > SWIPE_MIN && Math.abs(dx) > SWIPE_RATIO * Math.abs(dy)) step(dx < 0 ? 1 : -1);
  });
  el.addEventListener("touchcancel", () => { x0 = null; });
}

/* A pull down closes `sheet`. The sheet follows the finger through --pull, which its CSS adds to its
   own transform, and springs back when let go short of PULL_MIN. A pull counts only from the top of
   the content (`atTop()`), so scrolling back up a long pane never closes it; `live(target)` false
   (the sheet is shut, or the touch began on something with its own drag) leaves the touch alone. */
function onPullDown(sheet, atTop, live, close){
  let y0 = null, x0 = 0, dy = 0;
  const reset = () => { sheet.classList.remove("pulling"); sheet.style.removeProperty("--pull"); y0 = null; dy = 0; };
  sheet.addEventListener("touchstart", e => {
    const ok = e.touches.length === 1 && live(e.target) && atTop();
    y0 = ok ? e.touches[0].clientY : null;
    x0 = ok ? e.touches[0].clientX : 0;
    dy = 0;
  }, {passive: true});
  sheet.addEventListener("touchmove", e => {
    if (y0 === null) return;
    const d = e.touches[0].clientY - y0, side = Math.abs(e.touches[0].clientX - x0);
    if (!dy){
      if (Math.max(Math.abs(d), side) < 8) return;          // too small yet to tell which way it goes
      if (d <= 0 || side > d){ reset(); return; }            // up or sideways first: a scroll or a swipe
    }
    dy = Math.max(0, d);                                     // back above the start: nothing to close
    if (!REDUCED()){ sheet.classList.add("pulling"); sheet.style.setProperty("--pull", `${Math.round(dy * PULL_FOLLOW)}px`); }
  }, {passive: true});
  sheet.addEventListener("touchend", () => {
    if (y0 === null) return;
    const shut = dy > PULL_MIN;
    reset();
    if (shut) close();
  });
  sheet.addEventListener("touchcancel", reset);
}
