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
const dgLabel = id => ({recap: t("digest.recapRow.label"), hurt: t("digest.row.hurt"),
  mu: t("digest.row.mu"), wx: t("digest.row.wx"),
  adds: t("digest.row.adds"), t5: t("digest.row.t5"), gems: t("digest.row.gems"),
  news: t("digest.row.news")})[id];

/* The closed row's count and its pill's colour: red for who is hurt, sky for weather, lime for
   the wire. Top 5 and Stock are lists, not counts, so they carry none. */
function dgCount(id, d){
  if (id === "mu") return [d.calls || "", ""];
  if (id === "wx") return [dgWxMoves().length || "", "sky"];
  if (id === "adds") return [!d.adds.length ? "" : d.adds_source === "sleeper" ? dgBig(d.adds[0].count)
    : dgSigned(Math.round(d.adds[0].delta), 0), "go"];
  if (id === "gems") return [d.gems.length, ""];
  if (id === "news") return [d.news.length, ""];
  return ["", ""];
}

/* Matchups' one name is the best spot at WR (the position Matchups opens on), else the next. */
function dgMuLine(d){
  const b = ["WR", "RB", "TE", "QB"].map(p => d.best.find(r => r.pos === p)).find(Boolean);
  if (b) return t("digest.line.mu", {name: esc(b.n), vs: dgVs(b)});
  return d.calls === 1 ? t("digest.line.muCallsOne") : t("digest.line.muCalls", {n: d.calls});
}

/* "Rain in 4 games": what the weather is, when every game shares it, and how many. The cause a
   game counts under is its first proven condition, wind before rain before cold. */
const dgWxCond = r => ["wind", "precip", "cold"].find(c => r.conds.includes(c));
function dgWxLine(){
  const moves = dgWxMoves(), kinds = new Set(moves.map(dgWxCond)), games = dgGames(moves.length);
  const k = kinds.size === 1 ? [...kinds][0] : "";
  return k === "wind" ? t("digest.line.wxWind", {games}) : k === "precip" ? t("digest.line.wxRain", {games})
    : k === "cold" ? t("digest.line.wxCold", {games}) : t("digest.line.wxMixed", {games});
}

function dgGemLine(g){
  return g.metric === "tgt_pct" ? t("digest.line.gemTgt", {name: esc(g.n), usage: dgPct(g.usage), pos: esc(g.pos), ecr: g.ecr})
    : t("digest.line.gemTouch", {name: esc(g.n), usage: g.usage.toFixed(1), pos: esc(g.pos), ecr: g.ecr});
}

/* Matchups with nothing to call says so in Blip's voice, one of three lines, the same one all week
   (2026-09-29, David: "we can say something funny if we dont have stuff instead of boring stats").
   The record it used to quote lives on Start/Sit, where it has its splits beside it. */
const dgMuNone = next => dgPick([t("digest.wait.mu1", {week: next}), t("digest.wait.mu2"), t("digest.wait.mu3")], `mu|${next}`);

function dgLine(id, d){
  const top = pos => dgTop5(d, pos)[0];
  const it = d.news[0], a = d.adds[0];
  return {
    mu: () => dgMuLine(d), wx: () => dgWxLine(d),
    adds: () => d.adds_source === "sleeper" ? `<b>${esc(a.n)}</b> ${dgAddCount(a)}`
      : t("digest.line.adds", {name: esc(a.n), was: dgPct(a.was), now: dgPct(a.now)}),
    t5: () => DG_POS.map(top).filter(Boolean).map(r => `<b>${esc(dgLast(r.n))}</b>`).join(" · "),
    gems: () => dgGemLine(d.gems[0]),
    news: () => it.n ? `<b>${esc(it.n)}</b> ${esc(it.rest)}` : esc(it.headline),
  }[id]();
}

function dgRowHTML(id, d, open){
  const has = dgHas(id);
  const [n, tone] = has ? dgCount(id, d) : ["", ""];
  const line = has ? dgLine(id, d)
    : id === "hurt" && d && dgWeekDone(d) ? t("digest.line.hurtNext", {week: dgRowWeek(d)})
    : id === "wx" ? t("digest.line.wxCalm")
    : id === "mu" && d ? dgMuNone(dgRowWeek(d)) : t("digest.line.nothing");
  const on = has && open === id;
  return `<div class="dg-row${has ? "" : " empty"}" data-dgrow="${id}"${on ? " data-open data-today" : ""}>
    <button type="button" class="dg-head" aria-expanded="${on}"${has ? ` aria-controls="dg-b-${id}"` : " disabled"}>
      <span class="dg-l">${dgIcon(id)}${dgLabel(id)}</span><span class="dg-n ${n === "" ? "none" : tone}">${n}</span>
      <span class="dg-s">${line}</span>${has ? DG_CHEV : ""}</button>
    ${has ? `<div class="dg-body" id="dg-b-${id}"${on ? "" : " inert"}><div class="dg-in"><div class="dg-pad">${DG_BODY[id](d)}</div></div></div>` : ""}
  </div>`;
}

