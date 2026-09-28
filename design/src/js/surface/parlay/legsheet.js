/* THE LEG SHEET (2026-09-27): one leg, read in one screen. Tapping a pick on a slip, the ⓘ on a
   Build line, or a row of the TD board opens it from the bottom edge, where the thumb already is.
   Top to bottom, the order a bet is read in:

     1. who, the call, the model's chance -- and on one line the model's number against the line
        and the book's own chance
     2. the last ten games against the line, lime where the pick's side hit, and under them, when
        ff-jarvis sends per-game usage, the one stat that drives the bet
     3. three tiles: what the bet rests on (legtiles.js)
     4. the matchup as one line
     5. Add to slip -- the same path a tap on a Build line takes (builder/wire.js betsToggleLeg)

   It lives outside #view (shell.html), so render() never rebuilds it under the reader. It pushes
   a history entry as it opens (chrome/layers.js), so the phone's Back closes it before the view. */
let LEG_SHEET = null;    // the PROPS index on screen, or null
let LEG_RETURN = null;   // what had focus before it opened
const legEl = () => document.getElementById("legsheet");

function legHeadHTML(p, s){
  const team = (TEAM_COLOURS[p.team] || [])[0], opp = legOpp(p);
  const where = [esc(p.pos || ""), p.team && opp ? t("legsheet.head.vs", {team: esc(p.team), opp: esc(opp)}) : esc(p.team || ""), esc(p.kick || "")].filter(Boolean).join(" · ");
  const tag = whyNotSlip(p, s.book === "underdog" && !s.synthetic ? udPick(p) : null);
  const book = s.synthetic ? t("legsheet.head.modelRead") : esc(s.where);
  const mu = typeof p.mu === "number" ? (p.mkt === "TD" ? p.mu.toFixed(2) : p.mkt === "RECS" ? p.mu.toFixed(1) : Math.round(p.mu)) : null;
  const bp = legBookPct(s);
  const model = [mu === null ? "" : p.mkt === "TD" ? t("legsheet.head.modelTd", {v: mu}) : t("legsheet.head.model", {v: mu}), s.line != null ? t("legsheet.head.line", {v: s.line}) : "",
                 bp !== null ? t("legsheet.head.book", {v: bp}) : ""].filter(Boolean).join(" · ");
  return `<header class="ls-head">
      <span class="tk-face ls-face"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(p)}</span>
      <div class="ls-who">
        <h3 id="ls-title">${esc(nameInitial(p.n))}</h3>
        <span class="ls-meta">${where}${tag ? " " + tag : ""}</span>
        <span class="ls-call">${legCall(p, s.book)}${book ? ` · ${book}` : ""}</span>
      </div>
      ${typeof s.pct === "number" ? `<b class="ls-pct"><span>${Math.round(s.pct)}<i>%</i></span><small>${t("legsheet.head.chance")}</small></b>` : ""}
    </header>
    ${model ? `<p class="ls-model">${model}</p>` : ""}`;
}

/* The last ten games as bars on one grid with the week under each and the driver under that, so
   a number sits under its own game at any width. The rule is the line; for a touchdown it sits
   at one score. */
