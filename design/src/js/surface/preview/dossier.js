/* ------------------------------------------------------------------
   PREVIEW's dossier: one game, printed like a sports page (2026-09-29, storyboard option C; David:
   "make it clean so that it reads like a newspaper"). The story is words: the serif headline and dek,
   Claude's call, the player calls, what could go wrong, each led by a bold run-in word. The answer
   comes first (2026-10-05, plan U3): a block above the headline with Claude's pick, the line, the total
   and the win chance, so a reader who wants the number never reads a paragraph for it. The rest of the
   numbers sit in the box score beside the story (small type, hairline rules, no boxes): Defense rank,
   then the research sections (research.js). A section whose data is absent is not
   drawn. Show, don't tell (David, 2026-09-30: "no one cares"): no footnote explains a number, and
   Claude's research notes, sources and before-the-line process stay in the data for grading, off
   the page. A desktop from 1100px sets the box score as a column right of the story; a phone prints it
   under the call, so the numbers come before the player calls.

   Colour map: --up / --down a player's call, a soft / tough defense rank and a graded ✓ / ✗; --lime only
   the Confident / Very confident words; Vegas is grey, Claude's call white (storyboard 3A, 2026-10-05).
------------------------------------------------------------------ */
/* The kickoff in the reader's clock, the page's one format ("Mon 8:15 PM", lib/kick.js). Until 2026-10-05 it
   was Eastern ("Mon 8:15 PM ET") while Bets and the Digest said Pacific; the travel row's body clock is a
   team's own and says so. */
const pvKick = g => esc(kickFmt(g.kickoff));
const PV_CALL = {up: "▲", down: "▼", hold: "●"};
const pvCallWord = c => ({up: t("preview.call.up"), down: t("preview.call.down"), hold: t("preview.call.hold")})[c];
/* One box-score section: a plain bold name, then its rows. */
const pvRow = (cls, title, body) => `<section class="pva ${cls}"><h3 class="pva-h">${title}</h3>${body}</section>`;
const pvRunIn = key => `<b class="pv-rin">${key}</b>`;

/* The headline and the story, the full width. The story is 2-3 paragraphs split by a blank line
   (ff-jarvis STORY_VERSION 1, 2026-09-30), one voice, so every paragraph is set alike (David,
   2026-09-30: a smaller second paragraph read as a different author). */
function pvHeadHTML(g){
  const k = g.take;
  if (!k) return `<header class="pvn-head"><p class="pv-none">${t("preview.notake")}</p></header>`;
  const paras = k.lean.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean);
  return `<header class="pvn-head"><h2 class="pv-head">${esc(k.head)}</h2>${
    pvNamesHTML(paras, k.players).map(h => `<p class="pv-dek">${h}</p>`).join("")}</header>`;
}

/* Each player call's first mention in the story, bold and a tap to his profile (David, 2026-09-30: "bold
   them"). Only the calls under the story: linemen and coaches stay plain, they are not fantasy picks.
   The full name first; the surname alone only when no other call in the game shares it (IND @ WAS has
   two Warrens). `data-pvp` is the call's index, the same one the player rows use. */
const pvRx = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function pvNamesHTML(paras, players){
  const last = n => n.replace(/\s+(Jr\.?|Sr\.?|II|III|IV)$/, "").split(/\s+/).pop();
  const spans = paras.map(() => []);
  players.forEach((p, j) => {
    const solo = players.filter(q => last(q.n) === last(p.n)).length === 1;
    for (const name of solo ? [p.n, last(p.n)] : [p.n]){
      const rx = new RegExp(`(?<![\\w'’])${pvRx(name)}(?![\\w’])`);
      const i = paras.findIndex((s, pi) => { const m = rx.exec(s); return m && !spans[pi].some(x => m.index < x.e && m.index + name.length > x.s); });
      if (i < 0) continue;
      const at = rx.exec(paras[i]).index;
      spans[i].push({s: at, e: at + name.length, j});
      return;
    }
  });
  return paras.map((s, i) => {
    let out = "", at = 0;
    spans[i].sort((a, b) => a.s - b.s).forEach(x => {
      out += esc(s.slice(at, x.s)) + `<button type="button" class="pv-nm" data-pvp="${x.j}">${esc(s.slice(x.s, x.e))}</button>`;
      at = x.e;
    });
    return out + esc(s.slice(at));
  });
}

