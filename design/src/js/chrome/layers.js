/* Back closes what is on top. Every overlay that should answer to the phone's Back gesture (the
   search sheet, the profile, the drive strip) pushes one history entry as it opens, with no URL
   change, so the hash router in nav.js never hears about it. Back then pops that entry and this
   closes the topmost layer instead of leaving the view.

   Closing from the page itself (✕, Escape, the scrim) must take its entry back too, or the next
   Back would pop a dead entry and do nothing visible. layerDone does that; the popstate it causes
   is counted in LAYER_SKIP so it does not close a second layer. That step back also scrolled the
   page to the top once every popstate handler had run (2026-09-27: the pack's cards landed on a
   page scrolled down to them, and the close threw it back up), so the scroll of the moment the
   layer closed is put back on the next frame, before it paints. */
const LAYERS = [];     // {id, close}, topmost last
const LAYER_SKIP = []; // one scroll to put back per popstate that layerDone caused

function layerPush(id, close){
  if (LAYERS.some(l => l.id === id)) return;
  LAYERS.push({id, close});
  history.pushState({layer: id}, "");
}

/* A layer whose view is left while it stays open (Preview's dossier, handed on to Slips): its entry
   stays in the history and only the registration goes, so the Back that returns to it does not close
   it. layerAdopt takes the registration up again once the view is back on that entry. */
function layerForget(id){
  const i = LAYERS.findIndex(l => l.id === id);
  if (i >= 0) LAYERS.splice(i, 1);
}

function layerAdopt(id, close){
  if (!LAYERS.some(l => l.id === id)) LAYERS.push({id, close});
}

function layerDone(id){
  const i = LAYERS.findIndex(l => l.id === id);
  if (i < 0) return;
  LAYERS.splice(i, 1);
  // Only the top entry can be taken back; a layer closed from underneath leaves its entry, and
  // the popstate that eventually reaches it finds nothing open and does nothing.
  if (i === LAYERS.length && history.state && history.state.layer === id){
    LAYER_SKIP.push(window.scrollY);
    history.back();
  }
}

/* Close every open layer and take their history entries back, then run `then` once the entries are gone.
   A view change made with a layer up (a pill under Preview's dossier, a link out of a profile opened from the
   search sheet) must not leave those entries behind the new one: Back would come back to the view and need
   a second press, and the hash write's own popstate would close the topmost layer from underneath.
   `then` runs at once when nothing is open, and the page is not scrolled back (null in LAYER_SKIP): the new
   view starts at the top. A layer whose entry was left on purpose (layerForget) is not in LAYERS and stays. */
function layersUnwind(then){
  const open = LAYERS.splice(0).reverse();
  open.forEach(l => l.close());
  if (!open.length || !(history.state && history.state.layer)){ then(); return; }
  LAYER_SKIP.push(null);
  window.addEventListener("popstate", () => setTimeout(then), {once: true});
  history.go(-open.length);
}

window.addEventListener("popstate", () => {
  if (LAYER_SKIP.length){
    const y = LAYER_SKIP.shift();
    if (y !== null) requestAnimationFrame(() => window.scrollTo(0, y));
    return;
  }
  const top = LAYERS.pop();
  if (top) top.close();
});
