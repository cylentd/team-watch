/* ------------------------------------------------------------------
   PREVIEW's dossier: one game, printed like a sports page (2026-09-29, storyboard option C; David:
   "make it clean so that it reads like a newspaper"). Since ledger #82 (2026-10-09, storyboard draft A
   "Ledger"; David: the players are "the best part and buried") the order is (headline first again the same
   day, David: "The headline is gone! maybe swap?"): the headline, the story's first paragraph with the
   rest one tap away, what could go wrong; the player calls, each with his yards and chance to score; the
   answer (our score, then Vegas beside ours per bet, then the pick); the call's reason; then the box score (small type, hairline rules, no boxes): Defense rank and the research
   sections (research.js). A section whose data is absent is not drawn. Show, don't tell (David,
   2026-09-30: "no one cares"): no footnote explains a number, and Claude's research notes, sources and
   before-the-line process stay in the data for grading, off the page. From 1100px the story then the players sit left of
   the answer, its reason and the box score.

   Colour map: --up / --down a player's call, a soft / tough defense rank and a graded ✓ / ✗; --lime only
   the Confident / Very confident words; Vegas is grey, ours and the pick white (ledger #82).
------------------------------------------------------------------ */
/* The kickoff in the reader's clock, the page's one format ("Mon 8:15 PM", lib/kick.js). Until 2026-10-05 it
   was Eastern ("Mon 8:15 PM ET") while Bets and the Digest said Pacific; the travel row's body clock is a
   team's own and says so. */
const pvKick = g => esc(kickFmt(g.kickoff));
const PV_CALL = {up: "▲", down: "▼", hold: "●"};
const pvCallWord = c => ({up: t("preview.call.up"), down: t("preview.call.down"), hold: t("preview.call.hold")})[c];
/* One box-score section: a plain bold name, then its rows. */
const pvRow = (cls, title, body) => `<section class="pva ${cls}" data-testid="preview-section"><h3 class="pva-h" data-testid="preview-section-title">${title}</h3>${body}</section>`;
const pvRunIn = key => `<b class="pv-rin">${key}</b>`;

/* The headline and the story. The story is 2-5 paragraphs split by a blank line (ff-jarvis STORY_VERSION 1,
   2026-09-30), one voice, so every paragraph is set alike (David, 2026-09-30: a smaller second paragraph read
   as a different author). Since ledger #82 (2026-10-09) the first paragraph shows and the rest is one tap
   away in a native <details>: a live story ran to 2,000px of a 4,700px page ("no endless scroll"). What
   could go wrong stays open under it, the counterweight to the pick. */
function pvHeadHTML(g){
  const k = g.take;
  if (!k) return `<header class="pvn-head" data-testid="preview-header"><p class="pv-none">${t("preview.notake")}</p></header>`;
  const paras = pvNamesHTML(k.lean.split(/\n\s*\n/).map(s => s.trim()).filter(Boolean), k.players)
    .map(h => `<p class="pv-dek" data-testid="preview-dek">${h}</p>`);
  const more = paras.length > 1 ? `<details class="pv-more" data-testid="preview-more"><summary>${t("preview.story.more")}${SL_CHEV}</summary>${paras.slice(1).join("")}</details>` : "";
  const risk = k.risk ? `<p class="pv-risk" data-testid="preview-risk">${pvRunIn(t("preview.risk"))} ${esc(k.risk)}</p>` : "";
  return `<header class="pvn-head" data-testid="preview-header"><h2 class="pv-head" data-testid="preview-headline">${esc(k.head)}</h2>${
    paras[0] || ""}${more}${risk}</header>`;
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
  if (!k.ats) return `<div class="pvn-call" data-testid="preview-call"><p class="pv-vs">${esc(k.vs)}</p></div>`;
  return k.ats.edge ? `<div class="pvn-call" data-testid="preview-call"><p class="pv-callp">${pvRunIn(t("preview.run.call"))} ${esc(k.ats.edge)}</p></div>` : "";
}

/* The answer block: a finished game's final, our score, then one row per bet (ledger #82, 2026-10-09, storyboard
   draft A; it superseded 3A's Vegas-beside-a-verdict, which David found hard to read): Vegas's number grey, ours
   in the same unit white beside it (pvOurs, data/pvdossier.js), then the pick word with its confidence under it.
   Number beside number says why the pick is the pick, so 3A's "wins by 4 or more" line is gone. A graded game
   marks each pick ✓ / ✗. The rows are pvAnswer's (data/preview.js). */
