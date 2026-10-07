/* ============================== RECAP: ACCURACY ==============================
   The Accuracy tab (2026-10-05, FourthDown Lab audit: "Misses stay in the report"). Per week and position, our
   average miss beside FantasyPros' on the players both projected, then who was closer; the season to date
   above, with the scorecard's range. Misses are shown as they are, FantasyPros' wins included. Newest week
   first. Every number is the file's own (data/accuracy.js passes it through); a field the file lacks is a
   sentence saying so, never a zero. A card per subject, rows inside, none nested (DESIGN.md "Cards"). */

const acFmt = v => v.toFixed(2);
const acSigned = v => (v < 0 ? "−" : "") + Math.abs(v).toFixed(2);
const acPct = v => Math.round(v * 100) + "%";

/* Every key spelled out: assemble.py --check finds unused copy by scanning for literal lookups. */
const acWho = k => ({ours: t("weekrecap.acc.who.ours"), fp: t("weekrecap.acc.who.fp"), tie: t("weekrecap.acc.who.tie")})[k] || "";
const acModel = m => m === "pre-blend" ? t("weekrecap.acc.model.pre")
  : m === "blend" ? t("weekrecap.acc.model.blend") : m ? t("weekrecap.acc.model.other", {model: esc(m)}) : "";

const acColsHTML = () => `<div class="wr-ac-cols" aria-hidden="true"><span></span><span>${t("weekrecap.acc.ours")}</span><span>${
  t("weekrecap.acc.fp")}</span><span>${t("weekrecap.acc.closer")}</span></div>`;

/* One position: the two misses (the closer one lit), who was closer, and a line under it. */
function acRowHTML(pos, n, ours, fp, closer, under, extra){
  const num = (v, side) => v === null ? `<b class="wr-ac-v none">–</b>` : `<b class="wr-ac-v${closer === side ? " win" : ""}">${acFmt(v)}</b>`;
  const lab = pos === "ALL" ? t("weekrecap.acc.all") : pos;
  return `<div class="wr-ac-row" data-acpos="${pos}" data-closer="${closer || ""}"${extra || ""}>
    <span class="wr-ac-pos"><b>${lab}</b>${n === null ? "" : `<em>${t("weekrecap.acc.n", {n})}</em>`}</span>${num(ours, "ours")}${num(fp, "fp")
    }<span class="wr-ac-who ${closer || "none"}">${closer ? acWho(closer) : "–"}</span>${under ? `<p class="wr-ac-under">${under}</p>` : ""}</div>`;
}

/* The rank line, only for the numbers the file has. */
function acRankLine(r){
  const both = (a, b, f) => a !== null && b !== null ? [f(a), f(b)] : null;
  const rho = both(r.ours.rho, r.fp.rho, acFmt), hit = both(r.ours.hit, r.fp.hit, acPct);
  return [rho ? t("weekrecap.acc.rank", {o: rho[0], f: rho[1]}) : "",
    hit ? (r.hit_n === null ? t("weekrecap.acc.hitsAny", {o: hit[0], f: hit[1]}) : t("weekrecap.acc.hits", {n: r.hit_n, o: hit[0], f: hit[1]})) : ""]
    .filter(Boolean).join(" · ");
}

function acWeekHTML(w){
  const model = acModel(w.model), note = w.note ? `<p class="wr-ac-note">${esc(w.note)}</p>` : "";
  const rows = w.rows.map(r => acRowHTML(r.pos, r.n, r.ours.mae, r.fp.mae, r.closer, w.ranked ? acRankLine(r) : "")).join("");
  return `<section class="wr-card wr-ac-card" data-testid="accuracy-week" data-acweek="${w.week}"><div class="wr-chr"><h3 class="wr-ch">${
    t("weekrecap.acc.week", {n: w.week})}</h3>${model ? `<span class="wr-ac-model">${model}</span>` : ""}</div>${note}${acColsHTML()}${rows}${
    w.ranked ? "" : `<p class="wr-ac-none">${t("weekrecap.acc.rankNone")}</p>`}</section>`;
}

/* Under a season row: how far, and whether the range leaves 0 out (the file's rule: above 0, FantasyPros closer). */
function acSeasonUnder(r, level){
  if (r.d === null) return "";
  const gap = r.closer === "tie" ? "" : t("weekrecap.acc.by", {d: acFmt(Math.abs(r.d))});
  const ci = r.ci ? `${t("weekrecap.acc.ci", {level, lo: acSigned(r.ci[0]), hi: acSigned(r.ci[1])})} · ${
    r.clear ? t("weekrecap.acc.clear") : t("weekrecap.acc.noise")}` : t("weekrecap.acc.noCi");
  return [gap, ci].filter(Boolean).join(" · ");
}

function acSeasonHTML(s, level){
  const head = (sub) => `<div class="wr-chr"><h3 class="wr-ch">${t("weekrecap.acc.season")}</h3>${sub ? `<span class="wr-ac-model">${sub}</span>` : ""}</div>`;
  if (!s) return `<section class="wr-card wr-ac-card" data-acseason>${head("")}<p class="wr-ac-none">${t("weekrecap.acc.seasonNone")}</p></section>`;
  const rows = s.rows.map(r => acRowHTML(r.pos, r.n, r.maeOurs, r.maeFp, r.closer, acSeasonUnder(r, level),
    ` data-clear="${r.clear ? 1 : 0}"`)).join("");
  return `<section class="wr-card wr-ac-card" data-acseason>${head(t("weekrecap.acc.weeks", {range: s.range}))}${
    s.stale ? `<p class="wr-ac-note">${t("weekrecap.acc.stale", {range: s.range})}</p>` : ""}${acColsHTML()}${rows}</section>`;
}

/* The tab's body for acView's view. */
function acHTML(v){
  if (!v) return "";
  const weeks = v.missing.join(", ");
  const missing = v.missing.length ? `<p class="wr-strip">${v.missing.length > 1 ? t("weekrecap.acc.missingMany", {weeks}) : t("weekrecap.acc.missing", {weeks})}</p>` : "";
  return `<div class="wr-ac-body"><p class="wr-ac-how">${t("weekrecap.acc.how")}</p>${missing}${acSeasonHTML(v.season, v.ciLevel)}${
    v.weeks.map(acWeekHTML).join("")}</div>`;
}
