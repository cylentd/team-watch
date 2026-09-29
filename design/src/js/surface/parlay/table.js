/* The deal table, drawn (2026-09-29; the dealing is builder/table.js). Three cards, one subject
   each: the slip on the table (kind and length on its top row, one row per pick with a lock, the
   chance and payout on the stub, Deal again and Keep), the slips kept so far, and the pool it deals
   from, where a tap locks a pick onto the slip. A phone stacks them; a desktop sets the slip beside
   the kept slips, and the pool under both, two picks across (STYLE.md, rows not columns). */
const LOCK_SVG = `<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="7" width="10" height="7" rx="1.5"/><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2"/></svg>`;

function tableLockHTML(i){
  const on = TABLE.locks.includes(i), name = esc(nameInitial(PROPS[i].n));
  return `<button type="button" class="dt-lock" data-tlock="${i}" aria-pressed="${on}"
    aria-label="${on ? t("parlay.table.unlock", {name}) : t("parlay.table.lock", {name})}">${LOCK_SVG}</button>`;
}

const tableKindLabel = k => k === "td" ? t("parlay.table.kind.td") : k === "safe" ? t("parlay.table.kind.safe") : t("parlay.table.kind.mix");

/* "1 in 34" is the headline: at 3% a percentage reads as zero, a count of tries does not. */
const tableOdds = p => p > 0 ? t("parlay.table.oneIn", {n: Math.max(1, Math.round(1 / p))}) : "—";

function tableStubHTML(legs){
  const p = tableChance(legs), n = legs.length;
  let pays = "";
  if (PARLAY_BOOK === "underdog"){
    const x = udPayout(n);
    if (x){
      const tone = verdictTone(p * x);
      const word = tone === "up" ? t("parlay.slip.tone.up") : tone === "near" ? t("parlay.slip.tone.near") : t("parlay.slip.tone.down");
      pays = `${t("parlay.table.pays", {x, need: x})} · <b class="${tone}">${word}</b>`;
    } else pays = t("parlay.slip.typePay");
  } else {
    const prices = legs.map(i => overPrice(PROPS[i]));
    if (prices.every(a => a !== null)) pays = t("parlay.table.paysDk", {price: esc(fmtAm(decToAm(prices.reduce((a, x) => a * amToDec(x), 1))))});
  }
  return `<div class="tk-stub">
      <div class="tk-head"><b>${tableOdds(p)}</b> ${t("parlay.table.toHit", {p: (p * 100).toFixed(1), n})}</div>
      <div class="tk-note"><span>${pays}</span></div>
      <div class="dt-acts">
        <button type="button" class="dt-again" data-tdeal>${t("parlay.table.deal")}</button>
        <button type="button" class="ticket-cta dt-keep" data-tkeep>${t("parlay.table.keep")}</button>
      </div>
    </div>`;
}

function tableSegHTML(){
  const kinds = TABLE_KINDS.map(k => `<button type="button" class="dt-seg-b" data-tkind="${k}" aria-pressed="${TABLE.kind === k}">${tableKindLabel(k)}</button>`).join("");
  const legs = TABLE_LEGS.map(n => `<button type="button" class="dt-seg-b" data-tlegs="${n}" aria-pressed="${TABLE.n === n}">${n}</button>`).join("");
  return `<div class="dt-ctl">
      <div class="dt-seg" role="group" aria-label="${t("parlay.table.kindLabel")}">${kinds}</div>
      <div class="dt-seg dt-n" role="group" aria-label="${t("parlay.table.legsLabel")}">${legs}</div>
    </div>`;
}

function tableSlipHTML(pool){
  const legs = TABLE.legs;
  const rows = legs.map(i => legRowHTML(PROPS[i], PARLAY_BOOK, i, tableLockHTML(i), TABLE.locks.includes(i))).join("");
  const short = legs.length < TABLE.n
    ? `<p class="dt-short">${t("parlay.table.short", {n: pool.length, s: pool.length === 1 ? "" : "s"})}</p>` : "";
  return `<div class="ticket dt-slip">
      ${tableSegHTML()}
      ${legs.length ? rows + short + `<div class="ticket-tear"></div>` + tableStubHTML(legs)
        : `<div class="state-empty dt-none"><div><b>0</b><span>${t("parlay.table.empty")}</span></div></div>`}
    </div>`;
}

function tableKeptHTML(){
  const mine = KEPT.map((s, k) => [s, k]).filter(([s]) => s.book === PARLAY_BOOK);
  // Empty, it holds the slip's row on a desktop and is hidden on a phone (table.css).
  if (!mine.length) return `<div class="dt-card dt-kept dt-kept-empty"><div class="dt-head"><h3>${t("parlay.table.kept", {n: 0})}</h3></div>
      <p class="dt-kept-none">${t("parlay.table.keptNone")}</p></div>`;
  const winName = k => { const w = GAL_WINDOWS.find(x => x.k === k); return w ? kickName(w) : ""; };
  const rows = mine.map(([s, k]) => `<div class="dt-kept-row">
      <button type="button" class="dt-kept-load" data-tload="${k}">
        <span class="dt-kept-kind"><b>${s.legs.length}</b> ${tableKindLabel(s.kind)}<i>${esc(winName(s.win))}</i></span>
        <span class="dt-kept-who">${s.legs.map(i => esc(nameInitial(PROPS[i].n))).join(", ")}</span>
        <span class="dt-kept-odds">${tableOdds(tableChance(s.legs, s.book))}</span>
      </button>
      <button type="button" class="dt-kept-drop" data-tdrop="${k}" aria-label="${t("parlay.table.drop")}">&times;</button>
    </div>`).join("");
  return `<div class="dt-card dt-kept">
      <div class="dt-head"><h3>${t("parlay.table.kept", {n: mine.length})}</h3><span>${t("parlay.table.keptTip")}</span></div>
      ${rows}
    </div>`;
}

