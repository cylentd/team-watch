/* ONE LINE, THE ROW THE PLAYER SHEET AND PREVIEW SHARE (2026-10-03). The market and today's line,
   Higher and Lower (a touchdown: Yes), then his last four games against that line: lime where the
   game cleared it (over the line, one score for a touchdown), faded when the game is from an earlier
   season, "N of 4", and the model's chance small at the end, only when the model prices the line
   (Longest reception it does not). A tap on a side puts the line on the slip at that side; the same
   side again takes it off. One player can feed several legs. */
const SL_HIST = 4;

/* The line in force: Underdog's own when the reader is on Underdog and it has one, else the row's. */
function slLine(p){
  const u = PARLAY_BOOK === "underdog" ? ud(p) : null;
  return u && typeof u.line === "number" ? u.line : p.line;
}

/* The model's call at that line, or null: Underdog's pick and confidence; the model's own side of
   its P(over) at the row's own line ("lower 75%" for a 25% over, as Underdog words it); a
   touchdown's P(score). */
function slModel(p){
  const num = x => typeof x === "number";
  if (p.mkt === "TD") return num(p.model) ? {side: "higher", pct: Math.round(p.model)} : null;
  const u = PARLAY_BOOK === "underdog" ? udPick(p) : null;
  if (u && !u.synthetic && u.pick && num(u.conf)) return {side: u.pick, pct: Math.round(u.conf)};
  return num(p.model) && slLine(p) === p.line ? {side: p.model >= 50 ? "higher" : "lower", pct: Math.round(Math.max(p.model, 100 - p.model))} : null;
}

const slCleared = (p, line, v) => typeof v === "number" && (p.mkt === "TD" ? v >= 1 : typeof line === "number" && v > line);

/* His last four games in this stat; an entry may be null (no catch logged for Longest reception). */
function slHist(p){
  const log = LIVE_MARKET && LIVE_MARKET.logs && LIVE_MARKET.logs[slSlug(p)];
  const vals = log && log.g && log.v ? log.v[p.mkt] : null;
  if (!vals || !vals.length) return [];
  const k0 = Math.max(0, vals.length - SL_HIST);
  return vals.slice(k0).map((v, k) => { const g = log.g[k0 + k] || []; return {v, g, old: g[0] < BUILD_SEASON}; });
}

function slHistHTML(p, line, m){
  const h = slHist(p), known = h.filter(x => typeof x.v === "number");
  const md = m ? `<small class="sl-md">${p.mkt === "TD" ? t("slips.line.modelTd", {p: m.pct})
    : t("slips.line.model", {side: m.side === "lower" ? t("slips.side.lower") : t("slips.side.higher"), p: m.pct})}</small>` : "";
  if (!known.length) return md ? `<span class="sl-hist">${md}</span>` : "";
  const cells = h.map(x => `<i class="${slCleared(p, line, x.v) ? "hit" : ""}${x.old ? " old" : ""}"${x.g.length ? ` title="${x.g[0]} wk${x.g[1]}${x.g[2] ? " vs " + esc(x.g[2]) : ""}"` : ""}>${typeof x.v === "number" ? fmt2(x.v) : ""}</i>`).join("");
  const hit = known.filter(x => slCleared(p, line, x.v)).length;
  return `<span class="sl-hist">${cells}<em>${t("slips.line.of", {hit, n: known.length})}</em>${md}</span>`;
}

function slLineHTML(i){
  const p = PROPS[i], line = slLine(p), td = p.mkt === "TD", on = SLIP.includes(i), side = on ? slipSide(i) : null;
  const btn = (s, label) => `<button type="button" class="sl-side ${s}" data-slpick="${i}" data-side="${s}" aria-pressed="${side === s}">${label}</button>`;
  return `<div class="sl-ln${on ? " on" : ""}">
      <span class="sl-mk">${esc(MKT[p.mkt] || p.mkt)}${!td && line != null ? ` <b>${line}</b>` : ""}</span>
      <span class="sl-sides">${td ? btn("higher", t("slips.side.yes")) : btn("higher", t("slips.side.higher")) + btn("lower", t("slips.side.lower"))}</span>
      ${slHistHTML(p, line, slModel(p))}
    </div>`;
}

/* His longest catch in each of his last four games, history only (plan update 2026-10-03: no book's
   Longest reception line can be read, so no line, no sides, no "N of 4"). A game with no catch
   logged is a dash; no log at all, no row. */
function slLongHTML(slug){
  const log = LIVE_MARKET && LIVE_MARKET.logs && LIVE_MARKET.logs[slug];
  const vals = log && log.g && log.v && log.v.LONG;
  if (!vals || !vals.some(v => typeof v === "number")) return "";
  const k0 = Math.max(0, vals.length - SL_HIST);
  const cells = vals.slice(k0).map((v, k) => { const g = log.g[k0 + k] || [];
    return `<i class="${g[0] < BUILD_SEASON ? "old" : ""}"${g.length ? ` title="${g[0]} wk${g[1]}"` : ""}>${typeof v === "number" ? fmt2(v) : "–"}</i>`; }).join("");
  return `<div class="sl-ln sl-long"><span class="sl-mk">${t("slips.line.longest")}</span><span class="sl-hist">${cells}</span></div>`;
}

/* A side tapped, from the board's sheet or Preview: the slip changes, the view behind redraws (its
   tray and "on slip" marks), an open sheet redraws in place, and an added pick flies to the tray. */
function slPick(btn){
  const i = +btn.dataset.slpick, side = btn.dataset.side, from = btn.getBoundingClientRect();
  const sel = `[data-slpick="${i}"][data-side="${side}"]`, inSheet = !!btn.closest("#legsheet");
  const on = slipSet(i, side);
  const y = window.scrollY; render(); window.scrollTo(0, y);
  if (inSheet) lsRefresh(sel); else document.querySelector(`#view ${sel}`)?.focus({preventScroll: true});
  if (on) betsFly(from, PROPS[i].n); else betsLand(SLIP.length);
}
