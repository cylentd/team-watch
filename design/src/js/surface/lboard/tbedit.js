/* ============================== LEAGUE > TEAMS: THE TRADE BUILDER, EDIT ==============================
   2026-10-05 (storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, frame 4). The reader's own package,
   built inside the builder sheet: "Edit" on an offer card starts from that offer, "Make your own offer" from an
   empty package. It is its own layer (layers.js "tbedit"), so Back, Escape, the x, the scrim and a pull down
   each return to the offers first.

   Top: the package, YOU SEND and YOU GET, three rows tall whatever is in it (a fourth scrolls inside). Below: the
   reader's roster and the partner's, from the file's `values`, each row a switch that puts the player in or out of
   the package. Foot, never moving: the live gain by tbscore.js (green, red, or a dash for an empty package), the
   players the reader would drop to stay at the roster cap, Reset to the offer it started from, and Copy offer.
   Nothing about the partner's roster room is checked or shown. Only offers.js's guard (tbEditOk) lets it open. */

const TB_POS = ["QB", "RB", "WR", "TE"];

const tbSigned = g => (g > 0 ? "+" : g < 0 ? "−" : "") + lbNum(Math.abs(g));
const tbHas = (rows, key) => rows.find(p => tbKey(p) === key);
const tbPicked = key => TB_EDIT.send.includes(key) || TB_EDIT.get.includes(key);

const tbRowHTML = p => `<li><button type="button" class="tb-r" data-tbpick="${esc(tbKey(p))}" aria-pressed="${tbPicked(tbKey(p))}">
  <span class="lbs-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span><span class="tb-n">${esc(nameInitial(p.name))}</span>${tbPillHTML(p)}
  <b class="tb-v">${lbNum(p.proj)}</b><svg class="tb-tick" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></button></li>`;

/* The roster as a list: IR last, then by position, the highest projection first. */
const tbListHTML = rows => `<ul class="tb-list">${[...rows].sort((a, b) => a.ir - b.ir || TB_POS.indexOf(a.pos) - TB_POS.indexOf(b.pos)
  || b.proj - a.proj).map(tbRowHTML).join("")}</ul>`;

/* A package row is a button too: a tap takes the player back out. */
const tbPkgRowHTML = p => `<li><button type="button" class="tb-p tb-pr" data-tbpick="${esc(tbKey(p))}" aria-label="${esc(t("lboard.edit.remove", {name: p.name}))}">
  <span class="lbs-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span><span class="tb-n">${esc(nameInitial(p.name))}</span>${tbPillHTML(p)}
  <svg class="tb-out" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></li>`;

function tbPkgHTML(){
  const col = (label, keys, rows) => {
    const have = keys.map(k => tbHas(rows, k)).filter(Boolean);
    return `<div class="tb-col"><p class="tb-h">${label}</p><ul>${have.length ? have.map(tbPkgRowHTML).join("")
      : `<li class="tb-hint">${t("lboard.edit.hint")}</li>`}</ul></div>`;
  };
  return `<div class="tb-cols">${col(t("lboard.offer.send"), TB_EDIT.send, TB_EDIT.mine)}${col(t("lboard.offer.get"), TB_EDIT.get, TB_EDIT.theirs)}</div>`;
}

/* The foot: the gain, the drop line (its row is there with nothing in it, so nothing moves), the two buttons. */
function tbFootHTML(){
  const E = TB_EDIT, send = E.send.map(k => tbHas(E.mine, k)), get = E.get.map(k => tbHas(E.theirs, k));
  const r = tbGain(E.mine, send, get, E.lu, E.other), empty = !send.length && !get.length;
  const mood = !r.ok || r.gain === 0 ? "flat" : r.gain > 0 ? "up" : "neg";
  const same = ["send", "get"].every(s => E[s].slice().sort().join() === E.from[s].slice().sort().join());
  const n = `<b class="${mood}">${r.ok ? tbSigned(r.gain) : t("lboard.edit.none")}</b>`;
  return `<p class="tb-gain" aria-live="polite">${t("lboard.offer.gain", {n})}</p>
    <p class="tb-edrop">${r.ok && r.drop.length ? t("lboard.offer.drop", {names: esc(r.drop.map(p => nameInitial(p.name)).join(", "))}) : !r.ok && !empty ? t("lboard.edit.nocap") : ""}</p>
    <div class="tb-acts"><button type="button" class="tb-copy" data-tbreset${same ? " disabled" : ""}>${t("lboard.edit.reset")}</button>
      <button type="button" class="tb-copy tb-go" data-tbedcopy${r.ok && send.length && get.length ? "" : " disabled"}>${t("lboard.offer.copy")}</button></div>`;
}

