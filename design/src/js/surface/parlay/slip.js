/* What "Copy slip" puts on the clipboard: one leg per line, the way you would type it into the
   book, at the side on the slip ("George Kittle Higher 4.5 Receptions"). */
function slipText(){
  const word = i => PARLAY_BOOK === "dk" ? t("parlay.slip.over") : slipSide(i) === "lower" ? t("slips.side.lower") : t("slips.side.higher");
  const lines = SLIP.map(i => {
    const l = PROPS[i], line = slLine(l);
    return l.mkt === "TD" || line == null ? `${l.n} ${MKT[l.mkt]} ${t("slips.side.yes")}` : `${l.n} ${word(i)} ${line} ${MKT[l.mkt]}`;
  });
  return lines.join("\n") + `\n${t("parlay.copy.footer", {lines: LIVE_MARKET ? t("parlay.copy.lines", {when: LIVE_MARKET.fetched}) : t("parlay.copy.sampleLines")})}`;
}

/* The payout box (2026-09-25): the multiplier the Underdog app quotes for this slip, boosts and
   discounts included, filled with the standard board until the reader types one. The verdict under
   it is the graded chance against that number, and updates as they type (traywire.js). A slip with
   a leg the model does not price has no graded chance, so no verdict. */
function betsVerdictHTML(legs){
  const x = betsPayout(legs), p = udChance(legs);
  if (p === null) return "";
  return x > 1 ? slipVerdict(p * x, t("parlay.slip.vsPayout", {x}), (p*100).toFixed(1), (100/x).toFixed(1))
    : `<span class="tk-flag">${t("parlay.slip.typePay")}</span>`;
}
function betsPayHTML(legs){
  const x = betsPayout(legs);
  return `<label class="paybox"><span>${t("parlay.slip.appPays")}</span>
      <input data-bpay inputmode="decimal" autocomplete="off" value="${x ? x : ""}" placeholder="${t("parlay.slip.payHint")}"><i>×</i></label>
    <div class="payverdict" data-bpayv>${betsVerdictHTML(legs)}</div>`;
}

/* One Underdog leg: name, then the side on the slip, the line and the stat, and remove. */
function slipLegUdHTML(i){
  const l = PROPS[i], side = slipSide(i), td = l.mkt === "TD", line = slLine(l);
  const dir = td ? t("slips.side.yes") : side === "lower" ? t("slips.side.lower") : t("slips.side.higher");
  return `<div class="slipleg ud ${side}">
      <div><div class="p">${esc(l.n)}</div>
        <div class="m"><span class="dir">${dir}</span><b>${td || line == null ? t("parlay.call.td") : line}</b><span class="stat">${td ? t("parlay.call.anytime") : esc(MKT_SHORT[l.mkt] || l.mkt)}</span></div></div>
      <button class="legremove" data-removeleg="${i}" title="${t("common.action.remove")}">✕</button></div>`;
}

const slipEmptyHTML = key => `<div class="state-empty" style="margin:14px 15px;min-height:90px"><div><b>0</b><span>${key}</span></div></div>`;