/* The call's reason: "The call. CLE allows ...". The side and its confidence moved into the answer block
   above the story (2026-10-05), so this is prose only, and absent when the take gave no reason. A take
   from before confidence (no `ats`) keeps its one-line `vs`. */
function pvCallHTML(g){
  const k = g.take;
  if (!k) return "";
  if (!k.ats) return `<div class="pvn-call"><p class="pv-vs">${esc(k.vs)}</p></div>`;
  return k.ats.edge ? `<div class="pvn-call"><p class="pv-callp">${pvRunIn(t("preview.run.call"))} ${esc(k.ats.edge)}</p></div>` : "";
}

/* The answer block (storyboard 3A, 2026-10-05): a finished game's final, Claude's score, then a table of one
   row per bet, Vegas grey beside Claude white with his confidence word and what the call needs in points.
   A graded game marks each call ✓ / ✗. The rows are pvAnswer's (data/preview.js). */
const PV_MARK = {hit: "✓", miss: "✗", push: "–"};
const pvMarkHTML = h => h ? `<b class="pv-mk ${h}" aria-label="${({hit: t("preview.hit.hit"), miss: t("preview.hit.miss"), push: t("preview.hit.push")})[h]}">${PV_MARK[h]}</b> ` : "";

function pvAnsRowHTML(r, hasTake){
  const label = {ml: t("preview.bet.ml"), spread: t("preview.bet.spread"), total: t("preview.bet.total")}[r.id];
  const call = r.claude ? `${pvMarkHTML(r.hit)}${r.claude}${r.conf ? " " + pvConfHTML(r.conf) : ""}${r.sub && !r.hit ? `<small class="pv-as">${r.sub}</small>` : ""}`
    : hasTake ? pvConfHTML(null) : "–";
  return `<tr class="${r.id}"><th scope="row">${label}</th><td class="pv-vg">${r.vegas || "–"}</td><td class="pv-cc">${call}</td></tr>`;
}

function pvAnswerHTML(g){
  const rg = pvRecGameOf(g), a = pvAnswer(g, rg), fin = pvFinal(g, rg);
  if (!a.rows.length && !a.score) return "";
  const final = fin ? `<p class="pv-fin"><span>${t("preview.final")}</span><b>${fin}</b></p>` : "";
  const score = a.score ? `<span class="pv-ak">${t("preview.ans.pick")}</span><b class="pv-am">${a.score}</b>` : "";
  const table = a.rows.length ? `<table class="pv-bt"><thead><tr><th></th><th>${t("preview.ans.vegas")}</th><th>${t("preview.ans.claude")}</th></tr></thead>
    <tbody>${a.rows.map(r => pvAnsRowHTML(r, !!g.take)).join("")}</tbody></table>` : "";
  return `<section class="pvn-ans" aria-label="${t("preview.ans.label")}">${final}${score}${table}</section>`;
}

const pvKV = (k, v) => `<span class="pv-k">${k}</span><span class="pv-v">${v}</span>`;

function pvMatchupCell(side, pos){
  const c = side && (pos === "epa" ? {rank: side.epa} : side.pos[pos]);
  if (!c || c.rank == null) return `<td>–</td>`;
  const tone = pvRankTone(c.rank);
  return `<td${tone ? ` class="${tone}"` : ""}>${c.rank}${c.pts != null ? `<small>${c.pts.toFixed(1)}</small>` : ""}</td>`;
}

