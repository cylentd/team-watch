/* ============================== MATCHUPS: THE PICKER ==============================
   The Compare two page (was Start/Sit's top card until 2026-10-06; matchups.js): two or three players side by side, and who starts.
   It opens on the reader's closest call when he has a team (the pair the roster brief names:
   the bench player who gains the most on a starter he could replace, else the smallest gap), and
   empty with the search open and focused when he has not (2026-10-05, ssOpening in data/startsit.js:
   a first-time visitor was handed a pair he never chose). The search stays open until two are picked. The list is his roster at the first pick's
   position, then search (the Compare picker's pattern, cmppick.js). The page decides nothing: the
   verdict is the higher of ff-jarvis's two projections, "Coin flip" inside half a point, and every
   row is a number ff-jarvis made (LIVE_RANKS, LIVE_DEFENSE, LIVE_SSB, LIVE_PROJECTIONS).
   The card repaints itself in place: the Takes under it are never redrawn by a pick. Only the
   picks are kept, in localStorage; a reader with none kept gets the closest call. */
const SS_MAX = 3, SS_KEY = "tw-ss-picks", SS_FLIP = 0.5, SS_LIST_ROWS = 8;
let SS_PICKS = null;   // slugs in pick order; null until first read
let SS_OPEN = false;   // the add list is open
let SS_Q = "";
const ssSB = () => typeof LIVE_SSB !== "undefined" && LIVE_SSB ? LIVE_SSB : null;
const ssRank = slug => typeof LIVE_RANKS !== "undefined" && LIVE_RANKS ? LIVE_RANKS.rows.find(r => r.slug === slug) || null : null;
function ssPts(slug){
  const r = ssRank(slug);
  return r && typeof r.pts === "number" ? r.pts : projFor({slug});
}
/* His floor and ceiling (plan U5): the Ranks row's own band while he is on the list, else the projections'
   (the same two numbers either way, ff-jarvis ranges.py), null with none. */
function ssRange(slug){
  const r = ssRank(slug);
  return r ? rangeFrom(r) : rangeFor({slug});
}
function ssWx(slug){
  const row = typeof LIVE_PROJECTIONS !== "undefined" && LIVE_PROJECTIONS ? LIVE_PROJECTIONS.players[slug] : null;
  return row && row.wx ? row.wx : null;
}

/* The team the reader picked (lgMine: his pick, else none on a page with leaguemates), null when he has
   not. It was David's own roster for everyone until 2026-10-05 (the first-time visitor's "someone else's
   pair", plan U3), because myLeagueKeys lists the three rosters the page ships whoever is reading. */
function ssTeam(){
  const mine = lgMine();
  return mine && (mine.roster || []).length ? mine : null;
}
const ssRoster = team => team ? team.roster.map(r => Object.assign({}, r, {slug: r.slug || slugOf(r.n)})) : [];

/* The brief's pair (teams/brief.js briefPairs, here judged by the same points the verdict uses):
   the bench player who out-projects a starter he could replace by the most (the swap, else the
   close call), else the smallest gap the other way. Bench first. */
function ssClosest(){
  const team = ssTeam();
  if (!team) return [];
  const {best, close, near} = briefPairs({roster: ssRoster(team).filter(p => p.slot !== "OUT")}, p => ssPts(p.slug));
  const x = best || close || near;
  return x ? [x.b, x.s] : [];
}

function ssLoad(){
  if (SS_PICKS) return SS_PICKS;
  let kept = null;
  try {
    // Kept for the week they were picked in (the page's week, schedWeek): next week opens on the new
    // closest call. Same {week, picks} shape as before.
    const v = JSON.parse(localStorage.getItem(SS_KEY) || "null");
    if (v && v.week === schedWeek() && Array.isArray(v.picks)) kept = v.picks.filter(s => typeof s === "string").slice(0, SS_MAX);
  } catch (e) { /* none kept */ }
  const o = ssOpening({team: !!ssTeam(), kept, closest: kept ? [] : ssClosest().map(p => p.slug)});
  SS_PICKS = o.picks; SS_OPEN = o.open;   // nobody picked: the search is already open (data/startsit.js)
  return SS_PICKS;
}
function ssSave(){
  try { localStorage.setItem(SS_KEY, JSON.stringify({week: schedWeek(), picks: SS_PICKS})); } catch (e) { /* kept for this load */ }
}

