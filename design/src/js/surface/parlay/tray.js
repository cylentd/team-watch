/* The slip, on the bottom edge (2026-09-25; Save since 2026-10-03). The tray is always there on
   Slips and Build, and on Preview once a pick is in it -- the place a pick lands, the count, who is
   on it, and Save. A tap on the count grows it into the sheet: why the slip's chance is what it is,
   the slip itself (slip.js) with its legs, payout and copy, then the slips saved this week
   (builder/saved.js), each a tap from the tray again and an x from gone.

   The chance: Underdog, every leg's graded chance at the side on the slip multiplied (legHit,
   grade.js); DK, the model's chance of the same. A leg the model does not price has none, and the
   slip then shows no chance at all rather than a wrong one. */
function betsSlipLegs(){ return SLIP.map(i => PROPS[i]).filter(Boolean); }
function betsLegChance(l){
  if (PARLAY_BOOK === "underdog") return legHit(l);
  return typeof l.model === "number" ? (slipSideOf(l) === "lower" ? 100 - l.model : l.model) : null;
}
function betsSlipPct(){
  const c = betsSlipLegs().map(betsLegChance);
  return c.length && c.every(x => x !== null) ? c.reduce((a, x) => a * x / 100, 1) * 100 : null;
}

/* One name per player, however many legs he has on the slip: "T. Higgins ×2". Two players who share
   an initial and surname are told apart by their full names. Takes {n, slug} legs; plain text. */
function trayNames(legs){
  const by = new Map();
  legs.forEach(l => { const k = l.slug || l.n; (by.get(k) || by.set(k, {n: l.n, c: 0}).get(k)).c++; });
  const rows = [...by.values()], ini = rows.map(e => nameInitial(e.n));
  return rows.map((e, k) => (ini.indexOf(ini[k]) === ini.lastIndexOf(ini[k]) ? ini[k] : e.n)
    + (e.c > 1 ? t("slips.tray.times", {n: e.c}) : "")).join(", ");
}
const trayWho = (n = SLIP.length) => trayNames(SLIP.slice(0, n).map(i => ({n: PROPS[i].n, slug: slSlug(PROPS[i])})));

function trayHTML(){
  const n = SLIP.length, saved = slipIsSaved();
  return `<div class="tray${n ? "" : " empty"}">
    <button type="button" class="tray-open" data-tray aria-expanded="${BETS_SHEET}">
      <span class="tray-c">${t("slips.tray.label")} · <span class="tray-n">${n}</span></span>
      <span class="tray-who">${n ? esc(trayWho()) : t("slips.tray.empty")}</span>
    </button>
    <button type="button" class="tray-save" data-slsave ${n && !saved ? "" : "disabled"}>${saved ? t("slips.tray.saved") : t("slips.tray.save")}</button>
  </div>`;
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

const SV_X = `<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 2.5l7 7M9.5 2.5l-7 7"/></svg>`;

/* The slips saved this week: how many legs, who, and an x. A tap loads one into the tray. */
function savedHTML(){
  if (!SAVED.length) return "";
  const rows = SAVED.map((s, k) => `<li class="sv-row">
      <button type="button" class="sv-load" data-slload="${k}"><b>${t("slips.saved.legs", {n: s.legs.length})}</b>
        <span>${esc(trayNames(s.legs.map(l => ({n: l.n || l.slug, slug: l.slug}))))}</span></button>
      <button type="button" class="sv-drop" data-sldrop="${k}" aria-label="${t("slips.saved.drop")}">${SV_X}</button>
    </li>`).join("");
  return `<section class="sv"><h3>${t("slips.saved.title", {n: SAVED.length})}</h3><ul>${rows}</ul></section>`;
}

function sheetHTML(){
  return `<div class="sheet-scrim${BETS_SHEET ? " on" : ""}" data-sheetclose></div>
  <section class="slipsheet${BETS_SHEET ? " on" : ""}" role="dialog" aria-modal="true" aria-hidden="${!BETS_SHEET}"
    aria-label="${t("slips.tray.label")}">
    <button type="button" class="grab" data-sheetclose aria-label="${t("common.action.close")}"></button>
    ${betsOddsHTML()}
    ${slipHTML()}
    ${savedHTML()}
  </section>`;
}
