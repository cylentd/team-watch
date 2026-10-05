/* ============================== LEAGUE > TEAMS: THE TRADE BUILDER PAGE ==============================
   2026-10-05 (storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, frames 1-3; a full page, not a
   sheet, since the same day). Opened by the lime "Find trades with <team>" button on a team's page
   (lbpage.js), as the next page: its "‹ <team>" link, Back and the browser's Back return to that team. Two
   tabs, Bold (the biggest gain for the reader, whatever the partner makes of it) and Fair (both lineups
   gain), up to three offers each. An offer is two columns, YOU SEND and YOU GET, and one number, the reader's
   gain a week. "Copy offer" puts a message on the clipboard for the other manager, built from season
   averages alone. An offer that drops a player says so in one line. "Edit" on a card and "Make your own
   offer" under the list open the edit state (tbedit.js) on this same page, its own history entry, so Back
   returns to the offers. The data is offers.js's; nothing here is computed. */
let TB = null;            // {lg, me, tm} while the page is open: the league, the reader's team and the partner's
let TB_TAB = "bold";      // the last tab, kept for this visit only
let TB_EDIT = null;       // the reader's own package while the edit state is open (tbedit.js), else null
const tbBody = () => document.querySelector("#view .tb-body");

/* The four codes a status is shortened to; any other status shows its first letters. */
const tbInjCode = s => ({Out: t("lboard.inj.o"), IR: t("lboard.inj.ir"), Questionable: t("lboard.inj.q"),
  Doubtful: t("lboard.inj.d")})[s] || String(s).slice(0, 3).toUpperCase();

/* The amber pill: the status where one is set, else IR for a player in an IR slot (the rosters in Edit say so). */
const tbPillHTML = p => p.injury || p.ir
  ? `<i class="tb-inj" title="${esc(p.injury || "IR")}">${esc(tbInjCode(p.injury || "IR"))}</i>` : "";

function tbPlayerHTML(p){
  return `<li class="tb-p"><span class="lbp-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span>
    <span class="tb-n" title="${esc(p.name)}">${esc(nameInitial(p.name))}</span>${tbPillHTML(p)}</li>`;
}

/* "You drop: O. Gordon II": who the reader releases to stay at the roster cap, one quiet line. Nothing about the
   partner's roster: their room is theirs to manage. Initials, comma-separated. */
const tbNames = list => esc(list.map(p => nameInitial(p.name)).join(", "));
const tbDropHTML = drop => drop && drop.length ? `<p class="tb-drop">${t("lboard.offer.drop", {names: tbNames(drop)})}</p>` : "";

/* "To IR: C. Williams": who moves into an IR slot instead of being dropped, its own quiet line above the drop line. */
const tbIrHTML = moves => moves && moves.length ? `<p class="tb-ir">${t("lboard.offer.ir", {names: tbNames(moves)})}</p>` : "";

/* Both lines of an offer, IR first, each only when there is one. */
const tbRoomHTML = o => tbIrHTML(o.ir_moves) + tbDropHTML(o.drop);

function tbCardHTML(o, i){
  const col = (label, rows) => `<div class="tb-col"><p class="tb-h">${label}</p><ul>${rows.map(tbPlayerHTML).join("")}</ul></div>`;
  const edit = tbEditOk() ? `<button type="button" class="tb-copy" data-tbedit="${i}">${t("lboard.offer.edit")}</button>` : "";
  return `<article class="tb-card">
    <div class="tb-cols">${col(t("lboard.offer.send"), o.send)}${col(t("lboard.offer.get"), o.get)}</div>${tbRoomHTML(o)}
    <div class="tb-foot"><p class="tb-gain">${t("lboard.offer.gain", {n: `<b>+${lbNum(o.gain)}</b>`})}</p>
      <div class="tb-acts">${edit}<button type="button" class="tb-copy" data-tbcopy="${i}">${t("lboard.offer.copy")}</button></div></div></article>`;
}

/* Under the offers, in every state with a pair: the way in to a package of the reader's own (tbedit.js). */
const tbOwnHTML = () => tbEditOk() ? `<button type="button" class="tb-own" data-tbown>${t("lboard.offer.own")}</button>` : "";

/* Shapes where the cards will be, so the page is the size it will be: two columns of three bars, three cards. */
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

/* What is under the head: the error, the shapes while the file loads, the edit state, then the tabs and up to
   three offers. */
