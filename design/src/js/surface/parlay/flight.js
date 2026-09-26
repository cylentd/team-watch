/* Bets motion (2026-09-25), the four moments of the storyboard, each ending where its thing now
   lives (design/STYLE.md, "Motion"):
     a pick flies from its line to the tray, and the tray counts it and rolls the chance;
     "Load slip" pours the ticket's legs into the tray one by one, counted as they land;
     the tray grows into the sheet, the leg bars draw, then the all-hit bar, shorter;
     a filter slides the cards that stay and fades the ones that go.
   render() rebuilds #view on every tap, so each motion measures before the render and plays
   after it. Under reduced motion every function jumps to its end state. */
const betsCss = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const betsTray = () => document.querySelector(".tray");

/* The tray's count and chance, set in place without a render, so they can change on landing. */
function betsSetTray(n, pctText){
  const tray = betsTray();
  if (!tray) return;
  tray.classList.toggle("empty", !n);
  tray.querySelector(".tray-n").textContent = n;
  tray.querySelector(".tray-pc").textContent = n ? pctText : t("parlay.tray.empty");
}

function betsPop(){
  const n = betsTray()?.querySelector(".tray-n");
  if (n && !REDUCED()) n.animate([{transform: "scale(1)"}, {transform: "scale(1.5)"}, {transform: "scale(1)"}],
    {duration: parseFloat(betsCss("--dur-pop")) * 1000 || 690, easing: betsCss("--spring-pop")});
}

