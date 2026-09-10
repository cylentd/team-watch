const propLabel = p => p.line === null ? MKT[p.mkt] : `${MKT[p.mkt]} o${p.line}`;

/* Why a row the sort put on top is not on any gallery card: one pill, the first reason that
   applies, in the order legOKInBook would trip on it. A row can fail three gates at once (a
   backup, at a moved line, on a thin number) and three pills say "no" three times -- one is the
   answer. `u` is the Underdog pick when in that mode, for the line-size floor. */
/* The chevron that expands a line: every book's price and the game log. One helper for the
   three card shapes (DK card, Underdog card, Underdog line) so the tooltip cannot drift. */
function moreButtonHTML(i, open, log){
  return `<button class="more" data-more="${i}" aria-expanded="${open}" title="${log ? t("parlay.more.log", {n: log.g.length}) : t("parlay.more.plain")}" tabindex="-1">${open ? "▴" : "▾"}</button>`;
}
function whyNotSlip(p, u){
  if (p.flag === "out") return `<span class="tag t-out">${t("parlay.tag.out")}${p.injury_note ? " · " + esc(p.injury_note) : ""}</span>`;
  if (p.flag === "q") return `<span class="tag t-q">${t("parlay.tag.q")}${p.injury_note ? " · " + esc(p.injury_note) : ""}</span>`;
  if (p.flag === "backup") return `<span class="tag t-bk" title="${t("parlay.tag.backupTitle", {pos: esc(p.pos), depth: p.depth})}">${esc(p.pos)}${p.depth}</span>`;
  if (p.norole) return `<span class="tag t-bk" title="${t("parlay.tag.noRoleTitle")}">${t("parlay.tag.noRole")}</span>`;
  if (p.moved) return `<span class="tag t-role" title="${t("parlay.tag.movedTitle", {team: esc(p.moved)})}">${t("parlay.tag.moved")}<span class="was"> · ${t("parlay.tag.movedWas", {team: esc(p.moved)})}</span></span>`;
  if (u ? u.stale : p.stale) return `<span class="tag t-role" title="${t("parlay.tag.staleTitle")}">${t("parlay.tag.stale")}</span>`;
  if (typeof p.model === "number" && (p.games||0) < 8) return `<span class="tag t-bk" title="${t("parlay.tag.gamesTitle", {n: p.games||0})}">${t("parlay.tag.games", {n: p.games||0})}</span>`;
  if (u && !u.synthetic && u.line !== null && (p.mkt === "RECS" ? u.line < 2.5 : u.line < 15)) return `<span class="tag t-bk" title="${t("parlay.tag.thinTitle")}">${t("parlay.tag.thin")}</span>`;
  return "";
}

/* Underdog's whole pitch is one stat, one tap: higher or lower. Skip the DK-only model%/edge
   detail (there is no "book implied" the same way against a flat-multiplier payout) and lead
   the row with the pick itself -- that IS the primary info here, not noise the way it is for a
   priced-against-a-vig DK line. */
function udPropCard(p, i){
  const inSlip = SLIP.includes(i);
  const u = udPick(p);
  // No MODEL pill per row: it would sit on every TD row (Underdog prices none), which is
  // noise, not information. The list header says it once; the cart still marks the leg.
  const tag = whyNotSlip(p, u);
  const log = LIVE_MARKET && LIVE_MARKET.logs && p.slug ? LIVE_MARKET.logs[p.slug] : (LIVE_MARKET && LIVE_MARKET.logs ? LIVE_MARKET.logs[slugOf(p.n)] : null);
  const open = EXPANDED.has(i);
  // The call is one unit: "▼ LOWER / 1.5 REC". The stat lives here, not in the name line, so
  // the eye reads name, call, confidence, and nothing twice.
  const call = u.pick
    ? `<div class="udcall ${u.pick}"><span class="dir">${u.pick === "higher" ? t("parlay.call.higher") : t("parlay.call.lower")}</span><span class="num">${u.line !== null ? u.line : t("parlay.call.td")}</span><span class="stat">${u.line !== null ? MKT_SHORT[p.mkt] : t("parlay.call.anytime")}</span></div>`
    : `<div class="udcall"><span class="dir">${t("parlay.call.none")}</span><span class="num">—</span><span class="stat">${MKT_SHORT[p.mkt]}</span></div>`;
  const conf = typeof u.conf === "number"
    ? `<div class="udconf ${u.conf >= UD_MIN ? "" : "weak"}"><b>${u.conf}<i>%</i></b><div class="meter"><i style="transform:scaleX(${Math.max(0, Math.min(1, (u.conf - 50) / 50)).toFixed(2)})"></i></div></div>`
    : `<div class="udconf pending"><b>${t("parlay.call.pending")}</b></div>`;
  return `<div class="leg ud ${p.mine?"mine":""} ${inSlip?"inslip":""} ${p.flag==="out"?"isout":""} ${open?"open":""}" data-prop="${i}" role="button" tabindex="0" aria-pressed="${inSlip}">
    ${avatarHTML(p)}
    <div>
      <div class="prop">${esc(p.n)}${tag ? " " + tag : ""}</div>
      <div class="book">${esc(p.pos)} · ${esc(p.game)}${p.kick ? ` · ${esc(p.kick)}` : ""}</div>
    </div>
    ${call}${conf}
    ${moreButtonHTML(i, open, log)}
    ${open ? `<div class="legx">
      <div class="booklines">${esc(bookLine(p))}</div>
      ${log ? gameLogHTML(p, log) : ""}
    </div>` : ""}
  </div>`;
}

