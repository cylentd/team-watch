/* ============================== LEAGUE > TEAMS: A TEAM'S PAGE ==============================
   2026-10-05 (David: no pop-ups from the bottom). A tap on a team's row opens that team as a full page in
   the view, nav bar and League sub-row still on screen: a "‹ Teams" link, the team's name, its record and
   total, one action, then its lineup by slot and its bench (position, name as initials, projection). The
   action is "Find trades with <team>" (the next page, tbpage.js), "This is my team" when the reader has no
   team in this league, or a quiet "Your team" on their own. Pages are history entries (chrome/layers.js,
   no URL change, so a reload lands on the board): Back and the link each go back one page, and the board
   returns at the scroll the reader left it. LB_PAGE says which page the view draws; lboard.js reads it.
   Opening a team never changes the reader's team: only "This is my team" does, through pickTeam, the team
   switch's own function. */
let LB_PAGE = null;        // null: the board. Else {key: the team on screen, step: "team" | "trade"}
let LB_Y = [];             // the scroll of every page left behind, the latest last

/* A team's row, from any league; keys are unique across leagues (design/teams.py). */
const lbpFind = key => ((lbData() || {}).leagues || []).flatMap(l => l.teams).find(x => x.key === key) || null;
const lbpChev = `<svg class="lbp-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 4L6 8l4 4"/></svg>`;

const lbpBackHTML = label => `<button type="button" class="lbp-back" data-lbpback>${lbpChev}<span>${label}</span></button>`;

function lbpRowHTML(r, flex){
  return `<li class="lbp-r"><span class="lbp-pos" data-pos="${esc(r.pos)}">${esc(r.pos)}</span>
    <span class="lbp-n">${esc(nameInitial(r.n))}</span>${flex ? `<i class="lbp-flx">FLX</i>` : ""}
    <b class="lbp-pts">${lbNum(r.pts)}</b></li>`;
}

/* The action's slot is one height whatever it holds, so "This is my team" turning into "Your team" moves nothing. */
function lbpActHTML(tm){
  const gate = tbGate(tm);
  const act = gate === "find" ? `<button type="button" class="lbp-act" data-tbfind>${t("lboard.offer.find", {name: esc(tm.name)})}</button>`
    : gate === "set" ? `<button type="button" class="lbp-act" data-lbmine="${esc(tm.key)}">${t("lboard.team.mine")}</button>`
    : gate === "own" ? `<p class="lbp-yours" tabindex="-1">${t("lboard.team.yours")}</p>` : "";
  return `<div class="lbp-slot">${act}</div>`;
}

function lbTeamHTML(tm){
  const rec = lbRecord(tm);
  return `<div class="wrap lb lbp">${lbpBackHTML(t("lboard.team.back"))}
    <h1 class="lbp-title">${esc(tm.name)}</h1>
    <p class="lbp-sub">${rec ? `<b>${rec}</b><i>·</i>` : ""}<span>${t("lboard.team.sub", {tot: lbNum(tm.tot)})}</span></p>
    ${lbpActHTML(tm)}
    <h2>${t("lboard.team.lineup")}</h2>
    <ol class="lbp-list">${tm.lineup.map(r => lbpRowHTML(r, r.slot === "FLX")).join("")}</ol>
    <h2>${t("lboard.team.bench")}</h2>
    ${tm.bench.length ? `<ol class="lbp-list">${tm.bench.map(r => lbpRowHTML(r, false)).join("")}</ol>`
      : `<p class="lbp-none">${t("lboard.team.nobench")}</p>`}</div>`;
}

/* What the view draws while a page is open: the team's, or the trade builder's (tbpage.js). A team the data no
   longer has (a rebuild under an open tab) drops back to the board. */
function lbPageHTML(){
  const tm = LB_PAGE && lbpFind(LB_PAGE.key);
  if (!tm){ lbPageReset(); return ""; }
  return LB_PAGE.step === "trade" && TB ? tbPageHTML() : lbTeamHTML(tm);
}

/* ---- going forward and back. A forward step remembers the scroll and starts the new page at the top; a step
   back draws the page it returns to and puts that scroll back (twice: the browser also restores one of its own
   after a Back, a frame later). ---- */
function lbpForward(){ LB_Y.push(window.scrollY); }
function lbpShow(){
  render();
  window.scrollTo({top: 0, behavior: "instant"});
  document.querySelector(".lbp-back")?.focus({preventScroll: true});
}
function lbpBack(){
  const y = LB_Y.pop() || 0, put = () => window.scrollTo({top: y, behavior: "instant"});
  render();
  put();
  requestAnimationFrame(put);
}

function lbPageOpen(key){
  if (!lbpFind(key)) return;
  LB_PAGE = {key, step: "team"};
  lbpForward();
  layerPush("lbteam", lbTeamShut);
  lbpShow();
}

/* The close itself (Back arrives here); the link also takes back the history entry (lbBack). */
function lbTeamShut(){
  if (!LB_PAGE) return;
  const key = LB_PAGE.key;
  LB_PAGE = null;
  lbpBack();
  document.querySelector(`[data-lbopen="${CSS.escape(key)}"]`)?.focus({preventScroll: true});   // the row that opened it
}

/* The ‹ link: one page back, the innermost first (the edit state, the offers, the team). */
function lbBack(){
  if (!LB_PAGE) return;
  if (TB_EDIT) return tbEditClose();
  if (LB_PAGE.step === "trade") return tbTradeClose();
  lbTeamShut();
  layerDone("lbteam");
}

/* The reader left Teams with a page open (a tap on another group): nothing of it is kept. */
function lbPageReset(){
  LB_PAGE = null; LB_Y = [];
  TB = null; TB_EDIT = null;
  ["lbteam", "lbtrade", "tbedit"].forEach(layerForget);
}

/* "This is my team": the team switch's own pick (teamswitch.js), so My teams, Live and the rest follow. The page
   redraws as the reader's own. */
function lbMine(key){
  pickTeam(key);
  document.querySelector(".lbp-yours")?.focus({preventScroll: true});
}

/* Wired per draw: the page is new each time, so its one listener never stacks on the view. */
function wireLbPage(v){
  const root = v.querySelector(".lbp");
  if (!root) return;
  root.addEventListener("click", e => {
    const hit = sel => e.target.closest(sel);
    if (hit("[data-lbpback]")) return lbBack();
    const mine = hit("[data-lbmine]");
    if (mine) return lbMine(mine.dataset.lbmine);
    if (hit("[data-tbfind]")) return tbTradeOpen(LB_PAGE.key);
    if (LB_PAGE.step === "trade") tbClick(hit) || tbEditClick(hit);
  });
}
