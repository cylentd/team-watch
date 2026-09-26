/* The pack's cards on its stage (packshow.js): dealt one at a time in the centre, turned, sent to the
   pile at the foot of the screen, the best one given its moment, then every card flown home into
   its roster slot. A card's place is its `translate` and `scale` (individual transforms, so the
   tilt's `transform` in cards.css is left alone); pkMove animates to a place and then writes it
   inline, so no held animation fights the next one. With S.skip every step lands at once. */

async function pkMove(S, el, to, ms, easing){
  if (!S.skip){
    const a = el.animate([{translate: el.style.translate || "0 0", scale: el.style.scale || "1"}, to],
      {duration: ms, easing: easing || pkSpring(el), fill: "forwards"});
    await a.finished;
    a.cancel();
  }
  el.style.translate = to.translate; el.style.scale = to.scale;
}

/* Turn a card face up: edge-on, swap the face, and round with the page's spring. */
async function pkTurn(S, el, big){
  el.classList.remove("pk-down");
  if (S.skip) return;
  el.classList.add("pk-down");
  const a = el.animate([{rotate: "y 0deg"}, {rotate: "y 90deg"}], {duration: big ? 240 : 170, easing: "ease-in", fill: "forwards"});
  await a.finished;
  el.classList.remove("pk-down");
  const b = el.animate([{rotate: "y -90deg"}, {rotate: "y 0deg"}], {duration: big ? 640 : 380, easing: pkSpring(el), fill: "forwards"});
  await b.finished;
  a.cancel(); b.cancel();
}
async function pkSign(S, el){
  const ink = el.querySelector(".tc-sig");
  if (ink && !S.skip) await ink.animate([{clipPath: "inset(0 100% 0 0)"}, {clipPath: "inset(0 0 0 0)"}], {duration: 900, easing: "ease-in-out"}).finished;
}

/* The pile: small at the foot of the screen, fanned a little so the count shows. */
function pkPilePlace(S, k){
  const lift = innerHeight * .55 - 64, fan = (k - (S.cards.length - 1) / 2) * 18;
  return {translate: `${fan}px ${lift}px`, scale: ".3"};
}

async function pkDeal(S){
  for (const [k, c] of S.cards.entries()){
    const wrap = document.createElement("div");
    wrap.innerHTML = cardHTML(c.p, c.i, S.team.key).replace('class="tc ', 'class="tc pk-card pk-down ');
    const el = wrap.firstElementChild;
    S.st.appendChild(el);
    S.shown.push(el);
    const last = k === S.cards.length - 1;
    el.style.translate = "0 70px"; el.style.scale = ".7";
    await pkMove(S, el, {translate: "0 0", scale: "1"}, 360);
    if (last){ await pkHero(S, el, c); break; }
    await pkSleep(S, 180);
    await pkTurn(S, el, false);
    if (!S.skip) S.st.querySelector(".pk-msg").innerHTML = pkLabel(c);
    await pkSign(S, el);
    await pkSleep(S, 650);
    await pkMove(S, el, pkPilePlace(S, k), 480);
  }
}

/* The best card's moment, in the centre: rays behind it, shake, flash, a burst, a size up. */
async function pkHero(S, el, c){
  S.st.classList.add("pk-dim", `pk-best-${S.best}`);
  S.st.querySelector(".pk-msg").innerHTML = "";
  packBuzz([30, 60, 30]);
  if (!S.skip) await el.animate([0, -4, 4, -5, 5, -3, 3, 0].map(x => ({translate: `${x}px 0`})), {duration: 560}).finished;
  if (!S.skip){
    S.st.querySelector(".pk-flash").animate([{opacity: 0}, {opacity: .85, offset: .25}, {opacity: 0}], {duration: 700, easing: "ease-out"});
    const r = el.getBoundingClientRect();
    packBurst(r.left + r.width / 2, r.top + r.height / 2, {n: S.best === "one" ? 110 : 70, tier: S.best, spread: 2});
  }
  await pkMove(S, el, {translate: "0 0", scale: "1.16"}, 500);
  await pkTurn(S, el, true);
  await pkSign(S, el);
  const top = S.cards[S.cards.length - 1];
  S.st.querySelector(".pk-msg").innerHTML = t("teams.pack.done", {name: esc(nameInitial(top.p.n)), rank: top.rank, pos: esc(top.p.pos)});
  await pkSleep(S, 1500);
}

/* The stage fades to the roster and every card flies from where it is into its empty slot. */
async function pkHome(S){
  S.st.classList.add("pk-home");
  const view = document.getElementById("view");
  view.querySelector(".cards")?.scrollIntoView({block: "start", behavior: "instant"});
  window.scrollBy(0, -90);
  await pkSleep(S, 260);
  await Promise.all(S.shown.map(async (el, k) => {
    const slot = view.querySelector(`.cards .tc[data-pk="${k}"]`);
    if (slot && !S.skip){
      const a = el.getBoundingClientRect(), b = slot.getBoundingClientRect(), s = parseFloat(el.style.scale || "1");
      const [tx, ty] = (el.style.translate || "0 0").split(" ").map(parseFloat);
      await pkSleep(S, k * 90);
      await pkMove(S, el, {translate: `${tx + (b.left + b.width / 2) - (a.left + a.width / 2)}px ${ty + (b.top + b.height / 2) - (a.top + a.height / 2)}px`,
        scale: String(s * b.width / a.width)}, 620);
    }
    slot?.classList.remove("pk-slot");
    el.remove();
  }));
  layerDone("pack");
  pkClose(S);
}
