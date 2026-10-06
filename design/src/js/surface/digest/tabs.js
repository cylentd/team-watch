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
  const bar = tabs.map(x => `<button type="button" role="tab" class="dg-tab" data-testid="digest-tab" data-dgtab="${esc(x.key)}" id="${id(x)}-t"
    aria-controls="${id(x)}-p" aria-selected="${x.key === on}" tabindex="${x.key === on ? 0 : -1}">${x.label}${x.count != null
      ? `<b class="dg-tab-n${x.tone ? " " + x.tone : ""}">${x.count}</b>` : ""}</button>`).join("");
  /* Each panel also carries its own heading, the tab's label and count. A set the wall lays open, all
     panels at once with no bar (Results' lists, tabs.css), shows it; a phone and Top 5 do not. */
  const panels = tabs.map(x => `<div class="dg-tabp" data-testid="digest-tabpanel" role="tabpanel" id="${id(x)}-p" aria-labelledby="${id(x)}-t"
    data-dgpanel="${esc(x.key)}"${x.key === on ? "" : " data-off"}><h4 class="dg-tabh${x.tone ? " " + x.tone : ""}">${x.label}${x.count != null
      ? `<b>${x.count}</b>` : ""}</h4>${x.body}</div>`).join("");
  // The panels share one box (tabs.css), which is as tall as the tallest, so a tab never resizes it.
  return `<div class="dg-tabset" data-testid="digest-tabset" data-dgset="${set}"><div class="dg-tabs" role="tablist">${bar}</div><div class="dg-tabps">${panels}</div></div>`;
}

function dgTabPick(b){
  const set = b.closest("[data-dgset]"), key = b.dataset.dgtab;
  DG_TAB[set.dataset.dgset] = key;
  set.querySelectorAll("[data-dgtab]").forEach(x => {
    x.setAttribute("aria-selected", String(x === b));
    x.tabIndex = x === b ? 0 : -1;
  });
  // Not `hidden`: the page's reset makes [hidden] display:none !important, and the wall shows an off
  // panel (Results) or keeps it in the layout (Top 5). Where it is off, CSS hides it by display or
  // visibility, which both take it out of focus and the accessibility tree; no `inert`, which would
  // also have made the wall's open lists untappable.
  set.querySelectorAll("[data-dgpanel]").forEach(p => p.toggleAttribute("data-off", p.dataset.dgpanel !== key));
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