/* One card per player in Underdog mode: the header says who and when once, then one line per
   market. Player-level reasons (OUT, Q, depth, NEW TEAM, too few games) sit on the header;
   line-level ones (ROLE?, THIN LINE) sit on the line they belong to. `rows` arrive in list
   order, so the first row is the player's strongest call and the lines keep the sort. */
function lineTag(p, u){
  if (u.stale) return `<span class="tag t-role" title="${t("parlay.tag.staleTitle")}">${t("parlay.tag.stale")}</span>`;
  if (!u.synthetic && u.line !== null && (p.mkt === "RECS" ? u.line < 2.5 : u.line < 15)) return `<span class="tag t-bk" title="${t("parlay.tag.thinTitle")}">${t("parlay.tag.thin")}</span>`;
  return "";
}
function udLine(p, i, headerSaysNo){
  const u = udPick(p), inSlip = SLIP.includes(i), open = EXPANDED.has(i);
  const hasConf = typeof u.conf === "number";
  const fill = hasConf ? Math.max(0, Math.min(1, (u.conf - 50) / 50)).toFixed(2) : 0;
  // Colour is the confidence: grey under the 58% floor, then amber at the floor blending to
  // lime at 100%, so 62% and 94% differ in hue as well as length.
  const heat = hasConf && u.conf >= UD_MIN ? Math.round((u.conf - UD_MIN) / (100 - UD_MIN) * 100) : null;
  const fillColor = heat === null ? "var(--ink-3)" : `color-mix(in oklab, var(--lime) ${heat}%, var(--amber))`;
  const log = LIVE_MARKET && LIVE_MARKET.logs && p.slug ? LIVE_MARKET.logs[p.slug] : (LIVE_MARKET && LIVE_MARKET.logs ? LIVE_MARKET.logs[slugOf(p.n)] : null);
  return `<div class="udline ${u.pick||""} ${hasConf && u.conf < UD_MIN ? "weak" : ""}" data-prop="${i}" role="button" tabindex="0" aria-pressed="${inSlip}">
    <span class="dir">${u.pick === "higher" ? t("parlay.call.higher") : u.pick === "lower" ? t("parlay.call.lower") : t("parlay.call.none")}</span>
    <span class="ln"><b>${u.line !== null ? u.line : t("parlay.call.td")}</b><small>${u.line !== null ? MKT_SHORT[p.mkt] : t("parlay.call.anytime")}</small>${headerSaysNo ? "" : lineTag(p, u)}</span>
    <span class="meter"><i style="transform:scaleX(${fill});background:${fillColor}"></i></span>
    ${hasConf ? `<span class="pct">${u.conf}<i>%</i></span>` : `<span class="pct pending">${t("parlay.call.pending")}</span>`}
    ${moreButtonHTML(i, open, log)}
    ${open ? `<div class="legx"><div class="booklines">${esc(bookLine(p))}</div>${log ? gameLogHTML(p, log) : ""}</div>` : ""}
  </div>`;
}
function udPlayerCard(rows){
  const p = rows[0];
  const tag = whyNotSlip({...p, stale: 0, norole: 0}, null);
  return `<div class="pcard ${p.mine ? "mine" : ""} ${p.flag === "out" ? "isout" : ""}">
    <div class="phead2">
      ${avatarHTML(p)}
      <div>
        <div class="prop">${esc(p.n)}${tag ? " " + tag : ""}</div>
        <div class="book">${esc(p.pos)} · ${esc(p.game)}${p.kick ? ` · ${esc(p.kick)}` : ""}</div>
      </div>
    </div>
    ${rows.map(r => udLine(r, PROPS.indexOf(r), !!tag)).join("")}
  </div>`;
}
const UD_PAGE_SIZE = 10;   // players per page in Underdog mode; MKT_PAGE_SIZE counts lines in DK mode

