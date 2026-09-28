/* ============================== THIS WEEK > RECORDS (Yahoo) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5Sj3BRZqyfaVWkvCXCjgFV (its Records section; the page
   before it, JAp2FLPRYAXSVxnNtR8HKU, was a trophy list and two halls). The league's all-time book, apart
   from the week: head to head for any manager against every leaguemate (a row opens that pair's grudge
   card), the trophy case and the last-place case as shelves, then the Hall of Fame and the Hall of Shame.
   A record is filed under its manager's first name (David's call, 2026-09-27: team names change every
   season), with the team it was then underneath. Data: design/league_recap.py, design/league_back.py. */

/* Who holds a record: the manager by name (ff-jarvis yahoo_league_managers.json), else today's team,
   else the name it won under. */
const lgHolder = (mgr, id, name) => mgr ? esc(mgr) : id != null ? lgName(id) : esc(name || t("league.former"));

/* The manager whose head to head is on screen: the reader's tap, else the team they have picked when it
   is in this league, else the first by name. Kept for the session. */
let RC_MGR = null;

const rcManagers = () => [...LG.teams].sort((a, b) => lgMgr(a.id).localeCompare(lgMgr(b.id)));

function rcPicked(){
  if (RC_MGR != null && LG.teams.some(x => x.id === RC_MGR)) return RC_MGR;
  const mine = lgIdOf(TEAMS[VIEW]);
  return mine != null ? mine : rcManagers()[0].id;
}

/* A private pair (design/league_private.json) keeps its row with the record blacked out: dropping the
   row would say more than hiding the numbers. The build ships the pair, never its record. */
const rcWithheld = (a, b) => (LG.withheld || []).some(([x, y]) => (x === a && y === b) || (x === b && y === a));

/* One leaguemate's row from `id`'s side: [opp, games, win share, point difference, h2h row]. */
function rcRow(id, opp){
  const h = lgH2H(id, opp), m = (h && h.m) || [];
  const n = h ? h.w + h.l + h.t : 0;
  return {opp, h, n, pct: n ? (h.w + h.t / 2) / n : 0, diff: m.reduce((s, x) => s + x[2], 0)};
}

function rcRowHTML(id, r){
  const name = `<b>${lgMgr(r.opp)}</b>`;
  if (rcWithheld(id, r.opp)){
    const bar = `<span class="bp-redact" aria-hidden="true"></span>`;
    return `<li class="rc-h wh" aria-label="${t("records.h2h.withheld", {opp: lgMgr(r.opp)})}">${name}${bar}${bar}${bar}</li>`;
  }
  if (!r.n) return `<li class="rc-h"><b>${lgMgr(r.opp)}</b><span class="rc-never">${t("records.h2h.never")}</span></li>`;
  const wl = r.h.t ? `${r.h.w}–${r.h.l}–${r.h.t}` : `${r.h.w}–${r.h.l}`;
  const pd = `${r.diff >= 0 ? "+" : "−"}${lgPts(Math.abs(r.diff))}`;
  return `<li><button type="button" class="rc-h" data-rcpair="${r.opp}"
      aria-label="${t("records.h2h.aria", {a: lgMgr(id), b: lgMgr(r.opp), wl, pd})}">${name}
    <span class="rc-bar" aria-hidden="true"><i style="--w:${(100 * r.pct).toFixed(0)}%"></i></span>
    <span class="rc-wl">${wl}</span><span class="rc-pd ${r.diff >= 0 ? "up" : "dn"}">${pd}</span></button></li>`;
}

/* Head to head: pick a manager, then every leaguemate best to worst (win share, then points). Withheld
   rows go last, whatever the record, so their place in the order gives nothing away. */
function rcHeadToHeadHTML(){
  const id = rcPicked();
  const rows = LG.teams.filter(x => x.id !== id).map(x => rcRow(id, x.id));
  const open = rows.filter(r => !rcWithheld(id, r.opp)).sort((a, b) => (b.n > 0) - (a.n > 0) || b.pct - a.pct || b.diff - a.diff);
  const chips = rcManagers().map(x => `<button type="button" class="chip" data-rcmgr="${x.id}" aria-pressed="${x.id === id}">${lgMgr(x.id)}</button>`).join("");
  return `<section class="lg-sec rc-hh" aria-label="${t("records.h2h.title")}">
    <h2 class="bp-hd">${t("records.h2h.title")}<span>${t("records.h2h.sub")}</span></h2>
    <div class="setrow rc-mgrs" role="group" aria-label="${t("records.h2h.pick")}">${chips}</div>
    <ol class="rc-list">${[...open, ...rows.filter(r => rcWithheld(id, r.opp))].map(r => rcRowHTML(id, r)).join("")}</ol>
  </section>`;
}

