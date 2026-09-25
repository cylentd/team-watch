/* ------------------------------------------------------------------
   MOVERS -- the Board's second mode: whose role is growing, grouped by team (2026-09-25).

   A share is a slice of one team's pie, so a player's gain is some teammate's loss. A ranked list
   showed the gain alone and left the reader to guess why; a card per team puts the riser beside
   the teammate the work came from (K. Coleman +17.9, D. Moore -28.6, both BUF). The why is then
   in the data, not in a sentence.

   The Board owns the position chip and the switch; this file draws the cards, the pager, and
   wires the drawer. Receivers and tight ends share one pie (targets), so a WR card can name the
   TE who lost them; a back's pie is carries and a quarterback's is snaps.
------------------------------------------------------------------ */
const poolSigned = v => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1);
const poolNum = v => v === null || v === undefined ? "—" : Number(v).toFixed(0);   // the drawer's

/* Where he can be had: mine, free in both leagues, free in one, or gone. From watch's own
   rostered_by, never a percentage the leagues do not publish. `text` is short; `long` is the
   drawer's sentence. */
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

/* A move worth a card: five points of share. On a team throwing 35 times a game that is about two
   targets a game changing hands -- a role, not noise. Conventional, not backtested, like every
   threshold watch itself applies. */
const POOL_MOVE = 5;
const POOL_PIE = {WR: "tgt", TE: "tgt", RB: "car", QB: "snap"};
const poolShareLabel = pos => ({tgt: t("pool.share.tgt"), car: t("pool.share.car"), snap: t("pool.share.snap")})[POOL_PIE[pos]];
const poolMoved = () => POOL.some(r => r.dShare);
const poolBig = r => r.dShare !== null && r.dShare !== undefined && Math.abs(r.dShare) >= POOL_MOVE;

/* One card per team with a big move at this position. The card holds that team's big movers from
   the same pie, largest rise first, at most four; it sorts by the largest move of this position. */
function poolTeams(pos){
  const pie = POOL_PIE[pos], by = {};
  POOL.filter(r => POOL_PIE[r.pos] === pie && poolBig(r)).forEach(r => { (by[r.team] = by[r.team] || []).push(r); });
  return Object.entries(by)
    .map(([team, rows]) => ({team, rows: rows.sort((a, b) => b.dShare - a.dShare).slice(0, 4),
      lead: Math.max(0, ...rows.filter(r => r.pos === pos).map(r => Math.abs(r.dShare)))}))
    .filter(c => c.lead > 0)
    .sort((a, b) => b.lead - a.lead || a.team.localeCompare(b.team));
}

/* No verdict chip on the row. watch's verdict reads snaps before share, so a receiver whose targets
   rose while his snaps fell reads SELL NOW beside a green +23.4 (J. Waddle, week 3) -- two signals
   arguing in one row. The drawer carries the verdict with its reason, where the two can be read
   together. */
function poolRowHTML(r, pos){
  const was = r.share === null || r.share === undefined ? null : r.share - r.dShare;
  const pct = v => v === null ? "—" : Math.max(0, v).toFixed(1) + "%";
  return `<div class="xf-row${r.mine ? " mine" : ""}" data-pool="${POOL.indexOf(r)}" role="button" tabindex="0">
    <span class="xf-head">${avatarHTML(r)}</span>
    <span class="xf-nm"><b>${esc(nameInitial(r.n))}${r.pos !== pos ? ` <em>${esc(r.pos)}</em>` : ""}</b
      ><span>${pct(was)} → ${pct(r.share)}</span></span>
    <span class="xf-d ${r.dShare > 0 ? "up" : "down"}">${poolSigned(r.dShare)}</span>
  </div>`;
}

function poolCardHTML(c, pos, i){
  return `<section class="xf" style="animation-delay:${40 + i * 50}ms">
    <div class="xf-t"><b>${esc(c.team)}</b><span>${poolShareLabel(pos)}</span></div>
    ${c.rows.map(r => poolRowHTML(r, pos)).join("")}
  </section>`;
}

function poolPagerHTML(n, page, pages){
  if (pages <= 1) return "";
  return `<div class="filters" style="margin-top:12px">
    <span class="lbl">${t("pool.pager.teams", {n, s: n === 1 ? "" : "s"})}</span>
    <span style="flex:1"></span>
    <button class="chip" data-poolpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
    <span class="lbl">${t("common.pager.page", {page, pages})}</span>
    <button class="chip" data-poolpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
  </div>`;
}

/* Until any player has two weeks there is no move at all, and the one line says so. */
function poolHTML(pos){
  if (!poolMoved()) return `<p class="note pool-wait">${t("pool.wait.line")}</p>`;
  const cards = poolTeams(pos);
  if (!cards.length) return `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b
    ><span>${t("pool.empty.noMoves", {pos, n: POOL_MOVE})}</span></div></div>`;
  const pages = Math.max(1, Math.ceil(cards.length / POOL_PAGE_SIZE));
  const page = Math.min(POOL_PAGE, pages);
  return `<div class="xf-grid">${cards.slice((page-1)*POOL_PAGE_SIZE, page*POOL_PAGE_SIZE)
      .map((c, i) => poolCardHTML(c, pos, i)).join("")}</div>
    ${poolPagerHTML(cards.length, page, pages)}
    <p class="note bd-foot">${t("pool.foot", {n: POOL_MOVE, wk: (typeof LIVE_POOL !== "undefined" && LIVE_POOL && LIVE_POOL.through_week) || "—"})}</p>`;
}

/* The pager and the drawer. The position chip that filters the cards is the Board's (wireBd). */
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
}