function propCard(p, i){
  if (PARLAY_BOOK === "underdog") return udPropCard(p, i);
  const inSlip = SLIP.includes(i);
  const hasModel = typeof p.model === "number";
  const implied = overPrice(p) !== null ? Math.round(amToProb(overPrice(p)) * 100) : null;
  let detail;
  if (hasModel){
    const pos = p.edge >= 0;
    const w = Math.min(50, Math.abs(p.edge) * 4.4);
    detail = `<div class="probwrap"><b>${p.model}%</b><span>${t("parlay.detail.model")}</span></div>
    <div class="edgecell">
      <b class="${pos?"pos":"neg"}">${pos?"+":""}${p.edge.toFixed(1)}</b>
      <div class="ebar"><i class="${pos?"":"neg"}" style="${pos?`left:50%;width:${w}%`:`left:${50-w}%;width:${w}%`}"></i></div>
    </div>`;
  } else {
    detail = `<div class="probwrap implied"><b>${implied === null ? "—" : implied + "%"}</b><span>${t("parlay.detail.bookImplied")}</span></div>
    <div class="edgecell pending"><b>—</b><span>${t("parlay.detail.modelPending")}</span></div>`;
  }
  if (p.flag === "out") detail = `<div class="probwrap implied"><b>—</b><span>${t("parlay.detail.notPlaying")}</span></div>
    <div class="edgecell pending"><b>${t("parlay.tag.out")}</b><span>${esc((p.injury_note||p.injury||"").toUpperCase())}</span></div>`;
  else if (p.norole) detail = `<div class="probwrap implied"><b>—</b><span>${t("parlay.detail.noYardsLine")}</span></div>
    <div class="edgecell pending"><b>—</b><span>${t("parlay.detail.noRolePriced")}</span></div>`;
  const tag = whyNotSlip(p, null)
    + (p.cb ? `<span class="tag ${p.cb.v === "upgrade" ? "t-cbup" : "t-cbdn"}" title="${t("parlay.tag.cbTitle", {week: LIVE_MARKET && LIVE_MARKET.wrcb ? LIVE_MARKET.wrcb.week : "", v: esc(p.cb.v), cb: esc(p.cb.cb), why: esc(p.cb.why)})}">${t("parlay.tag.cb", {dir: p.cb.v === "upgrade" ? "↑" : "↓", name: esc(lastName(p.cb.cb))})}</span>` : "");
  const log = LIVE_MARKET && LIVE_MARKET.logs && p.slug ? LIVE_MARKET.logs[p.slug] : (LIVE_MARKET && LIVE_MARKET.logs ? LIVE_MARKET.logs[slugOf(p.n)] : null);
  const open = EXPANDED.has(i);
  return `<div class="leg ${p.mine?"mine":""} ${inSlip?"inslip":""} ${p.flag==="out"?"isout":""} ${open?"open":""}" data-prop="${i}" role="button" tabindex="0" aria-pressed="${inSlip}">
    ${avatarHTML(p)}
    <div>
      <div class="prop">${esc(p.n)} · ${esc(propLabel(p))}${tag ? " " + tag : ""}</div>
      <div class="book">${esc(p.pos)} · ${esc(p.game)}${p.kick ? ` · ${esc(p.kick)}` : ""}</div>
    </div>
    <div class="o">${esc(fmtAm(overPrice(p)))}</div>
    ${moreButtonHTML(i, open, log)}
    ${open ? `<div class="legx">
      ${detail}
      <div class="booklines">${esc(bookLine(p))}</div>
      ${log ? gameLogHTML(p, log) : ""}
    </div>` : ""}
  </div>`;
}

