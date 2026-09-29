/* ------------------------------------------------------------------
   PREVIEW's dossier: one game, printed like a sports page (2026-09-29, storyboard option C; David:
   "make it clean so that it reads like a newspaper"). The story is words: the serif headline and dek,
   Claude's call, the player calls, what could go wrong, each led by a bold run-in word. Every number
   sits in the box score beside it (small type, hairline rules, no boxes): Win chance, Lines,
   Defense rank, then the research sections (research.js). A section whose data is absent is not
   drawn. A desktop from 1100px sets the box score as a column right of the story; a phone prints it
   under the call, so the numbers come before the player calls.

   Colour map: --up / --down a player's call and a soft / tough defense rank; --lime Claude (his win
   %, the bar's dot, the STRONG / SOLID chips); the market is grey.
------------------------------------------------------------------ */
/* Eastern time, as the slate's windows say it: a reader's local clock ("Sun 10:00 AM" in Seattle) read as
   the body-clock time the travel row shows beside it (2026-09-29). */
const pvKick = g => t("preview.kick", {day: esc(g.day), et: esc(g.et)});
const PV_CALL = {up: "▲", down: "▼", hold: "●"};
const pvCallWord = c => ({up: t("preview.call.up"), down: t("preview.call.down"), hold: t("preview.call.hold")})[c];
/* One box-score section: a plain bold name, then its rows. */
const pvRow = (cls, title, body) => `<section class="pva ${cls}"><h3 class="pva-h">${title}</h3>${body}</section>`;
const pvRunIn = key => `<b class="pv-rin">${key}</b>`;

/* Claude's score over the market's, winner first; the market row is the implied totals. */
function pvScoreHTML(g){
  const p = g.take.pick, w = p.winner, l = w === g.home ? g.away : g.home, imp = g.line && g.line.implied;
  const mk = imp ? `<div class="pv-sc mk"><span>${t("preview.market")}</span><b>${esc(w)} ${imp[w]}</b><b>${esc(l)} ${imp[l]}</b></div>` : "";
  return `<div class="pv-score"><div class="pv-sc"><span>${t("preview.claude")}</span><b>${esc(w)} ${p.score[w]}</b><b>${esc(l)} ${p.score[l]}</b></div>${mk}</div>`;
}

/* The headline and the dek, the full width. */
function pvHeadHTML(g){
  const k = g.take;
  if (!k) return `<header class="pvn-head"><p class="pv-none">${t("preview.notake")}</p></header>`;
  return `<header class="pvn-head"><h2 class="pv-head">${esc(k.head)}</h2><p class="pv-dek">${esc(k.lean)}</p></header>`;
}

/* The call: "The call. PIT giving 2.5 [LEAN] CLE allows ...", then Claude before the line and the
   research notes. A take from before confidence (no `ats`) keeps its old score block here. */
