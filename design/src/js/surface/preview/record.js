/* ------------------------------------------------------------------
   PREVIEW's Past games (2026-10-05, storyboard https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV, picks 1A and
   2A; it replaced the record card atop the slate, which David found "randomly placed" and wordy). A game
   leaves the slate once it is over (data/preview.js pvOver); here it stays, one tap away, back to the first
   week Claude wrote previews.

   Top: Claude's season, one row per bet (Moneyline, Spread, Total) with its hit rate, and the spread by
   confidence in one grey line. Then a stepper, ‹ Week 4 ›, which stays one row wide however many weeks
   there are (David asked how 2A scales to 18). Under it that week's record in one line, then its games:
   the final and a ✓ / ✗ per call. A tap opens the game's preview as it was written, with the final on top.

   This week's finals are in the page; an earlier week's previews are in preview_archive.json, fetched the
   first time one is opened (design/preview_archive.py). The record's graded games draw the rows meanwhile.

   Colour map: --up / --down only a graded ✓ / ✗; a push and an ungraded call are grey.
------------------------------------------------------------------ */
const PV_ARC_URL = "preview_archive.json";

/* Fetch the archive once; a failure leaves "failed" until the reader taps retry (which sets PV_ARC null first). */
async function pvArcLoad(){
  if (PV_ARC !== null) return;
  if (!PAGE_SERVED()){ PV_ARC = "failed"; return; }   // from file:// there is no file to ask for
  PV_ARC = "loading";
  try {
    const res = await fetch(PV_ARC_URL);
    PV_ARC = res.ok ? await res.json() : "failed";
  } catch (e) { PV_ARC = "failed"; }
  if (SURFACE === "preview") render();
}

/* Claude's season: Moneyline, Spread, Total, each its record and hit rate, then the spread by confidence. */
function pvSeasonHTML(){
  const r = pvRecord();
  if (!r || !r.weeks.length) return "";
  const tr = (label, s) => { const h = pvHit(s); return `<tr><th scope="row">${label}</th><td>${pvWL(s)}</td><td>${h != null ? h + "%" : "–"}</td></tr>`; };
  const c = r.by_conf || {};
  return `<section class="pv-season"><h3 class="pv-sk">${t("preview.arc.season", {n: r.through})}</h3>
    <table class="pv-st"><tbody>${tr(t("preview.bet.ml"), r.su)}${tr(t("preview.bet.spread"), r.ats)}${tr(t("preview.bet.total"), r.total)}</tbody></table>
    <p class="pv-sc">${t("preview.arc.conf", {s: pvWL(c.strong), c: pvWL(c.solid), l: pvWL(c.lean)})}</p></section>`;
}

/* One call on a row: "Spread ✓ CLE", "Total ✗ Under", "Moneyline CLE" before it is graded. */
function pvArcCallHTML(label, c){
  if (!c) return "";
  const pick = c.pick === "over" ? t("preview.pick.over") : c.pick === "under" ? t("preview.pick.under") : esc(c.pick);
  return `<span>${label} ${pvMarkHTML(c.hit)}<b class="${c.hit || ""}">${pick}</b></span>`;
}

function pvArcRowHTML(x){
  const {g, i, key, rg} = x, c = pvArcCalls(g, rg), fin = pvFinal(g, rg);
  const open = i != null ? `data-pvopen="${i}"` : `data-pvarcg="${esc(key)}"`;
  return `<li><button type="button" class="pv-rg" ${open}>
    <span class="pv-rg-m">${esc(g.away)} @ ${esc(g.home)}</span><span class="pv-rg-f">${fin || t("preview.final")}</span>
    <span class="pv-rg-c">${pvArcCallHTML(t("preview.bet.ml"), c.ml)}${pvArcCallHTML(t("preview.bet.spread"), c.spread)}${pvArcCallHTML(t("preview.bet.total"), c.total)}</span>
  </button></li>`;
}

/* The week shown: its stepper, its record line, its games. */
function pvArcWeekHTML(wk){
  const last = pvArcLast();
  const step = `<header class="pv-top pv-wstep">
    <button class="pv-arrow" data-pvarcstep="-1"${wk <= 1 ? " disabled" : ""} aria-label="${t("preview.arc.prev")}">‹</button>
    <b class="pv-mt">${t("preview.arc.week", {n: wk})}</b>
    <button class="pv-arrow" data-pvarcstep="1"${wk >= last ? " disabled" : ""} aria-label="${t("preview.arc.next")}">›</button></header>`;
  const rw = pvRecWeek(wk);
  const line = rw ? `<p class="pv-wl">${t("preview.arc.weekline", {su: pvWL(rw.su), ats: pvWL(rw.ats), tot: pvWL(rw.total)})}</p>` : "";
  const rows = pvArcRows(wk);
  const body = rows.length ? `<ul class="pv-rgl">${rows.map(pvArcRowHTML).join("")}</ul>` : `<p class="pv-allover">${t("preview.arc.none")}</p>`;
  return step + line + body;
}

function pvRecSheetHTML(){
  const wk = PV_ARC_WK ?? pvArcWeekDefault();
  return `<section class="pv-rz" aria-label="${t("preview.arc.title")}">
    <button class="pv-back" data-pvrecback>${t("preview.backPv")}</button>
    <h2 class="pv-title">${t("preview.arc.title")}</h2>
    ${pvSeasonHTML()}${pvArcWeekHTML(wk)}</section>`;
}

/* An earlier week's game, once the archive is in: the same dossier as a live game. Before then, a line. */
function pvArcDossierHTML(enter){
  const gs = pvArcGames(PV_ARC_G.week), i = gs.findIndex(g => g.key === PV_ARC_G.key);
  if (i >= 0) return pvDossierHTML(gs[i], i, gs.length, enter);
  const msg = PV_ARC === "failed" ? `<button type="button" class="pv-fold" data-pvarcretry>${t("preview.arc.failed", {n: PV_ARC_G.week})}</button>`
    : `<p class="pv-allover">${t("preview.arc.loading", {n: PV_ARC_G.week})}</p>`;
  return `<div class="pv-dz"><button class="pv-back" data-pvback>${t("preview.backPv")}</button>${msg}</div>`;
}
