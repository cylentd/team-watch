/* ============================== DIGEST ==============================
   This week, the front page (2026-09-26; storyboard https://claude.ai/artifact/QyeSKebCWdeCqA9YvxXsdX).
   One fact leads (lead.js); every other topic is one ticker row: a label, a count, one line with
   the single most important name. A tap opens the row in place, one open at a time, and the day
   picks which one lies open (data/digest.js). An opened row ends in a link to its full view.
   The packet is ff-jarvis's (data/weekly_digest.json); the page computes nothing. */

const DG_CHEV = `<svg class="dg-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 6l4.5 4.5L12.5 6"/></svg>`;
const DG_ARROW = `<svg class="dg-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h9M8.5 4.5L12 8l-3.5 3.5"/></svg>`;
const DG_WIND = `<svg class="dg-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8h11a3 3 0 1 0-3-3M3 12h15a3 3 0 1 1-3 3M3 16h7"/></svg>`;
const DG_RAIN = `<svg class="dg-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 15a4 4 0 0 1 .5-8 5.5 5.5 0 0 1 10.3 1.5A3.5 3.5 0 0 1 17.5 15H7zM9 18l-1 3M13 18l-1 3M17 18l-1 3"/></svg>`;

/* Every label spelled out: assemble.py --check finds a copy key only as a literal lookup. */
const dgLabel = id => ({hurt: t("digest.row.hurt"), mu: t("digest.row.mu"), wx: t("digest.row.wx"),
  adds: t("digest.row.adds"), t5: t("digest.row.t5"), st: t("digest.row.st"), gems: t("digest.row.gems"),
  news: t("digest.row.news")})[id];

/* The closed row's count and its pill's colour: red for who is hurt, sky for weather, lime for
   the wire. Top 5 and Stock are lists, not counts, so they carry none. */
function dgCount(id, d){
  if (id === "hurt") return [d.hurt.length, "out"];
  if (id === "mu") return [d.calls || "", ""];
  if (id === "wx") return [d.wx.length || "", "sky"];
  if (id === "adds") return [d.adds.length ? dgSigned(Math.round(d.adds[0].delta), 0) : "", "go"];
  if (id === "gems") return [d.gems.length, ""];
  if (id === "news") return [d.news.length, ""];
  return ["", ""];
}

/* Hurt's line names the next two who will likely sit (the lead is already the first), then how
   many are questionable. */
function dgHurtLine(d){
  const lead = d.lead && d.lead.rule === "hurt" ? d.hurt[d.lead.index] : null;
  const word = {Out: () => t("digest.line.out"), IR: () => t("digest.line.ir"), Doubtful: () => t("digest.line.doubtful")};
  const sit = d.hurt.filter(r => r !== lead && word[r.status]).slice(0, 2).map(r => `<b>${esc(dgLast(r.n))}</b> ${word[r.status]()}`);
  const q = d.hurt.filter(r => r.status === "Questionable").length;
  return [...sit, q ? t("digest.line.q", {n: q}) : ""].filter(Boolean).join(", ");
}

/* Matchups' one name is the best spot at WR (the position Matchups opens on), else the next. */
function dgMuLine(d){
  const b = ["WR", "RB", "TE", "QB"].map(p => d.best.find(r => r.pos === p)).find(Boolean);
  return b ? t("digest.line.mu", {name: esc(b.n), vs: dgVs(b)}) : t("digest.line.muCalls", {n: d.calls});
}

function dgWxLine(d){
  const g = d.wx[0];
  if (!g) return t("digest.line.wxNone");
  return dgWxKind(g) === "wind" ? t("digest.line.wind", {game: dgGame(g), mph: g.wind_mph})
    : t("digest.line.rain", {game: dgGame(g), pct: g.precip_pct});
}

function dgGemLine(g){
  return g.metric === "tgt_pct" ? t("digest.line.gemTgt", {name: esc(g.n), usage: dgPct(g.usage), pos: esc(g.pos), ecr: g.ecr})
    : t("digest.line.gemTouch", {name: esc(g.n), usage: g.usage.toFixed(1), pos: esc(g.pos), ecr: g.ecr});
}

