/* Where the stuck chrome ends: the tab row's bottom edge, or the bar's when the group draws no row. Both stick
   at the top, so it is one number at any scroll; a view's own sticky column (Roster's brief, the Waivers rail,
   Preview's slate) starts under it rather than behind it (2026-10-08, when the desktop's tab row began to stick).
   nav.js paintSubnav publishes it as --stick-top. */
function navStickTop(){
  const sub = document.getElementById("subnav"), el = sub && !sub.hidden ? sub : document.querySelector(".navbar");
  return el ? Math.round(el.getBoundingClientRect().bottom) : 0;
}
