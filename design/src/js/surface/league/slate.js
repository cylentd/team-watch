/* ============================== LEAGUE: A GAME'S BOX SCORE AND FACTS (Yahoo) ==============================
   The box score of one game (the winner's side on the left) and its facts, the numbers in bold. Two
   places draw it: the game sheet a row opens (lead.js) and Your game's Box score disclosure (myrecap.js).
   (Until 2026-10-06 this file also drew the slate's game cards, each with a box that opened in place.) */

const lgKey = g => `${g.a}-${g.b}`;

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