function ssPlayer(slug){
  const rk = ssRank(slug);
  if (rk) return {n: rk.n, pos: rk.pos, team: rk.team, slug};
  const e = searchIndex().find(x => x.slug === slug);
  return e ? searchPlayer(e) : null;
}
/* His books number (rank_pts, running backs only): the Ranks row's own, else the projections' (rbrules.js). */
function ssBooks(slug){
  const r = ssRank(slug), row = r && typeof r.rank_pts === "number" ? r : rbProjRow(slug);
  return row && typeof row.rank_pts === "number" ? row.rank_pts : null;
}
const ssCols = () => ssLoad().map(ssPlayer).filter(Boolean).map(p => ({p, pos: p.pos, rk: ssRank(p.slug), pts: ssPts(p.slug), rp: ssBooks(p.slug)}));

/* The higher projection starts; the top two inside SS_FLIP points of each other are a coin flip. Two or
   more running backs the books all priced are called on the books' number instead (rbrules.js, ff-jarvis
   METHODOLOGY 12.86); the points shown stay ours. */
const ssVerdict = cols => rbVerdict(cols, SS_FLIP);

const ssVal = (val, sub, cls) => `<span class="ssv-v${cls ? " " + cls : ""}"><b>${val}</b>${sub ? `<small>${sub}</small>` : ""}</span>`;

/* Softest or toughest, whichever side of the middle he faces, as the profile's matchup line says. */
function ssDefCell(c){
  const opp = c.rk && c.rk.opp;
  if (!opp) return "";
  const where = c.rk.home ? t("startsit.def.home", {opp: esc(opp)}) : t("startsit.def.away", {opp: esc(opp)});
  const d = seasonDefRank(opp, c.p.pos);
  if (!d) return ssVal("—", where);
  const [n, of] = d, soft = n <= of / 2;
  const say = soft ? t("startsit.def.soft", {nth: ordinal(n)}) : t("startsit.def.tough", {nth: ordinal(of - n + 1)});
  return ssVal(say, where, matchupClass(n, of) === "mu-easy" ? "up" : matchupClass(n, of) === "mu-hard" ? "down" : "");
}

function ssOutCell(c){
  const out = (ssSB() && ssSB().out || {})[c.p.slug];
  return out && out.length ? `<span class="ssv-v">${out.slice(0, 3).map(o =>
    `<span class="ssv-o"><b>${esc(nameInitial(o.n))}</b><small>${esc(o.pos)} · ${esc(o.s)}</small></span>`).join("")}</span>` : "";
}

function ssWxCell(c){
  const wx = ssWx(c.p.slug);
  if (!wx) return "";
  const words = {wind: t("profile.weather.wind"), precip: t("startsit.wx.rain"), cold: t("startsit.wx.cold")};
  const sub = (wx.cond || []).map(k => words[k]).filter(Boolean).join(" · ");
  const adj = typeof wx.adj === "number";
  return ssVal(adj ? wtSigned(wx.adj) : "—", sub, adj && wx.adj <= -0.05 ? "down" : adj && wx.adj >= 0.05 ? "up" : "");
}

/* His row in the Usage grid, one tap (nav.js navGoRow; plan U3). Drawn only for a player the grid has. */
function ssGridCell(c){
  const rows = typeof USAGE !== "undefined" && USAGE ? USAGE.rows : null;
  const week = typeof USAGE_WEEK !== "undefined" ? USAGE_WEEK : null;
  return rows && navRowPlan("usage", c.p.slug, rows, {week}) ? `<button type="button" class="ssv-go" data-ssgrid="${esc(c.p.slug)}">${t("startsit.go.row")}</button>` : "";
}

/* One row per thing to compare: a label line, then a lane per player. A row nobody has data for is
   not drawn; a lane without data says a dash. */
