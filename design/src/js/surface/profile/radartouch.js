/* A hand on the dial, 2026-09-25. The six labels were the only way to pick a stat, and on a phone
   they sit on the rim of a chart that fills the width. Now the whole dial answers:

   - tap: picks the axis nearest the finger's angle;
   - drag: sweeps round the dial, picking each axis as the finger passes it.

   The target is .pf-radar-hit, an HTML circle over the disc (sheet.js says why it is HTML).

   A hold used to draw a "typical starter" ghost. Removed the same day: ranked against every
   qualified back, the median starter sits at 0.84 of the radius, right on the elite arcs, so it
   said nothing the arcs did not -- and nothing on the page told a reader to hold. */
function wireRadarTouch(el, s, g, pick){
  const hit = el.querySelector(".pf-radar-hit");
  const labels = [...el.querySelectorAll(".pf-radar-l")];
  if (!hit || labels.length !== s.axes.length) return;
  const n = s.axes.length;
  // The axis whose angle is nearest the pointer's, measured from the dial's own centre.
  const nearest = e => {
    const r = hit.getBoundingClientRect();
    const a = Math.atan2(e.clientY - r.top - r.height / 2, e.clientX - r.left - r.width / 2) + Math.PI / 2;
    return ((Math.round(a / (2 * Math.PI / n)) % n) + n) % n;
  };
  const go = i => {
    if (labels[i].classList.contains("on")) return;
    pick(labels[i]);
    if (navigator.vibrate) navigator.vibrate(4);
  };
  let down = null;
  hit.addEventListener("pointerdown", e => {
    if (e.button > 0) return;
    hit.setPointerCapture(e.pointerId);
    down = {x: e.clientX, y: e.clientY, scrub: false};
  });
  hit.addEventListener("pointermove", e => {
    if (!down) return;
    if (!down.scrub && Math.hypot(e.clientX - down.x, e.clientY - down.y) > 8){
      down.scrub = true;
      el.classList.add("scrub");
    }
    if (down.scrub) go(nearest(e));
  });
  const end = e => {
    if (!down) return;
    if (!down.scrub && e.type === "pointerup") go(nearest(e));
    el.classList.remove("scrub");
    down = null;
  };
  hit.addEventListener("pointerup", end);
  hit.addEventListener("pointercancel", end);
}
