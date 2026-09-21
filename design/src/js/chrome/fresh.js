/* ------------------------------------------------------------------
   IS THIS STILL THE LATEST BUILD?

   The page carries its data inside itself: every LIVE_* block is baked
   into index.html at build time. A tab left open since the morning
   refresh therefore holds the morning's numbers forever, and no HTTP
   cache rule can change that -- the tab never asks again. Vercel
   already serves the page `max-age=0, must-revalidate`, so a reload is
   always fresh; the gap is that nothing tells you a reload is worth it.

   /build.json is the hash of the injected data. Different hash means
   main moved. It is checked on the events that mean "I am about to
   read something" -- a tab click, or coming back to the window -- and
   never on a timer: the refresh runs once a day and the week turns on
   a Tuesday, so a five-minute poll would be 287 pointless requests to
   learn nothing.
------------------------------------------------------------------ */
const FRESH_GAP_MS = 60000;   // at most one check a minute, however much you click
let FRESH_AT = 0;
let FRESH_NEW = null;         // the newer stamp once there is one, else null

const freshId = () => (typeof BUILD !== "undefined" && BUILD) ? BUILD.id : null;

async function freshCheck(){
  const now = Date.now();
  // PAGE_SERVED: from disk there is no main to have moved on, and the attempt would only log.
  // Once it knows main has moved, there is nothing further to learn: the answer cannot go back
  // to "current" without a reload, and re-asking would only overwrite the banner with itself.
  if (FRESH_NEW || !PAGE_SERVED() || !freshId() || now - FRESH_AT < FRESH_GAP_MS) return;
  FRESH_AT = now;
  try {
    // Relative, so it follows the page rather than assuming the site root.
    const r = await fetch("build.json", {cache: "no-store"});
    if (!r.ok) return;
    const b = await r.json();
    if (!b || !b.id || b.id === freshId()) return;
    FRESH_NEW = b;
    paintFresh();
  } catch (e) {
    /* Offline, or the file is not deployed yet. Staying quiet is right: this is a convenience,
       and a page that cannot reach its own origin has bigger news to give than a stale build. */
  }
}

/* The signal goes on the DATA pill rather than beside it. That pill already answers "how current
   is this" -- five sources and the time of the last refresh -- but only once you open it, which
   is where it was too quiet. A newer build is the one thing on it worth seeing without a tap. */
function paintFresh(){
  const btn = document.getElementById("statusbtn");
  if (!btn || !FRESH_NEW) return;
  const week = FRESH_NEW.week;
  const turned = week && BUILD.week && week !== BUILD.week;
  btn.classList.add("stale");
  // A new week is the fact worth naming: it is how you know the data has moved on rather than
  // just been rebuilt. Otherwise say what is true and no more.
  btn.innerHTML = `<span class="dot"></span>` +
    (turned ? t("chrome.fresh.week", {week: week}) : t("chrome.fresh.new"));
  btn.setAttribute("title", t("chrome.fresh.tip"));
  btn.onclick = e => { e.stopPropagation(); location.reload(); };
}

function buildFresh(){
  freshCheck();
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") freshCheck();
  });
}
