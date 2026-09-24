/* The phone nav slides up while the reader scrolls down a list and comes back on the first scroll
   up. The page body owns one class; responsive/760.css decides what it moves, so on a desktop the
   class is set and nothing happens. The threshold keeps a finger's jitter from flickering the bar,
   and the top 120px never hides it: the reader has not left the header yet. */
const HIDEBAR_JITTER = 6;
const HIDEBAR_TOP = 120;

function buildHideBar(){
  let last = window.scrollY, away = false;
  window.addEventListener("scroll", () => {
    const y = window.scrollY, dy = y - last;
    if (Math.abs(dy) < HIDEBAR_JITTER) return;
    last = y;
    const next = dy > 0 && y > HIDEBAR_TOP;
    if (next === away) return;
    away = next;
    document.body.classList.toggle("hdr-away", away);
  }, {passive: true});
}