function ssRowsHTML(cols){
  const fp = (ssSB() && ssSB().fp) || {}, one = new Set(cols.map(c => c.p.pos)).size === 1;
  // FantasyPros ranking the man we sit ahead of him is the one row that argues with the verdict: say why it may.
  const fpNote = ssFpNote(ssFpCheck(cols, ssVerdict(cols), fp), Object.fromEntries(cols.map(c => [c.p.slug, shortName(c.p.n)])));
  const rows = [
    // The band under each number, said in words once, under the row's label, only when a lane draws one.
    {label: t("startsit.row.proj"), cells: cols.map(c => {
      const g = c.pts === null ? null : ssRange(c.p.slug);
      return c.pts === null ? "" : ssVal(c.pts.toFixed(1), g ? `<span class="ssv-rng" title="${t("range.tip", {floor: g.floor.toFixed(1), ceil: g.ceil.toFixed(1)})}">${g.text}</span>` : "", "big");
    }), note: cols.some(c => c.pts !== null && ssRange(c.p.slug)) ? t("range.note") : ""},
    {label: t("startsit.row.rank"), cells: cols.map(c => c.rk ? ssVal(t("startsit.fmt.rank", {pos: esc(c.rk.pos), n: c.rk.rank})) : "")},
    // `tip`: the failed test in the label's tooltip (2026-10-06); a WR's defense row already says it matters little.
    {label: one ? t("startsit.row.defPos", {pos: esc(cols[0].p.pos)}) : t("startsit.row.def"), cells: cols.map(ssDefCell),
      note: cols.some(c => c.p.pos === "WR") ? t("startsit.def.wr") : "",
      tip: cols.some(c => c.p.pos !== "WR") ? t("startsit.def.mark") : ""},
    {label: t("startsit.row.fp"), cells: cols.map(c => fp[c.p.slug] ? ssVal(t("startsit.fmt.rank", {pos: esc(fp[c.p.slug].pos), n: fp[c.p.slug].ecr})) : ""),
      note: fpNote},
    {label: t("startsit.row.out"), cells: cols.map(ssOutCell), tip: t("startsit.out.mark")},
    {label: t("startsit.row.wx"), cells: cols.map(ssWxCell),
      tip: cols.some(c => ((ssWx(c.p.slug) || {}).cond || []).includes("cold")) ? t("startsit.wx.mark") : ""},
    {label: t("startsit.row.grid"), cells: cols.map(ssGridCell)},
  ].filter(r => r.cells.some(Boolean));
  return rows.map(r => `<div class="ssv-row"><div class="ssv-lbl lbl"><span${r.tip ? ` title="${r.tip}"` : ""}>${r.label}</span>${r.note ? `<em>${r.note}</em>` : ""}</div>
    <div class="ssv-lanes" style="--n:${cols.length}">${r.cells.map(h => h || ssVal("—")).join("")}</div></div>`).join("");
}

const SS_X = '<svg class="ssv-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
const SS_PLUS = '<svg class="ssv-ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';

function ssBandHTML(cols){
  return `<div class="ssv-band" style="--n:${cols.length}">${cols.map((c, i) => `<div class="ssv-who ssv-s${i}">
    <button type="button" class="ssv-x" data-ssx="${esc(c.p.slug)}" aria-label="${t("startsit.pick.remove", {name: shortName(c.p.n)})}">${SS_X}</button>
    <span class="ssv-face">${headHTML(c.p)}</span><b>${shortName(c.p.n)}</b>
    <span class="lbl">${esc([c.p.pos, c.p.team].filter(Boolean).join(" · "))}</span></div>`).join("")}</div>`;
}

/* The gap is points, so a back the books put first on fewer points shows none (a negative gap is no gain). */
function ssVerdictHTML(cols){
  const v = ssVerdict(cols);
  const gain = v && v.gap > 0 ? `<span class="ssv-gain">${t("startsit.pick.gap", {n: v.gap.toFixed(1)})}</span>` : "";
  const call = !v ? "" : v.flip ? `<div class="ssv-verdict flip"><span class="ssv-coin">${t("startsit.pick.flip")}</span></div>`
    : `<div class="ssv-verdict"><span class="mu-tag start">${t("matchups.call.start")}</span><b>${shortName(v.win.p.n)}</b>${gain}</div>`;
  return call;
}

function ssOptHTML(p){
  const pts = ssPts(p.slug);
  return `<li><button type="button" class="ssv-opt" data-ssslug="${esc(p.slug)}"><span class="ssv-hd">${headHTML(p)}</span>
    <span class="ssv-ow"><b>${shortName(p.n)}</b><small>${esc([p.pos, p.team].filter(Boolean).join(" · "))}</small></span>
    <span class="ssv-op">${pts === null ? "—" : pts.toFixed(1)}</span></button></li>`;
}

/* Search when something is typed; else his roster at the first pick's position (or all of it, with
   no pick yet), highest projection first. */
