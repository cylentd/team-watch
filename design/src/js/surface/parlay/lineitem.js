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

const SL_TIERS = PT_TIERS;   // the one list, data/topcalls.js
const slTierWord = k => k === "very" ? t("slips.tier.very") : k === "confident" ? t("slips.tier.confident") : k === "slight" ? t("slips.tier.slight") : t("slips.tier.none");
/* The tier word, in Preview's looks: Slight grey, Confident lime text, Very confident a lime fill, with the
   chance of the model's side before it ("74% Confident", 2026-10-05): one vocabulary in Slips, Top calls and
   All lines. "No pick" has no chance to print. */
const slTierHTML = (k, q) => `<span class="sl-tp">${q && k !== "none" ? `<i class="sl-pc">${Math.round(q)}%</i>` : ""}<b class="sl-conf ${k}">${slTierWord(k)}</b></span>`;

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

/* Claude's call at the line shown, or null (2026-10-05, storyboard "Claude Calls" A): its side and one
   line of why, from ff-jarvis's claude_props. Found by player, market and the exact line value, so on
   Underdog a call made for another number gets nothing. A touchdown has no sides, so no call. */
function slClaude(p){
  const L = typeof LIVE_CLAUDE_PROPS !== "undefined" ? LIVE_CLAUDE_PROPS : null;
  const rows = L && L.calls && L.calls[slSlug(p)], line = slLine(p);
  const c = rows && p.mkt !== "TD" ? rows.find(r => r.mkt === p.mkt && r.line === line) : null;
  return c && (c.side === "higher" || c.side === "lower") ? {side: c.side, why: c.why || ""} : null;
}

/* Claude backs the model's outlined pick: lime. Any other call (the other side, or a line the model gave
   no pick) is ink. The model's tier word stays the only confidence word; Claude's is never shown. */
const slClaudeAgrees = (c, m) => !!c && !!m && !m.td && m.tier !== "none" && m.side === c.side;
const slClaudeBadge = (agree, more = "") => `<i class="sl-cb${agree ? " agree" : ""}${more}" aria-hidden="true">${t("slips.claude.c")}</i>`;

/* Higher and Lower, the model's side outlined; the tier word under that side ("No pick" under Lower).
   A line without a tier is just the two buttons. Claude's side wears a badge on its corner and is named
   "Higher, Claude picks this" to a screen reader. */
function slSidesHTML(i, m, side, c){
  const agree = slClaudeAgrees(c, m);
  const btn = (s, label) => {
    const mine = !!c && c.side === s;
    return `<button type="button" class="sl-side ${s}${m && m.side === s && m.tier !== "none" ? " pick" : ""}" data-slpick="${i}" data-side="${s}" aria-pressed="${side === s}"${mine ? ` aria-label="${t("slips.claude.name", {side: label})}"` : ""}>${label}${mine ? slClaudeBadge(agree) : ""}</button>`;
  };
  // "72% Very confident" is wider than one side, so it spans both under the buttons, to the right edge; "No pick"
  // has no chance and stays under Lower.
  const under = m && m.tier ? ["higher", "lower"].map(s => {
    const mine = m.tier === "none" ? s === "lower" : m.side === s;
    return `<span class="sl-under${mine && m.tier !== "none" ? " wide" : ""}">${mine ? slTierHTML(m.tier, m.q) : ""}</span>`;
  }).join("") : "";
  return `<span class="sl-sides">${btn("higher", t("slips.side.higher"))}${btn("lower", t("slips.side.lower"))}${under}</span>`;
}

function slLineHTML(i){
  const p = PROPS[i], line = slLine(p), td = p.mkt === "TD", on = SLIP.includes(i), side = on ? slipSide(i) : null, m = slModel(p), c = slClaude(p);
  const yes = `<span class="sl-sides"><button type="button" class="sl-side higher" data-slpick="${i}" data-side="higher" aria-pressed="${side === "higher"}">${t("slips.side.yes")}</button></span>`;
  return `<div class="sl-ln${on ? " on" : ""}${m && m.tier ? " tiered" : ""}">
      <span class="sl-mk">${esc(MKT[p.mkt] || p.mkt)}${!td && line != null ? ` <b>${line}</b>` : ""}</span>
      ${td ? yes : slSidesHTML(i, m, side, c)}
      ${slHistHTML(p, line, m)}
      ${c && c.why && !slClaudeAgrees(c, m) ? `<span class="sl-cwhy">${slClaudeBadge(false, " static")}<span>${esc(c.why)}</span></span>` : ""}
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
