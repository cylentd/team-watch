/* The Compare sheet (storyboard v5, https://claude.ai/artifact/BLusCqR3ZToXGQ8Kr3nVZM; DESIGN.md
   "Compare"). This week's projection leads, one centred card per player, the gap to the leader
   as a signed number under each other one; then the graph (cmpgraph.js); then one strip per stat
   (cmprows.js). Show, don't tell: no sentence says who is ahead, the numbers and the shapes do.

   A card is the player's button: a tap brings his shape forward on the graph and puts his ranks
   on its labels. The colour order is the pick order (cmp-s0..2), from card to graph to sparkline. */
function cmpShowHTML(){
  const ps = cmpPlayers(), wk = typeof LIVE_RANKS !== "undefined" && LIVE_RANKS ? LIVE_RANKS.week : null;
  return `<div class="cmp-h"><h4 id="cmp-t">${t("profile.compare.head")}${wk ? `<span class="cmp-wk lbl">${t("profile.compare.week", {n: wk})}</span>` : ""}</h4>
      <button type="button" class="cmp-change" data-cmp="change">${t("profile.compare.change")}</button>
      <button type="button" class="dr-close cmp-x" data-cmp="close" aria-label="${t("profile.compare.close")}">✕</button></div>
    <div class="cmp-band" style="--n:${ps.length}">${cmpCardsHTML(ps)}</div>
    <div class="cmp-graph-box">${cmpGraphHTML(ps, CMP.on)}</div>
    ${cmpStripsHTML(ps)}`;
}

function cmpCardsHTML(ps){
  const pts = ps.map(projFor), top = Math.max(...pts.filter(v => v !== null));
  return ps.map((p, i) => {
    const v = pts[i], rk = cmpRankRow(p), lead = v !== null && v === top;
    const gap = v !== null && !lead ? `<span class="cmp-gap">−${(top - v).toFixed(1)}</span>` : "";
    const rank = rk ? `${esc(rk.pos)}${rk.rank}` : esc(p.pos || "");
    const src = HEADS[p.slug];
    const face = src && p.pos !== "DST" ? headImgHTML(src, initials(p.n), p.slug, 56) : headHTML(p);
    return `<button type="button" class="cmp-card cmp-s${i}${lead ? " lead" : ""}${CMP.on === i ? " on" : ""}" data-cmp="focus" data-i="${i}" aria-pressed="${CMP.on === i}">
      <span class="cmp-face">${face}</span><b>${shortName(p.n)}</b>
      <span class="cmp-proj">${v === null ? "—" : v.toFixed(1)}</span>
      <span class="cmp-rank">${gap}${gap ? " · " : ""}${rank}</span></button>`;
  }).join("");
}

/* A tap on a card: the focus moves, the graph redraws, the cards keep their places. */
function cmpFocus(d, i){
  CMP.on = i;
  d.querySelectorAll(".cmp-card").forEach(b => { const me = +b.dataset.i === i; b.classList.toggle("on", me); b.setAttribute("aria-pressed", me); });
  const box = d.querySelector(".cmp-graph-box");
  if (box) box.innerHTML = cmpGraphHTML(cmpPlayers(), i);
}
