/* ------------------------------------------------------------------
   MOVERS -- the Board's second mode since 2026-09-25 (a view of its own before). The Board owns
   the position chip and the switch; this file draws what sits under them: the scatter, the pager,
   the rows, and it wires the pager and the drawer. No filter of its own: the Board's chip is the
   one filter, so there is no ALL.
------------------------------------------------------------------ */
const poolSigned = v => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1);
const poolNum = v => v === null || v === undefined ? "—" : Number(v).toFixed(0);
const poolTone = v => v === null || v === undefined ? "" : v > 0.5 ? "pos" : v < -0.5 ? "neg" : "";

/* Where he can be had: mine, free in both leagues, free in one, or gone. From watch's own
   rostered_by, never a percentage the leagues do not publish. */
/* `text` fits the table column; `long` is the drawer's sentence. */
function poolAvailability(r){
  if (r.mine) return {cls: "mine", text: t("pool.free.mine"), long: t("pool.free.mineLong")};
  const L = r.leagues || {};
  if (L.espn === undefined && L.yahoo === undefined) return {cls: "", text: "—", long: "—"};
  const freeEspn = !L.espn, freeYahoo = !L.yahoo;
  if (freeEspn && freeYahoo) return {cls: "free", text: t("pool.free.both"), long: t("pool.free.bothLong")};
  if (freeEspn) return {cls: "free", text: t("pool.free.espn"), long: t("pool.free.espnLong")};
  if (freeYahoo) return {cls: "free", text: t("pool.free.yahoo"), long: t("pool.free.yahooLong")};
  return {cls: "", text: t("pool.free.none"), long: t("pool.free.noneLong")};
}

/* Sorted by share change, largest rise first; a row with no move sinks below every row with one.
   Until any player anywhere has moved (the whole of week 1, when a move needs a second week) there
   is nothing to rank on, so the list ranks by role share and says why in one line above it. */
const poolMoved = () => POOL.some(r => r.dShare);
function poolRows(pos, moved){
  const key = moved ? "dShare" : "share";
  const val = r => r[key] === null || r[key] === undefined ? -Infinity : r[key];
  return POOL.filter(r => r.pos === pos).sort((a, b) => val(b) - val(a));
}

function poolRow(r, i, moved){
  // `i` is the display rank (1-based, correct across pages); the drawer needs the full POOL
  // array's index, which diverges from `i` the moment the list is filtered or re-sorted.
  // NEW (no earlier week to compare) is every row in week 1, so it draws no chip: a chip that is
  // the same on every row says nothing. The drawer still names it.
  const free = poolAvailability(r);
  return `<div class="prow ${r.mine?"mine":""}" style="animation-delay:${60+i*26}ms" data-pool="${POOL.indexOf(r)}" role="button" tabindex="0">
    <div class="pnum" style="color:var(--ink-3)">${String(i+1).padStart(2,"0")}</div>
    <div>${HEADS[r.slug] ? `<img class="pool-head" src="${HEADS[r.slug]}" alt="">` : `<div class="pool-head" style="display:grid;place-items:center;font-family:var(--mono);font-size:var(--t-1);color:var(--ink-3)">${esc(initials(r.n))}</div>`}</div>
    <div class="pname"><b>${esc(nameInitial(r.n))}</b><span>${esc(r.pos)} · ${esc(r.team)}</span></div>
    <div class="pnum">${poolNum(r.snaps)}</div>
    <div class="pnum ${poolTone(r.dSnap)}">${poolSigned(r.dSnap)}</div>
    <div class="pnum">${r.share === null || r.share === undefined ? "—" : r.share.toFixed(1)}</div>
    <div class="pnum ${poolTone(r.dShare)}">${poolSigned(r.dShare)}</div>
    <div class="pverdict">${r.v === "NEW" ? "" : `<span class="vchip ${VCLASS[r.v] || "v-hold"}" title="${esc(r.why || "")}">${esc(r.v.toUpperCase())}</span>`}</div>
    <div class="pnum pfree ${free.cls}">${free.text}</div>
    ${poolPillHTML(r, moved)}
  </div>`;
}

/* The phone's one number is the one the list is sorted on: the signed share change, filled by
   which way it went (the same 0.5 point threshold as the desktop columns' tint), or, before any
   move exists, the role share itself. */
function poolPillHTML(r, moved){
  const v = moved ? r.dShare : r.share;
  if (v === null || v === undefined) return `<div class="vpill none">—</div>`;
  if (!moved) return `<div class="vpill flat">${v.toFixed(0)}%</div>`;
  const dir = {pos: "up", neg: "down"}[poolTone(v)] || "flat";
  return `<div class="vpill ${dir}">${poolSigned(v)}</div>`;
}

function poolPagerHTML(n, page, pages){
  return `<div class="filters" style="margin-top:8px">
    <span class="lbl">${t("pool.pager.players", {n, s: n===1?"":"s"})}</span>
    <span style="flex:1"></span>
    <button class="chip" data-poolpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
    <span class="lbl">${t("common.pager.page", {page, pages})}</span>
    <button class="chip" data-poolpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
  </div>`;
}

/* The chart needs a share move, which needs two weeks; until then it is left out, and the one
   line above the list says why for the chart and the ranking both. */
function poolHTML(pos){
  const moved = poolMoved();
  const rows = poolRows(pos, moved);
  const plotted = rows.filter(poolPlottable);
  const pages = Math.max(1, Math.ceil(rows.length / POOL_PAGE_SIZE));
  const page = Math.min(POOL_PAGE, pages);
  const pageRows = rows.slice((page-1)*POOL_PAGE_SIZE, page*POOL_PAGE_SIZE);
  return `${plotted.length ? scatterHTML(plotted) : ""}
    ${moved ? "" : `<p class="note pool-wait">${t("pool.wait.line")}</p>`}
    ${poolPagerHTML(rows.length, page, pages)}
    <div class="ptable pooltable">
      <div class="phead">
        <div>#</div><div></div><div>${t("pool.table.player")}</div><div>${t("pool.table.snaps")}</div><div>${t("pool.table.dSnaps")}</div>
        <div>${t("pool.table.share")}</div><div>${t("pool.table.dShare")}</div><div>${t("pool.table.verdict")}</div><div>${t("pool.table.free")}</div>
      </div>
      ${pageRows.length ? pageRows.map((r,i)=>poolRow(r, (page-1)*POOL_PAGE_SIZE + i, moved)).join("")
        : `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b><span>${t("pool.empty.noPlayers")}</span></div></div>`}
    </div>`;
}

/* The pager and the drawer. The position chip that filters this list is the Board's (wireBd). */
function wirePool(v){
  // A page turn is a read of the same list, so the scroll position is held across the re-render.
  v.querySelectorAll("[data-poolpage]").forEach(b => b.addEventListener("click", () => {
    POOL_PAGE = Math.max(1, POOL_PAGE + (b.dataset.poolpage === "next" ? 1 : -1));
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-pool]").forEach(el => {
    const open = () => openPoolDrawer(+el.dataset.pool);
    el.addEventListener("click", open);
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " "){ e.preventDefault(); open(); } });
  });
  v.querySelectorAll(".dotg").forEach(g => g.addEventListener("click", () => openPoolDrawer(+g.dataset.i)));
}
