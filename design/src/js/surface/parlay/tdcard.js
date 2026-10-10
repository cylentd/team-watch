/* Anytime TDs (2026-10-09): the card under the Record line, for the open kickoff tab. The book's chance is the
   number; four groups from LIVE_TD_RESEARCH's tiers, LOCK and VALUE open three rows deep, MORE and LONG folded.
   A name opens a centred sheet with the six checks; the + adds his anytime-TD line through slPick. Words: tdwhy.js;
   rows, groups and the wait: data/tdcard.js. No block (null) = no card. */

const TD_OPEN_N = 3;
const TD_FOLDED = ["MORE", "LONG"];
let ATD_SHOW = {};   // tier -> true: LOCK/VALUE list in full, MORE/LONG unfolded
let ATD_TICK = null;

const tdBlock = () => typeof LIVE_TD_RESEARCH !== "undefined" ? LIVE_TD_RESEARCH : null;

function tdWinKeys(){
  const w = slWin();
  return w ? (w.wins || [w.k]) : [];
}

function tdGroupName(tier){
  if (tier === "LOCK") return t("slips.td.group.LOCK");
  if (tier === "VALUE") return t("slips.td.group.VALUE");
  if (tier === "MORE") return t("slips.td.group.MORE");
  return t("slips.td.group.LONG");
}

function atdRowHTML(r){
  const why = tdWhy(r), i = tdPropIdx(r.slug, PROPS, slSlug), team = (TEAM_COLOURS[r.team] || [])[0];
  const on = i >= 0 && SLIP.includes(i);
  const meta = [esc(r.pos || ""), t("legsheet.head.vs", {team: esc(r.team), opp: esc(r.opp)}), esc(kickTime(r.kickoff))].filter(Boolean).join(" · ");
  const chips = why.chips.map(c => `<span class="atd-chip">${esc(c)}</span>`).join("");
  const add = i < 0 ? `<span class="atd-noadd"></span>`
    : `<button type="button" class="sl-add${on ? " on" : ""}" data-testid="td-add" data-slpick="${i}" data-side="higher" aria-pressed="${on}"
        aria-label="${t("slips.td.add", {name: esc(r.name)})}"><i aria-hidden="true"></i></button>`;
  return `<li class="atd-row" data-testid="td-row" data-tdslug="${esc(r.slug)}">
      <button type="button" class="atd-main" data-testid="td-open" data-tdopen="${esc(r.slug)}" aria-haspopup="dialog" aria-label="${t("slips.td.open", {name: esc(r.name)})}">
        <span class="tk-face sl-face"${team ? ` style="--team:${team}"` : ""}>${avatarHTML({slug: r.slug, n: r.name})}</span>
        <span class="atd-body">
          <span class="atd-who"><b data-testid="td-name">${esc(r.name)}</b>${chips}</span>
          <span class="atd-meta">${meta}</span>
          ${why.forText ? `<span class="atd-for" data-testid="td-for">${esc(why.forText)}</span>` : ""}
          ${why.against ? `<span class="atd-against" data-testid="td-against">${esc(why.against)}</span>` : ""}
        </span>
      </button>
      <b class="atd-p" data-testid="td-p">${Math.round(r.book.p * 100)}%</b>
      ${add}
    </li>`;
}

function tdGroupHTML(tier, rows, b){
  if (!rows.length) return "";
  const folded = TD_FOLDED.includes(tier), show = !!ATD_SHOW[tier];
  const rule = tdRuleLine(tier, b.rules), rec = tdTierRecord(tier, b.record);
  const head = `<span class="atd-gname">${tdGroupName(tier)}</span><span class="atd-grule">${esc(rule)}${rec ? ` · ${esc(rec)}` : ""}</span>`;
  if (folded) {
    return `<section class="atd-group folded" data-testid="td-group" data-tier="${tier}">
        <button type="button" class="atd-ghead" data-testid="td-fold" data-tdshow="${tier}" aria-expanded="${show}">${head}<span class="atd-gn">${rows.length}</span></button>
        ${show ? `<ul class="atd-rows">${rows.map(atdRowHTML).join("")}</ul>` : ""}
      </section>`;
  }
  const list = show ? rows : rows.slice(0, TD_OPEN_N), more = rows.length - list.length;
  return `<section class="atd-group" data-testid="td-group" data-tier="${tier}">
      <header class="atd-ghead">${head}</header>
      <ul class="atd-rows">${list.map(atdRowHTML).join("")}</ul>
      ${more > 0 ? `<button type="button" class="atd-more" data-testid="td-more" data-tdshow="${tier}">${t("slips.td.more", {n: more})}</button>` : ""}
    </section>`;
}

