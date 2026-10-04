/* ============================== START/SIT: THE PICKER ==============================
   The top card of Start/Sit (2026-10-03): two or three players side by side, and who starts.
   It opens on the reader's closest call when he has a team (the pair the roster brief names:
   the bench player who gains the most on a starter he could replace, else the smallest gap), and
   empty with a one-line prompt when he has not. The list is his roster at the first pick's
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
function ssWx(slug){
  const row = typeof LIVE_PROJECTIONS !== "undefined" && LIVE_PROJECTIONS ? LIVE_PROJECTIONS.players[slug] : null;
  return row && row.wx ? row.wx : null;
}

/* The reader's own team on screen, else his first; null for a leaguemate's or none. */
function ssTeam(){
  const mine = myLeagueKeys().filter(k => TEAMS[k] && (TEAMS[k].roster || []).length);
  return mine.includes(VIEW) ? TEAMS[VIEW] : mine.length ? TEAMS[mine[0]] : null;
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
    // Kept for the week they were picked in: next week opens on the new closest call.
    const v = JSON.parse(localStorage.getItem(SS_KEY) || "null");
    if (v && v.week === schedWeek() && Array.isArray(v.picks)) kept = v.picks.filter(s => typeof s === "string").slice(0, SS_MAX);
  } catch (e) { /* none kept */ }
  SS_PICKS = kept || ssClosest().map(p => p.slug);
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
const ssCols = () => ssLoad().map(ssPlayer).filter(Boolean).map(p => ({p, rk: ssRank(p.slug), pts: ssPts(p.slug)}));

/* The higher projection starts; the top two inside SS_FLIP points of each other are a coin flip. */
function ssVerdict(cols){
  const ranked = cols.filter(c => c.pts !== null).sort((a, b) => b.pts - a.pts);
  if (ranked.length < 2) return null;
  const gap = +(ranked[0].pts - ranked[1].pts).toFixed(1);   // rounded to the one decimal shown, so 0.54 is "0.5", a coin flip, never a START at "+0.5"
  return gap <= SS_FLIP ? {flip: true, gap} : {flip: false, win: ranked[0], gap};
}

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

/* One row per thing to compare: a label line, then a lane per player. A row nobody has data for is
   not drawn; a lane without data says a dash. */
function ssRowsHTML(cols){
  const fp = (ssSB() && ssSB().fp) || {}, one = new Set(cols.map(c => c.p.pos)).size === 1;
  const rows = [
    {label: t("startsit.row.proj"), cells: cols.map(c => c.pts === null ? "" : ssVal(c.pts.toFixed(1), "", "big"))},
    {label: t("startsit.row.rank"), cells: cols.map(c => c.rk ? ssVal(t("startsit.fmt.rank", {pos: esc(c.rk.pos), n: c.rk.rank})) : "")},
    {label: one ? t("startsit.row.defPos", {pos: esc(cols[0].p.pos)}) : t("startsit.row.def"), cells: cols.map(ssDefCell),
      note: cols.some(c => c.p.pos === "WR") ? t("startsit.def.wr") : ""},
    {label: t("startsit.row.fp"), cells: cols.map(c => fp[c.p.slug] ? ssVal(t("startsit.fmt.rank", {pos: esc(fp[c.p.slug].pos), n: fp[c.p.slug].ecr})) : "")},
    {label: t("startsit.row.out"), cells: cols.map(ssOutCell)},
    {label: t("startsit.row.wx"), cells: cols.map(ssWxCell)},
  ].filter(r => r.cells.some(Boolean));
  return rows.map(r => `<div class="ssv-row"><div class="ssv-lbl lbl"><span>${r.label}</span>${r.note ? `<em>${r.note}</em>` : ""}</div>
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

function ssVerdictHTML(cols){
  const v = ssVerdict(cols);
  if (!v) return "";
  return v.flip ? `<div class="ssv-verdict flip"><span class="ssv-coin">${t("startsit.pick.flip")}</span></div>`
    : `<div class="ssv-verdict"><span class="mu-tag start">${t("matchups.call.start")}</span><b>${shortName(v.win.p.n)}</b>
      <span class="ssv-gain">${t("startsit.pick.gap", {n: v.gap.toFixed(1)})}</span></div>`;
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
  const cols = ssCols(), wk = typeof LIVE_RANKS !== "undefined" && LIVE_RANKS ? LIVE_RANKS.week : null;
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
    if (b.dataset.ssx){
      SS_PICKS = ssLoad().filter(s => s !== b.dataset.ssx);
      ssSave(); ssPaintPick(el, SS_REFOCUS);
      return;
    }
    if (b.dataset.ssslug){
      if (!ssLoad().includes(b.dataset.ssslug) && ssLoad().length < SS_MAX) SS_PICKS = [...ssLoad(), b.dataset.ssslug];
      SS_OPEN = false; SS_Q = "";
      ssSave(); ssPaintPick(el, SS_REFOCUS);
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
}