/* The chance rolls from what it was to what it is, so the cost of a leg is seen, not inferred. */
function betsLand(n, was){
  const now = betsSlipPct();
  betsSetTray(n, betsPctText(now));
  betsPop();
  const pc = betsTray()?.querySelector(".tray-pc");
  if (!pc || now === null || REDUCED()) return;
  const from = was === null || was === undefined ? 100 : was, t0 = performance.now();
  const step = at => {
    const k = Math.min(1, (at - t0) / 460), e = 1 - Math.pow(1 - k, 3);
    pc.textContent = betsPctText(from + (now - from) * e);
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* A chip with the player's name, from where he was tapped to the tray. */
function betsChip(from, label){
  const tray = betsTray();
  if (!tray || REDUCED()) return Promise.resolve();
  const to = tray.getBoundingClientRect();
  const chip = document.createElement("div");
  chip.className = "bets-fly"; chip.textContent = label;
  chip.style.left = `${from.left + 8}px`; chip.style.top = `${from.top + from.height / 2 - 14}px`;
  document.body.appendChild(chip);
  const dx = to.left + 28 - (from.left + 8), dy = to.top + 10 - (from.top + from.height / 2 - 14);
  return chip.animate([
    {transform: "translate(0,0) scale(1)", opacity: 1},
    {transform: `translate(${dx * .5}px,${dy * .35}px) scale(1.05)`, opacity: 1, offset: .45},
    {transform: `translate(${dx}px,${dy}px) scale(.6)`, opacity: .2}
  ], {duration: 520, easing: betsCss("--ease-flight") || "ease"}).finished.then(() => chip.remove());
}

function betsFly(from, name, was){
  const n = SLIP.length;
  betsSetTray(n - 1, betsPctText(was ?? null));
  betsChip(from, nameInitial(name)).then(() => betsLand(n, was));
}

/* 70ms apart, so each leg is a separate landing a reader can count. */
function betsPour(rects, names){
  const n = names.length;
  if (REDUCED()) return betsLand(n, null);
  betsSetTray(0, "");
  names.forEach((name, k) => setTimeout(() => betsChip(rects[k] || rects[0], nameInitial(name)).then(() => {
    if (k < n - 1){ betsSetTray(k + 1, "…"); betsPop(); } else betsLand(n, null);
  }), k * 70));
}

/* FLIP over the slip cards: measure, render, then slide each kept card from where it was and fade
   a ghost of each card that left. Cards arriving rise in on the view's own stagger. */
function betsFlip(fn){
  const before = new Map([...document.querySelectorAll(".ticket[data-card]")].map(el => [el.dataset.card, {el, r: el.getBoundingClientRect()}]));
  fn();
  if (REDUCED()) return;
  const spring = betsCss("--spring"), dur = parseFloat(betsCss("--dur-spring")) * 1000 || 460;
  const now = new Set();
  document.querySelectorAll(".ticket[data-card]").forEach(el => {
    now.add(el.dataset.card);
    const was = before.get(el.dataset.card);
    if (!was) return;
    const r = el.getBoundingClientRect();
    el.animate([{transform: `translate(${was.r.left - r.left}px,${was.r.top - r.top}px)`}, {transform: "none"}], {duration: dur, easing: spring});
  });
  before.forEach(({el, r}, id) => {
    if (now.has(id)) return;
    const ghost = el.cloneNode(true);
    Object.assign(ghost.style, {position: "fixed", left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, margin: 0, pointerEvents: "none", zIndex: 20});
    document.body.appendChild(ghost);
    ghost.animate([{opacity: 1, transform: "scale(1)"}, {opacity: 0, transform: "scale(.97)"}], {duration: 180, fill: "forwards"}).finished.then(() => ghost.remove());
  });
}

/* The tray grows into the sheet: it rises on the hand's spring, then the bars draw, legs first. */
function betsSheetOpen(){
  BETS_SHEET = true; render();
  const sheet = document.querySelector(".slipsheet");
  if (!sheet) return;
  sheet.querySelector(".grab")?.focus({preventScroll: true});
  if (REDUCED()) return;
  sheet.animate([{transform: "translateY(100%)"}, {transform: "translateY(0)"}],
    {duration: parseFloat(betsCss("--dur-spring")) * 1000 || 460, easing: betsCss("--spring")});
  sheet.querySelectorAll(".odds-bar > i").forEach((i, k, all) => i.animate([{width: "0%"}, {width: i.style.getPropertyValue("--w")}],
    {duration: 520, delay: 200 + k * 90 + (k === all.length - 1 ? 120 : 0), easing: betsCss("--ease"), fill: "backwards"}));
}

function betsSheetClose(){
  const sheet = document.querySelector(".slipsheet");
  const done = () => { BETS_SHEET = false; render(); betsTray()?.focus({preventScroll: true}); };
  if (!sheet || REDUCED()) return done();
  sheet.animate([{transform: "translateY(0)"}, {transform: "translateY(100%)"}], {duration: 260, easing: "cubic-bezier(.4,0,1,1)"}).finished.then(done);
}

function wireBets(v){
  v.querySelectorAll("[data-betspanel]").forEach(b => b.addEventListener("click", () => { BETS_PANEL = !BETS_PANEL; render(); }));
  v.querySelectorAll("[data-scope]").forEach(b => b.addEventListener("click", () => { SLIP_SCOPE = b.dataset.scope; betsFlip(render); }));
  // The legs leave the ticket for the tray one by one, counted as they land.
  v.querySelectorAll("[data-loadslip]").forEach(b => b.addEventListener("click", () => {
    const [book, i] = b.dataset.loadslip.split(":");
    const card = GALLERIES[book] && GALLERIES[book][+i];
    if (!card) return;
    const from = [...b.closest(".ticket").querySelectorAll(".tk-leg")].map(el => el.getBoundingClientRect());
    SLIP = card.legs.slice(); SLIP_MODE = "custom";
    const y = window.scrollY; render(); window.scrollTo(0, y);
    betsPour(from, SLIP.map(k => PROPS[k].n));
  }));
  // A pick opens its details in place (2026-09-25): only its own slip grows, and its column
  // re-packs under it.
  slipMasonry(v);
  v.querySelectorAll("[data-legmore]").forEach(el => {
    const flip = () => { el.setAttribute("aria-expanded", String(el.classList.toggle("open"))); slipMasonry(el.closest(".tk-group") || v); };
    el.addEventListener("click", flip);
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); flip(); } });
  });
  wireDeal(v);
  v.querySelectorAll("[data-tray]").forEach(b => b.addEventListener("click", betsSheetOpen));
  v.querySelectorAll("[data-sheetclose]").forEach(b => b.addEventListener("click", betsSheetClose));
  // The typed payout belongs to this exact slip; only the verdict redraws, so the field keeps focus.
  v.querySelectorAll("[data-bpay]").forEach(el => el.addEventListener("input", () => {
    const x = parseFloat(el.value.replace(",", "."));
    BETS_PAY = x > 1 ? {sig: slipSig(), x} : {sig: slipSig(), x: null};
    const out = v.querySelector("[data-bpayv]");
    if (out) out.innerHTML = betsVerdictHTML(betsSlipLegs());
  }));
}
document.addEventListener("keydown", e => { if (e.key === "Escape" && BETS_SHEET) betsSheetClose(); });
