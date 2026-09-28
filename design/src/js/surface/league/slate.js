/* ============================== LEAGUE: THE SLATE (Yahoo back page) ==============================
   Every game of the week as a card: winner over loser (the loser struck through), each side's record
   after that week, Claude's punchline (the stamp beside it on the week's blowout and lowest score),
   the 1-3 facts that back it up, and a box score that opens in place. The team on screen's game
   comes first and opens by default. */

/* The games whose box is open, by key; null until the reader taps one, meaning the team on screen's
   own game. Several may be open: closing one never moves another card. */
let LG_OPEN = null;

const lgKey = g => `${g.a}-${g.b}`;

const lgIsOpen = (g, id) => LG_OPEN ? LG_OPEN.has(lgKey(g)) : g.a === id || g.b === id;

function lgToggleBox(k, id){
  if (!LG_OPEN) LG_OPEN = new Set(lgWeek().games.filter(g => g.a === id || g.b === id).map(lgKey));
  LG_OPEN.has(k) ? LG_OPEN.delete(k) : LG_OPEN.add(k);
}

/* One starter row: the slot, both players (initials, the full name is not a heading here) and their
   points, the higher of the two in full ink. */
function lgSlotHTML([slot, an, ap, bn, bp]){
  const hi = (ap ?? -1) > (bp ?? -1) ? "a" : (bp ?? -1) > (ap ?? -1) ? "b" : "";
  const nm = n => n ? esc(nameInitial(n)) : t("league.box.empty");
  const pt = (v, side) => `<span class="bp-bn${hi === side ? " hi" : ""}">${v == null ? "–" : v.toFixed(1)}</span>`;
  return `<span class="bp-bs">${esc(slot)}</span><span class="bp-bp">${nm(an)}</span>${pt(ap, "a")}${pt(bp, "b")}<span class="bp-bp r">${nm(bn)}</span>`;
}

/* The box in the card's order: the winner on the left, as the card lists it first. The data is home
   (a) left, away (b) right, so an away win swaps every pair. */
function lgBoxHTML(g0){
  const flip = g0.win === "away", b0 = g0.box;
  const g = flip ? {...g0, a: g0.b, b: g0.a} : g0;
  const b = !flip ? b0 : {slots: b0.slots.map(([s, an, ap, bn, bp]) => [s, bn, bp, an, ap]),
    proj: [b0.proj[1], b0.proj[0]], left: [b0.left[1], b0.left[0]]};
  const miss = (m, tid) => m ? `<p class="bp-miss">${t("league.box.miss", {team: lgName(tid), benched: esc(nameInitial(m.benched)),
    bp: m.bp.toFixed(1), started: esc(nameInitial(m.started)), sp: m.sp.toFixed(1), lost: m.lost.toFixed(1)})}</p>` : "";
  return `<div class="bp-box" id="bp-box-${lgKey(g0)}">
    <div class="bp-bgrid"><span></span><span class="bp-bh">${lgName(g.a)}</span><span></span><span></span><span class="bp-bh r">${lgName(g.b)}</span>
      ${b.slots.map(lgSlotHTML).join("")}</div>
    ${miss(b.left[0], g.a)}${miss(b.left[1], g.b)}
    ${b.proj[0] != null ? `<p class="bp-proj">${t("league.box.proj", {a: lgPts(b.proj[0]), b: lgPts(b.proj[1])})}</p>` : ""}
  </div>`;
}

/* One fact under the punchline, its numbers in bold so the eye lands on them; a negative one in red
   (DJ Moore's -0.1). Split on the raw text, then escaped, so an entity's digits are never bolded. A
   hyphen after a digit is a record ("0-2"), not a sign. */
const lgBeatHTML = s => s.split(/((?<![\d.])-?\d+(?:\.\d+)?)/)
  .map((p, i) => i % 2 ? `<b${p.startsWith("-") ? ' class="neg"' : ""}>${p}</b>` : esc(p)).join("");

function lgGameHTML(g, id, i){
  const aWon = g.win !== "away";
  const [win, lose] = aWon ? [[g.a, g.ap, g.ar], [g.b, g.bp, g.br]] : [[g.b, g.bp, g.br], [g.a, g.ap, g.ar]];
  const mine = g.a === id || g.b === id;
  const open = lgIsOpen(g, id);
  const row = ([tid, pts, rec], lost) => `<span class="bp-t${lost ? " lo" : ""}"><b>${lgName(tid)}</b><small>${rec}</small></span>
    <span class="bp-p${lost ? " lo" : ""}">${lgPts(pts)}</span>`;
  // The stamp sits beside the punchline, so both names keep the card's full width.
  const stamp = g.stamp ? `<span class="bp-stamp">${esc(g.stamp)}</span>` : "";
  return `<article class="bp-game${mine ? " mine" : ""}" style="--i:${i}">
    <div class="bp-sc">${row(win, false)}${row(lose, g.win !== "tie")}</div>
    ${g.punch || stamp ? `<div class="bp-punch"><p>${g.punch ? esc(g.punch) : ""}</p>${stamp}</div>` : ""}
    ${g.beats.length ? `<ul class="bp-beats">${g.beats.map(b => `<li><span>${lgBeatHTML(b)}</span></li>`).join("")}</ul>` : ""}
    ${g.box ? `<button class="bp-open" data-lgbox="${lgKey(g)}" aria-expanded="${open}" aria-controls="bp-box-${lgKey(g)}">
      ${open ? t("league.box.hide") : t("league.box.show")}</button>${open ? lgBoxHTML(g) : ""}` : ""}
  </article>`;
}