function legBarsHTML(p, s, log){
  const vals = log.v[p.mkt] || [];
  if (!vals.length) return "";
  const td = p.mkt === "TD", line = td ? 1 : s.line, n = vals.length;
  // A fifth of headroom over the tallest bar holds its number.
  const top = Math.max(...vals, line || 0, 1) * 1.25, h = v => Math.max(2, v / top * 100).toFixed(1);
  const hit = vals.filter(v => legHitGame(p, s, v)).length;
  const avg = lsMean(vals), fmt = v => td || p.mkt === "RECS" ? v.toFixed(1) : Math.round(v);
  const cap = td ? t("legsheet.bars.scored", {hit, n}) : line == null ? "" : s.pick === "lower"
    ? t("legsheet.bars.under", {line, hit, n}) : t("legsheet.bars.over", {line, hit, n});
  const first = log.g[0], last = log.g[n - 1];
  const bars = vals.map((v, k) => {
    const g = log.g[k], yr = k > 0 && g[0] !== log.g[k - 1][0];
    return `<span class="ls-bar${legHitGame(p, s, v) ? " hit" : ""}${yr ? " yr" : ""}" style="--h:${h(v)}%" title="${g[0]} wk${g[1]}${g[2] ? " vs " + esc(g[2]) : ""}: ${v}"><em>${td ? (v >= 1 ? v : "") : fmt2(v)}</em></span>`;
  }).join("");
  const drv = legDriver(p, log);
  const row = (label, cells, cls) => `<span class="ls-lab">${label}</span>${cells.map(c => `<span class="ls-cell ${cls}">${c == null ? "" : c}</span>`).join("")}`;
  // A touchdown's rule sits between nothing and one score, so a game that scored rises through it.
  const rule = td ? h(0.5) : line == null ? null : h(line);
  return `<section class="ls-bars" style="--n:${n}${rule === null ? "" : `;--y:${rule}%`}" aria-label="${t("legsheet.bars.aria", {n})}">
      <div class="ls-cap"><b>${[cap, avg === null ? "" : t("legsheet.bars.avg", {v: fmt(avg)})].filter(Boolean).join(" · ")}</b>
        <span>${first[0] === last[0] ? t("legsheet.bars.spanOne", {y: first[0], a: first[1], b: last[1]}) : t("legsheet.bars.span", {y1: first[0], a: first[1], y2: last[0], b: last[1]})}</span></div>
      <div class="ls-grid">
        <span class="ls-lab ls-line">${line != null && !td ? `<i>${line}</i>` : ""}</span>
        <div class="ls-plot">${rule !== null ? `<i class="ls-rule"></i>` : ""}${bars}</div>
        ${row(t("legsheet.bars.wk"), log.g.map(g => g[1]), "wk")}
        ${drv ? row(drv.label, drv.vals, "drv") : ""}
      </div>
    </section>`;
}
const fmt2 = v => Number.isInteger(v) ? v : v.toFixed(1);

function legSheetHTML(i){
  const p = PROPS[i], s = legSide(p), log = legLog(p), inSlip = SLIP.includes(i);
  return `<button type="button" class="grab" data-legclose aria-label="${t("common.action.close")}"></button>
    ${legHeadHTML(p, s)}
    ${log ? legBarsHTML(p, s, log) : ""}
    ${legTilesHTML(p, log)}
    ${legMatchupHTML(p)}
    <button type="button" class="ls-add${inSlip ? " in" : ""}" data-legadd="${i}">${inSlip ? t("legsheet.action.remove") : t("legsheet.action.add")}</button>`;
}

function legSheetOpen(i, origin){
  const d = legEl();
  if (!d || !PROPS[i]) return;
  LEG_SHEET = i;
  LEG_RETURN = origin || document.activeElement;
  d.innerHTML = legSheetHTML(i);
  d.scrollTop = 0;
  d.classList.add("on");
  d.setAttribute("aria-hidden", "false");
  document.getElementById("legsheet-scrim").classList.add("on");
  d.querySelector("[data-legclose]").focus({preventScroll: true});
  layerPush("legsheet", legSheetShut);
}

/* The close itself; legSheetClose also takes back the history entry (layers.js). */
function legSheetShut(){
  const d = legEl();
  if (!d || LEG_SHEET === null) return;
  LEG_SHEET = null;
  d.classList.remove("on");
  d.setAttribute("aria-hidden", "true");
  document.getElementById("legsheet-scrim").classList.remove("on");
  const back = LEG_RETURN;
  LEG_RETURN = null;
  if (back && back.focus && back.isConnected) back.focus({preventScroll: true});
}
function legSheetClose(){ legSheetShut(); layerDone("legsheet"); }

/* Add or remove: the sheet steps aside first, so the pick's flight to the tray is seen. */
function legSheetAdd(i, btn){
  const from = btn.getBoundingClientRect();
  legSheetClose();
  betsToggleLeg(document.getElementById("view"), i, from);
}

/* Bound once: the sheet's markup is replaced on every open, its listeners are not. */
(() => {
  const d = legEl();
  if (!d) return;
  d.addEventListener("click", e => {
    if (e.target.closest("[data-legclose]")) return legSheetClose();
    const add = e.target.closest("[data-legadd]");
    if (add) legSheetAdd(+add.dataset.legadd, add);
  });
  d.addEventListener("keydown", e => {
    if (e.key !== "Tab") return;
    const f = [...d.querySelectorAll("button, summary")];
    if (e.shiftKey && document.activeElement === f[0]){ e.preventDefault(); f[f.length - 1].focus(); }
    else if (!e.shiftKey && document.activeElement === f[f.length - 1]){ e.preventDefault(); f[0].focus(); }
  });
  document.getElementById("legsheet-scrim").addEventListener("click", legSheetClose);
  document.addEventListener("keydown", e => { if (e.key === "Escape" && LEG_SHEET !== null) legSheetClose(); });
})();
