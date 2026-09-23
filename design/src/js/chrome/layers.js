/* Back closes what is on top. Every overlay that should answer to the phone's Back gesture (the
   search sheet, the profile, the drive strip) pushes one history entry as it opens, with no URL
   change, so the hash router in nav.js never hears about it. Back then pops that entry and this
   closes the topmost layer instead of leaving the view.

   Closing from the page itself (✕, Escape, the scrim) must take its entry back too, or the next
   Back would pop a dead entry and do nothing visible. layerDone does that; the popstate it causes
   is counted in LAYER_SKIP so it does not close a second layer. */
const LAYERS = [];     // {id, close}, topmost last
let LAYER_SKIP = 0;

function layerPush(id, close){
  if (LAYERS.some(l => l.id === id)) return;
  LAYERS.push({id, close});
  history.pushState({layer: id}, "");
}

function layerDone(id){
  const i = LAYERS.findIndex(l => l.id === id);
  if (i < 0) return;
  LAYERS.splice(i, 1);
  // Only the top entry can be taken back; a layer closed from underneath leaves its entry, and
  // the popstate that eventually reaches it finds nothing open and does nothing.
  if (i === LAYERS.length && history.state && history.state.layer === id){ LAYER_SKIP++; history.back(); }
}

window.addEventListener("popstate", () => {
  if (LAYER_SKIP){ LAYER_SKIP--; return; }
  const top = LAYERS.pop();
  if (top) top.close();
});
