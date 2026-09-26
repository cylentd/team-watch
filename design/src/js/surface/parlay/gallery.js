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
  if (book === "underdog") return udPick(l).synthetic ? t("parlay.why.tdUsage") : rate;
  return [t("parlay.why.dk", {model: l.model, implied: Math.round(amToProb(overPrice(l)) * 100)}), l.mkt === "TD" ? "" : rate]
    .filter(Boolean).join(" · ");
}

/* A leg read as a sentence, the way the book's own app prints it: "Lower 4.5 Receptions". The
   direction is a small tinted chip (2026-09-25), the way every pick'em slip marks it; nothing is
   in capitals. */
function legCall(l, book){
  if (book === "underdog"){
    const u = udPick(l);
    const dir = u.pick === "higher" ? t("parlay.slip.higher") : u.pick === "lower" ? t("parlay.slip.lower") : "";
    // A model-read TD says so in the pick's details (legRowHTML), not on the call.
    return `${dir ? `<em class="tk-dir ${u.pick}">${dir}</em> ` : ""}${u.line !== null ? `${u.line} ${esc(MKT[l.mkt])}` : esc(MKT.TD)}`;
  }
  return l.line === null ? esc(MKT[l.mkt]) : `<em class="tk-dir higher">${t("parlay.slip.over")}</em> ${l.line} ${esc(MKT[l.mkt])}`;
}

/* The verdict as words, so nobody does the arithmetic (the cart's pay box, slip.js): the slip's
   graded chance (udChance, slips.js) against what its payout needs, 1/x. A ratio under 1.25 is
   "near", since a rate a few points off erases it. Its title shows both numbers. */
const verdictTone = ratio => ratio >= 1.25 ? "up" : ratio >= 1 ? "near" : "down";
function slipVerdict(ratio, what, model, needs){
  const tone = verdictTone(ratio);
  const text = tone === "up" ? t("parlay.slip.beats", {what}) : tone === "near" ? t("parlay.slip.close", {what}) : t("parlay.slip.short", {what});
  return `<span class="tk-flag ${tone === "near" ? "" : tone}" title="${esc(t("parlay.slip.verdictTip", {model, needs}))}">${text}</span>`;
}

/* The verdict drawn (2026-09-25): the bar is the slip's chance, the tick is what the payout needs,
   on one 0-50% scale for every slip so two slips compare by eye. Green clears it by 25%, red falls
   short, grey is near. Underdog with a known payout only. */
const METER_TOP = 0.5;
function slipMeterHTML(p, x){
  const tone = verdictTone(p * x), pct = v => `${Math.min(v / METER_TOP, 1) * 100}%`;
  return `<div class="tk-meter"><i class="${tone}" style="width:${pct(p)}"></i><u style="left:${pct(1 / x)}"></u></div>`;
}

/* A gallery slip, drawn as a pick'em entry with a tear-off stub (2026-09-25; Underdog's navy share
   card before it, printed paper before that). The entry: how many picks and of what, the payout as
   a chip, one row per pick -- photo, name, the call, the one number (Underdog: the model's
   confidence; DK: the price), and under it the why with the game and kickoff. Past the perforation
   the stub holds what this page adds: the chance to hit all, the meter, and Load. One row per pick
   because nearly every pick is its own game: the game header per leg cost 31px each.
   A pick is two lines since 2026-09-25 ("too busy and it's small"): his face on his team's colour,
   his name, the call. The why, the game and the kickoff open under it on a tap. */
