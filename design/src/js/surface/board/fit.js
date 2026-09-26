/* ------------------------------------------------------------------
   THE BOARD — how many rows a page holds: as many as fit between the list's top and the bottom of
   the reader's screen, measured in his browser (2026-09-25; the whole list since 2026-09-26). A
   fixed count is a guess about a screen nobody has measured; this reads the real row, the real
   pager and the real bars.

   Measured at the top of the page, with every bar showing: on a phone the nav slides away while
   the reader scrolls down and comes back on the first scroll up (js/chrome/hidebar.js), so a page
   sized to the bars-hidden screen would lose its last rows under them.
------------------------------------------------------------------ */
const BD_FIT_MIN = 5, BD_FIT_MAX = 40;

// Fixed bars along the screen's bottom edge (the phone's nav), at their full height.
function bdBottomChromeH(){
  return [...document.querySelectorAll(".navbar, .modes-sub.dock")]
    .filter(el => getComputedStyle(el).position === "fixed" && el.offsetHeight && el.getBoundingClientRect().top > innerHeight / 2)
    .reduce((s, el) => s + el.offsetHeight, 0);
}

/* Rows that fit: from the first row's top (in page terms) to the screen's bottom, less the bottom
   bars and what the card holds under its rows (a pinned pick, the pager), in units of one row. */
function bdMeasureFit(){
  const card = document.querySelector(".bd-card");
  const rows = card ? [...card.querySelectorAll(".bd-list:not(.bd-pinned) > .bd-row")] : [];
  if (!rows.length) return null;
  const rowH = Math.max(...rows.map(r => r.offsetHeight));
  const top = rows[0].getBoundingClientRect().top + window.scrollY;
  const under = card.getBoundingClientRect().bottom - rows[rows.length - 1].getBoundingClientRect().bottom;
  // A pager that is not drawn yet (one page at the guessed size) will be once the list is cut.
  const pager = card.querySelector(".bd-pager") ? 0 : 56;
  const n = Math.floor((window.innerHeight - bdBottomChromeH() - top - under - pager - 8) / rowH);
  return Math.max(BD_FIT_MIN, Math.min(BD_FIT_MAX, n));
}

/* After a render: size the page on screen to the screen. Page 1 (under the hero) and the pages
   after it have their own counts, each set the first time it is shown. Renders again only when
   the count changes, so it settles in one pass. */
function bdFitPage(){
  const n = bdMeasureFit();
  const first = !!document.querySelector(".bd-card > .bd-hero");
  if (!n || n === (first ? BD_FIRST_SIZE : BD_PAGE_SIZE)) return;
  if (first) BD_FIRST_SIZE = n; else BD_PAGE_SIZE = n;
  render();
}
