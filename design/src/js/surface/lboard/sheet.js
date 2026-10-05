/* ============================== LEAGUE > TEAMS: THE ROSTER SHEET ==============================
   A tap on a team's row opens its roster from the bottom edge, outside #view (shell.html), so a repaint
   of the board never rebuilds it under the reader. The best lineup by slot, then the bench, each row a
   position, the player's name as initials and his projection. It is any team's, so it never calls
   pickTeam and never touches the reader's own pick. Back, Escape, the scrim, the grab and a pull down
   close it (chrome/layers.js, lib/swipe.js). */
let LBS = null;            // the team on screen (its LIVE_TEAMS row), or null when closed
let LBS_RETURN = null;     // what had focus when it opened
const lbsEl = () => document.getElementById("lbsheet");
const lbsScrim = () => document.getElementById("lbsheet-scrim");

/* A team's row, from any league; keys are unique across leagues (design/teams.py). */
const lbsFind = key => ((lbData() || {}).leagues || []).flatMap(l => l.teams).find(x => x.key === key) || null;

function lbsRowHTML(r, flex){
  return `<li class="lbs-r"><span class="lbs-pos" data-pos="${esc(r.pos)}">${esc(r.pos)}</span>
    <span class="lbs-n">${esc(nameInitial(r.n))}</span>${flex ? `<i class="lbs-flx">FLX</i>` : ""}
    <b class="lbs-pts">${lbNum(r.pts)}</b></li>`;
}

function lbsSheetHTML(tm){
  const rec = lbRecord(tm), sub = t("lboard.sheet.sub", {tot: lbNum(tm.tot)});
  return `<button type="button" class="lbs-grab" data-lbsclose aria-label="${t("common.action.close")}"></button>
    <div class="lbs-bar"><div class="lbs-ti"><h2 class="lbs-title" id="lbs-title">${esc(tm.name)}</h2>
      <p class="lbs-sub">${rec ? `<b>${rec}</b><i>·</i>` : ""}<span>${sub}</span></p></div>
      <button type="button" class="lbs-x" data-lbsclose aria-label="${t("common.action.close")}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
    <div class="lbs-body"><h3>${t("lboard.sheet.lineup")}</h3>
      <ol class="lbs-list">${tm.lineup.map(r => lbsRowHTML(r, r.slot === "FLX")).join("")}</ol>
      <h3>${t("lboard.sheet.bench")}</h3>
      ${tm.bench.length ? `<ol class="lbs-list">${tm.bench.map(r => lbsRowHTML(r, false)).join("")}</ol>`
        : `<p class="lbs-none">${t("lboard.sheet.nobench")}</p>`}</div>`;
}

function lbSheetOpen(key, origin){
  const tm = lbsFind(key), d = lbsEl();
  if (!tm || !d) return;
  LBS = tm;
  LBS_RETURN = origin || document.activeElement;
  d.innerHTML = lbsSheetHTML(tm);
  d.scrollTop = 0;
  d.classList.add("on");
  d.setAttribute("aria-hidden", "false");
  lbsScrim().classList.add("on");
  d.querySelector(".lbs-x").focus({preventScroll: true});
  layerPush("lbsheet", lbSheetShut);
}

/* The close itself; lbSheetClose also takes back the history entry (layers.js). */
function lbSheetShut(){
  const d = lbsEl();
  if (!d || !LBS) return;
  LBS = null;
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  lbsScrim().classList.remove("on");
  const back = LBS_RETURN;
  LBS_RETURN = null;
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}
function lbSheetClose(){ lbSheetShut(); layerDone("lbsheet"); }

/* Bound once: the sheet's markup is replaced on every open, its listeners are not. */
(() => {
  const d = lbsEl();
  if (!d) return;
  d.addEventListener("click", e => { if (e.target.closest("[data-lbsclose]")) lbSheetClose(); });
  d.addEventListener("keydown", e => {
    if (e.key === "Tab"){ e.preventDefault(); d.querySelector(".lbs-x").focus(); }   // one stop, the close
  });
  lbsScrim().addEventListener("click", lbSheetClose);
  onPullDown(d, () => d.querySelector(".lbs-body").scrollTop <= 0, () => !!LBS, lbSheetClose);
  document.addEventListener("keydown", e => { if (e.key === "Escape" && LBS) lbSheetClose(); });
})();
