/* The Waivers tab's once-only moments and the card flip. The one home for the two stamps it
   keeps in the browser:
   - tw.waiver.dealt: the local day the cards were last dealt. The first open of a day deals them
     in rank order and slams the Must-claim stamps; every later open shows them in place.
   - tw.wire.seen: when the rail was last looked at. Events newer than that flash once.
   Both are read once per page load, on the first Waivers render, and written straight back, so
   a team switch or any re-render never replays them. Storage can throw (a private window) or be
   empty; then nothing is dealt or flashed, which is the quiet failure. */
const WV_DEALT_KEY = "tw.waiver.dealt", WV_SEEN_KEY = "tw.wire.seen";
let WV_MOTION_TAKEN = false;

function wvStore(key, value){
  try {
    const old = localStorage.getItem(key);
    localStorage.setItem(key, value);
    return old;
  } catch (e){ return undefined; }
}

const wvToday = () => { const d = new Date(Date.now()); return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`; };

/* {deal, since}: whether this render deals the cards, and the time after which a rail event is
   new. Only the first call in a page load can say yes to either. */
function wvMotionTake(){
  if (WV_MOTION_TAKEN) return {deal: false, since: Infinity};
  WV_MOTION_TAKEN = true;
  const today = wvToday();
  const dealt = wvStore(WV_DEALT_KEY, today);
  const seen = wvStore(WV_SEEN_KEY, String(Date.now()));
  return {
    deal: dealt !== undefined && dealt !== today && !REDUCED(),
    // A first visit ever has nothing to compare with: nothing is "new", nothing flashes.
    since: seen ? Number(seen) || Infinity : Infinity,
  };
}

/* Claims are placed on a Tuesday (navWaiverDay, the reader's local day, the same injectable
   Date.now the render suite pins): that day the cards lead. Every other day the wire is still
   moving, so the rail leads. */
const wvMode = () => navWaiverDay() ? "claim" : "watch";

/* The flip. Both faces share one grid cell, so the card is as tall as its taller face and never
   changes height; the hidden face is inert, so tab order and a screen reader follow what shows. */
function wvFlip(card){
  const btn = card.querySelector(".wvc-flip"), on = btn.getAttribute("aria-pressed") !== "true";
  btn.setAttribute("aria-pressed", String(on));
  card.classList.toggle("flipped", on);
  const [front, back] = card.querySelectorAll(".wvc-face");
  [[front, on], [back, !on]].forEach(([face, hide]) => {
    face.inert = hide;
    face.setAttribute("aria-hidden", String(hide));
  });
}

/* The chat button floats over the page's right edge (fixed, so every row passes under it as the
   page scrolls). --fab-clear is how far it reaches into the Waivers column, measured from both
   boxes in the reader's browser, never guessed: the rail rows and the card footers keep that much
   clear on their right. Zero when the button is hidden or sits outside the column (a desktop). */
function wvFabClear(v){
  const wv = v.querySelector(".wv"), fab = document.getElementById("chatfab");
  if (!wv) return;
  const f = fab ? fab.getBoundingClientRect() : null;
  const clear = f && f.width ? Math.max(0, Math.ceil(wv.getBoundingClientRect().right - f.left + 8)) : 0;
  wv.style.setProperty("--fab-clear", `${clear}px`);
}
if (typeof window !== "undefined") window.addEventListener("resize", () => {
  if (SURFACE === "waivers") wvFabClear(document.getElementById("view"));
});

function wireWaivers(v){
  v.querySelectorAll(".wvc-flip").forEach(b => b.addEventListener("click", () => wvFlip(b.closest(".wvc"))));
  wvFabClear(v);
}
