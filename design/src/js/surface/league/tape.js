/* ============================== LEAGUE: THIS WEEK'S GRUDGE (Yahoo back page) ==============================
   The team on screen against this week's opponent, as one point: the series record, one sentence on
   who owns it and who is hot, and the last meetings as W/L chips. (2026-09-27: it was a tale of the
   tape with six stat rows, a bar per meeting, a legend and two footnotes, and nobody could tell who
   owned the series. Titles and all-time records live on Records now.) */

/* The current run in the series from the team on screen's side: ["W", 3], ["L", 1], or null. */
function lgRun(m){
  if (!m || !m.length) return null;
  const won = x => x[2] > 0, last = won(m[m.length - 1]);
  let n = 0;
  for (let i = m.length - 1; i >= 0 && m[i][2] !== 0 && won(m[i]) === last; i--) n++;
  return [last ? "W" : "L", n];
}

/* Who owns it and who is hot, in one sentence. Every case spelled out for assemble.py --check. */
function lgGrudgeLine(id, opp, h, m){
  if (!m.length) return t("league.grudge.first");
  const lead = h.w > h.l ? id : h.l > h.w ? opp : null;
  // A shutout series is the whole story: nothing else in the line competes with it.
  if (m.length >= 3 && (!h.w || !h.l) && !h.t)
    return t("league.grudge.never", {lead: `<b>${lgName(lead)}</b>`, other: `<b>${lgName(lead === id ? opp : id)}</b>`, n: m.length});
  const run = lgRun(m), hot = run && run[1] >= 2 ? (run[0] === "W" ? id : opp) : null;
  const at = {lead: `<b>${lgName(lead)}</b>`, other: `<b>${lgName(hot)}</b>`, n: run && run[1]};
  if (lead && hot && hot !== lead) return t("league.grudge.ownsBut", at);
  if (lead && hot) return t("league.grudge.ownsAnd", at);
  if (lead) return t("league.grudge.owns", at);
  return hot ? t("league.grudge.evenRun", at) : t("league.grudge.even");
}

/* The team on screen against this week's opponent (My recap). */
const lgGrudgeHTML = id => lgPairGrudgeHTML(id, id ? lgOpp(id) : null, t("league.grudge.title"));

/* One pairing's grudge card, from `id`'s side: My recap's own, or the league page's biggest one. */
function lgPairGrudgeHTML(id, opp, title){
  if (!LG.teams.some(x => x.id === id) || !LG.teams.some(x => x.id === opp)) return "";
  const h = lgH2H(id, opp) || {w: 0, l: 0, t: 0, m: []}, m = h.m || [];
  const chips = m.slice(-10).map(x => `<span><i class="${x[2] > 0 ? "w" : "l"}">${x[2] > 0 ? t("league.grudge.w") : t("league.grudge.l")}</i>
    <small>'${String(x[0]).slice(2)}</small></span>`).join("");
  return `<section class="lg-sec bp-grudge" aria-label="${title}">
    <h3 class="bp-hd">${title}<span>${t("league.tape.sub", {n: LG.week})}</span></h3>
    <div class="bp-gcard">
      <div class="bp-gvs"><span>${lgName(id)}</span><b>${h.t ? `${h.w}–${h.l}–${h.t}` : `${h.w}–${h.l}`}</b><span>${lgName(opp)}</span></div>
      <p class="bp-gline">${lgGrudgeLine(id, opp, h, m)}</p>
      ${chips ? `<div class="bp-gchips" role="img" aria-label="${t("league.grudge.chipsAria", {n: Math.min(10, m.length)})}">${chips}</div>` : ""}
    </div>
  </section>`;
}