const PV_MARK = {hit: "✓", miss: "✗", push: "–"};
const pvMarkHTML = h => h ? `<b class="pv-mk ${h}" aria-label="${({hit: t("preview.hit.hit"), miss: t("preview.hit.miss"), push: t("preview.hit.push")})[h]}">${PV_MARK[h]}</b> ` : "";

function pvAnsRowHTML(r, ours, hasTake){
  const label = {ml: t("preview.bet.ml"), spread: t("preview.bet.spread"), total: t("preview.bet.total")}[r.id];
  const pick = r.claude ? `${pvMarkHTML(r.hit)}${r.claude}${r.conf ? `<span class="pv-cw">${pvConfHTML(r.conf)}</span>` : ""}`
    : hasTake ? pvConfHTML(null) : "–";
  return `<tr class="${r.id}" data-testid="preview-bet"><th scope="row">${label}</th><td class="pv-vg">${r.vegas || "–"}</td>
    <td class="pv-us">${(ours && ours[r.id]) || "–"}</td><td class="pv-cc">${pick}</td></tr>`;
}

function pvAnswerHTML(g){
  const rg = pvRecGameOf(g), a = pvAnswer(g, rg), fin = pvFinal(g, rg), ours = pvOurs(g);
  if (!a.rows.length && !a.score) return "";
  const final = fin ? `<p class="pv-fin"><span>${t("preview.final")}</span><b>${fin}</b></p>` : "";
  const score = a.score ? `<span class="pv-ak">${t("preview.ans.pick")}</span><b class="pv-am" data-testid="preview-score">${a.score}</b>` : "";
  const table = a.rows.length ? `<table class="pv-bt" data-testid="preview-bets"><thead><tr><th></th><th>${t("preview.ans.vegas")}</th><th>${
    t("preview.ans.ours")}</th><th>${t("preview.ans.pickcol")}</th></tr></thead>
    <tbody>${a.rows.map(r => pvAnsRowHTML(r, ours, !!g.take)).join("")}</tbody></table>` : "";
  return `<section class="pvn-ans" data-testid="preview-answer" aria-label="${t("preview.ans.label")}">${final}${score}${table}</section>`;
}

const pvKV = (k, v) => `<span class="pv-k">${k}</span><span class="pv-v">${v}</span>`;

/* Defense rank (ledger #82): one row per offense, one column per position, the rank of the defense it faces,
   soft --up and tough --down. Points allowed and pass EPA left the page with the cleanup (the rank is the
   answer; EPA is a word a reader has to look up). The WR column stays faded: the backtest finds the WR
   matchup moves nothing (QB/RB/TE 8-18%). */
const PV_MX_POS = ["QB", "RB", "WR", "TE"];

function pvMatchupCell(side, pos){
  const c = side && side.pos[pos];
  if (!c || c.rank == null) return `<td${pos === "WR" ? ` class="dim"` : ""}>–</td>`;
  const cls = [pvRankTone(c.rank), pos === "WR" ? "dim" : ""].filter(Boolean).join(" ");
  return `<td${cls ? ` class="${cls}"` : ""}>${c.rank}</td>`;
}

function pvMatchupRow(g){
  const m = g.matchup;
  if (!m) return "";
  const tr = team => `<tr><th scope="row">${t("preview.mx.side", {off: esc(team)})}</th>${PV_MX_POS.map(p => pvMatchupCell(m[team], p)).join("")}</tr>`;
  return pvRow("matchup", t("preview.row.matchup"), `<table class="pv-mx" data-testid="preview-matchup">
    <thead><tr><th></th>${PV_MX_POS.map(p => `<th${p === "WR" ? ` class="dim"` : ""}>${p}</th>`).join("")}</tr></thead>
    <tbody>${tr(g.away)}${tr(g.home)}</tbody></table>`);
}

/* A player call (ledger #82: first on the page, David: "the best part"): face, Claude's ▲ ▼ ● and the name, his
   reason under it; the row opens his profile. On the right the yards our model expects and his chance to score
   (pvPlayerLine), a tap to his lines in the Slips player sheet, the hand-off that was its own box-score section
   until 2026-10-09. A player with no lines this week shows his projected points, plain text. */
