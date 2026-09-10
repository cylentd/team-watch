/* What "Copy slip" puts on the clipboard: one leg per line, the way you would type it into the
   book, plus the model's number so a pasted slip still says why. */
function slipText(picks){
  const legs = SLIP.map(i=>PROPS[i]);
  const lines = legs.map(l => picks
    ? `${l.n} ${MKT[l.mkt]} ${udPick(l).pick}${udPick(l).line !== null ? ` ${udPick(l).line}` : ""} (${udPick(l).synthetic ? t("parlay.copy.model") : t("parlay.copy.underdog")}) · ${udPick(l).conf}%`
    : `${l.n} ${propLabel(l)} ${fmtAm(overPrice(l))} (${l.books ? l.book : t("parlay.copy.book")})${typeof l.model === "number" ? ` · ${t("parlay.copy.modelPct", {n: l.model})}${typeof l.edge === "number" ? `, ${t("parlay.copy.edge", {n: `${l.edge>0?"+":""}${l.edge.toFixed(1)}`})}` : ""}` : ""}`);
  return lines.join("\n") + `\n${t("parlay.copy.footer", {lines: LIVE_MARKET ? t("parlay.copy.lines", {when: LIVE_MARKET.fetched}) : t("parlay.copy.sampleLines")})}`;
}

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
  const udP = udMode && legs.length ? legs.reduce((a,l)=>a*udPick(l).conf/100, 1) : null;
  const chips = `<div class="presets">
    ${PRESETS.map(([k,label]) =>
      `<button class="chip" data-preset="${k}" aria-pressed="${SLIP_MODE===k}">${label}</button>`).join("")}</div>`;
  if (udMode) return `<div class="slip">
    <div class="sliphead"><span class="lbl">${title}</span><span class="pill">${t("parlay.slip.pickCount", {n: legs.length})}</span></div>
    ${chips}
    ${legs.length ? legs.map((l,k)=>{ const u = udPick(l); return `<div class="slipleg ud ${u.pick||""}">
      <div><div class="p">${esc(l.n)}</div>
        <div class="m"><span class="dir">${u.pick === "higher" ? t("parlay.call.higher") : u.pick === "lower" ? t("parlay.call.lower") : t("parlay.call.none")}</span><b>${u.line !== null ? u.line : t("parlay.call.td")}</b><span class="stat">${u.line !== null ? MKT_SHORT[l.mkt] : t("parlay.call.anytime")}</span></div></div>
      <button class="legremove" data-removeleg="${SLIP[k]}" title="${t("common.action.remove")}">✕</button></div>`;}).join("")
      : `<div class="state-empty" style="margin:14px 15px;min-height:90px"><div><b>0</b><span>${t("parlay.slip.emptyUd", {n: UD_MIN})}</span></div></div>`}
    <div class="payout">
      <span class="lbl">${t("parlay.slip.allHit")}</span>
      <div class="bigedge">${udP === null ? "—" : `${(udP*100).toFixed(1)}%`}</div>
      <div class="payrow"><span>${t("parlay.slip.be6")}</span><b>16.7%</b></div>
      <div class="payrow"><span>${t("parlay.slip.be3")}</span><b>33.3%</b></div>
      <div class="payrow"><span>${legs.some(l=>udPick(l).synthetic) ? t("parlay.slip.tdModelRead") : t("parlay.slip.udLine")}</span><b>${legs.some(l=>udPick(l).synthetic) ? t("parlay.slip.notUdPrice") : t("parlay.slip.notDk")}</b></div>
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
      : `<div class="state-empty" style="margin:14px 15px;min-height:90px"><div><b>0</b><span>${SLIP_MODE === "mine" ? t("parlay.slip.emptyMine") : t("parlay.slip.emptyBlank")}</span></div></div>`}
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

