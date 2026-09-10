/* A scroll container with clipped content (the scatter, a rail) is easy to miss entirely on
   first view -- nudge it once so the swipe is felt, not just hinted at in small print. Once per
   rail per SESSION, not once per element: render() replaces the DOM wholesale on every filter
   click or tab switch, so a per-element flag (dataset.nudged) would fire again on every single
   re-render since the old element -- and its flag -- is gone. NUDGED is a module-level Set keyed
   by each rail's stable data-railkey, so it survives across re-renders instead.
   Bails when there's nothing to scroll (desktop, or a rail short enough to fit).

   The nudge is one continuous glide from the far end back to the front -- not an out-and-back
   twitch (peeking partway and snapping back read as two separate, slightly awkward motions) and
   not a repeating jiggle (a permanent few-px twitch read as janky/broken, not as an invitation).
   Jumping to the end happens synchronously, before the browser's first paint of this render, so
   what's actually seen is the whole rail already easing smoothly toward the front -- never a
   flash of the end position sitting still. It fires once; the static "SWIPE ->" label is what's
   left standing after.

   Also keeps the "SWIPE ->" hint honest: hides it (via the .no-swipe class) the moment there is
   nothing left to swipe to, whether that's because the content fits with no scrolling at all or
   because the user already scrolled to the end. Re-checked on every scroll and every re-render.

   Same pass also wires wheel-to-horizontal: a mouse has no horizontal swipe gesture, so without
   this a desktop rail is only draggable by its thin scrollbar. Vertical wheel motion over the
   rail pans it sideways instead of scrolling the page, same as most horizontal carousels. */
const NUDGED = new Set();
function nudgeScrollers(root){
  root.querySelectorAll(".quadscroll, .railscroll").forEach(el=>{
    const hintTarget = el.closest(".rail") || el;
    const key = hintTarget.dataset.railkey || el.dataset.railkey;
    const update = () => {
      const canScroll = el.scrollWidth > el.clientWidth + 4;
      const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 4;
      hintTarget.classList.toggle("no-swipe", !canScroll || atEnd);
    };
    update();
    if (!el.dataset.hintWired){
      el.dataset.hintWired = "1";
      el.addEventListener("scroll", update, {passive:true});
    }
    if (!el.dataset.wheelWired){
      el.dataset.wheelWired = "1";
      el.addEventListener("wheel", e=>{
        if (el.scrollWidth <= el.clientWidth + 4) return;
        const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
        if (!delta) return;
        e.preventDefault();
        el.scrollLeft += delta;
      }, {passive:false});
    }
    if (el.scrollWidth <= el.clientWidth + 4 || (key && NUDGED.has(key))) return;
    if (key) NUDGED.add(key);
    requestAnimationFrame(()=>{
      el.scrollLeft = el.scrollWidth - el.clientWidth;
      el.scrollTo({left: 0, behavior: "smooth"});
    });
  });
}

