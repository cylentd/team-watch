/* The stat sheet the sphere opens: the flat radar and its card (sheet.js radarHTML, unchanged) in a
   layer over the profile, inside #modal rather than a third dialog, so the profile under it keeps
   its scroll and its tab and the reader lands back exactly where they tapped.

   The entrance is one motion with two halves that end in the same place. The layer grows out of
   the badge (a FLIP from the badge's box), and at the same time the sphere, drawn over the flat
   chart's disc, swings its camera from ORB_PITCH to straight overhead and unwinds its turn to the
   radar's orientation. From overhead the crystal is exactly the flat shape, so when the canvas
   fades the SVG is already there under it: the sphere became the chart. The labels and the elite
   arcs come in after. Closing runs both halves backwards into the badge.

   Back closes it before it closes the profile (layers.js); Escape inside it closes it alone. */
const ORB_LAYER = "pf-orb";

/* STYLE.md's "Move" beat: --spring over --dur-spring out of the badge, --ease back into it. Read
   from the tokens, because WAAPI takes an easing string and not a var(), and a curve spelled here
   would be a second definition of the house motion. */
function flipFrom(el, from, reverse){
  const to = el.getBoundingClientRect(), f = from.getBoundingClientRect();
  const small = `translate(${f.left - to.left}px,${f.top - to.top}px) scale(${f.width / to.width},${f.height / to.height})`;
  const frames = [{transform: small, opacity: .3, borderRadius: "50%"}, {transform: "none", opacity: 1, borderRadius: "14px"}];
  const tok = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const ms = parseFloat(tok("--dur-spring")) * 1000 || 460;
  return el.animate(reverse ? frames.reverse() : frames,
    {duration: reverse ? 300 : ms, easing: (reverse ? tok("--ease") : tok("--spring")) || "ease-out"});
}

/* The camera move, drawn on a canvas laid exactly over the flat chart's disc (.pf-radar-hit is that
   box, in the viewBox's own percentages). `back` runs it from overhead down to the badge's view. */
function orbMorph(layer, btn, p, back, ms, done){
  const box = layer.querySelector(".pf-radar-box"), hit = box && box.querySelector(".pf-radar-hit");
  const geo = orbGeo(p);
  if (!hit || !geo){ if (done) done(); return; }
  let cv = box.querySelector(".pf-orb-morph");
  if (!cv){
    cv = document.createElement("canvas");
    cv.className = "pf-orb-morph"; cv.setAttribute("aria-hidden", "true");
    ["left", "top", "width", "height"].forEach(k => { cv.style[k] = hit.style[k]; });
    box.appendChild(cv);
  }
  cv.classList.remove("gone");
  const col = orbColors(layer.querySelector(".pf-sheet"));
  const y0 = (ORB_STATE.get(btn) || {yaw: 0}).yaw, yHome = y0 > Math.PI ? ORB_TAU : 0;
  const at = e => orbDraw(cv, geo, col, y0 + (yHome - y0) * e, ORB_PITCH + (ORB_TOP - ORB_PITCH) * e, cv.clientWidth / 2);
  const t0 = performance.now();
  const step = now => {
    const u = Math.min(1, (now - t0) / ms), s = back ? 1 - u : u;
    at(1 - Math.pow(1 - s, 3));
    if (u < 1){ requestAnimationFrame(step); return; }
    if (!back) cv.classList.add("gone");
    if (done) done();
  };
  requestAnimationFrame(step);
}

function orbOpen(d, p, btn){
  if (d.querySelector(".pf-orblayer") || !sheetFor(p)) return;
  const s = sheetFor(p);
  const layer = document.createElement("div");
  layer.className = "pf-orblayer";
  layer.innerHTML = `<div class="pf-orbscrim"></div>
    <div class="pf-orbsheet" role="dialog" aria-modal="true" aria-labelledby="pf-orb-t">
      <div class="pf-orbsheet-h"><div><h4 id="pf-orb-t">${esc(p.n)}</h4>
        <span class="lbl">${t("profile.orb.sub", {pos: esc(s.pos)})}</span></div>
        <button type="button" class="dr-close pf-orb-x" aria-label="${t("profile.orb.close")}">✕</button></div>
      ${radarHTML(p)}</div>`;
  d.appendChild(layer);
  [...d.children].forEach(c => { if (c !== layer) c.inert = true; });
  btn.dataset.open = "1";
  wireSheet(layer, {grow: false});
  const sheet = layer.querySelector(".pf-orbsheet");
  const shut = () => orbClose(d, true);
  layer.querySelector(".pf-orb-x").addEventListener("click", shut);
  layer.querySelector(".pf-orbscrim").addEventListener("click", shut);
  layer.addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); shut(); } });
  layer.querySelector(".pf-orb-x").focus({preventScroll: true});
  layerPush(ORB_LAYER, () => orbClose(d, false));
  if (REDUCED()) return;
  sheet.classList.add("morph");
  flipFrom(sheet, btn, false);
  orbMorph(layer, btn, p, false, 720, () => { sheet.classList.remove("morph"); sheet.classList.add("shown"); });
}

/* `fromPage` is a close the page started (✕, scrim, Escape), which takes its history entry back;
   Back has already popped it. */
function orbClose(d, fromPage){
  const layer = d.querySelector(".pf-orblayer");
  if (!layer || layer.dataset.closing) return;
  layer.dataset.closing = "1";
  if (fromPage) layerDone(ORB_LAYER);
  const btn = d.querySelector(".pf-orb"), sheet = layer.querySelector(".pf-orbsheet");
  const end = () => {
    layer.remove();
    [...d.children].forEach(c => { c.inert = false; });
    if (btn){ delete btn.dataset.open; btn.focus({preventScroll: true}); }
  };
  if (REDUCED() || !btn || !btn.isConnected) return end();
  sheet.classList.add("morph");
  layer.classList.add("closing");
  orbMorph(layer, btn, ORB_PROFILE.get(d), true, 300);
  flipFrom(sheet, btn, true).onfinish = end;
}

/* The player the open profile is about, for a close that has only the dialog in hand. */
const ORB_PROFILE = new WeakMap();

function wireOrbSheet(d, p){
  const btn = d.querySelector(".pf-orb");
  if (!btn) return;
  ORB_PROFILE.set(d, p);
  wireOrb(btn, p);
  btn.addEventListener("click", () => orbOpen(d, p, btn));
}
