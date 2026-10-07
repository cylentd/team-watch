/* BUILD'S LINES (2026-09-29, storyboard v2 option A). One column under a heading per kickoff, one
   block per player, one row per line: the line, his last games against it, and the call.

   The bars carry the evidence the old meter only repeated: lime is a game that cleared the call's
   side (the leg sheet's meaning), and a game from an earlier season is faded, so a new role reads
   off the row. A line the book moved far from the model shows no chance: "Line moved". The line
   and its bars open the leg sheet; the call puts the pick in the slip. */
const BUILD_PAGE_SIZE = 12;   // players per page
/* The model's season: "2026 wk3" from ff-jarvis, else the viewer's year. */
const BUILD_SEASON = parseInt(LIVE_MARKET && LIVE_MARKET.model && LIVE_MARKET.model.through, 10) || new Date(NOW).getFullYear();

/* His last games in this stat as bars against the line. The scale tops out at twice the line, so
   one 244-yard day does not flatten every other bar; a touchdown's rule sits at one score. */
function buildGamesHTML(p, s, moved){
  const logs = LIVE_MARKET && LIVE_MARKET.logs, log = logs ? logs[p.slug || slugOf(p.n)] : null;
  const vals = log && log.v ? log.v[p.mkt] || [] : [];
  if (!vals.length) return `<span class="bl-g"></span>`;
  const td = p.mkt === "TD", line = td ? 0.5 : s.line;
  if (line == null) return `<span class="bl-g"></span>`;
  const top = td ? 2 : Math.max(line * 2, 1), pct = v => Math.max(4, Math.min(v, top) / top * 100).toFixed(0);
  const bars = vals.map((v, k) => {
    const g = log.g[k] || [], old = g[0] < BUILD_SEASON, hit = !moved && legHitGame(p, s, v);
    return `<i class="${hit ? "hit" : ""}${old ? " old" : ""}" style="--h:${pct(v)}%" title="${g[0]} wk${g[1]}: ${v}"></i>`;
  }).join("");
  return `<span class="bl-g" style="--y:${pct(line)}%" aria-hidden="true">${bars}</span>`;
}

function buildRowHTML(p){
  const i = PROPS.indexOf(p), s = legSide(p), moved = lineMoved(p, PARLAY_BOOK);
  const best = moved ? null : bestOdds(p, PARLAY_BOOK);
  const td = s.line == null;
  const ev = `<button type="button" class="more bl-ev" data-testid="parlay-line-ev" data-legsheet="${i}" aria-haspopup="dialog" aria-label="${t("parlay.more.sheet")}">
      <span class="bl-ln"><b>${td ? t("parlay.call.td") : s.line}</b><small>${td ? t("parlay.call.anytime") : MKT_SHORT[p.mkt]}</small>${best ? `<em data-testid="parlay-line-why">${esc(best)}</em>` : ""}</span>
      ${buildGamesHTML(p, s, moved)}</button>`;
  if (moved) return `<div class="bline moved" data-testid="parlay-line">${ev}
    <button type="button" class="more bl-call" data-testid="parlay-line-call" data-legsheet="${i}" title="${t("parlay.tag.staleTitle")}">${t("parlay.call.moved")}</button></div>`;
  const inSlip = SLIP.includes(i), lower = s.pick === "lower";
  const word = td ? t("parlay.call.scores") : PARLAY_BOOK === "dk" ? t("parlay.call.over") : lower ? t("parlay.call.lowerWord") : t("parlay.call.higherWord");
  // Longest reception is never priced (2026-10-03), so it is not "pending" either: no number.
  const pct = typeof s.pct === "number" ? `${s.pct}%` : p.mkt === "LONG" ? "" : t("parlay.call.pending");
  const price = PARLAY_BOOK === "dk" ? ` <i>${esc(fmtAm(s.price))}</i>` : "";
  // The model's tier word under the chance (2026-10-05): the one vocabulary Slips uses, only where the
  // model's side is the side this row calls.
  const m = td ? null : slModel(p), tier = m && PT_RANK[m.tier] && m.side === (lower ? "lower" : "higher") ? m.tier : "";
  return `<div class="bline" data-testid="parlay-line" data-prop="${i}" role="button" tabindex="0" aria-pressed="${inSlip}">${ev}
    <span class="bl-call ${lower ? "lower" : "higher"}" data-testid="parlay-line-call">${word}<b>${pct}${price}</b>${tier ? `<span class="bl-tier ${tier}" title="${t("slips.tier.mark")}">${slTierWord(tier)}</span>` : ""}</span></div>`;
}

