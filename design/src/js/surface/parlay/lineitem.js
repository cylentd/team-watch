/* ONE LINE, THE ROW THE PLAYER SHEET AND PREVIEW SHARE (2026-10-03). The market and today's line,
   Higher and Lower (a touchdown: Yes), then his last four games against that line: lime where the
   game cleared it (over the line, one score for a touchdown), faded when the game is from an earlier
   season. The model's side gets a lime outline with its tier word under it (2026-10-05, storyboard
   "Prop Picks" A): Slight, Confident or Very confident, or "No pick" under Lower; the fill stays
   the reader's own pick. A touchdown has no side or tier, only "N% to score". The tier is
   ff-jarvis's (`tier`, `side` on the row and on each book, for that book's own line); the page never
   cuts one from the chance. A tap on a side puts the line on the slip at that side; the same side
   again takes it off. One player can feed several legs. */
const SL_HIST = 4;

/* The line in force: Underdog's own when the reader is on Underdog and it has one, else the row's. */
function slLine(p){
  const u = PARLAY_BOOK === "underdog" ? ud(p) : null;
  return u && typeof u.line === "number" ? u.line : p.line;
}

/* The row or book entry whose line slLine shows, and so whose tier belongs to that exact line:
   build.py puts `tier` on each book for the book's own line. */
const slSrc = p => PARLAY_BOOK === "underdog" && ud(p) && typeof ud(p).line === "number" ? ud(p) : p;

/* The model's call at the line shown, or null: a touchdown's P(score); a priced line's side, tier and
   the chance of that side (for ordering only); nothing when ff-jarvis sent no tier (an older producer,
   an Out player, Longest reception). */
function slModel(p){
  const num = x => typeof x === "number";
  if (p.mkt === "TD") return num(p.model) ? {td: true, pct: Math.round(p.model)} : null;
  const s = slSrc(p);
  if (!SL_TIERS.includes(s.tier)) return null;
  return {side: s.side === "lower" ? "lower" : "higher", tier: s.tier, q: num(s.model) ? Math.max(s.model, 100 - s.model) : 0};
}

const SL_TIERS = ["none", "slight", "confident", "very"];
const slTierWord = k => k === "very" ? t("slips.tier.very") : k === "confident" ? t("slips.tier.confident") : k === "slight" ? t("slips.tier.slight") : t("slips.tier.none");
/* The tier word, in Preview's looks: Slight grey, Confident lime text, Very confident a lime fill. */
const slTierHTML = k => `<b class="sl-conf ${k}">${slTierWord(k)}</b>`;

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
  const md = m && m.td ? `<small class="sl-md">${t("slips.line.modelTd", {p: m.pct})}</small>` : "";
  if (!known.length) return md ? `<span class="sl-hist">${md}</span>` : "";
  const cells = h.map(x => `<i class="${slCleared(p, line, x.v) ? "hit" : ""}${x.old ? " old" : ""}"${x.g.length ? ` title="${x.g[0]} wk${x.g[1]}${x.g[2] ? " vs " + esc(x.g[2]) : ""}"` : ""}>${typeof x.v === "number" ? fmt2(x.v) : ""}</i>`).join("");
  return `<span class="sl-hist">${cells}${md}</span>`;
}

/* Higher and Lower, the model's side outlined; the tier word under that side ("No pick" under Lower).
   A line without a tier is just the two buttons. */
function slSidesHTML(i, m, side){
  const btn = (s, label) => `<button type="button" class="sl-side ${s}${m && m.side === s && m.tier !== "none" ? " pick" : ""}" data-slpick="${i}" data-side="${s}" aria-pressed="${side === s}">${label}</button>`;
  const under = m && m.tier ? ["higher", "lower"].map(s => `<span class="sl-under">${(m.tier === "none" ? s === "lower" : m.side === s) ? slTierHTML(m.tier) : ""}</span>`).join("") : "";
  return `<span class="sl-sides">${btn("higher", t("slips.side.higher"))}${btn("lower", t("slips.side.lower"))}${under}</span>`;
}

function slLineHTML(i){
  const p = PROPS[i], line = slLine(p), td = p.mkt === "TD", on = SLIP.includes(i), side = on ? slipSide(i) : null, m = slModel(p);
  const yes = `<span class="sl-sides"><button type="button" class="sl-side higher" data-slpick="${i}" data-side="higher" aria-pressed="${side === "higher"}">${t("slips.side.yes")}</button></span>`;
  return `<div class="sl-ln${on ? " on" : ""}${m && m.tier ? " tiered" : ""}">
      <span class="sl-mk">${esc(MKT[p.mkt] || p.mkt)}${!td && line != null ? ` <b>${line}</b>` : ""}</span>
      ${td ? yes : slSidesHTML(i, m, side)}
      ${slHistHTML(p, line, m)}
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
