/* ------------------------------------------------------------------
   PREVIEW's dossier (2026-09-29, storyboard option A): one game, one card, rows inside (DESIGN.md
   "Cards"). Claude's call, Lines, Matchup, then the research rows (research.js), the player calls
   and the risk. A row whose data is absent is not drawn. On a desktop the rows pair two across.

   Colour map: --up / --down a player's call and a soft / tough defense rank; --lime Claude's winner.
------------------------------------------------------------------ */
/* Eastern time, as the slate's windows say it: a reader's local clock ("Sun 10:00 AM" in Seattle) read as
   the body-clock time the travel row shows beside it (2026-09-29). */
const pvKick = g => t("preview.kick", {day: esc(g.day), et: esc(g.et)});
const PV_CALL = {up: "▲", down: "▼", hold: "●"};
const pvCallWord = c => ({up: t("preview.call.up"), down: t("preview.call.down"), hold: t("preview.call.hold")})[c];
const pvRow = (cls, title, body) => `<section class="pvd-row ${cls}">${title ? `<h3 class="pvd-rt">${title}</h3>` : ""}${body}</section>`;

/* Claude's score over the market's, winner first; the market row is the implied totals. */
function pvScoreHTML(g){
  const p = g.take.pick, w = p.winner, l = w === g.home ? g.away : g.home, imp = g.line && g.line.implied;
  const mk = imp ? `<div class="pv-sc mk"><span>${t("preview.market")}</span><b>${esc(w)} ${imp[w]}</b><b>${esc(l)} ${imp[l]}</b></div>` : "";
  return `<div class="pv-score"><div class="pv-sc"><span>${t("preview.claude")}</span><b>${esc(w)} ${p.score[w]}</b><b>${esc(l)} ${p.score[l]}</b></div>${mk}</div>`;
}

function pvCallRow(g){
  const k = g.take;
  if (!k) return pvRow("call", "", `<p class="pv-none">${t("preview.notake")}</p>`);
  return pvRow("call", "", `<h2 class="pv-head">${esc(k.head)}</h2><p class="pv-lean">${esc(k.lean)}</p>
    ${pvScoreHTML(g)}<p class="pv-vs">${esc(k.vs)}</p>`);
}

const pvKV = (k, v) => `<span class="pv-k">${k}</span><span class="pv-v">${v}</span>`;

function pvLinesRow(g){
  const l = g.line;
  if (!l) return "";
  const o = l.open, small = s => s ? ` <small>${s}</small>` : "";
  const moved = o && (o.fav !== l.fav || o.by !== l.by);
  const tMoved = o && o.total != null && o.total !== l.total;
  let rows = pvKV(t("preview.line.spread"), pvSpread(l.fav, l.by) + small(moved ? t("preview.line.opened", {line: pvSpread(o.fav, o.by)}) : ""));
  if (l.total != null) rows += pvKV(t("preview.line.totalk"), pvNum(l.total) + small(tMoved ? t("preview.line.openedn", {n: pvNum(o.total)}) : ""));
  if (g.take){
    const s = g.take.pick.score, w = g.take.pick.winner, lo = w === g.home ? g.away : g.home;
    const by = s[w] - s[lo];
    rows += pvKV(t("preview.claude"), (by ? t("preview.line.by", {team: esc(w), n: by}) : t("preview.line.even"))
      + " · " + t("preview.line.total", {n: s[w] + s[lo]}));
  }
  return pvRow("lines", t("preview.row.lines"), `<div class="pv-kv">${rows}</div>`);
}

function pvMatchupCell(side, pos){
  const c = side && (pos === "epa" ? {rank: side.epa} : side.pos[pos]);
  if (!c || c.rank == null) return `<td>–</td>`;
  const tone = pvRankTone(c.rank);
  return `<td${tone ? ` class="${tone}"` : ""}>${c.rank}${c.pts != null ? `<small>${c.pts.toFixed(1)}</small>` : ""}</td>`;
}

