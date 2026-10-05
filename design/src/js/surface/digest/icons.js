/* One drawn icon per Digest topic, beside its label (2026-09-29, storyboard
   https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz, option 3A; David: "should we have icons for each
   category"). Stroked in currentColor, so an icon is always its label's colour: grey, or lime on the
   day's open topic. Never emoji (DESIGN.md "Say it in a shape"). */
const DG_ICON_PATH = {
  recap: '<path d="M7 4h10v4a5 5 0 0 1-10 0z"/><path d="M7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 13v4M8 20h8"/>',
  hurt: '<path d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z"/>',
  mu: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
  wx: '<path d="M7 17a4 4 0 0 1-.5-8A5.5 5.5 0 0 1 17 8.5a3.5 3.5 0 0 1 0 8.5z"/>',
  adds: '<circle cx="12" cy="12" r="8"/><path d="M12 8v8M8 12h8"/>',
  t5: '<path d="M4 20v-6h5v6M9 20V9h6v11M15 20v-8h5v8M3 20h18"/>',
  gems: '<path d="M6 4h12l3 5-9 11L3 9z"/><path d="M3 9h18M9 4l3 16 3-16"/>',
  news: '<path d="M4 5h13v14H6a2 2 0 0 1-2-2z"/><path d="M17 9h3v8a2 2 0 0 1-4 0M7 9h7M7 13h7M7 16h4"/>',
};
const dgIcon = id => DG_ICON_PATH[id]
  ? `<svg class="dg-lico" viewBox="0 0 24 24" aria-hidden="true">${DG_ICON_PATH[id]}</svg>` : "";
