/* ------------------------------------------------------------------
   PREVIEW — This week > Preview (2026-09-29). One game a screen: Claude's call on it, its score beside
   the market's, and the fantasy players it moves. A swipe (or the arrows by the matchup) turns the game; the
   day marker above says Thursday, Sunday or Monday, one dot a game, and a tap on a day jumps to it.
   The take is opinion and the footer says so once; the numbers in it are checked against ff-jarvis's.

   Data: data/preview.js. Colour map: --up / --down are a player's call (beats / falls short of his
   projection), --sky is rain that moves scoring, --down an out player; every other number is --ink.
------------------------------------------------------------------ */
const pvKick = iso => new Date(iso).toLocaleString([], {weekday: "short", hour: "numeric", minute: "2-digit"});
const PV_CALL = {up: "▲", down: "▼", hold: "●"};
const pvCallWord = c => ({up: t("preview.call.up"), down: t("preview.call.down"), hold: t("preview.call.hold")})[c];
let PV_ENTER = "";   // the side the card slides in from after a turn; "" on a plain draw

function pvDaysHTML(i){
  return `<div class="pv-days" role="group" aria-label="${t("preview.days.label")}">${pvDays().map(d => {
    const on = d.idx.includes(i);
    return `<button class="pv-day${on ? " on" : ""}" data-pvgo="${d.idx[0]}" aria-label="${t("preview.days.jump", {day: esc(d.day)})}">
      <b>${esc(d.day)}</b><span class="pv-dots" aria-hidden="true">${d.idx.map(j => `<i class="${j === i ? "on" : ""}"></i>`).join("")}</span></button>`;
  }).join("")}</div>`;
}

/* Claude's score over the market's, winner first; the market row is the implied totals, to the half point. */
function pvScoreHTML(g){
  const p = g.take.pick, w = p.winner, l = w === g.home ? g.away : g.home;
  const mk = g.implied ? `<div class="pv-sc mk"><span>${t("preview.market")}</span><b>${esc(w)} ${g.implied[w]}</b><b>${esc(l)} ${g.implied[l]}</b></div>` : "";
  return `<div class="pv-score"><div class="pv-sc"><span>${t("preview.claude")}</span><b>${esc(w)} ${p.score[w]}</b><b>${esc(l)} ${p.score[l]}</b></div>${mk}</div>`;
}

function pvChipsHTML(g){
  const rain = g.rain ? `<span class="pv-chip rain">${t("preview.rain", {n: g.rain})}</span>` : "";
  /* Who is out is one line, not a chip each: three chips wrapped to a second row on a phone (NYJ @ CHI, week 4). */
  const out = g.out.length ? `<span class="pv-out"><b>${t("preview.out")}</b>${g.out.map(m => shortName(m.n)).join(" · ")}</span>` : "";
  return rain || out ? `<div class="pv-chips">${rain}${out}</div>` : "";
}

function pvPlayerHTML(p, j){
  return `<li><button class="pv-p" data-pvp="${j}">
    <span class="pv-face">${headHTML(p)}</span>
    <span class="pv-call ${p.call}" aria-label="${pvCallWord(p.call)}">${PV_CALL[p.call]}</span>
    <span class="pv-pn">${shortName(p.n)}<small>${esc(p.pos)} · ${esc(p.team)}</small></span>
    <span class="pv-pj">${p.proj.toFixed(1)}</span>
    <span class="pv-pw">${esc(p.why)}</span></button></li>`;
}

/* Prev and Next flank the matchup, so turning costs no row of its own on a phone. */
function pvCardHTML(g){
  const i = pvIndex(), n = pvGames().length;
  const kick = pvDone(g) ? t("preview.kicked", {kick: pvKick(g.kickoff)}) : pvKick(g.kickoff);
  const top = `<header class="pv-top">
    <button class="pv-arrow" data-pvstep="-1"${i === 0 ? " disabled" : ""} aria-label="${t("preview.prev")}">‹</button>
    <b class="pv-mt" aria-label="${t("preview.count", {i: i + 1, n})}">${esc(g.away)} @ ${esc(g.home)}</b>
    <button class="pv-arrow" data-pvstep="1"${i === n - 1 ? " disabled" : ""} aria-label="${t("preview.next")}">›</button>
    <span class="pv-ko">${kick}</span></header>`;
  if (!g.take) return `<article class="pv-card${PV_ENTER}" data-pvswipe>${top}
    <p class="pv-none">${t("preview.notake")}</p>${pvChipsHTML(g)}</article>`;
  const k = g.take;
  return `<article class="pv-card${PV_ENTER}" data-pvswipe>
    <div class="pv-call-side">${top}
      <h2 class="pv-head">${esc(k.head)}</h2>
      <p class="pv-lean">${esc(k.lean)}</p>
      ${pvScoreHTML(g)}
      <p class="pv-vs">${esc(k.vs)}</p>
      ${pvChipsHTML(g)}
      <p class="pv-risk"><b>${t("preview.risk")}</b><span>${esc(k.risk)}</span></p>
    </div>
    <ul class="pv-pl">${k.players.map(pvPlayerHTML).join("")}</ul>
  </article>`;
}

function pvViewHTML(){
  const gs = pvGames();
  if (!gs.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("preview.empty.title")}</b><span>${t("preview.empty.sub")}</span></div></div></div>`;
  const i = pvIndex();
  const html = `<div class="wrap pv">
    ${pvDaysHTML(i)}
    ${pvCardHTML(gs[i])}
    <p class="pv-foot">${t("preview.foot")}</p>
  </div>`;
  PV_ENTER = "";
  return html;
}

/* A turn redraws the view with the new card sliding in from the side it came from. */
function pvTurn(d){
  if (!pvStep(d)) return;
  PV_ENTER = d > 0 ? " in-r" : " in-l";
  render();
}

function wirePreview(v){
  v.querySelectorAll("[data-pvstep]").forEach(b => b.addEventListener("click", () => pvTurn(+b.dataset.pvstep)));
  v.querySelectorAll("[data-pvgo]").forEach(b => b.addEventListener("click", () => {
    const to = +b.dataset.pvgo;
    if (to !== pvIndex()) pvTurn(to - pvIndex());
  }));
  const g = pvGames()[pvIndex()];
  v.querySelectorAll("[data-pvp]").forEach(el => el.addEventListener("click", () => {
    const p = g && g.take && g.take.players[+el.dataset.pvp];
    if (p) openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, el);
  }));
  // A horizontal swipe turns the game; a mostly-vertical drag is a scroll and is left alone (board.js).
  const card = v.querySelector("[data-pvswipe]");
  if (!card) return;
  let x0 = null, y0 = 0;
  card.addEventListener("touchstart", e => { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, {passive: true});
  card.addEventListener("touchend", e => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    x0 = null;
    if (Math.abs(dx) > 48 && Math.abs(dx) > 1.5 * Math.abs(dy)) pvTurn(dx < 0 ? 1 : -1);
  });
}