/* A drawn trophy and a drawn wooden spoon, one path each. */
const RC_CUP = `<svg class="rc-ico cup" viewBox="0 0 32 32" aria-hidden="true"><path d="M9 4h14v7a7 7 0 0 1-14 0zM9 6H4v3a5 5 0 0 0 5 5v-2a3 3 0 0 1-3-3V8h3M23 6h5v3a5 5 0 0 1-5 5v-2a3 3 0 0 0 3-3V8h-3M14 18h4v5h-4zM10 24h12v3H10z"/></svg>`;
const RC_SPOON = `<svg class="rc-ico spoon" viewBox="0 0 32 32" aria-hidden="true"><path transform="rotate(-20 16 16)" d="M16 3c4 0 6 3 6 6.5S20 16 16 16s-6-3-6-6.5S12 3 16 3zM14.6 15.5h2.8L17 29h-2z"/></svg>`;

/* One season on a shelf: the icon, the year, the manager, the team it was that year. */
const rcShelfItem = (ico, r) => `<li class="rc-item${r.final === false ? " est" : ""}">${ico}<b>${r.y}</b>
  <span>${lgHolder(r.mgr, r.id, r.name)}</span>${r.name ? `<small>${esc(r.name.trim())}</small>` : ""}</li>`;

/* Titles counted by manager, for the line under the trophies: everyone with two or more. */
function rcTally(){
  const n = new Map();
  LG.champs.forEach(c => { const k = c.mgr || c.name; n.set(k, (n.get(k) || 0) + 1); });
  return [...n].filter(([, c]) => c >= 2).sort((a, b) => b[1] - a[1])
    .map(([k, c]) => `<span>${t("records.trophy.tally", {mgr: `<b>${esc(k)}</b>`, n: c})}</span>`).join("");
}

function rcTrophyHTML(){
  const won = new Set(LG.champs.map(c => c.id).filter(x => x != null));
  const zero = LG.teams.filter(x => !won.has(x.id)).map(x => esc(x.mgr || x.name));
  const tally = rcTally();
  return `<section class="lg-sec" aria-label="${t("records.trophy.title")}">
    <h2 class="bp-hd">${t("records.trophy.title")}<span>${t("records.trophy.sub", {n: LG.champs.length})}</span></h2>
    <ul class="rc-shelf">${LG.champs.map(c => rcShelfItem(RC_CUP, c)).join("")}</ul>
    ${tally ? `<p class="rc-tally">${tally}</p>` : ""}
    ${zero.length ? `<p class="rc-tally"><span>${t("records.trophy.zero", {teams: zero.join(", ")})}</span></p>` : ""}
  </section>`;
}

/* The last-place case: Yahoo's final 12th (the consolation bracket counts). A season whose final
   standings were never read shows the worst regular season instead, dimmed, and says so. */
function rcSpoonHTML(){
  const s = LG.spoons || [];
  if (!s.length) return "";
  const est = s.filter(x => !x.final).map(x => x.y);
  return `<section class="lg-sec" aria-label="${t("records.spoon.title")}">
    <h2 class="bp-hd">${t("records.spoon.title")}<span>${t("records.spoon.sub")}</span></h2>
    <ul class="rc-shelf spoons">${s.map(x => rcShelfItem(RC_SPOON, x)).join("")}</ul>
    ${est.length ? `<p class="rc-tally"><span>${t("records.spoon.est", {ys: est.join(", ")})}</span></p>` : ""}
  </section>`;
}

/* A record's number and its name, shared with My recap's own lines (myrecap.js). */
const lgRecordValue = f => ({high: lgPts(f.v), blow: `+${lgPts(f.v)}`, streak: f.n, pf: lgPts(f.v), bestrec: `${f.w}–${f.l}`,
  low: lgPts(f.v), robbed: lgPts(f.v), stole: lgPts(f.v), lstreak: f.n, worstrec: `${f.w}–${f.l}`, lasts: `${f.n}×`})[f.k];
const lgRecordLabel = k => ({high: t("records.k.high"), blow: t("records.k.blow"), streak: t("records.k.streak"), pf: t("records.k.pf"),
  bestrec: t("records.k.bestrec"), low: t("records.k.low"), robbed: t("records.k.robbed"), stole: t("records.k.stole"),
  lstreak: t("records.k.lstreak"), worstrec: t("records.k.worstrec"), lasts: t("records.k.lasts")})[k];

