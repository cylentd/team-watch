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

function poolRow(r, i){
  // `i` is the display rank (1-based, correct across pages); the drawer needs the full POOL
  // array's index, which diverges from `i` the moment a position filter is active.
  const free = poolAvailability(r);
  return `<div class="prow ${r.mine?"mine":""}" style="animation-delay:${60+i*26}ms" data-pool="${POOL.indexOf(r)}" role="button" tabindex="0">
    <div class="pnum" style="color:var(--ink-3)">${String(i+1).padStart(2,"0")}</div>
    <div>${HEADS[r.slug] ? `<img class="pool-head" src="${HEADS[r.slug]}" alt="">` : `<div class="pool-head" style="display:grid;place-items:center;font-family:var(--mono);font-size:var(--t-1);color:var(--ink-3)">${esc(initials(r.n))}</div>`}</div>
    <div class="pname"><b>${esc(r.n)}</b><span>${esc(r.pos)} · ${esc(r.team)}</span></div>
    <div class="pnum">${poolNum(r.snaps)}</div>
    <div class="pnum ${poolTone(r.dSnap)}">${poolSigned(r.dSnap)}</div>
    <div class="pnum">${r.share === null || r.share === undefined ? "—" : r.share.toFixed(1)}</div>
    <div class="pnum ${poolTone(r.dShare)}">${poolSigned(r.dShare)}</div>
    <div><span class="vchip ${VCLASS[r.v] || "v-hold"}" title="${esc(r.why || "")}">${esc(r.v.toUpperCase())}</span></div>
    <div class="pnum pfree ${free.cls}">${free.text}</div>
  </div>`;
}

/* The chart needs a share move, which needs two weeks. Until then it says when, instead of an
   empty plot that reads like a bug. */
function poolChartHTML(rows){
  const plotted = rows.filter(poolPlottable);
  if (plotted.length) return scatterHTML(plotted);
  return `<div class="quadwrap"><div class="state-empty" style="min-height:150px"><div><b>${t("pool.chart.waitTitle")}</b><span>${t("pool.chart.waitSub")}</span></div></div></div>`;
}

function poolHTML(){
  const rows = POOL_FILTER === "ALL" ? POOL : POOL.filter(r=>r.pos===POOL_FILTER);
  // No header block: the player count, the ranking and each player's free status are all in the
  // list itself, and the rising/falling counts are what the chart plots.
  return `<div class="wrap">
    ${poolChartHTML(rows)}
    <div class="filters">
      <span class="lbl">${t("pool.filter.position")}</span>
      ${["ALL","QB","RB","WR","TE"].map(p=>`<button class="chip" data-pos="${p}" aria-pressed="${POOL_FILTER===p}">${p}</button>`).join("")}
      <span style="flex:1"></span>
      <span class="lbl">${t("pool.filter.sorted")}</span>
    </div>
    ${(() => {
      const pages = Math.max(1, Math.ceil(rows.length / POOL_PAGE_SIZE));
      const page = Math.min(POOL_PAGE, pages);
      const pageRows = rows.slice((page-1)*POOL_PAGE_SIZE, page*POOL_PAGE_SIZE);
      const pager = `<div class="filters" style="margin-top:8px">
        <span class="lbl">${t("pool.pager.players", {n: rows.length, s: rows.length===1?"":"s"})}</span>
        <span style="flex:1"></span>
        <button class="chip" data-poolpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
        <span class="lbl">${t("common.pager.page", {page: page, pages: pages})}</span>
        <button class="chip" data-poolpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
      </div>`;
      return `${pager}
      <div class="ptable">
        <div class="phead">
          <div>#</div><div></div><div>${t("pool.table.player")}</div><div>${t("pool.table.snaps")}</div><div>${t("pool.table.dSnaps")}</div>
          <div>${t("pool.table.share")}</div><div>${t("pool.table.dShare")}</div><div>${t("pool.table.verdict")}</div><div>${t("pool.table.free")}</div>
        </div>
        ${pageRows.length ? pageRows.map((r,i)=>poolRow(r, (page-1)*POOL_PAGE_SIZE + i)).join("")
          : `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b><span>${t("pool.empty.noPlayers")}</span></div></div>`}
      </div>`;
    })()}
  </div>`;
}
