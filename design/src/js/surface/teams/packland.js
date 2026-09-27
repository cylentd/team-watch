/* The pack's cards going home to their roster slots (split from packdeal.js 2026-09-27). */

/* Home (reworked 2026-09-27: every card flew at once while the page jumped to the cards under
   them). The page scrolls first, while the room is still dark; then the room fades and the cards
   land one at a time, PK_LAND_STEP apart, the best card first (last, it read as a card stuck on the
   screen): each lifts to just above its slot a size too big, drops, squashes on impact, kicks up
   smoke along the ground and knocks the cards beside it. */
const PK_LAND_STEP = 150;
async function pkHome(S){
  S.homing = true; S.rush = false;
  const view = document.getElementById("view");
  view.querySelector(".cards")?.scrollIntoView({block: "start", behavior: "instant"});
  window.scrollBy(0, -90);
  await new Promise(r => requestAnimationFrame(r));
  S.st.classList.add("pk-home");
  S.st.querySelectorAll(".pk-ring,.pk-aura,.pk-sheen").forEach(x => {
    if (S.skip) return x.remove();
    x.animate([{opacity: getComputedStyle(x).opacity}, {opacity: 0}], {duration: 150, fill: "forwards"}).finished.then(() => x.remove());
  });
  // The best card leaves at once, as the room starts to fade; the pile follows once it has gone
  // (2026-09-27: it waited out the fade in the middle of the screen and read as stuck).
  const last = S.shown.length - 1, order = [last, ...S.shown.keys()].filter((k, i) => i === 0 || k !== last);
  await Promise.all(order.map(async (k, i) => {
    const el = S.shown[k], slot = view.querySelector(`.cards .tc[data-pk="${k}"]`);
    if (slot && !S.skip){
      await pkSleep(S, i ? 250 + i * PK_LAND_STEP : 0);
      await pkLand(S, el, slot);
    }
    slot?.classList.remove("pk-slot");
    el.remove();
  }));
  layerDone("pack");
  pkClose(S);
}

/* An empty pack (2026-09-27): nobody on the roster made the top 12 this week. It is ripped like
   any other, then turned upside down and shaken, and nothing falls out but a puff of dust. The line
   says so, the pile counts 0, and it drops away. A tap, ✕ or Escape goes sooner. The line stays
   body size in the lead's place: as a headline it would sit on the pack. */
async function pkEmpty(S){
  const center = S.pack, moving = center && !S.skip;
  S.pack = null;
  S.st.querySelector(".pk-hint").textContent = "";
  if (moving){
    await pkAnim(S, center, [{rotate: "0deg"}, {rotate: "180deg"}], {duration: 520, easing: "cubic-bezier(.25,1,.5,1)", fill: "forwards"}).finished;
    await pkAnim(S, center, [0, -9, 9, -7, 7, -4, 4, 0].map(x => ({translate: `calc(-50% + ${x}px) -50%`, rotate: "180deg"})), {duration: 640}).finished;
    const r = center.querySelector(".pack-seal").getBoundingClientRect();
    packPuff(r.left + r.width / 2, r.bottom, r.width * .6);
    packBuzz(10);
  }
  S.st.querySelector(".pk-msg").innerHTML = t("teams.pack.empty");
  S.st.querySelector(".pk-count").textContent = t("teams.pack.count", {n: 0});
  await new Promise(r => { setTimeout(r, 2600); S.wake.add(r); S.st.addEventListener("click", r, {once: true}); });
  if (moving && !S.skip) await pkAnim(S, center, [{translate: "-50% -50%", rotate: "180deg", opacity: 1}, {translate: "-50% 10%", rotate: "180deg", opacity: 0}],
    {duration: 340, easing: "cubic-bezier(.5,0,.75,0)", fill: "forwards"}).finished;
  layerDone("pack");
  pkClose(S);
}

/* One card onto its slot. Centres from the boxes (a leaning card's box is wider than the card; its
   centre is not moved), the width from the layout, so the lean does not skew the scale. */
async function pkLand(S, el, slot){
  const a = el.getBoundingClientRect(), b = slot.getBoundingClientRect();
  const [tx, ty] = (el.style.translate || "0 0").split(" ").map(parseFloat);
  const s = b.width / el.offsetWidth, x = tx + (b.left + b.width / 2) - (a.left + a.width / 2), y = ty + (b.top + b.height / 2) - (a.top + a.height / 2);
  const at = `${x}px ${y}px`;
  if (S.skip) return;
  // One arc, never at rest (2026-09-27: a rise that eased to a stop above the slot, then a separate
  // drop, left every card hanging there for a beat, which read as stuck). The top of the arc is
  // short of the slot, so the card is still travelling across as it falls, and neither half ends
  // at a standstill; the fall gathers speed into the slot.
  const from = {translate: el.style.translate || "0 0", scale: el.style.scale || "1", rotate: el.style.rotate || "0deg"};
  const fx = parseFloat(from.translate) || 0;
  await pkAnim(S, el, [
    {...from, easing: "cubic-bezier(.25,.55,.5,.9)"},
    {translate: `${fx + (x - fx) * .85}px ${y - b.height * .6}px`, scale: String(s * 1.3), rotate: "0deg", offset: .72, easing: "cubic-bezier(.45,.25,1,.7)"},
    {translate: at, scale: String(s), rotate: "0deg"}], {duration: 500, fill: "forwards"}).finished;
  Object.assign(el.style, {translate: at, scale: String(s), rotate: "0deg"});
  el.getAnimations().forEach(a => a.cancel());
  packBuzz(14);
  packPuff(b.left + b.width / 2, b.bottom - 2, b.width);
  pkKnock(S, slot);
  // The squash keeps the card's foot on the ground: wide and short, then a touch tall, then still.
  await pkAnim(S, el, [
    {scale: `${s * 1.08} ${s * .88}`, translate: `${x}px ${y + b.height * .06}px`},
    {scale: `${s * .97} ${s * 1.03}`, translate: `${x}px ${y - b.height * .015}px`, offset: .5},
    {scale: String(s), translate: at}], {duration: 240, easing: "ease-out"}).finished;
}

/* The landing knocks the cards on either side of it in its row down and back. */
function pkKnock(S, slot){
  const row = [...slot.parentElement.children].filter(n => n !== slot && n.classList.contains("tc") && Math.abs(n.offsetTop - slot.offsetTop) < 4);
  row.forEach(n => pkAnim(S, n, [{translate: "0 0"}, {translate: "0 3px", offset: .3}, {translate: "0 0"}], {duration: 220, easing: "ease-out"}));
}
