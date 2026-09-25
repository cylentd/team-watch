/* The pack opens into the roster (2026-09-25; it opened onto a stage over the page the same day).
   Ripping it re-renders the Cards view with the pack's players face down in their real lineup
   slots, and they turn over by themselves, worst first, about a second apart, so you watch your
   own lineup fill in. The last card is the best, and gets the moment where it sits: the page dims
   around it, rays turn behind it, a flash, a burst of flakes in its tier's colours, a spin a size
   up, and its signature written in; then it settles back into its slot.
   A tap anywhere hurries the card that is turning (it never flips a card by accident); Skip turns
   the rest at once. On a phone each card is scrolled into view before it turns. Reduced motion
   shows every card face up at once. */
let PACK_REVEAL = null;     // "<league>-<week>" while this week's pack is turning over in the roster
let PACK_ORDER = new Map(); // profile index -> turn order (0 turns first, the best card last)

const packRevealing = team => !!team && PACK_REVEAL === `${team.key}-${packWeek()}`;
/* A pack card is drawn face down while the pack is turning over; everything else as usual. */
function packFaceDown(team, i, html){
  if (!packRevealing(team) || !PACK_ORDER.has(i)) return html;
  return html.replace('class="tc ', `data-pk="${PACK_ORDER.get(i)}" class="tc pk-down `);
}
/* The line above the cards while they turn: what just turned, and Skip. */
function packLiveHTML(team){
  return `<div class="pack pack-live"><p class="pack-msg" aria-live="polite">${t("teams.pack.turning", {n: packCards(team).length})}</p>
    <button class="chip pk-skip" type="button">${t("teams.pack.skip")}</button></div>`;
}

// Spelled out one call each: assemble.py --check finds a key only in a literal lookup.
const PACK_TIER_LABEL = {one: () => t("teams.pack.tier.one"), sig: () => t("teams.pack.tier.sig"),
                         sr: () => t("teams.pack.tier.sr"), ur: () => t("teams.pack.tier.ur")};
function pkLabel(c){
  return `<b>${t("teams.card.rank", {n: c.rank, pos: esc(c.p.pos)})}</b> · ${PACK_TIER_LABEL[cardTier(c.rank)]()}`;
}
const pkSpring = el => getComputedStyle(el).getPropertyValue("--spring").trim() || "ease-out";

/* Turn a card face up: edge-on, swap the face, and on round with the page's spring. */
async function pkTurn(el, big){
  await el.animate([{rotate: "y 0deg"}, {rotate: "y 90deg"}], {duration: big ? 220 : 160, easing: "ease-in", fill: "forwards"}).finished;
  el.classList.remove("pk-down");
  await el.animate([{rotate: "y -90deg", scale: big ? ".8" : "1"}, {rotate: "y 0deg", scale: big ? "1.18" : "1.06"}],
    {duration: big ? 620 : 360, easing: pkSpring(el), fill: "forwards"}).finished;
  el.getAnimations().forEach(a => a.cancel());
}
async function pkSign(el){
  const ink = el.querySelector(".tc-sig");
  if (ink) await ink.animate([{clipPath: "inset(0 100% 0 0)"}, {clipPath: "inset(0 0 0 0)"}], {duration: 900, easing: "ease-in-out"}).finished;
}

/* Everything the run shares: the cards in turn order, the message line, and how to wake a wait. */
function pkRunState(team){
  const v = document.getElementById("view");
  const cards = packCards(team);
  return {v, cards, best: cardTier(cards[cards.length - 1].rank), skip: false, wake: null,
    els: [...v.querySelectorAll(".cards .tc[data-pk]")].sort((a, b) => a.dataset.pk - b.dataset.pk),
    msg: v.querySelector(".pack-live .pack-msg")};
}
const pkSleep = (S, ms) => new Promise(r => { const id = setTimeout(r, ms); S.wake = () => { clearTimeout(id); r(); }; });
function pkHurry(S){
  S.v.getAnimations({subtree: true}).forEach(a => { if (a.effect && a.effect.getTiming().iterations !== Infinity) a.finish(); });
  document.querySelectorAll(".pk-scrim").forEach(l => l.getAnimations({subtree: true})
    .forEach(a => { if (a.effect.getTiming().iterations !== Infinity) a.finish(); }));
  if (S.wake) S.wake();
}
/* Bring a card on screen before it turns: a phone shows three rows, and the bench is below. */
async function pkShow(S, el){
  const r = el.getBoundingClientRect(), top = r.top < 70, bottom = r.bottom > innerHeight - 70;
  if (!top && !bottom) return;
  el.scrollIntoView({behavior: "smooth", block: "center"});
  await pkSleep(S, 420);
}