/* The cornerback he draws this week, when ff-jarvis rates it an upgrade or a downgrade. */
function cbTagHTML(c){
  return c ? `<span class="tag ${c.v === "upgrade" ? "t-cbup" : "t-cbdn"}" title="${t("parlay.tag.cbTitle", {week: LIVE_MARKET && LIVE_MARKET.wrcb ? LIVE_MARKET.wrcb.week : "", v: esc(c.v), cb: esc(c.cb), why: esc(c.why)})}">${t("parlay.tag.cb", {dir: c.v === "upgrade" ? "↑" : "↓", name: esc(lastName(c.cb))})}</span>` : "";
}

/* Who and when once; OUT, Q, depth, new team, a thin record and his cornerback sit here. */
function buildPlayerHTML(rows){
  const p = rows[0], cb = (rows.find(r => r.cb) || {}).cb;
  const tag = whyNotSlip({...p, stale: 0, norole: 0}, null) + roleNoteTagHTML(p) + cbTagHTML(cb);
  return `<div class="bplayer ${p.mine ? "mine" : ""} ${p.flag === "out" ? "isout" : ""}" data-testid="parlay-bplayer">
    <div class="bp-who">${avatarHTML(p)}<span class="bp-name">${esc(nameInitial(p.n))}</span><span class="bp-meta">${esc(p.pos)} · ${esc(p.game)}</span>${tag}</div>
    ${rows.map(buildRowHTML).join("")}
  </div>`;
}

/* The sorted lines as kickoffs in kickoff order, each a list of players in the order their best
   line sorted. Moved lines sink to the bottom of any sort: their chance is not one to rank on. */
function buildGroups(lines){
  const rank = k => { const r = WINDOWS.findIndex(w => w.k === k); return r < 0 ? WINDOWS.length : r; };
  const wins = new Map();
  lines.forEach(p => {
    const k = p.win || "", m = wins.get(k) || wins.set(k, new Map()).get(k);
    (m.get(p.n) || m.set(p.n, []).get(p.n)).push(p);
  });
  return [...wins.keys()].sort((a, b) => rank(a) - rank(b)).map(k => ({
    w: WINDOWS.find(w => w.k === k) || null, players: [...wins.get(k).values()],
    n: lines.filter(p => (p.win || "") === k).length,
  }));
}

function buildListHTML(lines){
  const groups = buildGroups(lines), flat = groups.flatMap(g => g.players.map(rows => ({g, rows})));
  const pages = Math.max(1, Math.ceil(flat.length / BUILD_PAGE_SIZE)), page = Math.min(MKT_PAGE, pages);
  const shown = flat.slice((page - 1) * BUILD_PAGE_SIZE, page * BUILD_PAGE_SIZE);
  const body = groups.filter(g => shown.some(x => x.g === g)).map(g => `<section class="bl-group">
      ${g.w ? `<div class="tk-when bl-when"><h3>${esc(galGroupName(g.w))}</h3><span>${t("parlay.build.groupMeta", {kick: esc(g.w.kick || ""), n: g.n, s: g.n === 1 ? "" : "s"})}</span></div>` : ""}
      ${shown.filter(x => x.g === g).map(x => buildPlayerHTML(x.rows)).join("")}
    </section>`).join("");
  return {body, page, pages, players: flat.length};
}
