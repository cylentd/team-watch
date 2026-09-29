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
  // The lowest row, not the last: from 1100px the page is two lists side by side. From 1100px the
  // #1 shares the lists' grid row and can stand taller than a short last page; that slack is not
  // under the rows, and counting it shrank the page, which grew the slack: a render loop (2026-09-29).
  const rowsBottom = Math.max(...rows.map(r => r.getBoundingClientRect().bottom));
  const hero = card.querySelector(":scope > .bd-hero");
  const slack = BD_WIDE.matches && hero ? Math.max(0, hero.getBoundingClientRect().bottom - rowsBottom) : 0;
  const under = card.getBoundingClientRect().bottom - rowsBottom - slack;
  const room = window.innerHeight - bdBottomChromeH() - top - under - 8;
  const fit = px => Math.max(BD_FIT_MIN, Math.min(BD_FIT_MAX, Math.floor(px / rowH))) * (BD_WIDE.matches ? 2 : 1);
  // No pager means every row is on screen. That stands if they fit without one; only a list that
  // must be cut reserves room for the pager it will then draw. Reserving it regardless shrank a
  // list that fitted, which drew the pager, which freed the room: a render loop (2026-09-27).
  const paged = !!card.querySelector(".bd-pager");
  if (!paged && rows.length <= fit(room)) return null;
  return fit(paged ? room : room - 56);
}

/* After a render: size the page on screen to the screen. Page 1 (under the hero) and the pages
   after it have their own counts, each set the first time it is shown. Renders again only when
   the count changes, so it settles in one pass. From 1100px every page has the #1 beside it, so
   one count serves both. */
function bdFitPage(){
  const n = bdMeasureFit();
  if (!n) return;
  if (BD_WIDE.matches){
    if (n === BD_FIRST_SIZE && n === BD_PAGE_SIZE) return;
    BD_FIRST_SIZE = BD_PAGE_SIZE = n;
    return render();
  }
  const first = !!document.querySelector(".bd-card > .bd-hero");
  if (n === (first ? BD_FIRST_SIZE : BD_PAGE_SIZE)) return;
  if (first) BD_FIRST_SIZE = n; else BD_PAGE_SIZE = n;
  render();
}

// Crossing 1100px changes the page's shape, so it is drawn and measured again.
BD_WIDE.addEventListener("change", () => { if (document.querySelector(".bd-card")) render(); });