async function packRevealRun(team){
  const S = pkRunState(team);
  if (!S.els.length) return;
  // While the pack turns, a tap hurries it instead of reaching a card (which would flip it over).
  const tap = e => {
    e.stopPropagation(); e.preventDefault();
    if (e.target.closest(".pk-skip")){ S.skip = true; pkHurry(S); } else pkHurry(S);
  };
  window.addEventListener("click", tap, true);
  if (!REDUCED()){
    await pkSleep(S, 350);
    for (const [k, el] of S.els.entries()){
      if (S.skip) break;
      await pkShow(S, el);
      if (k === S.els.length - 1){ await packHero(S, el); break; }
      await pkTurn(el, false);
      S.msg.innerHTML = pkLabel(S.cards[k]);
      if (el.querySelector(".tc-sig")) await pkSign(el);
      await pkSleep(S, 520);
    }
  }
  window.removeEventListener("click", tap, true);
  packRevealEnd(S);
}

/* The best card's moment, where it sits: the page dims around it, rays turn behind it. */
async function packHero(S, el){
  const r = el.getBoundingClientRect();
  const layer = document.createElement("div");
  layer.className = `pk-scrim pk-best-${S.best}`;
  layer.style.setProperty("--cx", `${r.left + r.width / 2}px`);
  layer.style.setProperty("--cy", `${r.top + r.height / 2}px`);
  layer.innerHTML = `<div class="pk-rays"></div><div class="pk-flash"></div>`;
  document.body.appendChild(layer);
  el.classList.add("pk-hero");
  requestAnimationFrame(() => layer.classList.add("on"));
  S.msg.innerHTML = "";
  packBuzz([30, 60, 30]);
  await el.animate([0, -4, 4, -5, 5, -3, 3, 0].map(x => ({translate: `${x}px 0`})), {duration: 560}).finished;
  layer.querySelector(".pk-flash").animate([{opacity: 0}, {opacity: .85, offset: .25}, {opacity: 0}], {duration: 700, easing: "ease-out"});
  packBurst(r.left + r.width / 2, r.top + r.height / 2, {n: S.best === "one" ? 110 : 70, tier: S.best, spread: 2});
  await pkTurn(el, true);
  await pkSign(el);
  await pkSleep(S, 1100);
  layer.classList.remove("on");
  el.classList.remove("pk-hero");
  setTimeout(() => layer.remove(), 500);
}

/* Every card face up, the line says who the best card is, and Done puts the roster back. */
function packRevealEnd(S){
  S.v.querySelectorAll(".cards .tc.pk-down").forEach(el => el.classList.remove("pk-down"));
  S.v.querySelectorAll(".cards .tc.pk-hero").forEach(el => el.classList.remove("pk-hero"));
  document.querySelectorAll(".pk-scrim").forEach(l => l.remove());
  const top = S.cards[S.cards.length - 1];
  S.msg.innerHTML = t("teams.pack.done", {name: esc(nameInitial(top.p.n)), rank: top.rank, pos: esc(top.p.pos)});
  const bar = S.v.querySelector(".pack-live");
  bar.querySelector(".pk-skip")?.remove();
  const done = document.createElement("button");
  done.type = "button"; done.className = "chip pack-done"; done.textContent = t("teams.pack.close");
  done.addEventListener("click", () => { PACK_REVEAL = null; render(); });
  bar.appendChild(done);
}