function pvCallHTML(g){
  const k = g.take;
  if (!k) return "";
  if (!k.ats) return `<div class="pvn-call">${pvScoreHTML(g)}<p class="pv-vs">${esc(k.vs)}</p></div>`;
  const a = k.ats;
  return `<div class="pvn-call"><p class="pv-callp">${pvRunIn(t("preview.run.call"))} <span class="pv-callline">${pvAtsHTML(g, a)}</span>${
    a.edge ? ` ${esc(a.edge)}` : ""}</p>${pvBlindHTML(k)}</div>`;
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

/* The bar under the win %: grey tick the market, lime dot Claude, the gap between them filled faintly. */
function pvBarHTML(mk, cl){
  const r1 = n => Math.round(n * 10) / 10;
  return `<span class="pv-pb" aria-hidden="true" style="--mk:${r1(mk)}%;--cl:${r1(cl)}%;--lo:${r1(Math.min(mk, cl))}%;--gap:${r1(Math.abs(cl - mk))}%">
    <i class="pv-pbt"></i><i class="pv-pbf"></i><i class="pv-pbm"></i><i class="pv-pbc"></i></span>`;
}

/* Win chance: Claude's win % for his winner over the market's, the bar, his score over the market's
   implied one, then how favourites of this spread have done. No market win %, no bar. */
function pvWinRow(g){
  const k = g.take;
  if (!k || !k.ats) return "";
  const w = k.pick.winner, lo = w === g.home ? g.away : g.home, imp = g.line && g.line.implied;
  const cl = k.win && k.win[w], mk = g.market_win && g.market_win[w];
  let kv = "";
  if (cl != null) kv += pvKV(t("preview.chance.claude", {team: esc(w)}), `<b class="pv-cl">${cl}%</b>`);
  if (mk != null) kv += pvKV(t("preview.chance.market", {team: esc(w)}), `${Math.round(mk)}%`);
  const bar = cl != null && mk != null ? pvBarHTML(mk, cl) : "";
  let sc = pvKV(t("preview.pick.score"), t("preview.pick.pair", {w: esc(w), a: k.pick.score[w], l: esc(lo), b: k.pick.score[lo]}));
  if (imp) sc += pvKV(t("preview.chance.mscore"), t("preview.pick.pair", {w: esc(w), a: imp[w], l: esc(lo), b: imp[lo]}));
  return pvRow("win", t("preview.row.win"), `${kv ? `<div class="pv-kv">${kv}</div>` : ""}${bar}<div class="pv-kv">${sc}</div>${pvBaseHTML(g)}`);
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
  return `<p class="pv-nh">${pvRunIn(t("preview.notes.title"))}</p><ul class="pv-notes">${notes.map(n =>
    `<li>${esc(n.text)} ${src(n.source)}</li>`).join("")}</ul>`;
}

const pvKV = (k, v) => `<span class="pv-k">${k}</span><span class="pv-v">${v}</span>`;

/* Lines: the spread and the total, each with where it opened when it moved, then Claude's total. */
function pvLinesRow(g){
  const l = g.line, tc = g.take && g.take.ats ? g.take.total : null;
  if (!l) return "";
  const o = l.open, small = s => s ? ` <small>${s}</small>` : "";
  const moved = o && (o.fav !== l.fav || o.by !== l.by);
  const tMoved = o && o.total != null && o.total !== l.total;
  let rows = pvKV(t("preview.line.spread"), pvSpread(l.fav, l.by) + small(moved ? t("preview.line.opened", {line: pvSpread(o.fav, o.by)}) : ""));
  if (l.total != null) rows += pvKV(t("preview.line.totalk"), pvNum(l.total) + small(tMoved ? t("preview.line.openedn", {n: pvNum(o.total)}) : ""));
  if (tc) rows += pvKV(t("preview.line.claude"), tc.call
    ? `${tc.call === "over" ? t("preview.pick.over") : t("preview.pick.under")} ${pvConfHTML(tc.conf)}` : pvConfHTML(null));
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
    <thead><tr><th></th><th>${t("preview.mx.side", {off: esc(g.away)})}</th><th>${t("preview.mx.side", {off: esc(g.home)})}</th></tr></thead>
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

/* The rest of the story, after the box score on a phone: research notes, the player calls, then what
   could go wrong. */
function pvStoryHTML(g){
  const k = g.take, ps = k ? k.players : [];
  const notes = k ? pvNotesHTML(k.notes) : "";
  const pl = ps.length ? `<p class="pv-plh">${pvRunIn(t("preview.run.players"))}</p><ul class="pv-pl">${ps.map(pvPlayerHTML).join("")}</ul>` : "";
  const risk = k ? `<p class="pv-risk">${pvRunIn(t("preview.risk"))} ${esc(k.risk)}</p>` : "";
  return notes || pl || risk ? `<div class="pvn-story">${notes}${pl}${risk}</div>` : "";
}

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
  const box = [pvWinRow(g), pvLinesRow(g), pvMatchupRow(g), pvInjRow(g), pvWxRow(g), pvRestRow(g)].join("");
  return `<div class="pv-dz">${pvTopHTML(g, i, n)}
    <article class="pvn${enter}" data-pvswipe>${pvHeadHTML(g)}${pvCallHTML(g)}${box ? `<aside class="pvn-box">${box}</aside>` : ""}${pvStoryHTML(g)}</article>
    <p class="pv-foot">${t("preview.foot")}</p></div>`;
}
