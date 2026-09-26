/* One compact card per gallery slip -- not the full slipHTML() payout block, since there can be
   a dozen or more of these in one rail. */
/* Why this leg, in one line under it: the history the model's chance rests on -- his per-game
   rate and how many games. A 70% resting on a rate the line sits far from is the leg to doubt,
   so the rate is never hidden. Underdog's confidence is already the number beside the leg, so
   its why is only the rate (or, for a model-read TD, where the chance comes from). DK's adds
   the model against the price. The kickoff is the game header's, never the leg's. */
function legWhy(l, book){
  const rate = typeof l.mu === "number"
    ? t("parlay.why.rate", {rate: l.mkt === "RECS" ? l.mu.toFixed(1) : Math.round(l.mu), unit: MKT_SHORT[l.mkt].toLowerCase(), games: l.games}) : "";
  let why;
  if (book === "underdog"){
    why = udPick(l).synthetic ? t("parlay.why.tdUsage") : rate;
  } else {
    why = [t("parlay.why.dk", {model: l.model, implied: Math.round(amToProb(overPrice(l)) * 100)}), l.mkt === "TD" ? "" : rate]
      .filter(Boolean).join(" · ");
  }
  return why ? `<span class="why">${esc(why)}</span>` : "";
}

/* A leg read as a sentence, the way the book's own app prints it: "Lower 4.5 Receptions". The
   direction word carries the colour; nothing is in capitals. */
function legCall(l, book){
  if (book === "underdog"){
    const u = udPick(l);
    const dir = u.pick === "higher" ? t("parlay.slip.higher") : u.pick === "lower" ? t("parlay.slip.lower") : "";
    return `<em class="${u.pick || ""}">${dir}</em> ${u.line !== null ? `${u.line} ${esc(MKT[l.mkt])}` : esc(MKT.TD)}${u.synthetic ? ` <span class="tk-model">${t("parlay.gallery.modelTag")}</span>` : ""}`;
  }
  return l.line === null ? esc(MKT[l.mkt]) : `<em class="higher">${t("parlay.slip.over")}</em> ${l.line} ${esc(MKT[l.mkt])}`;
}

/* The legs under the game they belong to, first appearance keeping the card's order. */
function legGroups(legs){
  const by = new Map();
  legs.forEach(l => (by.get(l.game) || by.set(l.game, []).get(l.game)).push(l));
  return [...by.values()];
}

/* A gallery slip, drawn after Underdog's own share card (2026-09-25; it was printed paper, which
   read as a bright panel on the dark page and set every line in spaced capitals). The number the
   slip is selling on top, big; then each game with its kickoff, and one rounded row per leg:
   his photo, his name, the call as a sentence, and the one number beside it (Underdog: the
   model's confidence; DK: the price). The why line stays under each call, quiet. */
function presetCard(card, bestOf){
  const legs = card.legs.map(i=>PROPS[i]);
  const best = card === (bestOf || GALLERY_BEST[card.book]);
  const ud = card.book === "underdog";
  let head, meta;
  if (ud){
    const udP = legs.reduce((a,l)=>a*udPick(l).conf/100, 1);
    meta = t("parlay.slip.udMeta", {n: legs.length, x: legs.length === 2 ? 3 : 6});
    head = `<b>${(udP*100).toFixed(1)}%</b> ${t("parlay.slip.toHitAll", {n: legs.length})}`;
  } else {
    const prices = legs.map(overPrice).filter(a => a !== null);
    const priced = prices.length === legs.length;
    const dec = priced ? prices.reduce((a,x)=>a*amToDec(x), 1) : null;
    const implied = priced ? prices.reduce((a,x)=>a*amToProb(x), 1) : null;
    const modelP = legs.reduce((a,l)=>a*l.model/100, 1);
    const pos = modelP >= implied;
    meta = t("parlay.slip.dkMeta", {n: legs.length, d: `${pos?"+":""}${((modelP-implied)*100).toFixed(1)}`});
    head = `<b class="${pos?"":"neg"}">${priced ? esc(fmtAm(decToAm(dec))) : "—"}</b> ${t("parlay.slip.forLegs", {n: legs.length})}`;
  }
  const flag = best ? `<span class="tk-flag best">${t("parlay.slip.best")}</span>`
    : card.low ? `<span class="tk-flag">${t("parlay.slip.low")}</span>` : "";
  const groups = legGroups(legs).map(g => `<div class="tk-game"><b>${esc(g[0].game)}</b>${g[0].kick ? `<span>${esc(g[0].kick)}</span>` : ""}</div>
    ${g.map(l => `<div class="tk-leg">${avatarHTML(l)}
      <div class="tk-who"><b>${esc(l.n)}</b><span class="tk-call">${legCall(l, card.book)}</span>${legWhy(l, card.book)}</div>
      <span class="tk-num">${ud ? `${udPick(l).conf}<i>%</i>` : esc(fmtAm(overPrice(l)))}</span></div>`).join("")}`).join("");
  return `<div class="ticket ${best ? "best" : ""}" data-card="${card.book}:${card.i}">
    <div class="tk-top"><span>${esc(card.scopeLabel)} · ${meta}</span><span class="tk-book">${ud ? t("parlay.book.underdog") : t("parlay.book.dk")}</span></div>
    <div class="tk-head">${head}</div>
    ${flag}
    ${groups}
    <div class="ticket-tear"></div>
    <button class="ticket-cta" data-loadslip="${card.book}:${card.i}">${t("parlay.gallery.loadSlip")}<span>${t("parlay.gallery.legCount", {n: legs.length, s: legs.length===1?"":"s"})}</span></button>
  </div>`;
}

function galleryHTML(){
  const cards = GALLERIES[PARLAY_BOOK].filter(c => (SLIP_SCOPE==="all"||c.scope===SLIP_SCOPE) && (GAL_WIN==="ALL"||c.win.k===GAL_WIN));
  // "Best" is the best of what is on screen: filter to Wednesday and the star moves to
  // Wednesday's strongest card instead of vanishing with the whole-week winner.
  const bestOf = bestCard(cards);
  // The legs filter and kickoff live in the Bets bar (bar.js); the cards stack down the page, one
  // column on a phone, so nothing scrolls sideways inside a page that scrolls down.
  return cards.length
    ? `<div class="tk-grid">${cards.map(c => presetCard(c, bestOf)).join("")}</div>`
    : (() => {
          // How close it came: the legs that pass every gate in what is filtered, so "1 line,
          // a card needs 2" reads as the model declining, not the page failing.
          const s = SLIP_SCOPE === "all" ? "mix" : SLIP_SCOPE;
          const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
          const ok = PROPS.filter(p => legOKInBook(p, s, PARLAY_BOOK) && inWin(p, win)).length;
          return `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>${ok}</b><span>${t("parlay.gallery.empty", {s: ok === 1 ? "" : "S"})}</span></div></div>`;
        })();
}

