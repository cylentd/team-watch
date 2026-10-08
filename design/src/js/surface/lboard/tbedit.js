/* ============================== LEAGUE > TRADES: THE TRADE BUILDER, EDIT ==============================
   2026-10-05 (storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, frame 4). The reader's own package,
   built on its own page (finder/page.js draws the head): "Edit" on an offer card starts from that offer, "Make your own
   offer" from an empty package. It is its own history entry (layers.js "tbedit"), so Back and the "‹ Offers" link
   return to the finder, at the scroll the reader left.

   Top: the package, YOU SEND and YOU GET, three rows tall whatever is in it (a fourth scrolls inside). Below: the
   reader's roster and the partner's, from the file's `values`, each row a switch that puts the player in or out of
   the package (side by side from 760px). The foot is a tray stuck to the bottom edge, where the thumb is (STYLE.md):
   the live gain by tbscore.js, in rest-of-season points like a card's (green, red, or a dash for an empty package), the players the reader would drop to
   stay at the roster cap, Reset to the offer it started from, and Copy offer. The partner's roster room is never
   shown here; it is worked out when Copy offer is pressed (tbTheir) and goes into the pitch. Only offers.js's guard
   (tbEditOk) lets it open. */

const TB_POS = ["QB", "RB", "WR", "TE"];

const tbSigned = g => (g > 0 ? "+" : g < 0 ? "−" : "") + lbNum(Math.abs(g));
const tbHas = (rows, key) => rows.find(p => tbKey(p) === key);
const tbPicked = key => TB_EDIT.send.includes(key) || TB_EDIT.get.includes(key);
/* A player a trade page opened Edit with ("Make your own offer with him", finder/tpage.js) stays in the package. */
const tbLocked = key => (TB_EDIT.lock || []).includes(key);

const tbRowHTML = p => `<li><button type="button" class="tb-r" data-tbpick="${esc(tbKey(p))}" aria-pressed="${tbPicked(tbKey(p))}"${tbLocked(tbKey(p)) ? " disabled" : ""}>
  <span class="lbp-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span><span class="tb-n">${esc(nameInitial(p.name))}</span>${tbTagsHTML(p)}
  <b class="tb-v">${lbNum(p.proj)}</b><svg class="tb-tick" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></button></li>`;

/* The roster as a list: IR last, then by position, the highest projection first. */
const tbListHTML = rows => `<ul class="tb-list">${[...rows].sort((a, b) => a.ir - b.ir || TB_POS.indexOf(a.pos) - TB_POS.indexOf(b.pos)
  || b.proj - a.proj).map(tbRowHTML).join("")}</ul>`;

/* A package row is a button too: a tap takes the player back out. A locked player is a plain row with no way out. */
const tbPkgRowHTML = p => tbLocked(tbKey(p)) ? `<li><span class="tb-p tb-pr tb-lock" data-testid="finder-locked">
  <span class="lbp-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span><span class="tb-n">${esc(nameInitial(p.name))}</span>${tbPillHTML(p)}</span></li>`
  : `<li><button type="button" class="tb-p tb-pr" data-tbpick="${esc(tbKey(p))}" aria-label="${esc(t("lboard.edit.remove", {name: p.name}))}">
  <span class="lbp-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span><span class="tb-n">${esc(nameInitial(p.name))}</span>${tbPillHTML(p)}
  <svg class="tb-out" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></li>`;

function tbPkgHTML(){
  const col = (label, keys, rows) => {
    const have = keys.map(k => tbHas(rows, k)).filter(Boolean);
    return `<div class="tb-col"><p class="tb-h">${label}</p><ul>${have.length ? have.map(tbPkgRowHTML).join("")
      : `<li class="tb-hint">${t("lboard.edit.hint")}</li>`}</ul></div>`;
  };
  return `<div class="tb-cols">${col(t("lboard.offer.send"), TB_EDIT.send, TB_EDIT.mine)}${col(t("lboard.offer.get"), TB_EDIT.get, TB_EDIT.theirs)}</div>`;
}

/* The foot: the gain, the IR line and the drop line (their rows are there with nothing in them, so nothing moves),
   the two buttons. */
function tbFootHTML(){
  const E = TB_EDIT, send = E.send.map(k => tbHas(E.mine, k)), get = E.get.map(k => tbHas(E.theirs, k));
  const r = tbGain(E.mine, send, get, E.lu, E.other, E.weeks), empty = !send.length && !get.length;
  const mood = !r.ok || r.gain === 0 ? "flat" : r.gain > 0 ? "up" : "neg";
  const same = ["send", "get"].every(s => E[s].slice().sort().join() === E.from[s].slice().sort().join());
  const n = `<b class="${mood}">${r.ok ? tbSigned(r.gain) : t("lboard.edit.none")}</b>`;
  return `<p class="tb-gain" aria-live="polite">${t("lboard.offer.gain", {n})}</p>
    <div class="tb-edroom"><p class="tb-eir">${r.ok && r.irMoves.length ? t("lboard.offer.ir", {names: tbNames(r.irMoves)}) : ""}</p>
      <p class="tb-edrop">${r.ok && r.drop.length ? t("lboard.offer.drop", {names: tbNames(r.drop)}) : !r.ok && !empty ? t("lboard.edit.nocap") : ""}</p></div>
    <div class="tb-acts"><button type="button" class="tb-copy" data-tbreset${same ? " disabled" : ""}>${t("lboard.edit.reset")}</button>
      <button type="button" class="tb-copy tb-go" data-tbedcopy${r.ok && send.length && get.length ? "" : " disabled"}>${t("lboard.offer.copy")}</button></div>`;
}

