/* ------------------------------------------------------------------
   MOVERS -- the Board's second mode: whose role is growing, grouped by team (2026-09-25).

   A share is a slice of one team's pie, so a player's gain is some teammate's loss. A card per team
   puts the riser beside the teammate the work came from (MIN: A. Jones +46.8, J. Mason -44.1). The
   why is then in the data, not in a sentence.

   Every card is the same shape: three rows, the team's three biggest moves in that pie, whether or
   not each clears the bar. A card that grew with its team's movers made the grid reflow on every
   page turn, and a team whose other back moved 4 points showed its riser alone, as if the carries
   came from nowhere. A tap on a player opens his profile, the same one the Leaders board opens.

   Receivers and tight ends share one pie (targets), so a WR card can name the TE who lost them; a
   back's pie is carries and a quarterback's is snaps.
------------------------------------------------------------------ */
const poolSigned = v => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1);

/* A move worth a card: five points of share. On a team throwing 35 times a game that is about two
   targets a game changing hands -- a role, not noise. Conventional, not backtested, like every
   threshold watch itself applies. */
const POOL_MOVE = 5;
const POOL_ROWS = 3;
const POOL_PIE = {WR: "tgt", TE: "tgt", RB: "car", QB: "snap"};
const poolShareLabel = pos => ({tgt: t("pool.share.tgt"), car: t("pool.share.car"), snap: t("pool.share.snap")})[POOL_PIE[pos]];
const poolMoved = () => POOL.some(r => r.dShare);
const poolHas = r => r.dShare !== null && r.dShare !== undefined;
const poolWas = r => r.share === null || r.share === undefined ? null : Math.max(0, r.share - r.dShare);

/* One card per team where a player of this position moved POOL_MOVE+. The card holds the team's
   three biggest moves in the same pie, largest rise first; cards sort by this position's largest. */
function poolTeams(pos){
  const pie = POOL_PIE[pos], by = {};
  POOL.filter(r => POOL_PIE[r.pos] === pie && poolHas(r)).forEach(r => { (by[r.team] = by[r.team] || []).push(r); });
  return Object.entries(by)
    .map(([team, rows]) => ({team,
      rows: rows.slice().sort((a, b) => Math.abs(b.dShare) - Math.abs(a.dShare)).slice(0, POOL_ROWS)
        .sort((a, b) => b.dShare - a.dShare),
      lead: Math.max(0, ...rows.filter(r => r.pos === pos && Math.abs(r.dShare) >= POOL_MOVE).map(r => Math.abs(r.dShare)))}))
    .filter(c => c.lead > 0)
    .sort((a, b) => b.lead - a.lead || a.team.localeCompare(b.team));
}

/* Cards per page: three rows of whatever the grid's width holds -- 3x3 on a desktop, 2x3 on a
   tablet -- and three stacked on a phone, which is what fits one phone screen. The widths are the
   page's own breakpoints (lint_css.py BREAKPOINTS), read at render. */
function poolPageSize(){
  if (window.matchMedia("(min-width: 960px)").matches) return 9;
  if (window.matchMedia("(min-width: 760px)").matches) return 6;
  return 3;
}

/* The row's bar is the move itself: a ghost to where his share was, the solid bar to where it is,
   on a scale shared by the card's rows so two teammates' bars compare. The solid bar grows from
   the ghost's length on arrival, so the motion is the transfer. */
function poolRowHTML(r, pos, top){
  const was = poolWas(r), now = Math.max(0, r.share || 0), pct = v => v === null ? "—" : v.toFixed(1) + "%";
  const w = v => (100 * (v || 0) / top).toFixed(1) + "%";
  const dir = r.dShare > 0 ? "up" : r.dShare < 0 ? "down" : "flat";   // a 0.0 is no move, not a loss
  return `<button type="button" class="xf-row${r.mine ? " mine" : ""}" data-poolslug="${esc(r.slug)}">
    <span class="xf-head">${avatarHTML(r)}</span>
    <span class="xf-nm"><b>${esc(nameInitial(r.n))}${r.pos !== pos ? ` <em>${esc(r.pos)}</em>` : ""}</b
      ><span>${pct(was)} → ${pct(now)}</span>
      <i class="xf-bar ${dir}" style="--was:${w(was)};--now:${w(now)}"><i></i></i></span>
    <span class="xf-d ${dir}">${poolSigned(r.dShare)}</span>
  </button>`;
}

