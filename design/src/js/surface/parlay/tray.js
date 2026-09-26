/* The slip, on the bottom edge (2026-09-25). The tray is always there on Slips and Build -- the
   place a pick lands and the count you are building -- and a tap grows it into the sheet: why the
   slip's chance is what it is, then the slip itself (slip.js) with its legs, payout and copy.

   The chance is the one number the slip is for. Underdog: every leg's graded chance multiplied
   (legHit, slips.js), the chance all of them hit. DK: the model's chance of the same, where every
   leg is modelled. */
function betsSlipLegs(){ return SLIP.map(i => PROPS[i]).filter(Boolean); }
function betsLegChance(l){
  if (PARLAY_BOOK === "underdog") return udPick(l) ? legHit(l) : null;
  return typeof l.model === "number" ? l.model : null;
}
function betsSlipPct(){
  const c = betsSlipLegs().map(betsLegChance);
  return c.length && c.every(x => x !== null) ? c.reduce((a, x) => a * x / 100, 1) * 100 : null;
}
const betsPctText = p => p === null ? "—" : `${p.toFixed(1)}%`;

function trayHTML(){
  const n = SLIP.length, p = betsSlipPct();
  return `<button type="button" class="tray${n ? "" : " empty"}" data-tray aria-expanded="${BETS_SHEET}">
    <span>${t("parlay.tray.label")} · <span class="tray-n">${n}</span> ${PARLAY_BOOK === "underdog"
      ? t("parlay.tray.picks", {s: n === 1 ? "" : "s"}) : t("parlay.tray.legs", {s: n === 1 ? "" : "s"})}</span>
    <span class="tray-pc">${n ? betsPctText(p) : t("parlay.tray.empty")}</span>
  </button>`;
}

/* Why three good legs make a worse slip: each leg's chance as a bar, then "all hit" as the last
   bar, drawn after the others and shorter than any of them. The bars carry their numbers; the
   picture is the multiplication. */
function betsOddsHTML(){
  const legs = betsSlipLegs(), p = betsSlipPct();
  if (!legs.length || p === null) return "";
  const row = (name, v, all) => `<div class="odds-row${all ? " all" : ""}"><span>${name}</span>
    <i class="odds-bar"><i style="--w:${v.toFixed(1)}%"></i></i><b>${v.toFixed(1)}%</b></div>`;
  return `<div class="odds">${legs.map(l => row(esc(nameInitial(l.n)), betsLegChance(l), false)).join("")}
    ${row(t("parlay.tray.allHit", {n: legs.length}), p, true)}</div>`;
}

function sheetHTML(){
  return `<div class="sheet-scrim${BETS_SHEET ? " on" : ""}" data-sheetclose></div>
  <section class="slipsheet${BETS_SHEET ? " on" : ""}" role="dialog" aria-modal="true" aria-hidden="${!BETS_SHEET}"
    aria-label="${t("parlay.tray.label")}">
    <button type="button" class="grab" data-sheetclose aria-label="${t("common.action.close")}"></button>
    ${betsOddsHTML()}
    ${slipHTML()}
  </section>`;
}
