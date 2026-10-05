/* ============================== LEAGUE > TEAMS: THE TRADE BUILDER SHEET ==============================
   2026-10-05 (storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, frames 1-3). Opened by the lime
   "Find trades with <team>" button at the foot of the roster sheet (sheet.js), above it: it is its own layer,
   so Back closes it and then the roster sheet. Two tabs, Bold (the biggest gain for the reader, whatever the
   partner makes of it) and Fair (both lineups gain), up to three offers each. An offer is two columns, YOU
   SEND and YOU GET, and one number, the reader's gain a week. "Copy offer" puts a message on the clipboard
   for the other manager, built from season averages alone. The data is offers.js's; nothing here is computed. */
let TB = null;            // {lg, me, tm} while open: the league, the reader's team and the partner's
let TB_TAB = "bold";      // the last tab, kept for this visit only
let TB_RETURN = null;     // what had focus when it opened
const tbEl = () => document.getElementById("tbsheet");
const tbScrim = () => document.getElementById("tbsheet-scrim");

/* The four codes a status is shortened to; any other status shows its first letters. */
const tbInjCode = s => ({Out: t("lboard.inj.o"), IR: t("lboard.inj.ir"), Questionable: t("lboard.inj.q"),
  Doubtful: t("lboard.inj.d")})[s] || String(s).slice(0, 3).toUpperCase();

function tbPlayerHTML(p){
  const inj = p.injury ? `<i class="tb-inj" title="${esc(p.injury)}">${esc(tbInjCode(p.injury))}</i>` : "";
  return `<li class="tb-p"><span class="lbs-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span>
    <span class="tb-n" title="${esc(p.name)}">${esc(nameInitial(p.name))}</span>${inj}</li>`;
}

function tbCardHTML(o, i){
  const col = (label, rows) => `<div class="tb-col"><p class="tb-h">${label}</p><ul>${rows.map(tbPlayerHTML).join("")}</ul></div>`;
  return `<article class="tb-card">
    <div class="tb-cols">${col(t("lboard.offer.send"), o.send)}${col(t("lboard.offer.get"), o.get)}</div>
    <div class="tb-foot"><p class="tb-gain">${t("lboard.offer.gain", {n: `<b>+${lbNum(o.gain)}</b>`})}</p>
      <button type="button" class="tb-copy" data-tbcopy="${i}">${t("lboard.offer.copy")}</button></div></article>`;
}

/* Shapes where the cards will be, so the sheet is the size it will be: two columns of three bars, three cards. */
const tbSkelHTML = () => `<p class="tb-line" role="status">${t("lboard.offer.loading")}</p>` + [0, 1, 2].map(() =>
  `<div class="tb-card tb-skel" aria-hidden="true"><div class="tb-cols">${[0, 1].map(() =>
    `<div class="tb-col"><i></i><i></i><i></i></div>`).join("")}</div></div>`).join("");

const tbEmptyHTML = line => `<div class="state-empty tb-empty"><b>${line}</b></div>`;

function tbTabsHTML(){
  const tab = (k, label) => `<button type="button" class="chip" data-tbtab="${k}" aria-pressed="${k === TB_TAB}">${label}</button>`;
  return `<div class="setrow tb-seg" role="group" aria-label="${t("lboard.offer.tabs")}">${tab("bold", t("lboard.offer.bold"))}${tab("fair", t("lboard.offer.fair"))}</div>
    <p class="tb-line">${TB_TAB === "bold" ? t("lboard.offer.boldLine") : t("lboard.offer.fairLine")}</p>`;
}

/* The date the offers were made, as "Oct 5": bookkeeping, at the bottom. */
const tbUpdated = () => t("lboard.offer.updated", {date: new Date(`${String(TB_DATA.updated).slice(0, 10)}T12:00:00`)
  .toLocaleDateString("en-US", {month: "short", day: "numeric"})});

/* The tab's offers for this pair, at most three. */
const tbOffers = () => ((tbPair(TB.lg, TB.me, TB.tm) || {})[TB_TAB] || []).slice(0, 3);

/* What is under the head: the error, the shapes while the file loads, then the tabs and up to three offers. */
function tbMainHTML(){
  if (TB_ERR) return `<div class="state-empty tb-empty"><div><b>${t("lboard.offer.error")}</b>
    <button type="button" class="chip" data-tbretry>${t("lboard.offer.retry")}</button></div></div>`;
  if (!TB_DATA) return tbSkelHTML();
  const foot = `<p class="tb-upd">${tbUpdated()}</p>`, offers = tbOffers();
  if (!tbPair(TB.lg, TB.me, TB.tm)) return tbEmptyHTML(t("lboard.offer.none")) + foot;
  return tbTabsHTML() + (offers.length ? offers.map(tbCardHTML).join("")
    : tbEmptyHTML(TB_TAB === "bold" ? t("lboard.offer.noBold") : t("lboard.offer.noFair"))) + foot;
}

