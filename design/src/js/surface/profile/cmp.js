/* Compare (2026-09-30, storyboard https://claude.ai/artifact/LR2pMmjnZdSfcVsq6Qzt3o, option A): a
   layer over the profile, opened from the head's Compare button. The picker first (cmppick.js):
   the reader's own team at this position, then waivers, then any player by search; then the sheet
   (cmpshow.js): every player on one radar, a row of numbers under it.

   One layer in #modal like the stat sheet's (orbsheet.js), with one history entry: Back closes the
   whole layer and leaves the profile where it was. Picker and sheet are two stages of it, not two
   entries, so Back never walks the reader through a list they already left. */
const CMP_LAYER = "compare", CMP_MAX = 3;
const CMP = {base: null, picks: [], stage: "pick", q: ""};

function cmpOpen(d){
  if (d.querySelector(".cmp-layer") || !CMP.base) return;
  CMP.picks = []; CMP.stage = "pick"; CMP.q = "";
  const layer = document.createElement("div");
  layer.className = "cmp-layer";
  layer.innerHTML = `<div class="cmp-scrim"></div>
    <div class="cmp-sheet" role="dialog" aria-modal="true" aria-labelledby="cmp-t"></div>`;
  d.appendChild(layer);
  [...d.children].forEach(c => { if (c !== layer) c.inert = true; });
  const sheet = layer.querySelector(".cmp-sheet");
  orbHoldScroll(layer, sheet);
  layer.querySelector(".cmp-scrim").addEventListener("click", () => cmpClose(d, true));
  layer.addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); cmpClose(d, true); } });
  sheet.addEventListener("click", e => cmpClick(d, e));
  sheet.addEventListener("input", e => { if (e.target.id === "cmp-q"){ CMP.q = e.target.value; cmpPaintList(sheet); } });
  layerPush(CMP_LAYER, () => cmpClose(d, false));
  cmpPaint(d);
  const q = sheet.querySelector("#cmp-q");
  if (q && !matchMedia("(pointer:coarse)").matches) q.focus({preventScroll: true});
}

/* `fromPage` is a close the page started (✕, scrim, Escape), which takes its history entry back;
   Back has already popped it. */
function cmpClose(d, fromPage){
  const layer = d.querySelector(".cmp-layer");
  if (!layer) return;
  if (fromPage) layerDone(CMP_LAYER);
  layer.remove();
  [...d.children].forEach(c => { c.inert = false; });
  const btn = d.querySelector("[data-compare]");
  if (btn) btn.focus({preventScroll: true});
}

function cmpPaint(d){
  const sheet = d.querySelector(".cmp-sheet");
  if (!sheet) return;
  sheet.innerHTML = CMP.stage === "show" ? cmpShowHTML() : cmpPickHTML();
  sheet.scrollTop = 0;
  // The stage's own close button holds focus, so Escape and Tab stay inside the layer.
  const x = sheet.querySelector(".cmp-x");
  if (x) x.focus({preventScroll: true});
}

/* Everyone on the sheet: the profile's player first, then the picks in the order they were taken.
   The order is the colour order (cmp-s0..2), so a player keeps his colour from tray to radar. */
const cmpPlayers = () => [CMP.base, ...CMP.picks];

function cmpToggle(p){
  const i = CMP.picks.findIndex(x => x.slug === p.slug);
  if (i >= 0) CMP.picks.splice(i, 1);
  else if (p.slug !== CMP.base.slug && CMP.picks.length < CMP_MAX - 1) CMP.picks.push(p);
}

function cmpClick(d, e){
  const el = e.target.closest("[data-cmp]");
  if (!el) return;
  const act = el.dataset.cmp;
  if (act === "close") return cmpClose(d, true);
  if (act === "go"){ if (CMP.picks.length){ CMP.stage = "show"; cmpPaint(d); } return; }
  if (act === "change"){ CMP.stage = "pick"; cmpPaint(d); return; }
  if (act === "pick"){
    const p = CMP_ROWS[+el.dataset.i];
    if (!p) return;
    cmpToggle(p);
    // A search pick is done searching: the box clears and the lists come back with him ticked.
    if (CMP.q){ CMP.q = ""; const q = d.querySelector("#cmp-q"); if (q) q.value = ""; }
    const sheet = d.querySelector(".cmp-sheet");
    cmpPaintList(sheet);
    // The repaint replaced the row that had focus; hand it to his new row, or Escape and Tab would
    // start from the page behind the layer.
    const back = [...sheet.querySelectorAll(".cmp-row")].find(b => b.dataset.slug === p.slug) || sheet.querySelector("#cmp-q");
    if (back) back.focus({preventScroll: true});
  }
}

/* The head's button, delegated from #modal and bound once: openProfile refills #modal on every
   open (panel.js says why delegation is the binding that survives). */
document.getElementById("modal").addEventListener("click", e => {
  if (!e.target.closest("[data-compare]")) return;
  cmpOpen(document.getElementById("modal"));
});

const cmpButtonHTML = () =>
  `<button type="button" class="cmp-open" data-compare aria-haspopup="dialog">${t("profile.compare.open")}</button>`;