function digestHTML(){
  // After the week's first kickoff the Digest shares Live's poll (now.js); before it, nothing is asked.
  // Asked after this render, not during it: the reply repaints the Digest, which must not render inside a render.
  if (dgKicked()) queueMicrotask(gdEnsure);
  const d = dgD(), open = dgOpenRow();
  const rows = DG_ROWS.filter(dgShown);
  // Need to know lies open above the rows (need.js; 2026-09-29); Right now stands beside it from the
  // first kickoff (now.js). Before kickoff nothing does: Highlights left the Digest on 2026-10-04.
  const now = d ? dgNowHTML() : "";
  const mnf = dgMnfHTML(), needOff = !!d && dgNeedEmpty(d);
  // The wall's layout names which bands exist (wall.css): the Recap link, tonight's card (or the last
  // game's, mnf.js), the last slot, and the week being over (the preview rows have left, dgWaiting).
  // Need to know leaves the band to Right now when nothing in it is left to say, and takes the whole
  // band when Right now is not drawn.
  const cls = d ? [dgHas("recap") ? "has-recap" : "", d.tn.length || mnf ? "has-tn" : "", d.tnLast ? "tn-last" : "",
    dgWaiting(d) ? "wk-done" : "", needOff ? "no-need" : "", now ? "" : "no-facts"].filter(Boolean).join(" ") : "";
  const body = rows.map(id => id === "recap" ? dgRecapRowHTML() : dgRowHTML(id, d, open));
  const lead = dgLeadHTML();
  DG_LAST = {lead, now, mnf};
  DG_DRAWN = dgPhaseKey();
  const ticker = d ? `<section class="dg-ticker${cls ? " " + cls : ""}" aria-label="${t("digest.ticker.label")}">${dgTonightHTML(d, mnf)}${needOff ? "" : dgNeedHTML(d)}${now}${body.join("")}</section>`
    : `<p class="dg-none">${t("digest.empty.ticker")}</p>`;
  return `<div class="dg">${lead}${ticker}</div>`;
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
  v.querySelectorAll(".dg-row:not(.empty):not(.link)").forEach(r => dgSetOpen(r, DG_WALL.matches || r.dataset.dgrow === open));
}

/* Opened in place, never by re-render: the row's own spring is the motion, and the rest of the
   list must not be redrawn under the reader. One open at a time; a second tap closes it. */
function wireDigest(v){
  v.querySelectorAll(".dg-row:not(.empty):not(.link) .dg-head").forEach(h => h.addEventListener("click", () => {
    if (DG_WALL.matches) return;
    const id = h.parentElement.dataset.dgrow;
    DG_OPEN = dgOpenRow() === id ? "" : id;
    v.querySelectorAll(".dg-row").forEach(r => dgSetOpen(r, r.dataset.dgrow === DG_OPEN));
  }));
  dgSyncWall(v);
  DG_WALL.onchange = () => { const cur = document.querySelector(".dg"); if (cur) dgSyncWall(cur.parentElement); };
  /* A set of tabs (Top 5's positions) swaps its panel in place, and the pick is kept across repaints
     (DG_TAB, tabs.js). */
  v.querySelectorAll("[data-dgtab]").forEach(b => b.addEventListener("click", () => dgTabPick(b)));
  // The Recap row is a real link (#weekrecap): the hash opens the view, this only does what the other links do.
  v.querySelectorAll("a.dg-head[href]").forEach(a => a.addEventListener("click", () => { morphLogo(); window.scrollTo({top: 0}); }));
  v.querySelectorAll("[data-dgneedall]").forEach(b => b.addEventListener("click", () => {
    const y = window.scrollY; DG_NEED_ALL = true; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-dggo]").forEach(b => b.addEventListener("click", () => {
    morphLogo(); navGo(b.dataset.dggo); window.scrollTo({top: 0});
  }));
  // A usage line's Grid link: the player's row in the Grid, not the Grid (nav.js navGoRow).
  v.querySelectorAll("[data-dggrid]").forEach(b => b.addEventListener("click", () => {
    morphLogo(); navGoRow("usage", b.dataset.dggrid);
  }));
  // A live scorer, the touchdown count and the last game's link: one listener, so the parts a poll
  // repaints in place need no wiring (now.js).
  v.querySelector(".dg")?.addEventListener("click", dgLiveClick);
  const d = dgD();
  v.querySelectorAll("[data-dgslug]").forEach(el => el.addEventListener("click", () => {
    const slug = el.dataset.dgslug;
    const p = [...d.hurt, ...d.starters, ...d.best, ...d.adds, ...d.gems].find(x => x.slug === slug);
    if (p) return openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, el);
    // A News player need not be in any list above: search's index knows everyone on the page.
    const e = searchIndex().find(x => x.slug === slug);
    if (e) openProfile(searchPlayer(e), el);
  }));
  // The day's open row arrives open; its bars still grow once, from last week to this week.
  const adds = v.querySelector(".dg-row[data-dgrow='adds'][data-open]");
  if (adds && !REDUCED()){
    adds.classList.add("hold");
    requestAnimationFrame(() => requestAnimationFrame(() => adds.classList.remove("hold")));
  }
}