const TABLE_POOL_TOP = 10;
function tablePoolHTML(pool){
  if (!pool.length) return "";
  const shown = TABLE_POOL_ALL ? pool : pool.slice(0, TABLE_POOL_TOP);
  const rows = shown.map(i => {
    const p = PROPS[i], on = TABLE.locks.includes(i), team = (TEAM_COLOURS[p.team] || [])[0];
    return `<button type="button" class="dt-pick${TABLE.legs.includes(i) ? " dealt" : ""}" data-tpool="${i}" aria-pressed="${on}">
        <span class="tk-face" data-slug="${esc(p.slug)}"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(p)}</span>
        <span class="tk-who"><b>${esc(nameInitial(p.n))}</b><span class="tk-call">${legCall(p, PARLAY_BOOK)}</span></span>
        <span class="tk-num">${Math.round(tableConf(p))}<i>%</i></span>
        <span class="dt-lock" aria-hidden="true">${LOCK_SVG}</span>
      </button>`;
  }).join("");
  const more = pool.length > TABLE_POOL_TOP
    ? `<button type="button" class="chip dt-more" data-tpoolall>${TABLE_POOL_ALL ? t("parlay.table.poolLess", {n: TABLE_POOL_TOP}) : t("parlay.table.poolAll", {n: pool.length})}</button>` : "";
  return `<div class="dt-card dt-pool">
      <div class="dt-head"><h3>${t("parlay.table.pool", {n: pool.length})}</h3><span>${t("parlay.table.poolTip")}</span></div>
      <div class="dt-picks">${rows}</div>${more}
    </div>`;
}

function tableHTML(){
  tableEnsure();
  const pool = tablePool();
  return `<section class="dt">${tableSlipHTML(pool)}${tableKeptHTML()}${tablePoolHTML(pool)}</section>`;
}

/* After a deal: the unlocked picks drop in one by one, 70ms apart so each is counted (STYLE.md). */
function tablePlay(){
  if (!TABLE_FRESH) return;
  TABLE_FRESH = false;
  if (REDUCED()) return;
  const spring = betsCss("--spring"), dur = parseFloat(betsCss("--dur-spring")) * 1000 || 460;
  document.querySelectorAll(".dt-slip .tk-leg:not(.locked)").forEach((el, k) => el.animate(
    [{opacity: 0, transform: "translateY(-10px)"}, {opacity: 1, transform: "none"}],
    {duration: dur, delay: k * 70, easing: spring, fill: "backwards"}));
}
function tablePopKept(){
  const row = document.querySelector(".dt-kept-row");
  if (row && !REDUCED()) row.animate([{transform: "scale(.96)", opacity: 0}, {transform: "none", opacity: 1}],
    {duration: parseFloat(betsCss("--dur-pop")) * 1000 || 690, easing: betsCss("--spring-pop")});
}

function wireTable(v){
  const again = fn => () => { fn(); const y = window.scrollY; render(); window.scrollTo(0, y); tablePlay(); };
  v.querySelectorAll("[data-tkind]").forEach(b => b.addEventListener("click", again(() => { TABLE.kind = b.dataset.tkind; TABLE_POOL_ALL = false; tableDeal(); })));
  v.querySelectorAll("[data-tlegs]").forEach(b => b.addEventListener("click", again(() => { TABLE.n = +b.dataset.tlegs; tableDeal(); })));
  v.querySelectorAll("[data-tdeal]").forEach(b => b.addEventListener("click", again(tableDeal)));
  v.querySelectorAll("[data-tpoolall]").forEach(b => b.addEventListener("click", again(() => { TABLE_POOL_ALL = !TABLE_POOL_ALL; })));
  // The lock sits inside the pick's row, which opens the leg sheet; the lock must not.
  v.querySelectorAll("[data-tlock]").forEach(b => b.addEventListener("click", e => { e.stopPropagation(); again(() => tableLock(+b.dataset.tlock))(); }));
  v.querySelectorAll("[data-tpool]").forEach(b => b.addEventListener("click", again(() => tableLock(+b.dataset.tpool))));
  v.querySelectorAll("[data-tkeep]").forEach(b => b.addEventListener("click", () => {
    const added = tableKeep();
    const y = window.scrollY; render(); window.scrollTo(0, y);
    if (added) tablePopKept();
  }));
  v.querySelectorAll("[data-tdrop]").forEach(b => b.addEventListener("click", again(() => keptDrop(+b.dataset.tdrop))));
  // A kept slip loads like any slip: its legs pour into the tray, counted as they land.
  v.querySelectorAll("[data-tload]").forEach(b => b.addEventListener("click", () => {
    const s = KEPT[+b.dataset.tload];
    if (!s) return;
    const from = b.getBoundingClientRect();
    SLIP = s.legs.slice(); SLIP_MODE = "custom";
    const y = window.scrollY; render(); window.scrollTo(0, y);
    betsPour(SLIP.map(() => from), SLIP.map(i => PROPS[i].n));
  }));
}