function pvPlayerHTML(p, j, on, live){
  const rows = slPlayerRows(p.slug), ln = pvPlayerLine(p.pos, rows.map(i => PROPS[i]));
  const num = ln.yds != null ? `<b data-testid="preview-player-yds-n">${ln.yds} <small>${ln.unit}</small></b>${
    ln.td != null ? `<small class="pv-td" data-testid="preview-player-td">${t("preview.pl.td", {n: ln.td})}</small>` : ""}${
    on ? `<span class="sl-on" data-testid="preview-slip-on">${t("slips.onSlip")}</span>` : ""}`
    : `<b class="pv-pts" data-testid="preview-player-yds-n">${p.proj != null ? t("preview.pl.pts", {n: p.proj.toFixed(1)}) : "–"}</b>`;
  const yds = ln.yds != null && live ? `<button type="button" class="pv-py" data-testid="preview-player-yds" data-slplayer="${esc(p.slug)}" aria-label="${t("preview.pl.lines")}">${num}</button>`
    : `<span class="pv-py" data-testid="preview-player-yds">${num}</span>`;
  return `<li class="pv-pr" data-testid="preview-player-row"><button type="button" class="pv-p" data-pvp="${j}" data-testid="preview-player">
    <span class="pv-face">${headHTML(p)}</span>
    <span class="pv-pn"><i class="pv-call ${p.call}" aria-label="${pvCallWord(p.call)}" title="${pvCallWord(p.call)}. ${t("preview.call.mark")}">${PV_CALL[p.call]}</i><span data-testid="preview-player-name">${shortName(p.n)}</span><small class="pv-pt">${esc(p.pos)} · ${esc(p.team)}</small></span>
    <span class="pv-pw">${esc(p.why)}</span></button>${yds}</li>`;
}

/* The players, then the way to every player of the game in Slips (handoff.js), while the game has lines. */
function pvPlayersHTML(g){
  const ps = g.take ? g.take.players : [];
  if (!ps.length) return "";
  const live = !(PV_ARC_G || pvOver(g)) && !!LIVE_MARKET, on = onSlipSlugs();
  return `<section class="pvn-pl" aria-label="${t("preview.pl.title")}"><h3 class="pva-h">${t("preview.pl.title")}</h3>
    <ul class="pv-pl" data-testid="preview-players">${ps.map((p, j) => pvPlayerHTML(p, j, on.has(p.slug), live)).join("")}</ul>${live ? pvSlipAllHTML(g) : ""}</section>`;
}

/* The header: back (a phone) to the slate, or to Past games when it opened the game, ‹ AWAY @ HOME ›, the
   kickoff. An earlier week's kickoff names its week, since the day alone would not say which. */
function pvTopHTML(g, i, n){
  const kick = PV_ARC_G ? `${t("preview.arc.week", {n: PV_ARC_G.week})} · ${pvKick(g)}`
    : pvOver(g) ? `${t("preview.final")} · ${pvKick(g)}` : pvDone(g) ? t("preview.kicked", {kick: pvKick(g)}) : pvKick(g);
  return `<button class="pv-back" data-pvback data-testid="preview-back">${PV_ARC_G || PV_REC ? t("preview.backArc") : t("preview.back")}</button>
    <header class="pv-top">
    <button class="pv-arrow" data-pvstep="-1" data-testid="preview-step"${i === 0 ? " disabled" : ""} aria-label="${t("preview.prev")}">‹</button>
    <b class="pv-mt" data-testid="preview-match" aria-label="${t("preview.count", {i: i + 1, n})}">${esc(g.away)} @ ${esc(g.home)}</b>
    <button class="pv-arrow" data-pvstep="1" data-testid="preview-step"${i === n - 1 ? " disabled" : ""} aria-label="${t("preview.next")}">›</button>
    <span class="pv-ko" data-testid="preview-kickoff">${kick}</span></header>`;
}

function pvDossierHTML(g, i, n, enter){
  // Once a game is over its lines are gone, so the hand-off to Slips is too; an earlier week's always is.
  const box = [pvMatchupRow(g), pvInjRow(g), pvDsRow(g), pvWxRow(g), pvRestRow(g)].join("");
  return `<div class="pv-dz" data-testid="preview-dossier">${pvTopHTML(g, i, n)}
    <article class="pvn${enter}" data-pvswipe data-testid="preview-article">${pvHeadHTML(g)}${pvPlayersHTML(g)}${pvAnswerHTML(g)}${pvCallHTML(g)}${box ? `<aside class="pvn-box" data-testid="preview-box">${box}</aside>` : ""}</article></div>`;
}
