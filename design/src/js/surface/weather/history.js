/* The history lines under a Weather game (2026-09-26, casual wording the same day): for each
   condition the game meets (data/wxhistory.js), two questions in plain words.
     Does it matter?                 "Yes. Players score fewer points than usual: QB −1.5 · K −0.7"
     Already in our projections?     "Yes, since Sep 26." / "Not yet." / "We don't project kickers."
   The build answers both (design/wx_history.py); this file only words them. No stats talk on the
   card and no verdict about a player; sample sizes and ranges sit behind "Why". */
const wtSigned = v => Math.abs(v) < 0.05 ? "0.0" : (v > 0 ? "+" : "−") + Math.abs(v).toFixed(1);
const wtPosWord = pos => ({QB: t("weather.pos.qb"), RB: t("weather.pos.rb"), WR: t("weather.pos.wr"),
  TE: t("weather.pos.te"), K: t("weather.pos.k")})[pos] || esc(pos);
const wtWhere = cond => ({dome: t("weather.where.dome"), wind: t("weather.where.wind"),
  cold: t("weather.where.cold"), precip: t("weather.where.precip")})[cond] || "";

function wtHistHead(cond){
  const th = LIVE_WX_HISTORY.thresholds || {};
  if (cond === "dome") return t("weather.hist.dome");
  if (cond === "wind") return t("weather.hist.wind", {mph: th.wind_mph});
  if (cond === "cold") return t("weather.hist.cold", {f: th.cold_f});
  return t("weather.hist.precip");
}

/* No position passed: say so, then the closest one and why it fell short, in plain words. */
function wtNoEffect(s, cond){
  if (!s.top) return t("weather.hist.none");
  if (s.top.reason !== "rolling") return `${t("weather.hist.none")} ${t("weather.hist.none.noisy")}`;
  const args = {who: wtPosWord(s.top.pos), where: wtWhere(cond)};
  return `${t("weather.hist.none")} ${s.top.mean >= 0 ? t("weather.hist.none.rollingMore", args) : t("weather.hist.none.rollingFewer", args)}`;
}

function wtMatters(s, cond){
  if (!s.matters.length) return wtNoEffect(s, cond);
  const rest = s.unproven.length ? ` ${t("weather.hist.unproven", {list: s.unproven.map(wtPosWord).join(", ")})}` : "";
  if (s.matters.length === 1){
    const c = s.matters[0], args = {who: wtPosWord(c.pos), n: Math.abs(c.mean).toFixed(1)};
    return (c.mean < 0 ? t("weather.hist.oneFewer", args) : t("weather.hist.oneMore", args)) + rest;
  }
  const neg = s.matters.every(c => c.mean < 0), pos = s.matters.every(c => c.mean > 0);
  const lead = neg ? t("weather.hist.yesFewer") : pos ? t("weather.hist.yesMore") : t("weather.hist.yesMixed");
  return `${lead} <span class="wt-hx">${s.matters.map(c => `${esc(c.pos)} ${wtSigned(c.mean)}`).join(" · ")}</span>.${rest}`;
}

/* "Already in our projections?" from the projections' weather_adjust block; "" without it. */
function wtInProj(s){
  const p = s.inproj;
  if (!p || !LIVE_WX_HISTORY.since) return "";
  const since = new Date(`${LIVE_WX_HISTORY.since}T12:00:00Z`).toLocaleDateString([], {month: "short", day: "numeric", timeZone: "UTC"});
  const parts = [];
  if (p.yes.length && !p.no.length) parts.push(t("weather.hist.inproj.yes", {since}));
  else if (p.no.length && !p.yes.length) parts.push(t("weather.hist.inproj.no"));
  else if (p.yes.length){
    parts.push(t("weather.hist.inproj.someYes", {list: p.yes.map(wtPosWord).join(", "), since}));
    parts.push(t("weather.hist.inproj.someNo", {list: p.no.map(wtPosWord).join(", ")}));
  }
  if (p.kickers) parts.push(t("weather.hist.inproj.kickers"));
  return parts.join(" ");
}

function wtHistLineHTML(cond, r){
  const s = wtSummary(cond);
  const note = cond === "precip" ? `<p class="wt-hn">${t("weather.hist.precipNote", {pct: r.fc.precip_pct})}</p>` : "";
  const q = (label, answer) => `<p class="wt-hq"><em>${label}</em> <span>${answer}</span></p>`;
  const inproj = wtInProj(s);
  const why = s.why.map(c => `<li>${t("weather.hist.why.cell", {pos: esc(c.pos), n: c.n, lo: wtSigned(c.lo), hi: wtSigned(c.hi)})}</li>`).join("");
  return `<div class="wt-hl">
      <div class="wt-hh">${wtHistHead(cond)}</div>${note}
      ${q(t("weather.hist.q.matters"), wtMatters(s, cond))}
      ${inproj ? q(t("weather.hist.q.inproj"), inproj) : ""}
      <details class="wt-why"><summary>${t("weather.hist.why")}</summary>
        <p>${t("weather.hist.why.note")}</p><ul>${why}</ul></details>
    </div>`;
}

/* Every line a game gets, or "" when it meets none or there is no backtest. */
function wtHistHTML(r){
  const lines = wtConditions(r).map(c => wtHistLineHTML(c, r));
  return lines.length ? `<div class="wt-hist">${lines.join("")}</div>` : "";
}

/* The footnote, once per view, only when there is a backtest to explain. */
function wtHistFootHTML(){
  if (!wtHistOk()) return "";
  const s = LIVE_WX_HISTORY.seasons || [];
  return `<p class="wt-foot">${t("weather.hist.foot", {from: s[0] || "", to: s[s.length - 1] || ""})}</p>`;
}