function pvMatchupRow(g){
  const m = g.matchup;
  if (!m) return "";
  const a = m[g.away], h = m[g.home];
  const tr = (pos, label, dim) => `<tr${dim ? ` class="dim"` : ""}><th scope="row">${label}</th>${pvMatchupCell(a, pos)}${pvMatchupCell(h, pos)}</tr>`;
  return pvRow("matchup", t("preview.row.matchup"), `<table class="pv-mx">
    <thead><tr><th></th><th>${t("preview.mx.side", {off: esc(g.away)})}</th><th>${t("preview.mx.side", {off: esc(g.home)})}</th></tr></thead>
    <tbody>${tr("QB", "QB")}${tr("RB", "RB")}${tr("TE", "TE")}${tr("WR", "WR", true)}${tr("epa", t("preview.mx.epa"))}</tbody></table>`);
}

function pvPlayerHTML(p, j){
  return `<li><button class="pv-p" data-pvp="${j}">
    <span class="pv-face">${headHTML(p)}</span>
    <span class="pv-call ${p.call}" aria-label="${pvCallWord(p.call)}">${PV_CALL[p.call]}</span>
    <span class="pv-pn">${shortName(p.n)}<small>${esc(p.pos)} · ${esc(p.team)}</small></span>
    <span class="pv-pj">${p.proj != null ? p.proj.toFixed(1) : ""}</span>
    <span class="pv-pw">${esc(p.why)}</span></button></li>`;
}

/* The rest of the story, after the box score on a phone: the player calls, then what could go wrong. */
function pvStoryHTML(g){
  const k = g.take, ps = k ? k.players : [];
  const pl = ps.length ? `<p class="pv-plh">${pvRunIn(t("preview.run.players"))}</p><ul class="pv-pl">${ps.map(pvPlayerHTML).join("")}</ul>` : "";
  const risk = k ? `<p class="pv-risk">${pvRunIn(t("preview.risk"))} ${esc(k.risk)}</p>` : "";
  return pl || risk ? `<div class="pvn-story">${pl}${risk}</div>` : "";
}

/* The header: back (a phone) to the slate, or to Past games when it opened the game, ‹ AWAY @ HOME ›, the
   kickoff. An earlier week's kickoff names its week, since the day alone would not say which. */
function pvTopHTML(g, i, n){
  const kick = PV_ARC_G ? `${t("preview.arc.week", {n: PV_ARC_G.week})} · ${pvKick(g)}`
    : pvOver(g) ? `${t("preview.final")} · ${pvKick(g)}` : pvDone(g) ? t("preview.kicked", {kick: pvKick(g)}) : pvKick(g);
  return `<button class="pv-back" data-pvback>${PV_ARC_G || PV_REC ? t("preview.backArc") : t("preview.back")}</button>
    <header class="pv-top">
    <button class="pv-arrow" data-pvstep="-1"${i === 0 ? " disabled" : ""} aria-label="${t("preview.prev")}">‹</button>
    <b class="pv-mt" aria-label="${t("preview.count", {i: i + 1, n})}">${esc(g.away)} @ ${esc(g.home)}</b>
    <button class="pv-arrow" data-pvstep="1"${i === n - 1 ? " disabled" : ""} aria-label="${t("preview.next")}">›</button>
    <span class="pv-ko">${kick}</span></header>`;
}

function pvDossierHTML(g, i, n, enter){
  // Once a game is over its lines are gone, so the hand-off to Slips is too; an earlier week's always is.
  const box = [pvMatchupRow(g), PV_ARC_G || pvOver(g) ? "" : pvSlipRow(g), pvInjRow(g), pvWxRow(g), pvRestRow(g)].join("");
  return `<div class="pv-dz">${pvTopHTML(g, i, n)}
    <article class="pvn${enter}" data-pvswipe>${pvAnswerHTML(g)}${pvHeadHTML(g)}${pvCallHTML(g)}${box ? `<aside class="pvn-box">${box}</aside>` : ""}${pvStoryHTML(g)}</article></div>`;
}
