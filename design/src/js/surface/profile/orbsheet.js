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
   box, in the viewBox's own percentages). `back` runs it from overhead down to the badge's view.

   The hand-over happens while it moves, not after (2026-09-29, David: "it flickers towards the end").
   The solid, lit crystal and the flat chart's translucent fill are not the same picture even when
   their outlines agree, and a cross-fade started once the camera stopped read as the shape
   blinking. So the canvas fades over the last third of the swing (ORB_HANDOVER) as the crystal
   flattens onto the chart under it, and is gone the moment it lands. Its first frame is drawn at
   once, too: a blank canvas for one frame showed the flat chart before the crystal. */
const ORB_HANDOVER = .35;
/* By the clock, not by the eased position: ease-out has the crystal 65% flat a third of the way in,
   and a fade keyed to that would start while it is still a sphere. `u` is the share of the time
   gone; opening fades out at the end, closing fades in at the start. */
const orbAlpha = (u, back) => Math.max(0, Math.min(1, (back ? u : 1 - u) / ORB_HANDOVER));
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
  const col = orbColors(layer.querySelector(".pf-sheet"));
  const y0 = (ORB_STATE.get(btn) || {yaw: 0}).yaw, yHome = y0 > Math.PI ? ORB_TAU : 0;
  const at = u => {
    const s = back ? 1 - u : u, e = 1 - Math.pow(1 - s, 3);
    cv.style.opacity = orbAlpha(u, back);
    orbDraw(cv, geo, col, y0 + (yHome - y0) * e, ORB_PITCH + (ORB_TOP - ORB_PITCH) * e, cv.clientWidth / 2);
  };
  at(0);
  const t0 = performance.now();
  const step = now => {
    const u = Math.min(1, (now - t0) / ms);
    at(u);
    if (u < 1){ requestAnimationFrame(step); return; }
    if (done) done();
  };
  requestAnimationFrame(step);
}

/* Centred once, then held (2026-09-29, David: tapping a stat "will expand the shape of the
   container which causes the content to jump"). A centred box re-centres on every fold, so the
   chart moved up by half of each fold's height under the reader's finger. Its top is pinned where
   it opened, and a fold grows it downward only, to the layer's edge, then the sheet scrolls. */
function orbPin(sheet){
  const top = sheet.offsetTop;
  sheet.style.top = `${top}px`;
  sheet.style.bottom = "auto";
  sheet.style.maxHeight = `calc(100% - ${top + 12}px)`;
}

/* The layer keeps the reader's scroll and swipe (2026-09-29, David: "scrolling or swiping on this
   modal will move the content behind it"). A wheel or a touch drag reaches the profile or the page
   under the layer whenever the sheet has nothing to scroll or the finger is on the scrim, because
   `inert` stops focus and clicks, not scroll chaining. So both are cancelled unless they land in
   the sheet while it can scroll; overscroll-behavior (orb.css) holds the sheet's own ends. The
   profile's swipe gestures stand down while the layer is up (modal.js). */
function orbHoldScroll(layer, sheet){
  const hold = e => { if (!sheet.contains(e.target) || sheet.scrollHeight <= sheet.clientHeight) e.preventDefault(); };
  layer.addEventListener("wheel", hold, {passive: false});
  layer.addEventListener("touchmove", hold, {passive: false});
}

function orbOpen(d, p, btn){
  if (d.querySelector(".pf-orblayer") || !sheetFor(p)) return;
  const s = sheetFor(p);
  const layer = document.createElement("div");
  layer.className = "pf-orblayer";
  layer.setAttribute("data-testid", "profile-orblayer");
  layer.innerHTML = `<div class="pf-orbscrim" data-testid="profile-orbscrim"></div>
    <div class="pf-orbsheet" data-testid="profile-orbsheet" role="dialog" aria-modal="true" aria-labelledby="pf-orb-t">
      <div class="pf-orbsheet-h"><div><h4 id="pf-orb-t">${esc(p.n)}</h4>
        <span class="lbl">${t("profile.orb.sub", {pos: esc(s.pos)})}</span></div>
        <button type="button" class="dr-close pf-orb-x" aria-label="${t("profile.orb.close")}">✕</button></div>
      ${radarHTML(p)}</div>`;
  // The crystal is this sheet's entrance: the flat shape's own grow-in (sheet.css, .74s) stands
  // down before it can start, or it would still be growing when the crystal lands on it.
  layer.querySelector(".pf-sheet").classList.add("js-grow");
  d.appendChild(layer);
  [...d.children].forEach(c => { if (c !== layer) c.inert = true; });
  btn.dataset.open = "1";
  wireSheet(layer, {grow: false});
  const sheet = layer.querySelector(".pf-orbsheet");
  orbPin(sheet);
  orbHoldScroll(layer, sheet);
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
