/* Slips pack into their columns (2026-09-25): a grid row is as tall as its tallest slip, so a
   4-pick under a 5-pick left a hole the height of two cards beside it. Each slip spans as many
   2px rows as it is tall, measured in the reader's browser (STYLE.md: measure, never guess), and
   the grid's own placement fills the holes, keeping the order left to right. One column (a
   phone) needs none of it. Re-measured after a render, a pick opening, a resize and the fonts. */
const MASONRY_ROW = 2;

function slipMasonry(root){
  (root || document).querySelectorAll(".tk-grid").forEach(grid => {
    const cols = getComputedStyle(grid).gridTemplateColumns.split(" ").length;
    grid.classList.toggle("masonry", cols > 1);
    const gap = parseFloat(getComputedStyle(grid).columnGap) || 0;
    grid.querySelectorAll(":scope > .ticket").forEach(card => {
      card.style.gridRowEnd = cols > 1 ? `span ${Math.ceil((card.offsetHeight + gap) / MASONRY_ROW)}` : "";
    });
  });
}

let masonryTimer = 0;
window.addEventListener("resize", () => {
  clearTimeout(masonryTimer);
  masonryTimer = setTimeout(() => { if (SURFACE === "parlay") slipMasonry(); }, 120);
});
if (document.fonts) document.fonts.ready.then(() => { if (SURFACE === "parlay") slipMasonry(); });
