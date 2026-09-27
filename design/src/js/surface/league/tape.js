/* ============================== LEAGUE: TALE OF THE TAPE (Yahoo back page) ==============================
   The team on screen against this week's opponent, as a fight card: the series score big, then one
   row per measure with the better side lit, then every meeting as a bar from a zero line, up when the
   team on screen won, as tall as the margin, ringed when it was a playoff game. */

const lgRec = r => r[2] ? `${r[0]}–${r[1]}–${r[2]}` : `${r[0]}–${r[1]}`;

/* The current run in the series from the team on screen's side: "W3", "L1", or "" before a meeting. */
function lgRun(m){
  if (!m || !m.length) return "";
  const won = x => x[2] > 0, last = won(m[m.length - 1]);
  let n = 0;
  for (let i = m.length - 1; i >= 0 && m[i][2] !== 0 && won(m[i]) === last; i--) n++;
  return `${last ? "W" : "L"}${n}`;
}

/* One measure: both sides' values, the better one lit. `better` is 1, -1 or 0 from the left side's view. */
const lgTapeRow = (label, l, r, better) =>
  `<span class="bp-tl${better > 0 ? " up" : ""}">${l}</span><span class="bp-tm">${label}</span><span class="bp-tr${better < 0 ? " up" : ""}">${r}</span>`;

function lgMeetsHTML(m){
  if (!m || !m.length) return "";
  const max = Math.max(...m.map(x => Math.abs(x[2])), 1);
  const bars = m.map((x, i) => `<i class="${x[2] > 0 ? "u" : "d"}${x[3] ? " po" : ""}" style="--h:${Math.max(3, 100 * Math.abs(x[2]) / max).toFixed(0)}%;--i:${i}"
    title="${t("league.tape.meet", {y: x[0], wk: x[1], m: (x[2] > 0 ? "+" : "") + x[2].toFixed(1)})}"></i>`).join("");
  return `<div class="bp-meets" role="img" aria-label="${t("league.tape.meetsAria", {n: m.length})}">${bars}</div>
    <div class="bp-ends"><span>${m[0][0]}</span><span>${t("league.tape.key")}</span><span>${m[m.length - 1][0]}</span></div>`;
}

function lgTapeHTML(id){
  const opp = id ? lgOpp(id) : null;
  const me = LG.teams.find(x => x.id === id), them = LG.teams.find(x => x.id === opp);
  if (!me || !them) return "";
  const h = lgH2H(id, opp) || {w: 0, l: 0, t: 0, m: []}, m = h.m || [];
  const po = m.filter(x => x[3]), pw = po.filter(x => x[2] > 0).length;
  const pct = r => sum(r) ? (r[0] + r[2] / 2) / sum(r) : 0, sum = r => r[0] + r[1] + r[2];
  const run = lgRun(m);
  const rows = [
    lgTapeRow(t("league.tape.season"), lgRec([me.w, me.l, me.t]), lgRec([them.w, them.l, them.t]), Math.sign(pct([me.w, me.l, me.t]) - pct([them.w, them.l, them.t]))),
    lgTapeRow(t("league.tape.all"), lgRec(me.all), lgRec(them.all), Math.sign(pct(me.all) - pct(them.all))),
    lgTapeRow(t("league.tape.titles"), me.titles.length, them.titles.length, Math.sign(me.titles.length - them.titles.length)),
    lgTapeRow(t("league.tape.lasts"), me.lasts.length, them.lasts.length, Math.sign(them.lasts.length - me.lasts.length)),
    po.length ? lgTapeRow(t("league.tape.playoffs"), `${pw}–${po.length - pw}`, `${po.length - pw}–${pw}`, Math.sign(2 * pw - po.length)) : "",
    run ? lgTapeRow(t("league.tape.run"), run[0] === "W" ? run : "", run[0] === "L" ? `W${run.slice(1)}` : "", run[0] === "W" ? 1 : -1) : "",
  ].join("");
  const big = (side, tid) => side && side.big ? t("league.rival.big", {team: lgName(tid), v: lgPts(side.big.v), y: side.big.y, wk: side.big.wk}) : "";
  const foot = m.length ? [big(h, id), big(lgH2H(opp, id), opp)].filter(Boolean).join(" ") : t("league.rival.first");
  return `<section class="lg-sec bp-tapesec" aria-label="${t("league.rival.aria")}">
    <h3 class="bp-hd">${t("league.tape.title")}<span>${t("league.tape.sub", {n: LG.week})}</span></h3>
    <div class="bp-tape">
      <div class="bp-vs"><span class="bp-va">${lgName(id)}</span>
        <span class="bp-vn">${h.t ? `${h.w}–${h.l}–${h.t}` : `${h.w}–${h.l}`}<small>${m.length ? t("league.tape.since", {y: m[0][0]}) : ""}</small></span>
        <span class="bp-vb">${lgName(opp)}</span></div>
      <div class="bp-tt">${rows}</div>
      ${lgMeetsHTML(m)}
      ${foot ? `<p class="bp-foot">${foot}</p>` : ""}
    </div>
  </section>`;
}
