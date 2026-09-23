/* Waivers on a wide screen: the markup and the measurements follow what wdesk.css laid out. The
   CSS owns every breakpoint and says what it did through two flags this file reads back:
   --wvc-both on a card laid open (both faces showing), --wvr-side on a rail in the side column.
   Runs after every Waivers render and on resize. On a phone neither flag is set and nothing here
   touches the markup. */

const wvFlag = (el, name) => getComputedStyle(el).getPropertyValue(name).trim() === "1";

/* A card laid open has no hidden face: none of it may be inert. Only cards whose state changes
   are touched, so a phone render stays exactly as rendered. */
function wvFaces(v){
  v.querySelectorAll(".wvc.tier-must").forEach(card => {
    const both = wvFlag(card, "--wvc-both");
    if (both === card.classList.contains("both")) return;
    card.classList.toggle("both", both);
    wvLive(card);
  });
}

/* A rail in the side column has room for the whole wire: claim day's "Show all" opens itself,
   and the rail sticks just under the nav, which is itself sticky under the topbar. */
function wvRailSide(wv){
  const rail = wv.querySelector(".wvr"), nav = document.querySelector(".navbar");
  if (!rail || !wvFlag(rail, "--wvr-side")) return;
  const more = rail.querySelector(".wvr-more");
  if (more && !more.open) more.open = true;
  if (nav) wv.style.setProperty("--wv-stick", `${Math.round((parseFloat(getComputedStyle(nav).top) || 0) + nav.offsetHeight)}px`);
}

/* The chat button floats over the page's right edge (fixed, so every row passes under it as the
   page scrolls). --fab-clear is how far it reaches into a box, measured from both boxes in the
   reader's browser, never guessed: the rail rows and the card footers keep that much clear on
   their right. Set on the whole tab, then overridden on any card or rail that ends elsewhere --
   a card in the left column of a wide screen never sits under the button, so it keeps nothing. */
function wvFabClear(v){
  const wv = v.querySelector(".wv"), fab = document.getElementById("chatfab");
  if (!wv) return;
  const f = fab ? fab.getBoundingClientRect() : null;
  const clear = el => f && f.width ? Math.max(0, Math.ceil(el.getBoundingClientRect().right - f.left + 8)) : 0;
  const all = clear(wv);
  wv.style.setProperty("--fab-clear", `${all}px`);
  v.querySelectorAll(".wvr, .wvc").forEach(el => {
    const own = clear(el);
    if (own !== all) el.style.setProperty("--fab-clear", `${own}px`);
    else el.style.removeProperty("--fab-clear");
  });
}

function wvDesk(v){
  const wv = v.querySelector(".wv");
  if (!wv) return;
  wvFaces(v);
  wvRailSide(wv);
  wvFabClear(v);
}
if (typeof window !== "undefined") window.addEventListener("resize", () => {
  if (SURFACE === "waivers") wvDesk(document.getElementById("view"));
});