function ssResultsHTML(){
  const picked = new Set(ssLoad()), q = SS_Q.trim();
  if (q){
    const hits = searchFind(q, 8).map(x => searchPlayer(x.e)).filter(p => !picked.has(p.slug));
    return hits.length ? `<ol class="ssv-ol">${hits.map(ssOptHTML).join("")}</ol>` : `<p class="ssv-none">${t("startsit.list.none")}</p>`;
  }
  const team = ssTeam(), first = ssCols()[0], pos = first && first.p.pos;
  const rows = ssRoster(team).filter(p => !picked.has(p.slug) && (!pos || p.pos === pos))
    .sort((a, b) => (ssPts(b.slug) ?? -1) - (ssPts(a.slug) ?? -1)).slice(0, SS_LIST_ROWS);
  if (!rows.length) return `<p class="ssv-none">${t("startsit.list.hint")}</p>`;
  const cap = pos ? t("startsit.list.minePos", {team: esc(team.name), pos: esc(pos)}) : t("startsit.list.mine", {team: esc(team.name)});
  return `<div class="ssv-cap lbl">${cap}</div><ol class="ssv-ol">${rows.map(ssOptHTML).join("")}</ol>`;
}

function ssPickInnerHTML(){
  const cols = ssCols(), wk = schedWeek();
  const add = cols.length < SS_MAX ? `<button type="button" class="ssv-add" data-ssadd aria-expanded="${SS_OPEN}" aria-controls="ssv-box">${SS_PLUS}${t("startsit.pick.add")}</button>` : "";
  const box = SS_OPEN ? `<div class="ssv-box" id="ssv-box"><input id="ssv-q" class="ssv-q" type="search" autocomplete="off" spellcheck="false"
    placeholder="${t("startsit.list.search")}" aria-label="${t("startsit.list.search")}" value="${esc(SS_Q)}"><div class="ssv-res">${ssResultsHTML()}</div></div>` : "";
  const prompt = cols.length < 2 ? `<p class="ssv-prompt">${cols.length ? t("startsit.pick.one") : t("startsit.pick.none")}</p>` : "";
  return `<div class="ssv-h"><h3>${t("startsit.pick.title")}${wk ? `<span class="lbl">${t("startsit.pick.week", {n: wk})}</span>` : ""}</h3>${add}</div>
    ${prompt}${box}${cols.length ? ssBandHTML(cols) : ""}
    ${ssVerdictHTML(cols)}${cols.length ? ssRowsHTML(cols) : ""}`;
}

const ssPickHTML = () => `<section class="ssv-card ssv-pick" id="ssv-pick" tabindex="-1" aria-label="${t("startsit.pick.title")}">${ssPickInnerHTML()}</section>`;

/* After a repaint focus goes to `focus`, else the card itself, so a keyboard reader is never dropped
   on the page. The Add button is gone at three picks, so its fallback is the first Remove. */
const SS_REFOCUS = "[data-ssadd], .ssv-x";
function ssPaintPick(el, focus){
  el.innerHTML = ssPickInnerHTML();
  (el.querySelector(focus) || el).focus();
}

/* One set of listeners on the card, which outlives every repaint of what is inside it. */
function ssWirePick(v){
  const el = v.querySelector("#ssv-pick");
  if (!el) return;
  el.addEventListener("click", e => {
    const b = e.target.closest("button");
    if (!b || !el.contains(b)) return;
    if (b.dataset.ssadd !== undefined){ SS_OPEN = !SS_OPEN; SS_Q = ""; ssPaintPick(el, SS_OPEN ? "#ssv-q" : SS_REFOCUS); return; }
    if (b.dataset.ssgrid){ morphLogo(); navGoRow("usage", b.dataset.ssgrid); return; }
    if (b.dataset.ssx){
      SS_PICKS = ssLoad().filter(s => s !== b.dataset.ssx);
      ssSave(); ssPaintPick(el, SS_REFOCUS);
      return;
    }
    if (b.dataset.ssslug){
      if (!ssLoad().includes(b.dataset.ssslug) && ssLoad().length < SS_MAX) SS_PICKS = [...ssLoad(), b.dataset.ssslug];
      // One pick is not a comparison: the search stays open (and focused) until there are two.
      SS_OPEN = ssLoad().length < 2; SS_Q = "";
      ssSave(); ssPaintPick(el, SS_OPEN ? "#ssv-q" : SS_REFOCUS);
    }
  });
  el.addEventListener("input", e => {
    if (e.target.id !== "ssv-q") return;
    SS_Q = e.target.value;
    el.querySelector(".ssv-res").innerHTML = ssResultsHTML();
  });
  el.addEventListener("keydown", e => {
    if (e.key === "Escape" && SS_OPEN){ SS_OPEN = false; SS_Q = ""; ssPaintPick(el, SS_REFOCUS); }
  });
  // Nobody picked yet: the search is open and the cursor is in it, so the first tap is a name (plan U3).
  if (SS_OPEN && !ssLoad().length) el.querySelector("#ssv-q")?.focus({preventScroll: true});
}
