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
    x.animate([{opacity: getComputedStyle(x).opacity}, {opacity: 0}], {duration: 200, fill: "forwards"}).finished.then(() => x.remove());
  });
  await pkSleep(S, 250);
  const last = S.shown.length - 1, order = [last, ...S.shown.keys()].filter((k, i) => i === 0 || k !== last);
  await Promise.all(order.map(async (k, i) => {
    const el = S.shown[k], slot = view.querySelector(`.cards .tc[data-pk="${k}"]`);
    if (slot && !S.skip){
      await pkSleep(S, i * PK_LAND_STEP);
      await pkLand(S, el, slot);
    }
    slot?.classList.remove("pk-slot");
    el.remove();
  }));
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
  await pkMove(S, el, {translate: `${x}px ${y - b.height * .6}px`, scale: String(s * 1.3), rotate: "0deg"}, 360, "cubic-bezier(.3,.7,.3,1)");
  await pkMove(S, el, {translate: at, scale: String(s)}, 140, "cubic-bezier(.6,0,1,.6)");   // the drop gathers speed
  if (S.skip) return;
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