/* The card's header wears the club's colour, the brighter of its two: the page is dark, and a navy
   kit (CHI, NE) washed over a dark panel reads as no colour at all. The colour says whose card it
   is before the abbreviation is read. */
function poolTeamTint(team){
  const c = TEAM_COLOURS[team];
  if (!c) return "";
  return `--team:${teamLuma(c[0]) >= teamLuma(c[1]) ? c[0] : c[1]};`;
}

function poolCardHTML(c, pos, i){
  const top = Math.max(1, ...c.rows.map(r => Math.max(poolWas(r) || 0, r.share || 0)));
  const empty = POOL_ROWS - c.rows.length;
  return `<section class="xf" style="${poolTeamTint(c.team)}--i:${i}">
    <div class="xf-t"><b>${esc(c.team)}</b><span>${poolShareLabel(pos)}</span></div>
    ${c.rows.map(r => poolRowHTML(r, pos, top)).join("")}
    ${"<div class=\"xf-row xf-none\" aria-hidden=\"true\"></div>".repeat(empty)}
  </section>`;
}

function poolPagerHTML(n, page, pages){
  if (pages <= 1) return "";
  return `<div class="filters xf-pager">
    <span class="lbl">${t("pool.pager.teams", {n, s: n === 1 ? "" : "s"})}</span>
    <span style="flex:1"></span>
    <button class="chip" data-poolpage="prev" ${page<=1?"disabled":""}>${t("common.pager.prev")}</button>
    <span class="lbl">${t("common.pager.page", {page, pages})}</span>
    <button class="chip" data-poolpage="next" ${page>=pages?"disabled":""}>${t("common.pager.next")}</button>
  </div>`;
}

/* Which way the last page turn went: the cards arrive from that side. 0 is a fresh draw. */
let POOL_DIR = 0;

/* Until any player has two weeks there is no move at all, and the one line says so. */
function poolHTML(pos){
  if (!poolMoved()) return `<p class="note pool-wait">${t("pool.wait.line")}</p>`;
  const cards = poolTeams(pos);
  if (!cards.length) return `<div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b
    ><span>${t("pool.empty.noMoves", {pos, n: POOL_MOVE})}</span></div></div>`;
  const size = poolPageSize(), pages = Math.max(1, Math.ceil(cards.length / size));
  const page = Math.min(POOL_PAGE, pages);
  const dir = POOL_DIR > 0 ? " from-next" : POOL_DIR < 0 ? " from-prev" : "";
  return `<div class="xf-grid${dir}">${cards.slice((page-1)*size, page*size)
      .map((c, i) => poolCardHTML(c, pos, i)).join("")}</div>
    ${poolPagerHTML(cards.length, page, pages)}
    <p class="note bd-foot">${t("pool.foot", {n: POOL_MOVE, wk: (typeof LIVE_POOL !== "undefined" && LIVE_POOL && LIVE_POOL.through_week) || "—"})}</p>`;
}

/* The pager and the rows. The position chip that filters the cards is the Board's (wireBd). */
function wirePool(v){
  // A page turn keeps the grid's top where the reader's eye is; the cards arrive from the side
  // the turn went.
  v.querySelectorAll("[data-poolpage]").forEach(b => b.addEventListener("click", () => {
    POOL_DIR = b.dataset.poolpage === "next" ? 1 : -1;
    POOL_PAGE = Math.max(1, POOL_PAGE + POOL_DIR);
    const y = window.scrollY; render(); window.scrollTo(0, y);
    POOL_DIR = 0;
  }));
  v.querySelectorAll("[data-poolslug]").forEach(el => el.addEventListener("click", () => {
    const r = POOL.find(x => x.slug === el.dataset.poolslug);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