/* The state itself: the package, the two rosters (the only part that scrolls), the foot. */
function tbEditHTML(){
  return `<div class="tb-pkg tb-card">${tbPkgHTML()}</div>
    <div class="tb-lists"><h3>${t("lboard.edit.mine")}</h3>${tbListHTML(TB_EDIT.mine)}
      <h3>${t("lboard.edit.theirs", {name: esc(TB.tm.name)})}</h3>${tbListHTML(TB_EDIT.theirs)}</div>
    <div class="tb-edfoot">${tbFootHTML()}</div>`;
}

/* What a tap changes: the package and the foot, and which rows read as picked. The lists are left alone, so they
   keep their scroll and the tapped row its focus. */
function tbEditPaint(){
  const d = tbEl();
  d.querySelector(".tb-pkg").innerHTML = tbPkgHTML();
  d.querySelector(".tb-edfoot").innerHTML = tbFootHTML();
  d.querySelectorAll(".tb-r").forEach(b => b.setAttribute("aria-pressed", String(tbPicked(b.dataset.tbpick))));
}

function tbEditOpen(offer, opener){
  const lgd = tbLeagueData(TB.lg);
  if (!tbEditOk() || !lgd) return;
  const send = offer ? offer.send.map(tbKey) : [], get = offer ? offer.get.map(tbKey) : [];
  TB_EDIT = {mine: lgd.values[TB.me.name], theirs: lgd.values[TB.tm.name], lu: lgd.lineup, other: tbOther(lgd, TB.me.name), send, get,
    from: {send: send.slice(), get: get.slice()}, back: opener && opener.dataset.tbedit !== undefined ? `[data-tbedit="${opener.dataset.tbedit}"]` : "[data-tbown]"};
  layerPush("tbedit", tbEditShut);
  tbPaint();
  tbEl().querySelector(".lbs-x").focus({preventScroll: true});
}

/* The close itself (Back arrives here); tbEditClose also takes back the history entry. */
function tbEditShut(){
  if (!TB_EDIT) return;
  const back = TB_EDIT.back;
  TB_EDIT = null;
  if (!TB) return;
  tbPaint();
  tbEl().querySelector(back)?.focus({preventScroll: true});
}
function tbEditClose(){ tbEditShut(); layerDone("tbedit"); }

/* A tap on a player: out of the package if he is in it, in on his own side if not. */
function tbToggle(key, fromPackage){
  const E = TB_EDIT, side = tbHas(E.mine, key) ? "send" : "get", i = E[side].indexOf(key);
  if (i < 0) E[side].push(key); else E[side].splice(i, 1);
  tbEditPaint();
  const d = tbEl();
  if (i < 0) d.querySelectorAll(".tb-pkg .tb-col ul")[side === "send" ? 0 : 1].scrollTop = 1e6;     // the new row shows when a fourth scrolls
  if (fromPackage) d.querySelector(`.tb-r[data-tbpick="${CSS.escape(key)}"]`)?.focus({preventScroll: true});
}

function tbReset(){
  TB_EDIT.send = TB_EDIT.from.send.slice();
  TB_EDIT.get = TB_EDIT.from.get.slice();
  tbEditPaint();
}

/* Copy offer, from the foot: the same message as a card's, of season averages. */
function tbEditCopy(btn){
  const E = TB_EDIT, lists = tbEl().querySelector(".tb-lists");
  lists.scrollTop = 0;
  tbCopyText(btn, tbText({send: E.send.map(k => tbHas(E.mine, k)), get: E.get.map(k => tbHas(E.theirs, k))}), lists, "afterbegin");
}

/* Bound once, on the sheet: its markup is replaced on every open, its listeners are not. */
(() => {
  const d = tbEl();
  if (!d) return;
  d.addEventListener("click", e => {
    const hit = sel => e.target.closest(sel);
    const edit = hit("[data-tbedit]"), own = hit("[data-tbown]"), pick = hit("[data-tbpick]");
    if (edit && TB_DATA) return tbEditOpen(tbOffers()[+edit.dataset.tbedit], edit);
    if (own && TB_DATA) return tbEditOpen(null, own);
    if (!TB_EDIT) return;
    if (pick) return tbToggle(pick.dataset.tbpick, pick.classList.contains("tb-pr"));
    if (hit("[data-tbreset]")) return tbReset();
    const copy = hit("[data-tbedcopy]");
    if (copy) tbEditCopy(copy);
  });
})();
