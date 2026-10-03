/* The tray's and the slip sheet's wiring, in one place since 2026-10-03 because three views draw
   them: Slips, Build and Preview. Every handler redraws with the scroll kept. */
const trayRedraw = () => { const y = window.scrollY; render(); window.scrollTo(0, y); };

async function trayCopy(b){
  const text = slipText();
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; }
  catch (e) {
    const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta);
    ta.select(); try { ok = document.execCommand("copy"); } catch (e2) {} ta.remove();
  }
  const was = b.textContent; b.textContent = ok ? t("parlay.slip.copied") : t("parlay.slip.copyFailed");
  setTimeout(() => { b.textContent = was; }, 1400);
}

function wireTray(v){
  v.querySelectorAll("[data-tray]").forEach(b => b.addEventListener("click", betsSheetOpen));
  v.querySelectorAll("[data-sheetclose]").forEach(b => b.addEventListener("click", betsSheetClose));
  v.querySelectorAll("[data-copy]").forEach(b => b.addEventListener("click", () => trayCopy(b)));
  v.querySelectorAll("[data-removeleg]").forEach(b => b.addEventListener("click", () => {
    const i = +b.dataset.removeleg;
    SLIP = SLIP.filter(x => x !== i); delete SLIP_SIDE[i];
    SLIP_MODE = "custom";
    trayRedraw();
  }));
  v.querySelectorAll("[data-preset]").forEach(b => b.addEventListener("click", () => {
    SLIP_MODE = b.dataset.preset; SLIP = presetSlip(SLIP_MODE, PARLAY_BOOK); SLIP_SIDE = {};
    trayRedraw();
  }));
  // Save keeps the tray as it is, so the slip can still be copied; the button then says Saved.
  v.querySelectorAll("[data-slsave]").forEach(b => b.addEventListener("click", () => {
    if (slipSave()){ trayRedraw(); betsPop(); }
  }));
  v.querySelectorAll("[data-sldrop]").forEach(b => b.addEventListener("click", () => { savedDrop(+b.dataset.sldrop); trayRedraw(); }));
  // A saved slip pours back into the tray, each leg counted as it lands.
  v.querySelectorAll("[data-slload]").forEach(b => b.addEventListener("click", () => {
    const from = b.getBoundingClientRect();
    if (!savedLoad(+b.dataset.slload)) return;
    trayRedraw();
    betsPour(SLIP.map(() => from), SLIP.map(i => PROPS[i].n));
  }));
  // The typed payout belongs to this exact slip; only the verdict redraws, so the field keeps focus.
  v.querySelectorAll("[data-bpay]").forEach(el => el.addEventListener("input", () => {
    const x = parseFloat(el.value.replace(",", "."));
    BETS_PAY = x > 1 ? {sig: slipSig(), x} : {sig: slipSig(), x: null};
    const out = v.querySelector("[data-bpayv]");
    if (out) out.innerHTML = betsVerdictHTML(betsSlipLegs());
  }));
}
