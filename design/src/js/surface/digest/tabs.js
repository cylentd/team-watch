/* The Digest's tabs (2026-09-29, storyboard https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz): Results'
   Smashed / Busts / Left hurt (2A; David: "should we redesign so it just opens a big panel") and Top 5's
   positions (5A). Three toggles side by side read as one panel cut in three; one bar over one panel says
   which list is showing. Every panel is drawn and all but one hidden, so a tap swaps them in place and
   nothing is redrawn under the reader. The pick is kept across repaints, per set. */
const DG_TAB = {};

/* `tabs`: [{key, label, count, tone, body}]. `count` is optional; `tone` colours it. */
function dgTabsHTML(set, tabs){
  if (!tabs.length) return "";
  const on = tabs.some(x => x.key === DG_TAB[set]) ? DG_TAB[set] : tabs[0].key;
  const id = x => `dg-${set}-${x.key}`;
  const bar = tabs.map(x => `<button type="button" role="tab" class="dg-tab" data-dgtab="${esc(x.key)}" id="${id(x)}-t"
    aria-controls="${id(x)}-p" aria-selected="${x.key === on}" tabindex="${x.key === on ? 0 : -1}">${x.label}${x.count != null
      ? `<b class="dg-tab-n${x.tone ? " " + x.tone : ""}">${x.count}</b>` : ""}</button>`).join("");
  const panels = tabs.map(x => `<div class="dg-tabp" role="tabpanel" id="${id(x)}-p" aria-labelledby="${id(x)}-t"
    data-dgpanel="${esc(x.key)}"${x.key === on ? "" : " data-off inert"}>${x.body}</div>`).join("");
  // The panels share one box (tabs.css), which is as tall as the tallest, so a tab never resizes it.
  return `<div class="dg-tabset" data-dgset="${set}"><div class="dg-tabs" role="tablist">${bar}</div><div class="dg-tabps">${panels}</div></div>`;
}

function dgTabPick(b){
  const set = b.closest("[data-dgset]"), key = b.dataset.dgtab;
  DG_TAB[set.dataset.dgset] = key;
  set.querySelectorAll("[data-dgtab]").forEach(x => {
    x.setAttribute("aria-selected", String(x === b));
    x.tabIndex = x === b ? 0 : -1;
  });
  // Not `hidden`: the page's reset makes [hidden] display:none !important, and the wall keeps an off
  // panel in the layout (tabs.css). `inert` takes it out of focus and the accessibility tree instead.
  set.querySelectorAll("[data-dgpanel]").forEach(p => {
    const off = p.dataset.dgpanel !== key;
    p.toggleAttribute("data-off", off);
    p.inert = off;
  });
}

/* Left and Right walk the bar, as a tablist does. */
document.addEventListener("keydown", e => {
  const b = e.target.closest && e.target.closest(".dg-tab");
  if (!b || (e.key !== "ArrowLeft" && e.key !== "ArrowRight")) return;
  const all = [...b.parentElement.querySelectorAll(".dg-tab")];
  const next = all[(all.indexOf(b) + (e.key === "ArrowRight" ? 1 : all.length - 1)) % all.length];
  e.preventDefault();
  next.focus();
  dgTabPick(next);
});
