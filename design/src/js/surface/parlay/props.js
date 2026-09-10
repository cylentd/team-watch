const propLabel = p => p.line === null ? MKT[p.mkt] : `${MKT[p.mkt]} o${p.line}`;

/* Why a row the sort put on top is not on any gallery card: one pill, the first reason that
   applies, in the order legOKInBook would trip on it. A row can fail three gates at once (a
   backup, at a moved line, on a thin number) and three pills say "no" three times -- one is the
   answer. `u` is the Underdog pick when in that mode, for the line-size floor. */
function whyNotSlip(p, u){
  if (p.flag === "out") return `<span class="tag t-out">OUT${p.injury_note ? " · " + esc(p.injury_note) : ""}</span>`;
  if (p.flag === "q") return `<span class="tag t-q">Q${p.injury_note ? " · " + esc(p.injury_note) : ""}</span>`;
  if (p.flag === "backup") return `<span class="tag t-bk" title="Depth chart says ${esc(p.pos)}${p.depth}. Not slip material.">${esc(p.pos)}${p.depth}</span>`;
  if (p.norole) return `<span class="tag t-bk" title="A touchdown line on a player the book prices no yards for.">NO ROLE</span>`;
  if (p.moved) return `<span class="tag t-role" title="Every game the model has read was for ${esc(p.moved)}. The rate knows nothing about the new offense or quarterback, and the model has no feature for a team change. Not slip material.">NEW TEAM<span class="was"> · WAS ${esc(p.moved)}</span></span>`;
  if (u ? u.stale : p.stale) return `<span class="tag t-role" title="The book's line is far from last season's rate: the role changed and the model has not caught up. Not slip material.">ROLE?</span>`;
  if (typeof p.model === "number" && (p.games||0) < 8) return `<span class="tag t-bk" title="The rate rests on ${p.games||0} of his own games; a slip leg needs 8.">${p.games||0} GAMES</span>`;
  if (u && !u.synthetic && u.line !== null && (p.mkt === "RECS" ? u.line < 2.5 : u.line < 15)) return `<span class="tag t-bk" title="A line this small is confidence for free and Underdog prices it that way. Not slip material.">THIN LINE</span>`;
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
    ? `<div class="udcall ${u.pick}"><span class="dir">${u.pick === "higher" ? "▲ HIGHER" : "▼ LOWER"}</span><span class="num">${u.line !== null ? u.line : "TD"}</span><span class="stat">${u.line !== null ? MKT_SHORT[p.mkt] : "ANYTIME"}</span></div>`
    : `<div class="udcall"><span class="dir">NO CALL</span><span class="num">—</span><span class="stat">${MKT_SHORT[p.mkt]}</span></div>`;
  const conf = typeof u.conf === "number"
    ? `<div class="udconf ${u.conf >= UD_MIN ? "" : "weak"}"><b>${u.conf}<i>%</i></b><div class="meter"><i style="transform:scaleX(${Math.max(0, Math.min(1, (u.conf - 50) / 50)).toFixed(2)})"></i></div></div>`
    : `<div class="udconf pending"><b>PENDING</b></div>`;
  return `<div class="leg ud ${p.mine?"mine":""} ${inSlip?"inslip":""} ${p.flag==="out"?"isout":""} ${open?"open":""}" data-prop="${i}" role="button" tabindex="0" aria-pressed="${inSlip}">
    ${HEADS[p.slug] ? `<img src="${HEADS[p.slug]}" alt="">` : `<div class="fallback">${esc(initials(p.n))}</div>`}
    <div>
      <div class="prop">${esc(p.n)}${tag ? " " + tag : ""}</div>
      <div class="book">${esc(p.pos)} · ${esc(p.game)}${p.kick ? ` · ${esc(p.kick)}` : ""}</div>
    </div>
    ${call}${conf}
    <button class="more" data-more="${i}" aria-expanded="${open}" title="${log ? `Last ${log.g.length} games against this line` : "More on this line"}" tabindex="-1">${open ? "▴" : "▾"}</button>
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
  if (u.stale) return `<span class="tag t-role" title="The book's line is far from last season's rate: the role changed and the model has not caught up. Not slip material.">ROLE?</span>`;
  if (!u.synthetic && u.line !== null && (p.mkt === "RECS" ? u.line < 2.5 : u.line < 15)) return `<span class="tag t-bk" title="A line this small is confidence for free and Underdog prices it that way. Not slip material.">THIN LINE</span>`;
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
    <span class="dir">${u.pick === "higher" ? "▲ HIGHER" : u.pick === "lower" ? "▼ LOWER" : "NO CALL"}</span>
    <span class="ln"><b>${u.line !== null ? u.line : "TD"}</b><small>${u.line !== null ? MKT_SHORT[p.mkt] : "ANYTIME"}</small>${headerSaysNo ? "" : lineTag(p, u)}</span>
    <span class="meter"><i style="transform:scaleX(${fill});background:${fillColor}"></i></span>
    ${hasConf ? `<span class="pct">${u.conf}<i>%</i></span>` : `<span class="pct pending">PENDING</span>`}
    <button class="more" data-more="${i}" aria-expanded="${open}" title="${log ? `Last ${log.g.length} games against this line` : "More on this line"}" tabindex="-1">${open ? "▴" : "▾"}</button>
    ${open ? `<div class="legx"><div class="booklines">${esc(bookLine(p))}</div>${log ? gameLogHTML(p, log) : ""}</div>` : ""}
  </div>`;
}
function udPlayerCard(rows){
  const p = rows[0];
  const tag = whyNotSlip({...p, stale: 0, norole: 0}, null);
  return `<div class="pcard ${p.mine ? "mine" : ""} ${p.flag === "out" ? "isout" : ""}">
    <div class="phead2">
      ${HEADS[p.slug] ? `<img src="${HEADS[p.slug]}" alt="">` : `<div class="fallback">${esc(initials(p.n))}</div>`}
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
    detail = `<div class="probwrap"><b>${p.model}%</b><span>MODEL</span></div>
    <div class="edgecell">
      <b class="${pos?"pos":"neg"}">${pos?"+":""}${p.edge.toFixed(1)}</b>
      <div class="ebar"><i class="${pos?"":"neg"}" style="${pos?`left:50%;width:${w}%`:`left:${50-w}%;width:${w}%`}"></i></div>
    </div>`;
  } else {
    detail = `<div class="probwrap implied"><b>${implied === null ? "—" : implied + "%"}</b><span>BOOK IMPLIED</span></div>
    <div class="edgecell pending"><b>—</b><span>MODEL PENDING</span></div>`;
  }
  if (p.flag === "out") detail = `<div class="probwrap implied"><b>—</b><span>NOT PLAYING</span></div>
    <div class="edgecell pending"><b>OUT</b><span>${esc((p.injury_note||p.injury||"").toUpperCase())}</span></div>`;
  else if (p.norole) detail = `<div class="probwrap implied"><b>—</b><span>NO YARDS LINE</span></div>
    <div class="edgecell pending"><b>—</b><span>NO ROLE PRICED</span></div>`;
  const tag = whyNotSlip(p, null)
    + (p.cb ? `<span class="tag ${p.cb.v === "upgrade" ? "t-cbup" : "t-cbdn"}" title="RotoBaller WR/CB matchups, week ${LIVE_MARKET && LIVE_MARKET.wrcb ? LIVE_MARKET.wrcb.week : ""}: ${esc(p.cb.v)} vs ${esc(p.cb.cb)}. ${esc(p.cb.why)} — opinion, not in the number.">CB ${p.cb.v === "upgrade" ? "↑" : "↓"} ${esc(lastName(p.cb.cb))}</span>` : "");
  const log = LIVE_MARKET && LIVE_MARKET.logs && p.slug ? LIVE_MARKET.logs[p.slug] : (LIVE_MARKET && LIVE_MARKET.logs ? LIVE_MARKET.logs[slugOf(p.n)] : null);
  const open = EXPANDED.has(i);
  return `<div class="leg ${p.mine?"mine":""} ${inSlip?"inslip":""} ${p.flag==="out"?"isout":""} ${open?"open":""}" data-prop="${i}" role="button" tabindex="0" aria-pressed="${inSlip}">
    ${HEADS[p.slug] ? `<img src="${HEADS[p.slug]}" alt="">` : `<div class="fallback">${esc(initials(p.n))}</div>`}
    <div>
      <div class="prop">${esc(p.n)} · ${esc(propLabel(p))}${tag ? " " + tag : ""}</div>
      <div class="book">${esc(p.pos)} · ${esc(p.game)}${p.kick ? ` · ${esc(p.kick)}` : ""}</div>
    </div>
    <div class="o">${esc(fmtAm(overPrice(p)))}</div>
    <button class="more" data-more="${i}" aria-expanded="${open}" title="${log ? `Last ${log.g.length} games against this line` : "More on this line"}" tabindex="-1">${open ? "▴" : "▾"}</button>
    ${open ? `<div class="legx">
      ${detail}
      <div class="booklines">${esc(bookLine(p))}</div>
      ${log ? gameLogHTML(p, log) : ""}
    </div>` : ""}
  </div>`;
}

