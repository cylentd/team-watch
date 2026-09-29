/* ============================== LEAGUE > TRADES: what makes it feel alive ==============================
   David, 2026-09-28: "readability first, then fun sprinkled in". Two behaviours, each with its guards:
   - the ranking row nearest the middle of a phone screen lights while the reader scrolls, so the list
     reads as tappable (a mouse gets the same from hover, in CSS);
   - the trades that decided a season shuffle a new set in every 10 s (cards.js, trDecidedShown), only
     while that section is on screen, never while a finger or pointer is on it, never under reduced
     motion or after Show all. A bar fills over the 10 s, so a swap is announced, never sudden. */
const TR_TICK = 100, TR_EVERY = 10000, TR_HOLD = 8000;   // ms: timer step, one shuffle, a touch's pause
let TR_IO = null;

/* The phone's scroll highlight: a band across the middle of the screen, the row inside it is "hot". */
function trWatchRows(root){
  if (TR_IO) TR_IO.disconnect();
  if (!matchMedia("(hover: none)").matches || typeof IntersectionObserver === "undefined") return;
  TR_IO = new IntersectionObserver(es => es.forEach(e => e.target.classList.toggle("hot", e.isIntersecting)),
    {rootMargin: "-49% 0px -49% 0px"});   // a ~2% band: one row at a time (44px rows), two only as one hands over
  root.querySelectorAll(".tr-mgr").forEach(b => TR_IO.observe(b));
}

function trShuffle(root){
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  // A mouse over the section is read from :hover at each tick (it survives the swap replacing the cards
  // under it); a touch or a focus inside holds it for TR_HOLD.
  let spent = 0, holdUntil = 0;
  const inside = e => !!e.target.closest?.(".tr-decided");
  root.addEventListener("pointerdown", e => { if (inside(e)) holdUntil = Date.now() + TR_HOLD; });
  root.addEventListener("focusin", e => { if (inside(e)) holdUntil = Date.now() + TR_HOLD; });
  const timer = setInterval(() => {
    if (!root.isConnected) return clearInterval(timer);
    const sec = root.querySelector(".tr-decided"), bar = sec?.querySelector(".tr-shuffle i");
    if (!bar || TR_ALL) return;
    const r = sec.getBoundingClientRect();
    const live = !document.hidden && !sec.matches(":hover") && Date.now() > holdUntil && r.top < innerHeight && r.bottom > 0;
    if (!live) return;
    spent += TR_TICK;
    bar.style.setProperty("--p", Math.min(1, spent / TR_EVERY));
    if (spent < TR_EVERY) return;
    spent = 0;
    TR_ROT += trDecidedShown().n;
    sec.outerHTML = trDecidedBlockHTML(true);
  }, TR_TICK);
}
