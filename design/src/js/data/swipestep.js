/* ============================== IS THIS TOUCH A SWIPE BETWEEN TABS? ==============================
   2026-10-06 (David: "it switches tabs while I am scrolling"). The tab swipe (chrome/tabswipe.js) first
   used lib/swipe.js's rule, read only where the finger let go: 48px sideways and 1.5 times more sideways
   than down. A thumb scrolling a list moves on an arc, and its sideways drift passed that. This reads the
   whole touch instead. Pure and DOM-free (tests/test_js_swipestep.py); DESIGN.md "Swipe between tabs".

   The rule, and why each number:
     lock    10px   The axis is decided by the first 10px the finger travels. A touch that starts
                    more up or down than sideways is a scroll, however it ends: by then the page is
                    already moving under it. 10px is about where iOS itself decides a pan's axis.
     min     72px   Sideways distance before it counts: a fifth of a 360-390px phone. 48px fired on
                    the drift of a quick scroll and on a thumb resting and rolling.
     ratio   2.2    And 2.2 times more sideways than down: within ~24 degrees of level (atan 1/2.2).
                    1.5 allowed ~34 degrees, which is a normal scroll's arc.
     scroll  4px    A touch during which the page scrolled more than this is a scroll. A couple of px
                    is the rubber band settling, not the reader's intent. */
const TAB_SWIPE = {lock: 10, min: 72, ratio: 2.2, scroll: 4};

/* swipeStep(pts, scrolled, rule) -> 1 | -1 | null.
   pts: the touch's points in order, [x, y] each (start, every move, end); scrolled: how many px the page
   moved while the finger was down. 1 is a swipe left (the next tab), -1 a swipe right, null not a swipe. */
function swipeStep(pts, scrolled, rule = TAB_SWIPE){
  if (pts.length < 2 || Math.abs(scrolled) > rule.scroll) return null;
  const [x0, y0] = pts[0];
  const first = pts.find(([x, y]) => Math.max(Math.abs(x - x0), Math.abs(y - y0)) >= rule.lock);
  if (!first || Math.abs(first[1] - y0) >= Math.abs(first[0] - x0)) return null;   // a tap, or it began up or down
  const [x1, y1] = pts[pts.length - 1], dx = x1 - x0, dy = y1 - y0;
  if (Math.abs(dx) < rule.min || Math.abs(dx) < rule.ratio * Math.abs(dy)) return null;
  return dx < 0 ? 1 : -1;
}
