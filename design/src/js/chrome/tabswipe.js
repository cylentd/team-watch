/* ============================== SWIPE BETWEEN TABS ==============================
   2026-10-06 (David: "I find myself trying to do that a lot because I don't want to reach all the way
   to the top"). A sideways swipe on the page is a tap on the next thing in the top tab row: the stop is
   data/tabrow.js tabRowStep, whether a touch is a swipe at all data/swipestep.js swipeStep. DESIGN.md
   "Swipe between tabs". It supersedes "never a swipe between views" (2026-09-30), whose worry was the
   surfaces that already own a sideways gesture; a touch that starts on one of them stays theirs.
   Same day, from David's phone: the page's empty space below a short view did nothing (the touch was the
   body's, not #view's), and a scroll's sideways drift turned the tab (lib/swipe.js's rule reads only the
   end point). So the gesture listens on the document, keeps every point, and lets swipeStep decide. */
const TAB_SWIPE_EDGE = 24;   // px from either screen edge: iOS Safari's own Back swipe starts there

/* True when the touch is not the tab swipe's: an overlay is open (LAYERS, chrome/layers.js), it began
   outside the view and the page under it (the header, the tab row, the bottom bar, a sheet), at a screen
   edge, on a surface with its own sideways gesture (data-ownswipe, set by onSwipeX and the Roster's
   drags), in something that scrolls sideways, or on a slider. */
function tabSwipeSkip(target, touch){
  const view = document.getElementById("view");
  if (LAYERS.length) return true;
  if (target !== document.body && target !== document.documentElement && !view.contains(target)) return true;
  if (touch.clientX < TAB_SWIPE_EDGE || touch.clientX > innerWidth - TAB_SWIPE_EDGE) return true;
  for (let el = target; el && el !== view && el !== document.body; el = el.parentElement){
    if (el.hasAttribute("data-ownswipe") || el.matches("input[type=range]")) return true;
    if (el.scrollWidth > el.clientWidth + 1 && /auto|scroll/.test(getComputedStyle(el).overflowX)) return true;
  }
  return false;
}

/* The slide: the page's blocks arrive from the side the finger came from (css/chrome/motion.css). What a
   view pins to the screen (Bets' slip tray, its sheet and scrim) stays put: an animation on it would
   override its own transform and opacity, and the scrim flashed dark over the whole page (2026-10-06). */
function tabSlide(v, d){
  v.classList.remove("enter");               // one arrival: the slide, not the cards' rise on top of it
  v.classList.toggle("sliding", !REDUCED()); // nothing the slide moves widens the page (motion.css)
  const on = d > 0 ? "tab-in-r" : "tab-in-l";
  for (const c of v.children){
    const again = c.classList.contains("tab-in-r") || c.classList.contains("tab-in-l");
    c.classList.remove("tab-in-r", "tab-in-l");
    if (getComputedStyle(c).position === "fixed") continue;
    if (again) void c.offsetWidth;           // restart a slide still running (two swipes close together)
    c.classList.add(on);
  }
}

/* d = +1 on a swipe left. A tab of the open view selects in place, as its segment's tap does; another
   view opens from its top on the tab nearest the side it came from (tabRowEnter). */
function tabSwipe(d){
  const to = tabRowStep(navTabPlan(), d);
  if (!to) return;
  NAV_GLIDE = true;
  try {
    if (to.seg){ navModesOf(SURFACE).select(to.seg); paintSubnav(); }
    else {
      morphLogo(); navGo(to.leaf); window.scrollTo(0, 0);
      const m = navModesOf(SURFACE), seg = tabRowEnter(m, d, NAV_PHONE.matches);
      if (seg){ m.select(seg); paintSubnav(); }
    }
  } finally { NAV_GLIDE = false; }
  tabSlide(document.getElementById("view"), d);
}

/* One listener set on the document, so the whole page between the tab row and the bottom bar takes the
   swipe, the empty space under a short view included. Every point is kept for swipeStep, and the page's
   scroll at the start, so a touch that scrolled the page is never a swipe. */
function wireTabSwipe(){
  const v = document.getElementById("view");
  let pts = null, y0 = 0;
  document.addEventListener("touchstart", e => {
    const t = e.touches[0];
    pts = e.touches.length === 1 && !tabSwipeSkip(e.target, t) ? [[t.clientX, t.clientY]] : null;
    y0 = window.scrollY;
  }, {passive: true});
  document.addEventListener("touchmove", e => {
    if (pts && e.touches.length === 1) pts.push([e.touches[0].clientX, e.touches[0].clientY]);
    else pts = null;                         // a second finger: a pinch, not a swipe
  }, {passive: true});
  document.addEventListener("touchend", e => {
    if (!pts) return;
    const t = e.changedTouches[0], step = swipeStep([...pts, [t.clientX, t.clientY]], window.scrollY - y0);
    pts = null;
    if (step && !LAYERS.length) tabSwipe(step);
  });
  document.addEventListener("touchcancel", () => { pts = null; });
  v.addEventListener("animationend", e => {
    if (e.target.parentElement !== v || !/^view-in-/.test(e.animationName)) return;
    e.target.classList.remove("tab-in-r", "tab-in-l");
    if (!v.querySelector(":scope > .tab-in-r, :scope > .tab-in-l")) v.classList.remove("sliding");
  });
}
