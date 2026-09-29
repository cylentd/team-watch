/* ============================== LEAGUE > TRADES: what makes it feel alive ==============================
   David, 2026-09-28: "readability first, then fun sprinkled in". Two behaviours, each with its guards:
   - the ranking row nearest the middle of a phone screen lights while the reader scrolls, so the list
     reads as tappable (a mouse gets the same from hover, in CSS);
   - the trades that decided a season shuffle a new set in every 10 s (cards.js, trDecidedShown), only
     while that section is on screen, never while a finger or pointer is on it, never under reduced
     motion or after Show all. The bar that filled over the 10 s is gone (David, 2026-09-28: "too
     distracting"); the new cards drop in one after another, so a swap still reads as a swap. */
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

/* A phone's swipe rows (cards.js): the pager under each follows the card nearest the left edge. Crossing
   the phone/desktop line redraws the decided cards, which show all on a phone and shuffle on a desktop. */
function trSwipes(root){
  root.addEventListener("scroll", e => {
    const row = e.target;
    if (!row.classList?.contains("tr-swipe")) return;
    const pager = row.parentElement.querySelector(":scope > .tr-pager"), card = row.firstElementChild;   // the pager sits over its row
    if (!pager || !card) return;
    const step = card.getBoundingClientRect().width + parseFloat(getComputedStyle(row).columnGap || 0);
    const n = row.children.length, i = Math.min(n, Math.round(row.scrollLeft / step) + 1);
    pager.textContent = t("trades.swipe.pos", {i, n});
  }, true);   // scroll does not bubble; capture sees every row's, including a redrawn one
  const mq = matchMedia(TR_PHONE);
  mq.addEventListener?.("change", () => {
    if (!root.isConnected) return;
    const sec = root.querySelector(".tr-decided");
    if (sec) sec.outerHTML = trDecidedBlockHTML();
  });
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
    const sec = root.querySelector(".tr-decided[data-trrot]");
    if (!sec || TR_ALL) return;
    const r = sec.getBoundingClientRect();
    const live = !document.hidden && !sec.matches(":hover") && Date.now() > holdUntil && r.top < innerHeight && r.bottom > 0;
    if (!live) return;
    spent += TR_TICK;
    if (spent < TR_EVERY) return;
    spent = 0;
    TR_ROT += trDecidedShown().n;
    sec.outerHTML = trDecidedBlockHTML(true);
  }, TR_TICK);
}