function legRowHTML(l, book){
  const ud = book === "underdog", u = ud ? udPick(l) : null;
  const team = (TEAM_COLOURS[l.team] || [])[0];
  const more = [u && u.synthetic ? t("parlay.gallery.modelTag") : "", legWhy(l, book)].filter(Boolean).join(" · ");
  return `<div class="tk-leg" role="button" tabindex="0" aria-expanded="false" data-legmore>
      <span class="tk-face"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(l)}</span>
      <div class="tk-who"><b>${esc(nameInitial(l.n))}</b><span class="tk-call">${legCall(l, book)}</span></div>
      <span class="tk-num">${ud ? `${u.conf}<i>%</i>` : esc(fmtAm(overPrice(l)))}</span>
      <div class="tk-more">${more ? `<span>${esc(more)}</span>` : ""}<span>${esc([l.game, l.kick].filter(Boolean).join(" · "))}</span></div>
    </div>`;
}
function presetCard(card, best, groupName){
  const legs = card.legs.map(i=>PROPS[i]);
  const ud = card.book === "underdog";
  const n = legs.length;
  let pays, head, meter = "", note = "";
  if (ud){
    const p = udChance(legs);
    const x = card.scope === "stack" ? null : udPayout(n);
    pays = x ? t("parlay.slip.pays", {x}) : "";
    head = `<b>${(p*100).toFixed(1)}%</b> ${t("parlay.slip.toHitAll", {n})}`;
    if (x){
      const tone = verdictTone(p * x);
      const word = tone === "up" ? t("parlay.slip.tone.up") : tone === "near" ? t("parlay.slip.tone.near") : t("parlay.slip.tone.down");
      meter = slipMeterHTML(p, x);
      note = `<span title="${esc(t("parlay.slip.verdictTip", {model: (p*100).toFixed(1), needs: (100/x).toFixed(1)}))}">${t("parlay.slip.needs", {x, p: (100/x).toFixed(1)})} · <b class="${tone}">${word}</b></span>`;
    } else note = `<span>${t("parlay.slip.typePay")}</span>`;
  } else {
    const prices = legs.map(overPrice).filter(a => a !== null);
    const priced = prices.length === n;
    const dec = priced ? prices.reduce((a,x)=>a*amToDec(x), 1) : null;
    const implied = priced ? prices.reduce((a,x)=>a*amToProb(x), 1) : null;
    const modelP = legs.reduce((a,l)=>a*l.model/100, 1);
    const pos = modelP >= implied;
    pays = "";   // the price is the stub's headline; a chip would say it twice
    head = `<b class="${pos?"":"neg"}">${priced ? esc(fmtAm(decToAm(dec))) : "—"}</b>`;
    // No verdict on DraftKings: the overs the model calls +EV lost when graded singly at the
    // close (ff-jarvis METHODOLOGY 12.31: -2.3% and -10.3%, n 427 each), so a "beats" would overclaim.
    note = `<span>${t("parlay.slip.edgeLabel")} ${pos?"+":""}${((modelP-implied)*100).toFixed(1)}</span>`;
  }
  const mark = card.low ? `<span>${t("parlay.slip.low")}</span>` : "";
  const pill = best ? `<span class="tk-bestpill">${t("parlay.slip.bestAt", {when: esc(groupName)})}</span>` : "";
  return `<div class="ticket ${best ? "best" : ""}" data-card="${card.book}:${card.i}">
    <div class="tk-top"><span class="tk-kind">${t("parlay.slip.pickCount", {n})}<span>${esc(card.scopeLabel)}</span></span>${pill}${pays ? `<span class="tk-pays">${pays}</span>` : ""}</div>
    ${legs.map(l => legRowHTML(l, card.book)).join("")}
    <div class="ticket-tear"></div>
    <div class="tk-stub">
      <div class="tk-head">${head}<button class="ticket-cta" data-loadslip="${card.book}:${card.i}">${t("parlay.gallery.loadSlip")}</button></div>
      ${meter}
      <div class="tk-note">${mark}${note}</div>
    </div>
  </div>`;
}

/* The slips under a heading per kickoff (2026-09-25), the group's best first with its pill. The
   best is the best of what is on screen: filter to TDs and the pill moves to the best TD slip.
   Picking a whole day in the kickoff filter keeps every group of that day. */
function galleryHTML(){
  const pick = GAL_WINDOWS.find(w => w.k === GAL_WIN);
  const inPick = c => GAL_WIN === "ALL" || c.win.k === GAL_WIN || !!(pick && pick.wins && pick.wins.includes(c.win.k));
  const cards = GALLERIES[PARLAY_BOOK].filter(c => (SLIP_SCOPE==="all"||c.scope===SLIP_SCOPE) && inPick(c));
  // The legs filter and kickoff live in the Bets bar (bar.js); the cards stack down the page, one
  // column on a phone, so nothing scrolls sideways inside a page that scrolls down.
  const groups = GAL_GROUPS.map(g => {
    const mine = cards.filter(c => c.win === g);
    if (!mine.length) return "";
    const best = bestCard(mine), name = galGroupName(g);
    const ordered = best ? [best, ...mine.filter(c => c !== best)] : mine;
    return `<section class="tk-group">
      <div class="tk-when"><h3>${esc(name)}</h3><span>${t("parlay.gallery.groupMeta", {kick: esc(g.kick || ""), n: g.games, s: g.games === 1 ? "" : "s"})}</span></div>
      <div class="tk-grid">${ordered.map(c => presetCard(c, c === best, name)).join("")}</div>
    </section>`;
  }).join("");
  return cards.length
    ? groups
    : (() => {
          // How close it came: the legs that pass every gate in what is filtered, so "1 line,
          // a card needs 2" reads as the model declining, not the page failing.
          const s = SLIP_SCOPE === "all" ? "mix" : SLIP_SCOPE;
          const win = GAL_WINDOWS.find(w => w.k === GAL_WIN);
          const ok = PROPS.filter(p => legOKInBook(p, s, PARLAY_BOOK) && inWin(p, win)).length;
          return `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>${ok}</b><span>${t("parlay.gallery.empty", {s: ok === 1 ? "" : "S"})}</span></div></div>`;
        })();
}

