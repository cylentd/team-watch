/* One compact card per gallery slip -- not the full slipHTML() payout block, since there can be
   a dozen or more of these in one rail. Every leg in a card shares one kickoff (that's what a
   window is), so the kickoff is said once in the header, never per row. Underdog rows reuse the
   exact call unit the prop market and the cart already use -- name, then HIGHER/LOWER + the
   stat, one unit, no per-leg confidence -- since the card's own headline number already covers
   that. No model%/edge on the leg rows themselves; one headline stat carries the number once. */
/* Why this leg, in one line under it: the model's chance for the call and the history that chance
   rests on -- his per-game rate and how many games. A 70% resting on a rate the line sits far
   from is the leg to doubt, so the rate is never hidden behind the headline. */
function legWhy(l, book, withKick){
  const rate = typeof l.mu === "number"
    ? t("parlay.why.rate", {rate: l.mkt === "RECS" ? l.mu.toFixed(1) : Math.round(l.mu), unit: MKT_SHORT[l.mkt], games: l.games}) : "";
  let why;
  if (book === "underdog"){
    const u = udPick(l);
    why = u.synthetic
      ? t("parlay.why.td", {model: u.conf})
      : [t("parlay.why.ud", {model: u.conf}), rate].join(" · ");
  } else {
    why = [t("parlay.why.dk", {model: l.model, implied: Math.round(amToProb(overPrice(l)) * 100)}), l.mkt === "TD" ? "" : rate]
      .filter(Boolean).join(" · ");
  }
  return `<div class="why">${withKick ? `${esc(l.kick)} · ` : ""}${esc(why)}</div>`;
}

function presetCard(card, bestOf){
  const legs = card.legs.map(i=>PROPS[i]);
  const best = card === (bestOf || GALLERY_BEST[card.book]);
  const day = !!card.win.wins;   // a whole-day card spans kickoffs, so each leg says its own
  const legRows = legs.map(l => { const u = card.book === "underdog" ? udPick(l) : null; return card.book === "underdog"
    ? `<div class="slipleg ud ${u.pick||""}">
        <div><div class="p">${esc(l.n)}</div>
          <div class="m"><span class="dir">${u.pick === "higher" ? t("parlay.call.higher") : u.pick === "lower" ? t("parlay.call.lower") : t("parlay.call.none")}</span><b>${u.line !== null ? u.line : t("parlay.call.td")}</b><span class="stat">${u.line !== null ? MKT_SHORT[l.mkt] : t("parlay.call.anytime")}</span>${u.synthetic ? `<span class="udtag">${t("parlay.gallery.modelTag")}</span>` : ""}</div>
          ${legWhy(l, card.book, day)}</div>
      </div>`
    : `<div class="slipleg">
        <div><div class="p">${esc(l.n)}</div><div class="m">${esc(propLabel(l).toUpperCase())}</div>${legWhy(l, card.book, day)}</div>
        <div class="o">${esc(fmtAm(overPrice(l)))}</div></div>`; }).join("");
  // The headline is the one number this card is selling: Underdog's combined hit rate, or DK's
  // combined price -- not a payrow list of secondary stats a curated card doesn't need to defend.
  let stat;
  if (card.book === "underdog"){
    const udP = legs.reduce((a,l)=>a*udPick(l).conf/100, 1);
    stat = `<div class="ticket-stat"><b>${(udP*100).toFixed(1)}%</b><span>${t("parlay.gallery.allHit", {n: legs.length, x: legs.length === 2 ? 3 : 6})}</span></div>`;
  } else {
    const prices = legs.map(overPrice).filter(a => a !== null);
    const priced = prices.length === legs.length;
    const dec = priced ? prices.reduce((a,x)=>a*amToDec(x), 1) : null;
    const implied = priced ? prices.reduce((a,x)=>a*amToProb(x), 1) : null;
    const modelP = legs.reduce((a,l)=>a*l.model/100, 1);
    const pos = modelP >= implied;
    stat = `<div class="ticket-stat"><b class="${pos?"":"neg"}">${priced ? esc(fmtAm(decToAm(dec))) : "—"}</b><span>${t("parlay.gallery.legsOverBook", {n: legs.length, d: `${pos?"+":""}${((modelP-implied)*100).toFixed(1)}`})}</span></div>`;
  }
  const kick = day ? card.win.short : card.win.kick || card.win.short;
  return `<div class="ticket ${best ? "best" : ""}">
    <div class="ticket-top">
      <div><span class="ticket-eyebrow">${esc(card.scopeLabel)}</span><div class="ticket-kick">${esc(kick.toUpperCase())}</div></div>
      ${best ? `<span class="ticket-best">${t("parlay.gallery.best")}</span>` : card.low ? `<span class="ticket-low">${t("parlay.gallery.lowTag")}</span>` : ""}
    </div>
    ${stat}
    <div class="ticket-tear"></div>
    ${legRows}
    <button class="ticket-cta" data-loadslip="${card.book}:${card.i}">${t("parlay.gallery.loadSlip")}<span>${t("parlay.gallery.legCount", {n: legs.length, s: legs.length===1?"":"s"})}</span></button>
  </div>`;
}

function galleryHTML(){
  const scopes = galleryScopes(PARLAY_BOOK);
  const cards = GALLERIES[PARLAY_BOOK].filter(c => (SLIP_SCOPE==="all"||c.scope===SLIP_SCOPE) && (GAL_WIN==="ALL"||c.win.k===GAL_WIN));
  // "Best" is the best of what is on screen: filter to Wednesday and the star moves to
  // Wednesday's strongest card instead of vanishing with the whole-week winner.
  const bestOf = bestCard(cards);
  return `<div class="rule"><h2>${t("parlay.gallery.heading")}</h2><span class="hair"></span>
    <span class="side">${t("parlay.gallery.sub")}</span></div>
  <div class="filters">
    <span class="lbl">${t("parlay.gallery.legsLabel")}</span>
    ${scopes.map(([k,label])=>`<button class="chip" data-scope="${k}" aria-pressed="${SLIP_SCOPE===k}">${label}</button>`).join("")}
    <span style="flex:1"></span>
    <label class="selwrap"><span class="lbl">${t("parlay.filter.kickoff")}</span>
      <select class="msel" data-msel="gwin">
        <option value="ALL" ${GAL_WIN==="ALL"?"selected":""}>${t("parlay.option.all")}</option>
        ${GAL_WINDOWS.map(w=>`<option value="${w.k}" ${GAL_WIN===w.k?"selected":""}>${esc(w.label)}</option>`).join("")}
      </select>
    </label>
  </div>
  ${cards.length
    ? `<div class="rail" data-railkey="parlay-gallery"><div class="railscroll">${cards.map(c => presetCard(c, bestOf)).join("")}</div></div>`
    : (() => {
          // How close it came: the legs that pass every gate in what is filtered, so "1 line,
          // a card needs 2" reads as the model declining, not the page failing.
          const s = SLIP_SCOPE === "all" ? "mix" : SLIP_SCOPE;
          const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
          const ok = PROPS.filter(p => legOKInBook(p, s, PARLAY_BOOK) && inWin(p, win)).length;
          return `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>${ok}</b><span>${t("parlay.gallery.empty", {s: ok === 1 ? "" : "S"})}</span></div></div>`;
        })()}`;
}

