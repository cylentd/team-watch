/* ============================== SWIPE BETWEEN TABS ==============================
   2026-10-06 (David: "I find myself trying to do that a lot because I don't want to reach all the way
   to the top"). A sideways swipe on the view is a tap on the next thing in the top tab row: the stop
   is data/tabrow.js tabRowStep, the gesture lib/swipe.js onSwipeX. DESIGN.md "Swipe between tabs".
   It supersedes "never a swipe between views" (2026-09-30), whose worry was the surfaces that already
   own a sideways gesture; a touch that starts on one of them stays theirs (tabSwipeSkip). */
const TAB_SWIPE_EDGE = 24;   // px from either screen edge: iOS Safari's own Back swipe starts there

/* True when the touch is not the tab swipe's: it began on a surface with its own sideways gesture
   (data-ownswipe, set by onSwipeX and the Roster's drags), in something that scrolls sideways, on a
   slider, or at a screen edge. */
function tabSwipeSkip(target, touch){
  const view = document.getElementById("view");
  if (touch.clientX < TAB_SWIPE_EDGE || touch.clientX > innerWidth - TAB_SWIPE_EDGE) return true;
  for (let el = target; el && el !== view; el = el.parentElement){
    if (el.hasAttribute("data-ownswipe") || el.matches("input[type=range]")) return true;
    if (el.scrollWidth > el.clientWidth + 1 && /auto|scroll/.test(getComputedStyle(el).overflowX)) return true;
  }
  return false;
}

/* d = +1 on a swipe left. A tab of the open view selects in place, as its segment's tap does; another
   view opens from its top, sliding in from the side the finger came from. */
function tabSwipe(d){
  const to = tabRowStep(navTabPlan(), d);
  if (!to) return;
  if (to.seg){ navModesOf(SURFACE).select(to.seg); paintSubnav(); }
  else { morphLogo(); navGo(to.leaf); window.scrollTo(0, 0); }
  const v = document.getElementById("view");
  v.classList.remove("in-r", "in-l");
  void v.offsetWidth;                      // restart the slide when two swipes come close together
  v.classList.add(d > 0 ? "in-r" : "in-l");
}

function wireTabSwipe(){
  const v = document.getElementById("view");
  onSwipeX(v, tabSwipe, tabSwipeSkip);
  delete v.dataset.ownswipe;               // the view is the tab swipe's own surface, not one it skips
  v.addEventListener("animationend", e => { if (e.target.parentElement === v) v.classList.remove("in-r", "in-l"); });
}
