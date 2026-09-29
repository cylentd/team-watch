/* ------------------------------------------------------------------
   PREVIEW's dossier (2026-09-29, storyboard option A): one game, one card, rows inside (DESIGN.md
   "Cards"). The headline, Claude's call (side and confidence, win % beside the market's, the total,
   the score, the spread's base rate; 2026-09-29, storyboard option A), Lines, Matchup, then the
   research rows (research.js), the player calls and the risk. A row whose data is absent is not
   drawn. On a desktop the rows pair two across.

   Colour map: --up / --down a player's call and a soft / tough defense rank; --lime Claude (his
   winner, the STRONG / SOLID chips); the market is grey.
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

/* The headline and the lean, the full width. A take from before confidence (no `ats`) keeps its old
   score block and market line here, since it has no call row to fold them into. */
function pvCallRow(g){
  const k = g.take;
  if (!k) return pvRow("call full", "", `<p class="pv-none">${t("preview.notake")}</p>`);
  if (!k.ats) return pvRow("call full", "", `<h2 class="pv-head">${esc(k.head)}</h2><p class="pv-lean">${esc(k.lean)}</p>
    ${pvScoreHTML(g)}<p class="pv-vs">${esc(k.vs)}</p>`);
  return pvRow("call full", "", `<h2 class="pv-head">${esc(k.head)}</h2><p class="pv-lean">${esc(k.lean)}</p>`);
}

/* "A 3.5-point favorite, 2011–2025: wins 67%, covers 49%, n 1,314." (a pick'em: the home side's wins). */
function pvBaseHTML(g){
  const b = g.base, l = g.line;
  if (!b || !l) return "";
  const n = b.n.toLocaleString("en-US");
  if (!l.fav) return b.home == null ? "" : `<p class="pv-note">${t("preview.base.even", {home: b.home, n})}</p>`;
  if (b.wins == null || b.covers == null) return "";
  return `<p class="pv-note">${t("preview.base.fav", {by: pvNum(l.by), wins: b.wins, covers: b.covers, n})}</p>`;
}

/* Claude's call (A2): the side and its chip, the edge, win % beside the market's, the total's call,
   the score beside the market's implied one, then how favourites of this spread have done. */
function pvPickRow(g){
  const k = g.take;
  if (!k || !k.ats) return "";
  const a = k.ats, w = k.pick.winner, lo = w === g.home ? g.away : g.home, l = g.line || {};
  const mk = g.market_win && g.market_win[w], imp = l.implied, tc = k.total;
  let kv = "";
  if (k.win && k.win[w] != null) kv += pvKV(t("preview.pick.win"), `${esc(w)} ${k.win[w]}%${mk != null ? ` <small>${t("preview.odds.market", {n: Math.round(mk)})}</small>` : ""}`);
  if (tc) kv += pvKV(t("preview.line.totalk"), tc.call
    ? `${tc.call === "over" ? t("preview.pick.over") : t("preview.pick.under")}${l.total != null ? " " + pvNum(l.total) : ""} ${pvConfHTML(tc.conf)}` : pvConfHTML(null));
  kv += pvKV(t("preview.pick.score"), t("preview.pick.pair", {w: esc(w), a: k.pick.score[w], l: esc(lo), b: k.pick.score[lo]})
    + (imp ? ` <small>${t("preview.pick.market", {s: t("preview.pick.pair", {w: esc(w), a: imp[w], l: esc(lo), b: imp[lo]})})}</small>` : ""));
  return pvRow("pick", t("preview.row.pick"), `<p class="pv-callline">${pvAtsHTML(g, a)}</p>
    ${a.edge ? `<p class="pv-edge">${esc(a.edge)}</p>` : ""}<div class="pv-kv">${kv}</div>${pvBlindHTML(k)}${pvBaseHTML(g)}${pvNotesHTML(k.notes)}`);
}

/* The research pass (2026-09-29): "Claude before seeing the line: WAS by 1.5, total 48.5", in words
   like the line, then how the final call moved from it. Either absent, nothing. */
function pvBlindHTML(k){
  const b = k.blind;
  const line = b ? `<p class="pv-blind">${t("preview.blind.line", {line: pvSpread(b.fav, b.by)})}${
    b.total != null ? t("preview.blind.total", {n: pvNum(b.total)}) : ""}</p>` : "";
  return line + (k.vs_blind ? `<p class="pv-vsb">${esc(k.vs_blind)}</p>` : "");
}

/* Research notes, each with a small source: the site's name as a link, or "play-by-play". */
const pvHost = u => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch (e) { return ""; } };
function pvNotesHTML(notes){
  if (!notes || !notes.length) return "";
  const src = s => s === "pbp" ? `<span class="pv-src">${t("preview.notes.pbp")}</span>`
    : s && pvHost(s) ? `<a class="pv-src" href="${esc(s)}" target="_blank" rel="noopener noreferrer">${esc(pvHost(s))}</a>` : "";
  return `<h4 class="pv-nh">${t("preview.notes.title")}</h4><ul class="pv-notes">${notes.map(n =>
    `<li>${esc(n.text)} ${src(n.source)}</li>`).join("")}</ul>`;
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
  /* The headline spans; Claude's call and the research rows pair two across on a desktop, an odd one
     out taking the full width. */
  const pair = [pvPickRow(g), pvLinesRow(g), pvMatchupRow(g), pvInjRow(g), pvWxRow(g), pvRestRow(g)].filter(Boolean);
  if (pair.length % 2) pair[pair.length - 1] = pair[pair.length - 1].replace(/^<section class="pvd-row ([^"]*)"/, '<section class="pvd-row $1 full"');
  return `<div class="pv-dz">${pvTopHTML(g, i, n)}
    <article class="pvd-card${enter}" data-pvswipe>${pvCallRow(g)}${pair.join("")}${pvPlayersRow(g)}${pvRiskRow(g)}</article>
    <p class="pv-foot">${t("preview.foot")}</p></div>`;
}