const tbSwap = `<svg class="tb-swap" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h12M15 3l4 4-4 4M17 17H5M9 13l-4 4 4 4"/></svg>`;

function tbHeadHTML(){
  return `<button type="button" class="lbs-grab" data-tbclose aria-label="${t("common.action.close")}"></button>
    <div class="lbs-bar"><div class="lbs-ti"><h2 class="lbs-title" id="tb-title" aria-label="${t("lboard.offer.title", {name: esc(TB.tm.name)})}">${t("lboard.offer.you")}${tbSwap}${esc(TB.tm.name)}</h2></div>
      <button type="button" class="lbs-x" data-tbclose aria-label="${t("common.action.close")}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
    <div class="lbs-body tb-body"></div>`;
}

/* Redraws what is under the head; the head keeps its focus. */
function tbPaint(){
  const body = tbEl().querySelector(".tb-body");
  if (body) body.innerHTML = tbMainHTML();
}

function tbShow(key, origin){
  const lg = tbLeagueOf(key), me = tbMine(lg), tm = lg && lg.teams.find(x => x.key === key), d = tbEl();
  if (!tm || !me || me.key === tm.key || !d) return;
  TB = {lg, me, tm};
  TB_RETURN = origin || document.activeElement;
  const loading = TB_DATA ? null : tbLoad();          // first, so an error from an earlier open is cleared
  d.innerHTML = tbHeadHTML();
  tbPaint();
  d.classList.add("on");
  d.setAttribute("aria-hidden", "false");
  tbScrim().classList.add("on");
  d.querySelector(".lbs-x").focus({preventScroll: true});
  layerPush("tbsheet", tbSheetShut);
  if (loading) loading.then(() => { if (TB && TB.tm === tm) tbPaint(); });
}

/* The close itself; tbSheetClose also takes back the history entry (layers.js). */
function tbSheetShut(){
  const d = tbEl();
  if (!d || !TB) return;
  TB = null;
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  tbScrim().classList.remove("on");
  const back = TB_RETURN;
  TB_RETURN = null;
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}
function tbSheetClose(){ tbSheetShut(); layerDone("tbsheet"); }

/* The card's offer, as a message. The clipboard call is made inside the click, as browsers insist; where it is
   refused (an in-app browser, file://) the text shows in a box, selected, for the reader to copy by hand. */
async function tbCopy(btn){
  const text = tbText(tbOffers()[+btn.dataset.tbcopy]);
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { /* the box below */ }
  if (!ok){
    const card = btn.closest(".tb-card");
    let box = card.querySelector(".tb-box");
    if (!box) card.insertAdjacentHTML("beforeend", `<textarea class="tb-box" readonly rows="3" aria-label="${t("lboard.offer.copyBox")}">${esc(text)}</textarea>`);
    box = card.querySelector(".tb-box");
    box.focus(); box.select();
    return;
  }
  btn.textContent = t("lboard.offer.copied");
  btn.classList.add("done");
  setTimeout(() => { if (btn.isConnected){ btn.textContent = t("lboard.offer.copy"); btn.classList.remove("done"); } }, 1600);
}

/* Bound once: the sheet's markup is replaced on every open, its listeners are not. */
(() => {
  const d = tbEl();
  if (!d) return;
  d.addEventListener("click", e => {
    const hit = sel => e.target.closest(sel);
    if (hit("[data-tbclose]")) return tbSheetClose();
    const tab = hit("[data-tbtab]");
    if (tab && tab.dataset.tbtab !== TB_TAB){
      TB_TAB = tab.dataset.tbtab;
      tbPaint();
      d.querySelector(`[data-tbtab="${TB_TAB}"]`)?.focus({preventScroll: true});
    }
    if (hit("[data-tbretry]")){ TB_ERR = false; tbPaint(); tbLoad().then(() => { if (TB) tbPaint(); }); }
    const copy = hit("[data-tbcopy]");
    if (copy && TB_DATA) tbCopy(copy);
  });
  d.addEventListener("keydown", e => {            // Tab stays inside the sheet
    if (e.key !== "Tab") return;
    const stops = [...d.querySelectorAll("button, textarea")].filter(x => x.offsetParent !== null);
    const i = stops.indexOf(document.activeElement), next = stops[(i + (e.shiftKey ? -1 : 1) + stops.length) % stops.length];
    if (next){ e.preventDefault(); next.focus(); }
  });
  tbScrim().addEventListener("click", tbSheetClose);
  onPullDown(d, () => d.querySelector(".tb-body").scrollTop <= 0, () => !!TB, tbSheetClose);
  // On the window, in the capture phase: Escape closes this sheet alone, never the roster sheet under it.
  window.addEventListener("keydown", e => { if (e.key === "Escape" && TB){ e.stopPropagation(); tbSheetClose(); } }, true);
})();
