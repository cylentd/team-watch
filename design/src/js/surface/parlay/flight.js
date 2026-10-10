/* Bets motion (2026-09-25), the four moments of the storyboard, each ending where its thing now
   lives (design/STYLE.md, "Motion"):
     a pick flies from its line to the tray, and the tray counts it;
     a saved slip pours its legs into the tray one by one, counted as they land;
     the tray grows into the sheet, the leg bars draw, then the all-hit bar, shorter;
     a filter slides the cards that stay and fades the ones that go.
   render() rebuilds #view on every tap, so each motion measures before the render and plays
   after it. Under reduced motion every function jumps to its end state. The tray stopped rolling a
   chance on 2026-10-03: it names who is on the slip instead, and the chance lives in its sheet. */
const betsCss = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const betsTray = () => document.querySelector(".tray");

/* The tray's count and names, set in place without a render, so they can change on landing. */
function betsSetTray(n){
  const tray = betsTray();
  if (!tray) return;
  tray.classList.toggle("empty", !n);
  tray.querySelector(".tray-n").textContent = n;
  tray.querySelector(".tray-who").textContent = n ? trayWho(n) : t("slips.tray.empty");
}

function betsPop(){
  const n = betsTray()?.querySelector(".tray-n");
  if (n && !REDUCED()) n.animate([{transform: "scale(1)"}, {transform: "scale(1.5)"}, {transform: "scale(1)"}],
    {duration: parseFloat(betsCss("--dur-pop")) * 1000 || 690, easing: betsCss("--spring-pop")});
}

function betsLand(n){
  betsSetTray(n);
  betsPop();
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

function betsFly(from, name){
  const n = SLIP.length;
  if (REDUCED()) return betsLand(n);
  betsSetTray(n - 1);
  betsChip(from, nameInitial(name)).then(() => betsLand(n));
}

/* 70ms apart, so each leg is a separate landing a reader can count. */
function betsPour(rects, names){
  const n = names.length;
  if (REDUCED()) return betsLand(n);
  betsSetTray(0);
  names.forEach((name, k) => setTimeout(() => betsChip(rects[k] || rects[0], nameInitial(name)).then(() => {
    if (k < n - 1){ betsSetTray(k + 1); betsPop(); } else betsLand(n);
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
  const done = () => { BETS_SHEET = false; render(); document.querySelector(".tray-open")?.focus({preventScroll: true}); };
  if (!sheet || REDUCED()) return done();
  sheet.animate([{transform: "translateY(0)"}, {transform: "translateY(100%)"}], {duration: 260, easing: "cubic-bezier(.4,0,1,1)"}).finished.then(done);
}

function wireBets(v){
  v.querySelectorAll("[data-betspanel]").forEach(b => b.addEventListener("click", () => { BETS_PANEL = !BETS_PANEL; render(); }));
  // A kickoff tab on Slips: the board shows that kickoff's games (board.js).
  v.querySelectorAll("[data-gwin]").forEach(b => b.addEventListener("click", () => {
    GAL_WIN = b.dataset.gwin; MKT_PAGE = 1;
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  // A Build line's ⓘ opens its leg sheet (legsheet.js).
  v.querySelectorAll("[data-legsheet]").forEach(el => {
    const open = e => { e.stopPropagation(); legSheetOpen(+el.dataset.legsheet, el); };
    el.addEventListener("click", open);
    if (el.tagName !== "BUTTON") el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(e); } });
  });
  wireSlRecord(v);
  wireTdCard(v);
  wireSlBoard(v);
  wireTray(v);
}
document.addEventListener("keydown", e => { if (e.key === "Escape" && BETS_SHEET) betsSheetClose(); });