/* One record card: what it is, the number, whose it is (the manager), and the team and when. */
function lgRecordHTML(f, id){
  const val = lgRecordValue(f), label = lgRecordLabel(f.k);
  if (val == null) return "";
  const ids = f.ids || [f.id];
  const who = f.ids ? f.ids.map((x, i) => lgHolder((f.mgrs || [])[i], x)).join(", ") : lgHolder(f.mgr, f.id, f.name);
  // Under the manager, the team it was: the name it had that season, or today's for an all-time record.
  const team = f.name ? t("records.as", {name: esc(f.name.trim())}) : f.mgr && f.id != null ? lgName(f.id) : "";
  const gone = !f.mgr && f.id == null && !f.ids ? t("records.gone") : "";
  const when = f.wk ? t("records.when", {y: f.y, wk: f.wk}) : f.y ? String(f.y) : f.w != null ? t("records.alltime") : "";
  const d = [team || gone, when].filter(Boolean).join(", ");
  return `<div class="rc-card${id != null && ids.includes(id) ? " me" : ""}"><span class="rc-k">${label}</span><span class="rc-v">${val}</span>
    <span class="rc-t">${who}</span>${d ? `<span class="rc-d">${d}</span>` : ""}</div>`;
}

function lgHallHTML(kind, id){
  // Titles are the trophy case's and last places the spoon case's; the halls do not count them twice.
  const list = (LG.book[kind] || []).filter(f => f.k !== "titles" && f.k !== "lasts");
  if (!list.length) return "";
  const title = kind === "fame" ? t("records.fame") : t("records.shame");
  return `<section class="lg-sec rc-${kind}" aria-label="${title}">
    <h2 class="bp-hd">${title}</h2>
    <div class="rc-grid">${list.map(f => lgRecordHTML(f, id)).join("")}</div>
  </section>`;
}

/* This week > Records: the same page for every reader. */
function lgRecordsPageHTML(){
  if (!lgUseYahoo()) return `<div class="wrap"><p class="lg-none">${t("league.none")}</p></div>`;
  return `<div class="wrap">${lgPageHead(t("league.page.sub", {y: LG.since}))}<div class="lg rc">
    <div class="lg-col">${rcHeadToHeadHTML()}</div>
    <div class="lg-col">${rcTrophyHTML()}${rcSpoonHTML()}</div>
    <div class="rc-halls">${lgHallHTML("fame", null)}${lgHallHTML("shame", null)}</div>
  </div></div>`;
}

/* The series split by kind of game, from `a`'s side: regular season, playoffs, consolation, each only
   when they met in it (league_back.MEET_KIND). A long series reads as a mistake until the playoff
   games in it are visible (David, 2026-09-27: Lateef and Theo, 16 meetings). */
function rcSplitHTML(a, b){
  const m = (lgH2H(a, b) || {}).m || [];
  const kinds = [[0, t("records.split.reg")], [1, t("records.split.po")], [2, t("records.split.cons")]];
  const rows = kinds.map(([k, label]) => {
    const g = m.filter(x => (x[3] || 0) === k);
    if (!g.length) return "";
    const w = g.filter(x => x[2] > 0).length, l = g.filter(x => x[2] < 0).length, tie = g.length - w - l;
    return `<dt>${label}</dt><dd>${tie ? `${w}–${l}–${tie}` : `${w}–${l}`}</dd>`;
  }).join("");
  return rows ? `<div class="rc-split"><p>${t("records.split.head", {a: lgMgr(a)})}</p><dl>${rows}</dl></div>` : "";
}

/* A pair's grudge card in the sheet, its margins toggle redrawing the card in place. */
function rcOpenPair(a, b, originEl){
  const d = document.getElementById("modal");
  d.innerHTML = `<div class="dr-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <h3 id="rc-sheet-title" class="bp2-sheet-t">${t("records.h2h.sheet", {a: lgMgr(a), b: lgMgr(b)})}</h3>
    </div><div class="dr-body bp2-sheet rc-sheet">${lgGrudgeCardHTML(a, b)}${rcSplitHTML(a, b)}</div>`;
  d.querySelector(".rc-sheet").addEventListener("click", e => {
    const btn = e.target.closest("[data-lgmargins]");
    if (!btn) return;
    const card = btn.closest(".bp-gcard");
    LG_MARGINS = !LG_MARGINS;
    card.outerHTML = lgGrudgeCardHTML(Number(card.dataset.a), Number(card.dataset.b));
  });
  showModal(d, originEl, "rc-sheet-title");
}

/* A manager chip redraws the head to head alone, so the shelves beside it never move. */
function wireRecords(v){
  const root = v.querySelector(".rc");
  if (!root) return;
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-rcmgr],[data-rcpair]");
    if (!b) return;
    if (b.dataset.rcmgr){
      RC_MGR = Number(b.dataset.rcmgr);
      root.querySelector(".rc-hh").outerHTML = rcHeadToHeadHTML();
      root.querySelector(`[data-rcmgr="${RC_MGR}"]`)?.focus();
    } else rcOpenPair(rcPicked(), Number(b.dataset.rcpair), b);
  });
}
