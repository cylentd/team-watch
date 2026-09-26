/* Deal me 3, drawn (2026-09-25; the dealing is builder/deal.js). The kickoff's approved picks sit
   in a row of faces, the deck, so the reader sees what the slips were dealt from. A deal shuffles
   the deck in place, then each chosen face flies into its row in its slip, 70ms apart so every
   pick is a landing that can be counted; the faces not dealt dim. The motion ends where the pick
   now lives (STYLE.md, Motion). A redeal leaves the model's pick where it is. */

function dealButtonHTML(w){
  if (PARLAY_BOOK !== "underdog" || !dealOK(w) || DEALS[w.k]) return "";
  return `<button class="tk-dealbtn" type="button" data-deal="${esc(w.k)}">${t("parlay.deal.button")}</button>`;
}

function dealBlockHTML(w, name){
  const d = PARLAY_BOOK === "underdog" && DEALS[w.k];
  if (!d) return "";
  const pool = dealPool(w);
  const deck = pool.map(i => {
    const p = PROPS[i], team = (TEAM_COLOURS[p.team] || [])[0];
    return `<span class="tk-face" data-slug="${esc(p.slug)}" title="${esc(nameInitial(p.n))}"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(p)}</span>`;
  }).join("");
  const tiers = [["medium", t("parlay.deal.tier.medium")], ["hard", t("parlay.deal.tier.hard")], ["model", t("parlay.deal.tier.model")]];
  const cards = tiers.filter(([tier]) => d[tier]).map(([tier, pill]) => presetCard(
    {book: "underdog", scope: tier === "hard" ? "long" : "mix", scopeLabel: t("parlay.deal.from"),
     win: w, legs: d[tier], low: false, i: `deal-${w.k}-${tier}`},
    false, name, {load: `${w.k}:${tier}`, pill, tone: tier})).join("");
  return `<div class="tk-deal" data-dealt="${esc(w.k)}">
      <div class="tk-deckhead"><span>${t("parlay.deal.deck", {n: pool.length})}</span>
        <button class="tk-again" type="button" data-deal="${esc(w.k)}">${t("parlay.deal.again")}</button></div>
      <div class="tk-deck">${deck}</div>
      <div class="tk-grid">${cards}</div>
    </div>`;
}

/* After the render that drew a fresh deal: shuffle the deck (FLIP), then fly each dealt face. */
function dealPlay(){
  const fresh = DEAL_FRESH;
  DEAL_FRESH = null;
  const block = fresh && document.querySelector(`.tk-deal[data-dealt="${CSS.escape(fresh.k)}"]`);
  if (!block || REDUCED()) return;
  const deck = block.querySelector(".tk-deck");
  const faces = [...deck.children];
  const before = new Map(faces.map(f => [f, f.getBoundingClientRect()]));
  dealShuffle(faces.map((_, k) => k)).forEach(k => deck.appendChild(faces[k]));
  const spring = betsCss("--spring"), dur = parseFloat(betsCss("--dur-spring")) * 1000 || 460;
  faces.forEach(f => {
    const a = before.get(f), b = f.getBoundingClientRect();
    f.animate([{transform: `translate(${a.left - b.left}px,${a.top - b.top}px)`}, {transform: "none"}], {duration: 300, easing: spring});
  });
  const targets = [...block.querySelectorAll(".ticket" + (fresh.model ? "" : ":not(.model)") + " .tk-leg .tk-face")];
  const dealt = new Set(targets.map(el => el.dataset.slug));
  targets.forEach(el => { el.style.opacity = "0"; });
  setTimeout(() => {
    faces.forEach(f => f.classList.toggle("out", !dealt.has(f.dataset.slug)));
    targets.forEach((to, k) => setTimeout(() => {
      const from = deck.querySelector(`.tk-face[data-slug="${CSS.escape(to.dataset.slug)}"]`);
      if (!from){ to.style.opacity = ""; return; }
      const a = from.getBoundingClientRect(), b = to.getBoundingClientRect();
      const fly = from.cloneNode(true);
      fly.classList.remove("out");
      fly.classList.add("tk-fly");
      Object.assign(fly.style, {left: `${a.left}px`, top: `${a.top}px`, width: `${a.width}px`, height: `${a.height}px`});
      document.body.appendChild(fly);
      fly.animate([{transform: "translate(0,0) scale(1)"},
        {transform: `translate(${b.left - a.left}px,${b.top - a.top}px) scale(${b.width / a.width})`}],
        {duration: dur, easing: spring, fill: "forwards"}).finished.then(() => { to.style.opacity = ""; fly.remove(); });
    }, k * 70));
  }, 300);
}

function wireDeal(v){
  v.querySelectorAll("[data-deal]").forEach(b => b.addEventListener("click", () => {
    const w = GAL_GROUPS.find(g => g.k === b.dataset.deal);
    if (!w) return;
    dealFor(w);
    const y = window.scrollY; render(); window.scrollTo(0, y);
    dealPlay();
  }));
  // A dealt slip loads like a gallery one: its legs pour into the tray.
  v.querySelectorAll("[data-loaddeal]").forEach(b => b.addEventListener("click", () => {
    const [k, tier] = b.dataset.loaddeal.split(":");
    const legs = DEALS[k] && DEALS[k][tier];
    if (!legs) return;
    const from = [...b.closest(".ticket").querySelectorAll(".tk-leg")].map(el => el.getBoundingClientRect());
    SLIP = legs.slice(); SLIP_MODE = "custom";
    const y = window.scrollY; render(); window.scrollTo(0, y);
    betsPour(from, SLIP.map(i => PROPS[i].n));
  }));
}
