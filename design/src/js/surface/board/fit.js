/* ------------------------------------------------------------------
   THE BOARD — how many rows a page of the full list holds: as many as the reader's screen shows
   at once, measured in his browser (2026-09-25). A fixed count is a guess about a screen nobody
   has measured; this reads the real row, the real pager and the real bars.

   The bars are counted as if showing. On a phone the nav and the view tabs slide away while the
   reader scrolls down and come back on the first scroll up (js/chrome/hidebar.js), so a page sized
   to the bars-hidden screen would lose its last rows under them the moment he scrolls back.
------------------------------------------------------------------ */
const BD_FIT_MIN = 5, BD_FIT_MAX = 40;

// The sticky and fixed chrome above the page, at its full height whether or not it is showing now.
function bdChromeH(){
  return [...document.querySelectorAll(".topbar, .navbar, .subnav")]
    .filter(el => { const p = getComputedStyle(el).position; return (p === "sticky" || p === "fixed") && el.offsetHeight; })
    .reduce((s, el) => s + el.offsetHeight, 0);
}

/* Rows that fit: the viewport less the chrome, less everything in the open list that is not a
   row (its pager, padding, border, margin), in units of one row. Null when there is no open list
   to measure. */
function bdMeasureFit(){
  const more = document.querySelector(".bd-more");
  const rows = more ? [...more.querySelectorAll(".bd-row")] : [];
  if (!rows.length) return null;
  const rowH = Math.max(...rows.map(r => r.offsetHeight));
  const overhead = more.offsetHeight - rows.reduce((s, r) => s + r.offsetHeight, 0)
    + parseFloat(getComputedStyle(more).marginTop || 0);
  const n = Math.floor((window.innerHeight - bdChromeH() - overhead) / rowH);
  return Math.max(BD_FIT_MIN, Math.min(BD_FIT_MAX, n));
}

/* After the list opens or turns a page: size the page to the screen, keeping the first row the
   reader was about to see, then put the list's top edge just under the chrome. */
function bdFitPage(){
  const n = bdMeasureFit();
  if (n && n !== BD_PAGE_SIZE){
    const first = BD_TOP + (BD_PAGE - 1) * BD_PAGE_SIZE;
    BD_PAGE_SIZE = n;
    BD_PAGE = Math.floor((first - BD_TOP) / n) + 1;
    render();
  }
  const more = document.querySelector(".bd-more");
  if (more) window.scrollTo(0, more.getBoundingClientRect().top + window.scrollY - bdChromeH());
}