function tbMainHTML(){
  if (TB_ERR) return `<div class="state-empty tb-empty"><div><b>${t("lboard.offer.error")}</b>
    <button type="button" class="chip" data-tbretry>${t("lboard.offer.retry")}</button></div></div>`;
  if (!TB_DATA) return tbSkelHTML();
  if (TB_EDIT) return tbEditHTML();
  const foot = `<p class="tb-upd">${tbUpdated()}</p>`, offers = tbOffers();
  if (!tbPair(TB.lg, TB.me, TB.tm)) return tbEmptyHTML(t("lboard.offer.none")) + tbOwnHTML() + foot;
  return tbTabsHTML() + (offers.length ? offers.map(tbCardHTML).join("")
    : tbEmptyHTML(TB_TAB === "bold" ? t("lboard.offer.noBold") : t("lboard.offer.noFair"))) + tbOwnHTML() + foot;
}

const tbSwap = `<svg class="tb-swap" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h12M15 3l4 4-4 4M17 17H5M9 13l-4 4 4 4"/></svg>`;

/* The page: the link back (to the offers from the edit state, else to the team), the head "You ⇄ Team", the body. */
function tbPageHTML(){
  return `<div class="wrap lb lbp">${lbpBackHTML(TB_EDIT && TB_DATA ? t("lboard.offer.backOffers") : esc(TB.tm.name))}
    <h1 class="lbp-title" id="tb-title" aria-label="${t("lboard.offer.title", {name: esc(TB.tm.name)})}">${t("lboard.offer.you")}${tbSwap}${esc(TB.tm.name)}</h1>
    <div class="tb-body${TB_EDIT && TB_DATA ? " tb-ed" : ""}">${tbMainHTML()}</div></div>`;
}

/* Redraws what is under the head (a tab, the file arriving); the link and the head keep their focus. */
function tbPaint(){
  const body = tbBody();
  if (!body) return;
  body.classList.toggle("tb-ed", !!TB_EDIT && !!TB_DATA);
  body.innerHTML = tbMainHTML();
}

function tbTradeOpen(key){
  const lg = tbLeagueOf(key), me = tbMine(lg), tm = lg && lg.teams.find(x => x.key === key);
  if (!tm || !me || me.key === tm.key || !LB_PAGE) return;
  TB = {lg, me, tm};
  TB_EDIT = null;
  LB_PAGE.step = "trade";
  const loading = TB_DATA ? null : tbLoad();          // first, so an error from an earlier open is cleared
  lbpForward();
  layerPush("lbtrade", tbTradeShut);
  lbpShow();
  if (loading) loading.then(() => { if (TB && TB.tm === tm) tbPaint(); });
}

/* The close itself (Back arrives here): the team's page again. tbTradeClose also takes back the history entry. */
function tbTradeShut(){
  if (!LB_PAGE || LB_PAGE.step !== "trade") return;
  TB = null;
  TB_EDIT = null;
  LB_PAGE.step = "team";
  lbpBack();
  document.querySelector("[data-tbfind]")?.focus({preventScroll: true});
}
function tbTradeClose(){ tbTradeShut(); layerDone("lbtrade"); }

/* The offer, as a message. The clipboard call is made inside the click, as browsers insist; where it is refused
   (an in-app browser, file://) the text shows in a box, selected, for the reader to copy by hand: in `host`, at
   its `where` ("beforeend" of a card, "afterbegin" of the edit state's foot). */
async function tbCopyText(btn, text, host, where){
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { /* the box below */ }
  if (!ok){
    let box = host.querySelector(".tb-box");
    if (!box) host.insertAdjacentHTML(where, `<textarea class="tb-box" readonly rows="3" aria-label="${t("lboard.offer.copyBox")}">${esc(text)}</textarea>`);
    box = host.querySelector(".tb-box");
    box.focus(); box.select();
    return;
  }
  btn.textContent = t("lboard.offer.copied");
  btn.classList.add("done");
  setTimeout(() => { if (btn.isConnected){ btn.textContent = t("lboard.offer.copy"); btn.classList.remove("done"); } }, 1600);
}
const tbCopy = btn => tbCopyText(btn, tbText(tbOffers()[+btn.dataset.tbcopy]), btn.closest(".tb-card"), "beforeend");

/* The offers' own taps (lbpage.js wires them): a tab, Try again, Copy offer. True when one was handled. */
function tbClick(hit){
  const tab = hit("[data-tbtab]");
  if (tab){
    if (tab.dataset.tbtab !== TB_TAB){
      TB_TAB = tab.dataset.tbtab;
      tbPaint();
      document.querySelector(`[data-tbtab="${TB_TAB}"]`)?.focus({preventScroll: true});
    }
    return true;
  }
  if (hit("[data-tbretry]")){ TB_ERR = false; tbPaint(); tbLoad().then(() => { if (TB) tbPaint(); }); return true; }
  const copy = hit("[data-tbcopy]");
  if (copy && TB_DATA){ tbCopy(copy); return true; }
  return false;
}
