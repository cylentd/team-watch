/* What "Copy slip" puts on the clipboard: one leg per line, the way you would type it into the
   book, plus the model's number so a pasted slip still says why. */
function slipText(picks){
  const legs = SLIP.map(i=>PROPS[i]);
  const lines = legs.map(l => picks
    ? `${l.n} ${MKT[l.mkt]} ${udPick(l).pick}${udPick(l).line !== null ? ` ${udPick(l).line}` : ""} (${udPick(l).synthetic ? "model" : "Underdog"}) · ${udPick(l).conf}%`
    : `${l.n} ${propLabel(l)} ${fmtAm(overPrice(l))} (${l.books ? l.book : "book"})${typeof l.model === "number" ? ` · model ${l.model}%${typeof l.edge === "number" ? `, edge ${l.edge>0?"+":""}${l.edge.toFixed(1)}` : ""}` : ""}`);
  return lines.join("\n") + `\nTeam Watch · ${LIVE_MARKET ? "lines " + LIVE_MARKET.fetched : "sample lines"}`;
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
  const title = SLIP_MODE === "mine" ? "My players" : udMode ? "Underdog picks" : "Your slip";
  const udP = udMode && legs.length ? legs.reduce((a,l)=>a*udPick(l).conf/100, 1) : null;
  const chips = `<div class="presets">
    ${PRESETS.map(([k,label]) =>
      `<button class="chip" data-preset="${k}" aria-pressed="${SLIP_MODE===k}">${label}</button>`).join("")}</div>`;
  if (udMode) return `<div class="slip">
    <div class="sliphead"><span class="lbl">${title}</span><span class="pill">${legs.length} picks</span></div>
    ${chips}
    ${legs.length ? legs.map((l,k)=>{ const u = udPick(l); return `<div class="slipleg ud ${u.pick||""}">
      <div><div class="p">${esc(l.n)}</div>
        <div class="m"><span class="dir">${u.pick === "higher" ? "▲ HIGHER" : u.pick === "lower" ? "▼ LOWER" : "NO CALL"}</span><b>${u.line !== null ? u.line : "TD"}</b><span class="stat">${u.line !== null ? MKT_SHORT[l.mkt] : "ANYTIME"}</span></div></div>
      <button class="legremove" data-removeleg="${SLIP[k]}" title="Remove">✕</button></div>`;}).join("")
      : `<div class="state-empty" style="margin:14px 15px;min-height:90px"><div><b>0</b><span>NO PICK THE MODEL PUTS PAST ${UD_MIN}%</span></div></div>`}
    <div class="payout">
      <span class="lbl">All picks hit</span>
      <div class="bigedge">${udP === null ? "—" : `${(udP*100).toFixed(1)}%`}</div>
      <div class="payrow"><span>BREAK-EVEN IF IT PAYS 6×</span><b>16.7%</b></div>
      <div class="payrow"><span>BREAK-EVEN IF IT PAYS 3×</span><b>33.3%</b></div>
      <div class="payrow"><span>${legs.some(l=>udPick(l).synthetic) ? "TD PICKS ARE MODEL-READ" : "PICKS ARE AT UNDERDOG'S LINE"}</span><b>${legs.some(l=>udPick(l).synthetic) ? "NOT AN UD PRICE" : "NOT DK'S"}</b></div>
      <button class="btn" data-copy="picks" style="width:100%;margin-top:14px" ${legs.length ? "" : "disabled"}>Copy picks</button>
    </div>
  </div>`;
  return `<div class="slip">
    <div class="sliphead"><span class="lbl">${title}</span><span class="pill">${legs.length} legs</span></div>
    ${chips}
    ${legs.length ? legs.map((l,k)=>`<div class="slipleg">
      <div><div class="p">${esc(l.n)}</div><div class="m">${esc(propLabel(l).toUpperCase())}${l.books ? ` · ${esc(ABBR[l.book]||l.book)}` : ""}${l.kick ? ` · ${esc(l.kick.toUpperCase())}` : ""}${typeof l.edge === "number" ? ` · ${l.model}% · ${l.edge>0?"+":""}${l.edge.toFixed(1)}` : ""}</div></div>
      <div class="o">${esc(fmtAm(overPrice(l)))}</div>
      <button class="legremove" data-removeleg="${SLIP[k]}" title="Remove">✕</button></div>`).join("")
      : `<div class="state-empty" style="margin:14px 15px;min-height:90px"><div><b>0</b><span>${SLIP_MODE === "mine" ? "NONE OF MY PLAYERS PRICE AN EDGE RIGHT NOW" : "TAP A LINE BELOW, OR LOAD A CARD FROM THE GALLERY"}</span></div></div>`}
    ${corr ? `<div class="corr"><span>⚠</span>TWO LEGS IN ${esc(corr.toUpperCase())} — CORRELATED, PRICE IT AS ONE</div>` : ""}
    <div class="payout">
      <span class="lbl">${modeled ? "Model edge over the book" : "Model edge"}</span>
      <div class="bigedge ${modeled ? "" : "pending"}">${modeled ? `${modelP >= implied ? "+" : ""}${((modelP-implied)*100).toFixed(1)}` : "pending"}</div>
      <div class="payrow"><span>MODEL PROBABILITY</span><b>${modeled ? pct(modelP) : "—"}</b></div>
      <div class="payrow"><span>BOOK IMPLIED</span><b>${priced ? pct(implied) : "—"}</b></div>
      <div class="payrow"><span>COMBINED ODDS</span><b>${priced ? fmtAm(decToAm(dec)) : "—"}</b></div>
      <div class="payrow"><span>$25 RETURNS</span><b>${priced ? `$${Math.round(25*dec)}` : "—"}</b></div>
      <button class="btn" data-copy="slip" style="width:100%;margin-top:14px" ${legs.length ? "" : "disabled"}>Copy slip</button>
    </div>
  </div>`;
}

