/* THE PLAYER SHEET (2026-10-03; it grew out of the leg sheet, legsheet.js, which Build's ⓘ still
   opens). A tap on a board row opens every line he has, so one player can feed a TD slip and a
   receptions slip from one screen. Since 2026-10-05 it is a centred modal closed by ✕, the scrim or Back,
   not a bottom sheet: it is something to read (design/STYLE.md Overlays). Top to bottom:

     1. who: his face, name, position, club, opponent and kickoff, and ff-jarvis's reason
     2. his work week by week: snaps, targets or carries, red-zone looks, his last four games
     3. every line he has, each the shared line row (lineitem.js): sides, last four, "N of 4", and
        the model's chance small at the end where the model prices the line; then his longest
        catch in each of those games, history only (no book's line for it can be read)
     4. the matchup as one line (legtiles.js)

   It draws into the leg sheet's own overlay (#legsheet), so it opens, closes and answers Back the
   same way; LEG_SHEET holds his slug while it is up. */
const psNum = v => typeof v === "number";

/* His last four games of usage: the log's per-game `u`, else this season's grid weeks. Each row is
   kept only when it has a number other than zero (a receiver's carries are noise). */
function psUsage(p){
  const log = LIVE_MARKET && LIVE_MARKET.logs && LIVE_MARKET.logs[slSlug(p)];
  let cols, rows;
  if (log && log.u && log.g && log.g.length){
    const k0 = Math.max(0, log.g.length - SL_HIST), cut = k => (log.u[k] || []).slice(k0);
    const rzT = cut("rz_tgt"), rzC = cut("rz_car");
    cols = log.g.slice(k0).map(g => ({y: g[0], w: g[1]}));
    rows = [["snap", cut("snap")], ["tgt", cut("tgt")], ["car", cut("car")],
            ["rz", rzT.map((v, k) => v == null && rzC[k] == null ? null : (v || 0) + (rzC[k] || 0))]];
  } else {
    const weeks = legWeeks(p).slice(-SL_HIST);
    if (!weeks.length) return null;
    cols = weeks.map(r => ({y: USAGE.season, w: r.wk}));
    rows = [["snap", weeks.map(r => r.v.snap)], ["tgt", weeks.map(r => r.v.tgt)],
            ["car", weeks.map(r => r.v.car ?? r.v.rush)], ["rz", weeks.map(r => r.v.rz ?? r.v.rz_tgt)]];
  }
  rows = rows.filter(([k, a]) => a.some(v => psNum(v) && (v > 0 || k === "snap")));
  return rows.length ? {cols, rows} : null;
}

const psRowLabel = k => ({snap: t("slips.sheet.snap"), tgt: t("slips.sheet.tgt"), car: t("slips.sheet.car"), rz: t("slips.sheet.rz")})[k];

function psUsageHTML(p){
  const u = psUsage(p);
  if (!u) return "";
  const old = c => c.y < BUILD_SEASON;
  const head = u.cols.map(c => `<span class="ps-wk${old(c) ? " old" : ""}">${old(c) ? t("slips.sheet.wkOld", {y: c.y, w: c.w}) : t("slips.sheet.wk", {w: c.w})}</span>`).join("");
  const body = u.rows.map(([k, a]) => `<span class="ps-k">${psRowLabel(k)}</span>${a.map((v, j) =>
    `<span class="ps-v${old(u.cols[j]) ? " old" : ""}">${psNum(v) ? `${Math.round(v)}${k === "snap" ? "%" : ""}` : ""}</span>`).join("")}`).join("");
  return `<section class="ps-use" style="--n:${u.cols.length}" aria-label="${t("slips.sheet.useLabel")}"><span></span>${head}${body}</section>`;
}

function psHeadHTML(p, why){
  const team = (TEAM_COLOURS[p.team] || [])[0], opp = legOpp(p);
  const where = [esc(p.pos || ""), p.team && opp ? t("legsheet.head.vs", {team: esc(p.team), opp: esc(opp)}) : esc(p.team || ""), esc(p.kick || "")].filter(Boolean).join(" · ");
  return `<header class="ls-head ps-head">
      <span class="tk-face ls-face"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(p)}</span>
      <div class="ls-who"><h3 id="ls-title">${esc(p.n)}</h3><span class="ls-meta">${where}</span></div>
      <button type="button" class="ps-x" data-legclose aria-label="${t("common.action.close")}">${SV_X}</button>
    </header>
    ${why ? `<p class="ps-why">${esc(why)}</p>` : ""}`;
}

function playerSheetHTML(slug){
  const rows = slPlayerRows(slug);
  if (!rows.length) return "";
  const p = PROPS[rows[0]], r = REASONS[slug];
  const match = PROPS[rows.find(i => PROPS[i].mkt !== "TD") ?? rows[0]];
  return `${psHeadHTML(p, r && r.why)}
    ${psUsageHTML(p)}
    <section class="ps-lines" aria-label="${t("slips.sheet.linesLabel", {n: rows.length})}">${rows.map(slLineHTML).join("")}${slLongHTML(slug)}</section>
    ${legMatchupHTML(match)}`;
}