function tdWaitHTML(b, keys){
  const at = tdPendingAt(b.pending, keys, PROPS, Date.now());
  if (at === null) return "";
  return `<p class="atd-wait" data-testid="td-wait">${t("slips.td.wait", {at: esc(kickFmt(new Date(at).toISOString()))})}
      · <span data-tdleft="${at}">${tdLeft(at, Date.now())}</span></p>`;
}

function tdCardHTML(){
  const b = tdBlock();
  if (!b) return "";
  const keys = tdWinKeys(), rows = tdRows(b, keys, PROPS, Date.now());
  const wait = tdWaitHTML(b, keys);
  if (!rows.length && !wait) return "";
  const g = tdGroups(rows);
  return `<section class="atd-card" data-testid="td-card" aria-labelledby="td-title">
      <header class="atd-head"><h2 id="td-title">${t("slips.td.title")}</h2><span class="atd-rec" data-testid="td-record">${esc(tdRecordLine(b))}</span></header>
      <p class="atd-sub">${t("slips.td.sub")}</p>
      ${wait}
      ${TD_TIERS.map(k => tdGroupHTML(k, g[k], b)).join("")}
    </section>`;
}

/* The countdown is text, rewritten once a minute while it is on the page; nothing moves. */
function tdTick(){
  clearTimeout(ATD_TICK);
  const el = document.querySelector("[data-tdleft]");
  if (!el) return;
  el.textContent = tdLeft(+el.dataset.tdleft, Date.now());
  ATD_TICK = setTimeout(tdTick, TD_MIN_MS);
}

function tdSheetHTML(slug){
  const b = tdBlock(), r = b && b.players.find(x => x.slug === slug);
  if (!r) return "";
  const team = (TEAM_COLOURS[r.team] || [])[0], c = tdSheetChecks(r), work = tdWork(r), wx = tdWeather(r);
  const meta = [esc(r.pos || ""), t("legsheet.head.vs", {team: esc(r.team), opp: esc(r.opp)}), esc(kickFmt(r.kickoff))].filter(Boolean).join(" · ");
  const book = r.book.book ? t("slips.td.sheet.book", {book: esc(r.book.book), price: fmtAm(r.book.price)}) : "";
  const checks = c.rows.map(x => `<li class="atd-ck${x.passed ? " pass" : ""}" data-testid="td-check">
      <span class="atd-ckm" aria-hidden="true">${x.passed ? "✓" : "✕"}</span>
      <span class="atd-ckb"><b>${esc(x.label)}</b>${x.num ? `<span class="atd-ckn">${esc(x.num)}</span>` : ""}<span class="atd-ckw">${esc(x.meaning)}</span></span></li>`).join("");
  return `<header class="ls-head ps-head">
      <span class="tk-face ls-face"${team ? ` style="--team:${team}"` : ""}>${avatarHTML({slug: r.slug, n: r.name})}</span>
      <div class="ls-who"><h3 id="ls-title">${esc(r.name)}</h3><span class="ls-meta">${meta}</span></div>
      <button type="button" class="ps-x" data-legclose aria-label="${t("common.action.close")}">${SV_X}</button>
    </header>
    <div class="atd-sbook" data-testid="td-sheet-book"><b>${Math.round(r.book.p * 100)}%</b><span>${book}</span></div>
    <section class="atd-ss"><h4>${t("slips.td.sheet.why", {n: c.n})}</h4><ul class="atd-cks">${checks}</ul></section>
    ${work.length ? `<section class="atd-ss"><h4>${t("slips.td.sheet.work")}</h4><ul class="atd-work">${work.map(w => `<li>${esc(w)}</li>`).join("")}</ul></section>` : ""}
    ${wx ? `<section class="atd-ss"><h4>${t("slips.td.sheet.weather")}</h4><p class="atd-wx">${esc(wx)}</p></section>` : ""}
    ${r.ours ? `<section class="atd-ss atd-ours" data-testid="td-sheet-ours"><h4>${t("slips.td.sheet.second")}</h4>
      <p><b>${t("slips.td.sheet.ours", {p: Math.round(r.ours.p * 100)})}</b> ${t("slips.td.sheet.oursNote")}</p></section>` : ""}
    <button type="button" class="atd-close" data-testid="td-sheet-close" data-legclose>${t("slips.td.close")}</button>`;
}

function wireTdCard(v){
  v.querySelectorAll("[data-tdshow]").forEach(b => b.addEventListener("click", () => {
    ATD_SHOW[b.dataset.tdshow] = !ATD_SHOW[b.dataset.tdshow];
    slRedraw();
  }));
  v.querySelectorAll("[data-tdopen]").forEach(b => b.addEventListener("click", () => {
    const html = tdSheetHTML(b.dataset.tdopen);
    if (html) lsShow("td:" + b.dataset.tdopen, html, b);
  }));
  // The + is .sl-add[data-slpick]: wireSlBoard binds every one on the view, these included.
  tdTick();
}