/* The state itself: the package, the two rosters, the foot as the tray. */
function tbEditHTML(){
  const roster = (title, rows) => `<section class="tb-roster"><h2>${title}</h2>${tbListHTML(rows)}</section>`;
  return `<div class="tb-pkg tb-card">${tbPkgHTML()}</div>
    <div class="tb-lists">${roster(t("lboard.edit.mine"), TB_EDIT.mine)}${roster(t("lboard.edit.theirs", {name: esc(TB.tm.name)}), TB_EDIT.theirs)}</div>
    <div class="tb-edfoot">${tbFootHTML()}</div>`;
}

/* What a tap changes: the package and the foot, and which rows read as picked. The lists are left alone, so
   the page keeps its scroll and the tapped row its focus. */
function tbEditPaint(){
  const v = document.getElementById("view");
  v.querySelector(".tb-pkg").innerHTML = tbPkgHTML();
  v.querySelector(".tb-edfoot").innerHTML = tbFootHTML();
  v.querySelectorAll(".tb-r").forEach(b => b.setAttribute("aria-pressed", String(tbPicked(b.dataset.tbpick))));
}

/* Opens the edit state against `tm`, the partner (a LIVE_TEAMS row), for the reader's `me` in `lg`. `offer` is the card
   it starts from, null for Make your own; `pick` lets the reader change the partner on the page (Make your own with no
   partner chosen). `lock` (a trade page's Make your own) names the players who stay in the package. Nothing opens when
   the guard has Edit shut or the file has no values for the pair. */
function tbEditOpen(lg, me, tm, offer, opener, pick, lock){
  const lgd = tbLeagueData(lg);
  if (!tbEditOk(lg, me) || !lgd || !lgd.values[tm.name]) return;
  TB = {lg, me, tm};
  const send = offer ? offer.send.map(tbKey) : [], get = offer ? offer.get.map(tbKey) : [];
  TB_EDIT = {mine: lgd.values[me.name], theirs: lgd.values[tm.name], lu: lgd.lineup, weeks: lgd.weeks_left, other: tbOther(lgd, me.name), otherTheirs: tbOther(lgd, tm.name), send, get,
    from: {send: send.slice(), get: get.slice()}, pick: !!pick, lock: lock || [],
    back: opener && opener.dataset.tbedit !== undefined ? `[data-tbedit="${opener.dataset.tbedit}"]`
      : opener && opener.dataset.tpown !== undefined ? "[data-tpown]" : "[data-tbown]"};
  tfForward();
  layerPush("tbedit", tbEditShut);
  tfShow();
}

/* The partner changed on the page (Make your own with no partner chosen): his roster replaces the old one's, what the
   reader gets from the old one is out of the package, what he sends stays. */
function tbEditPartner(tm){
  const lgd = tbLeagueData(TB.lg);
  if (!lgd || !lgd.values[tm.name]) return;
  TB = {...TB, tm};
  Object.assign(TB_EDIT, {theirs: lgd.values[tm.name], otherTheirs: tbOther(lgd, tm.name), get: []});
  TB_EDIT.from.get = [];
  render();
  document.querySelector("[data-tbpartner]")?.focus({preventScroll: true});
}

/* The close itself (Back arrives here); tbEditClose also takes back the history entry. */
function tbEditShut(){
  if (!TB_EDIT) return;
  const back = TB_EDIT.back;
  TB_EDIT = null;
  TB = null;
  tfBack();
  document.querySelector(back)?.focus({preventScroll: true});
}
function tbEditClose(){ tbEditShut(); layerDone("tbedit"); }

/* A tap on a player: out of the package if he is in it, in on his own side if not. */
function tbToggle(key, fromPackage){
  if (tbLocked(key)) return;
  const E = TB_EDIT, side = tbHas(E.mine, key) ? "send" : "get", i = E[side].indexOf(key);
  if (i < 0) E[side].push(key); else E[side].splice(i, 1);
  tbEditPaint();
  const v = document.getElementById("view");
  if (i < 0) v.querySelectorAll(".tb-pkg .tb-col ul")[side === "send" ? 0 : 1].scrollTop = 1e6;     // the new row shows when a fourth scrolls
  if (fromPackage) v.querySelector(`.tb-r[data-tbpick="${CSS.escape(key)}"]`)?.focus({preventScroll: true});
}

function tbReset(){
  TB_EDIT.send = TB_EDIT.from.send.slice();
  TB_EDIT.get = TB_EDIT.from.get.slice();
  tbEditPaint();
}

/* Copy offer, from the foot: the same message as a card's, of season averages. A refused clipboard shows the box
   in the tray, so it is on screen wherever the page is scrolled to. */
function tbEditCopy(btn){
  const E = TB_EDIT, send = E.send.map(k => tbHas(E.mine, k)), get = E.get.map(k => tbHas(E.theirs, k));
  const th = tbTheir(E.theirs, send, get, E.lu, E.otherTheirs, E.weeks);        // the partner's room for this package, live
  const their = th.short ? null : {ir_moves: th.irMoves, drop: th.drop};   // nobody left to cut: no claim about their room
  tbCopyText(btn, tbText({send, get, their}), btn.closest(".tb-edfoot"), "afterbegin");
}

/* The edit page's taps (finder/page.js wires them): a player, Reset and Copy offer inside it. True when one was handled. */
function tbEditClick(hit){
  const pick = hit("[data-tbpick]");
  if (!TB_EDIT) return false;
  if (pick) return tbToggle(pick.dataset.tbpick, pick.classList.contains("tb-pr")), true;
  if (hit("[data-tbreset]")) return tbReset(), true;
  const copy = hit("[data-tbedcopy]");
  if (copy) return tbEditCopy(copy), true;
  return false;
}