function slipHTML(){
  const legs = SLIP.map(i=>PROPS[i]);
  const games = legs.map(l=>l.game);
  const corr = games.find((g,i)=>games.indexOf(g)!==i);
  /* Book terms are arithmetic on the posted prices: the parlay pays the product of the decimal
     odds, and its implied probability is the product of each leg's. The model half is not. */
  const prices = legs.map(overPrice).filter(a => a !== null);
  const priced = prices.length === legs.length && legs.length > 0;
  const dec = priced ? prices.reduce((a,x)=>a*amToDec(x), 1) : null;
  const implied = priced ? prices.reduce((a,x)=>a*amToProb(x), 1) : null;
  const modeled = legs.length > 0 && legs.every(l => typeof l.model === "number");
  const modelP = modeled ? legs.reduce((a,l)=>a*l.model/100, 1) : null;
  const pct = x => `${(x*100).toFixed(1)}%`;
  const udMode = PARLAY_BOOK === "underdog";
  const title = SLIP_MODE === "mine" ? t("parlay.slip.titleMine") : udMode ? t("parlay.slip.titleUd") : t("parlay.slip.titleDk");
  const udP = udMode && legs.length ? udChance(legs) : null;
  const chips = `<div class="presets">
    ${PRESETS.map(([k,label]) =>
      `<button class="chip" data-preset="${k}" aria-pressed="${SLIP_MODE===k}">${label}</button>`).join("")}</div>`;
  const model = legs.some(l => (udPick(l) || {}).synthetic);
  if (udMode) return `<div class="slip">
    <div class="sliphead"><span class="lbl">${title}</span><span class="pill">${t("parlay.slip.pickCount", {n: legs.length})}</span></div>
    ${chips}
    ${legs.length ? SLIP.map(slipLegUdHTML).join("") : slipEmptyHTML(t("slips.tray.emptySheet"))}
    <div class="payout">
      <span class="lbl">${t("parlay.slip.allHit")}</span>
      <div class="bigedge">${udP === null ? "—" : `${(udP*100).toFixed(1)}%`}</div>
      ${legs.length >= 2 ? betsPayHTML(legs) : ""}
      <div class="payrow"><span>${model ? t("parlay.slip.tdModelRead") : t("parlay.slip.udLine")}</span><b>${model ? t("parlay.slip.notUdPrice") : t("parlay.slip.notDk")}</b></div>
      <button class="btn" data-copy="picks" style="width:100%;margin-top:14px" ${legs.length ? "" : "disabled"}>${t("parlay.slip.copyPicks")}</button>
    </div>
  </div>`;
  return `<div class="slip">
    <div class="sliphead"><span class="lbl">${title}</span><span class="pill">${t("parlay.slip.legCount", {n: legs.length})}</span></div>
    ${chips}
    ${legs.length ? legs.map((l,k)=>`<div class="slipleg">
      <div><div class="p">${esc(l.n)}</div><div class="m">${esc(propLabel(l).toUpperCase())}${l.books ? ` · ${esc(ABBR[l.book]||l.book)}` : ""}${l.kick ? ` · ${esc(l.kick.toUpperCase())}` : ""}${typeof l.edge === "number" ? ` · ${l.model}% · ${l.edge>0?"+":""}${l.edge.toFixed(1)}` : ""}</div></div>
      <div class="o">${esc(fmtAm(overPrice(l)))}</div>
      <button class="legremove" data-removeleg="${SLIP[k]}" title="${t("common.action.remove")}">✕</button></div>`).join("")
      : slipEmptyHTML(SLIP_MODE === "mine" ? t("parlay.slip.emptyMine") : t("slips.tray.emptySheet"))}
    ${corr ? `<div class="corr"><span>⚠</span>${t("parlay.slip.corr", {game: esc(corr.toUpperCase())})}</div>` : ""}
    <div class="payout">
      <span class="lbl">${modeled ? t("parlay.slip.edgeOverBook") : t("parlay.slip.edgeLabel")}</span>
      <div class="bigedge ${modeled ? "" : "pending"}">${modeled ? `${modelP >= implied ? "+" : ""}${((modelP-implied)*100).toFixed(1)}` : t("parlay.slip.pending")}</div>
      <div class="payrow"><span>${t("parlay.slip.modelProb")}</span><b>${modeled ? pct(modelP) : "—"}</b></div>
      <div class="payrow"><span>${t("parlay.detail.bookImplied")}</span><b>${priced ? pct(implied) : "—"}</b></div>
      <div class="payrow"><span>${t("parlay.slip.combinedOdds")}</span><b>${priced ? fmtAm(decToAm(dec)) : "—"}</b></div>
      <div class="payrow"><span>${t("parlay.slip.returns25")}</span><b>${priced ? `$${Math.round(25*dec)}` : "—"}</b></div>
      <button class="btn" data-copy="slip" style="width:100%;margin-top:14px" ${legs.length ? "" : "disabled"}>${t("parlay.slip.copySlip")}</button>
    </div>
  </div>`;
}
