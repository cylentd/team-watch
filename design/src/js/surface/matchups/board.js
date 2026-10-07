/* ============================== START/SIT: THE MATCHUP BOARD ==============================
   The middle card (2026-10-03): for one position, the four offenses facing the defenses that give up
   the most to it this week (Best) and the four facing the ones that give up the least (Worst).
   A bar is points allowed per game at that position, a tick on it the league average, so a row reads
   against the middle of the league and not against the other rows. Every number is ff-jarvis's
   (LIVE_SSB.board, design/startsit_board.py); the page only draws it. A row opens nothing in v1.
   A position without a block gets no tab, and with none at all (or without LIVE_SSB) no card. */
const SS_BPOS = ["QB", "RB", "WR", "TE"];
let SS_BTAB = "";   // the tab the reader chose; until then the first pick's position

const ssBoardOk = b => !!b && typeof b.avg === "number" && [...(b.best || []), ...(b.worst || [])].some(r => typeof r.pts === "number");
const ssBoardTabs = () => ssSB() && ssSB().board ? SS_BPOS.filter(p => ssBoardOk(ssSB().board[p])) : [];

function ssBoardPos(){
  const tabs = ssBoardTabs(), first = ssCols()[0], want = SS_BTAB || (first ? first.p.pos : "");
  return tabs.includes(want) ? want : tabs[0] || "";
}

function ssBoardRowHTML(r, scale, tone){
  return `<li class="ssv-br ${tone}"><b class="ssv-bt">${esc(r.team)}</b><span class="ssv-bo">${t("startsit.board.vs", {opp: esc(r.opp)})}</span>
    <span class="ssv-bar" style="--w:${(r.pts / scale * 100).toFixed(1)}%"><i></i></span><em>${r.pts.toFixed(1)}</em></li>`;
}

function ssBoardListHTML(title, rows, tone, scale, avg){
  return `<div class="ssv-bl"><h4 class="lbl" title="${t("startsit.board.mark")}">${title}<span>${t("startsit.board.cols")}</span></h4>
    <ol class="ssv-bol" style="--avg:${(avg / scale * 100).toFixed(1)}%">${rows.map(r => ssBoardRowHTML(r, scale, tone)).join("")}</ol></div>`;
}

/* The position's best spot: the starter with the softest matchup, ff-jarvis's `best` (the Digest's
   Matchups card), with its reasons and any teammate out. Not a take, so it carries no START. */
function ssSpotHTML(pos){
  const s = ((typeof LIVE_STARTSIT !== "undefined" && LIVE_STARTSIT && LIVE_STARTSIT.best) || []).find(r => r.pos === pos);
  if (!s) return "";
  const out = ((ssSB() && ssSB().out) || {})[s.slug] || [];
  const bits = [esc(muVs(s)), ...s.why.slice(0, 2).map(esc),
    ...out.slice(0, 2).map(o => t("startsit.board.out", {n: esc(nameInitial(o.n)), s: esc(o.s)}))];
  return `<button type="button" class="ssv-spot" data-ssprof="${esc(s.slug)}" title="${t("startsit.board.mark")}">
    <span class="lbl">${t("startsit.board.spot")}</span><span class="xf-head mu-hd">${avatarHTML(s)}</span>
    <span class="mu-nm"><b>${esc(nameInitial(s.n))}</b><span>${bits.join(" · ")}</span></span><em>${s.pts.toFixed(1)}</em></button>`;
}

function ssBoardInnerHTML(){
  const pos = ssBoardPos();
  if (!pos) return "";
  const b = ssSB().board[pos], rows = k => (b[k] || []).filter(r => typeof r.pts === "number");
  const scale = Math.max(b.avg, ...rows("best").map(r => r.pts), ...rows("worst").map(r => r.pts)) || 1;
  return `<div class="ssv-h"><h3>${t("startsit.board.title", {pos})}</h3></div>
    <div class="setrow" role="group" aria-label="${t("startsit.board.tabs")}">${ssBoardTabs().map(p =>
      `<button type="button" class="chip" data-ssbpos="${p}" aria-pressed="${pos === p}">${p}</button>`).join("")}</div>
    ${ssSpotHTML(pos)}
    <div class="ssv-bls">${ssBoardListHTML(t("startsit.board.best"), rows("best"), "best", scale, b.avg)}${ssBoardListHTML(t("startsit.board.worst"), rows("worst"), "worst", scale, b.avg)}</div>
    <p class="ssv-key"><i aria-hidden="true"></i>${t("startsit.board.avg", {pts: b.avg.toFixed(1)})}</p>`;
}

function ssBoardHTML(){
  const inner = ssBoardInnerHTML();
  return inner ? `<section class="ssv-card ssv-board" id="ssv-board" aria-label="${t("startsit.board.title", {pos: ssBoardPos()})}">${inner}</section>` : "";
}

/* A tab repaints the card in place, so the page keeps its scroll and the Takes under it stay put. */
function ssWireBoard(v){
  const el = v.querySelector("#ssv-board");
  if (!el) return;
  el.addEventListener("click", e => {
    const sp = e.target.closest("[data-ssprof]");
    const s = sp && (LIVE_STARTSIT.best || []).find(r => r.slug === sp.dataset.ssprof);
    if (s) return openProfile({n: s.n, pos: s.pos, team: s.team, slug: s.slug}, sp);
    const b = e.target.closest("[data-ssbpos]");
    if (!b || b.dataset.ssbpos === ssBoardPos()) return;
    SS_BTAB = b.dataset.ssbpos;
    el.innerHTML = ssBoardInnerHTML();
    el.setAttribute("aria-label", t("startsit.board.title", {pos: SS_BTAB}));
    el.querySelector(`[data-ssbpos="${SS_BTAB}"]`)?.focus();
  });
}