function dgLine(id, d){
  const top = pos => d.top5.find(r => r.pos === pos);
  const it = d.news[0], a = d.adds[0], up = d.up[0], dn = d.down[0];
  return {
    hurt: () => dgHurtLine(d), mu: () => dgMuLine(d), wx: () => dgWxLine(d),
    adds: () => t("digest.line.adds", {name: esc(a.n), was: dgPct(a.was), now: dgPct(a.now)}),
    t5: () => DG_POS.map(top).filter(Boolean).map(r => `<b>${esc(dgLast(r.n))}</b>`).join(" · "),
    st: () => [up ? `<b>${esc(dgLast(up.n))}</b> <span class="up">${dgSigned(up.d_pts, 1)}</span>` : "",
               dn ? `<b>${esc(dgLast(dn.n))}</b> <span class="dn">${dgSigned(dn.d_pts, 1)}</span>` : ""].filter(Boolean).join(" · "),
    gems: () => dgGemLine(d.gems[0]),
    news: () => it.n ? `<b>${esc(it.n)}</b> ${esc(it.rest)}` : esc(it.headline),
  }[id]();
}

function dgRowHTML(id, d, open){
  const has = dgHas(id);
  const [n, tone] = has ? dgCount(id, d) : ["", ""];
  const line = has ? dgLine(id, d) : t("digest.line.nothing");
  const on = has && open === id;
  return `<div class="dg-row${has ? "" : " empty"}" data-dgrow="${id}"${on ? " data-open data-today" : ""}>
    <button type="button" class="dg-head" aria-expanded="${on}"${has ? ` aria-controls="dg-b-${id}"` : " disabled"}>
      <span class="dg-l">${dgLabel(id)}</span><span class="dg-n ${n === "" ? "none" : tone}">${n}</span>
      <span class="dg-s">${line}</span>${has ? DG_CHEV : ""}</button>
    ${has ? `<div class="dg-body" id="dg-b-${id}"${on ? "" : " inert"}><div class="dg-in"><div class="dg-pad">${DG_BODY[id](d)}</div></div></div>` : ""}
  </div>`;
}

function digestHTML(){
  const d = dgD(), open = dgOpenRow();
  const ticker = d ? `<section class="dg-ticker" aria-label="${t("digest.ticker.label")}">${DG_ROWS.map(id => dgRowHTML(id, d, open)).join("")}</section>`
    : `<p class="dg-none">${t("digest.empty.ticker")}</p>`;
  return `<div class="dg">${dgLeadHTML()}${ticker}</div>`;
}

function dgSetOpen(row, open){
  row.toggleAttribute("data-open", open);
  row.querySelector(".dg-head").setAttribute("aria-expanded", open);
  const body = row.querySelector(".dg-body");
  if (body) body.inert = !open;
}

/* From 1100px there is room for every topic at once (2026-09-26): the rows become the wall's
   panels, all open, and a head is a title, not a toggle. Narrower, one row is open at a time. */
const DG_WALL = matchMedia("(min-width:1100px)");
function dgSyncWall(v){
  const open = dgOpenRow();
  v.querySelectorAll(".dg-row:not(.empty)").forEach(r => dgSetOpen(r, DG_WALL.matches || r.dataset.dgrow === open));
}

/* Opened in place, never by re-render: the row's own spring is the motion, and the rest of the
   list must not be redrawn under the reader. One open at a time; a second tap closes it. */
function wireDigest(v){
  v.querySelectorAll(".dg-row:not(.empty) .dg-head").forEach(h => h.addEventListener("click", () => {
    if (DG_WALL.matches) return;
    const id = h.parentElement.dataset.dgrow;
    DG_OPEN = dgOpenRow() === id ? "" : id;
    v.querySelectorAll(".dg-row").forEach(r => dgSetOpen(r, r.dataset.dgrow === DG_OPEN));
  }));
  dgSyncWall(v);
  DG_WALL.onchange = () => { const cur = document.querySelector(".dg"); if (cur) dgSyncWall(cur.parentElement); };
  v.querySelectorAll("[data-dggo]").forEach(b => b.addEventListener("click", () => {
    morphLogo(); navGo(b.dataset.dggo); window.scrollTo({top: 0});
  }));
  const d = dgD();
  v.querySelectorAll("[data-dgslug]").forEach(el => el.addEventListener("click", () => {
    const p = [...d.hurt, ...d.best, ...d.adds, ...d.gems].find(x => x.slug === el.dataset.dgslug);
    if (p) openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, el);
  }));
  // The day's open row arrives open; its bars still grow once, from last week to this week.
  const adds = v.querySelector(".dg-row[data-dgrow='adds'][data-open]");
  if (adds && !REDUCED()){
    adds.classList.add("hold");
    requestAnimationFrame(() => requestAnimationFrame(() => adds.classList.remove("hold")));
  }
}