function pvMatchupRow(g){
  const m = g.matchup;
  if (!m) return "";
  const a = m[g.away], h = m[g.home], n = Math.max((a || {}).games || 0, (h || {}).games || 0);
  const tr = (pos, label, dim) => `<tr${dim ? ` class="dim"` : ""}><th scope="row">${label}</th>${pvMatchupCell(a, pos)}${pvMatchupCell(h, pos)}</tr>`;
  return pvRow("matchup", t("preview.row.matchup"), `<table class="pv-mx">
    <thead><tr><th></th><th>${t("preview.mx.side", {off: esc(g.away), def: esc(g.home)})}</th><th>${t("preview.mx.side", {off: esc(g.home), def: esc(g.away)})}</th></tr></thead>
    <tbody>${tr("QB", "QB")}${tr("RB", "RB")}${tr("TE", "TE")}${tr("WR", "WR", true)}${tr("epa", t("preview.mx.epa"))}</tbody></table>
    <p class="pv-note">${t("preview.mx.note", {n})}</p><p class="pv-note">${t("preview.mx.wr")}</p>`);
}

function pvPlayerHTML(p, j){
  return `<li><button class="pv-p" data-pvp="${j}">
    <span class="pv-face">${headHTML(p)}</span>
    <span class="pv-call ${p.call}" aria-label="${pvCallWord(p.call)}">${PV_CALL[p.call]}</span>
    <span class="pv-pn">${shortName(p.n)}<small>${esc(p.pos)} · ${esc(p.team)}</small></span>
    <span class="pv-pj">${p.proj.toFixed(1)}</span>
    <span class="pv-pw">${esc(p.why)}</span></button></li>`;
}

function pvPlayersRow(g){
  const ps = g.take ? g.take.players : [];
  if (!ps.length) return "";
  return pvRow("players full", t("preview.row.players", {n: ps.length}), `<ul class="pv-pl">${ps.map(pvPlayerHTML).join("")}</ul>`);
}

const pvRiskRow = g => g.take ? pvRow("risk full", "", `<p class="pv-risk"><b>${t("preview.risk")}</b><span>${esc(g.take.risk)}</span></p>`) : "";

/* The header: back to the slate (a phone), ‹ AWAY @ HOME ›, the kickoff. */
function pvTopHTML(g, i, n){
  const kick = pvDone(g) ? t("preview.kicked", {kick: pvKick(g)}) : pvKick(g);
  return `<button class="pv-back" data-pvback>${t("preview.back")}</button>
    <header class="pv-top">
    <button class="pv-arrow" data-pvstep="-1"${i === 0 ? " disabled" : ""} aria-label="${t("preview.prev")}">‹</button>
    <b class="pv-mt" aria-label="${t("preview.count", {i: i + 1, n})}">${esc(g.away)} @ ${esc(g.home)}</b>
    <button class="pv-arrow" data-pvstep="1"${i === n - 1 ? " disabled" : ""} aria-label="${t("preview.next")}">›</button>
    <span class="pv-ko">${kick}</span></header>`;
}

function pvDossierHTML(g, i, n, enter){
  /* The research rows pair two across on a desktop; an odd one out takes the full width. */
  const pair = [pvCallRow(g), pvLinesRow(g), pvMatchupRow(g), pvInjRow(g), pvWxRow(g), pvRestRow(g)].filter(Boolean);
  if (pair.length % 2) pair[pair.length - 1] = pair[pair.length - 1].replace('class="pvd-row ', 'class="pvd-row full ');
  return `<div class="pv-dz">${pvTopHTML(g, i, n)}
    <article class="pvd-card${enter}" data-pvswipe>${pair.join("")}${pvPlayersRow(g)}${pvRiskRow(g)}</article>
    <p class="pv-foot">${t("preview.foot")}</p></div>`;
}
