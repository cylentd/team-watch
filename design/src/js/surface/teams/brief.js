/* "This week": the roster's checklist (2026-09-25, from the storyboard David picked; it replaced a
   brief of at most three lines that usually held one). One line per thing to check before
   kickoff, most urgent first: who is hurt, whether the lineup is right, the weather, the
   matchups, the wire, the news. Each line says the fact, a second line says what it touches, and
   a tap opens the player or the view it names. Every fact is read from data the page already
   carries; nothing here computes a verdict of its own. */

let BRIEF_ALL = false;   // a phone shows three lines until "Show all"

/* The profile index a roster row carries: starters, then bench, then out (drawer.js findPlayer). */
function briefOrder(team){
  return team.roster.filter(p=>p.start)
    .concat(team.roster.filter(p=>!p.start && p.slot!=="OUT"))
    .concat(team.roster.filter(p=>p.slot==="OUT"));
}
const briefName = p => esc(nameInitial(p.n));
const briefList = ps => ps.map(briefName).join(", ");
const briefStatus = p => { const r = injFor(p); return r ? INJ_WORD[r.s]().toLowerCase() : ""; };

/* Hurt: starters first (a decision before kickoff), then the bench (a decision on the wire). */
function briefHurt(team, at){
  const out = [], hurt = team.roster.filter(p => p.slot !== "OUT" && injFor(p));
  const starters = hurt.filter(p => p.start), bench = hurt.filter(p => !p.start);
  const says = ps => ps.map(p => `<b>${briefName(p)}</b> ${briefStatus(p)}`).join(" · ");
  if (starters.length) out.push({kind: "hurt", tone: starters.some(injSits) ? "down" : "warn", i: at(starters[0]),
    text: says(starters), sub: t("teams.brief.hurtStart")});
  if (bench.length) out.push({kind: "hurt", tone: "warn", i: at(bench[0]),
    text: says(bench), sub: starters.length ? t("teams.brief.hurtBench") : t("teams.brief.hurtBenchOnly")});
  return out;
}

/* Which lineup slots a position can fill: its own, a flex (RB/WR/TE), a superflex (any). */
function briefFits(slot, pos){
  const s = slotLabel(slot);
  if (s === pos) return true;
  if (s === "FLX" || s === "W/R/T" || s === "RB/WR/TE") return ["RB", "WR", "TE"].includes(pos);
  if (s === "SFLX" || s === "OP" || s === "Q/W/R/T") return ["QB", "RB", "WR", "TE"].includes(pos);
  return false;
}
/* The lineup check: a healthy bench player who out-projects a starter he could replace by a full
   point (under that, a projection's own noise decides it). None is "set", and the second line
   names the closest call, or a bench player who projects higher but will likely sit. */
const BRIEF_SWAP_PTS = 1;
function briefLineup(team, at){
  const starters = team.roster.filter(p => p.start && projFor(p) !== null);
  const bench = team.roster.filter(p => !p.start && p.slot !== "OUT" && projFor(p) !== null);
  let best = null, close = null, sitting = null;
  const keep = (cur, x) => !cur || x.gain > cur.gain ? x : cur;
  bench.forEach(b => starters.filter(s => briefFits(s.slot, b.pos) && projFor(b) > projFor(s)).forEach(s => {
    const x = {b, s, gain: projFor(b) - projFor(s)};
    if (injSits(b)) sitting = keep(sitting, x);
    else if (x.gain >= BRIEF_SWAP_PTS) best = keep(best, x);
    else close = keep(close, x);
  }));
  const pts = p => projFor(p).toFixed(1);
  const pair = x => ({in: briefName(x.b), inPts: pts(x.b), out: briefName(x.s), outPts: pts(x.s)});
  if (best) return [{kind: "lu", tone: "lime", i: at(best.b), text: t("teams.brief.swap", pair(best)),
    sub: t("teams.brief.swapSub", {n: best.gain.toFixed(1)})}];
  const sub = close ? t("teams.brief.setClose", pair(close))
    : sitting ? t("teams.brief.setBecause", {...pair(sitting), status: briefStatus(sitting.b)}) : t("teams.brief.setSub");
  return [{kind: "lu", tone: "ok", i: at(close ? close.b : starters[0] || team.roster[0]), text: t("teams.brief.set"), sub}];
}

/* Weather: the forecast that touches the most of his players, starters named first. */
function briefWeather(team, at){
  const by = new Map();
  team.roster.filter(p => p.slot !== "OUT").forEach(p => {
    const g = cardGame(p.team), w = cardWeather(g), wx = cardWeatherNote(w, p.pos);
    if (!wx) return;
    const k = `${g.venue}|${wx.kind}`;
    (by.get(k) || by.set(k, {g, wx, ps: []}).get(k)).ps.push(p);
  });
  const top = [...by.values()].sort((a, b) => b.ps.filter(p => p.start).length - a.ps.filter(p => p.start).length || b.ps.length - a.ps.length)[0];
  if (!top) return [];
  const start = top.ps.filter(p => p.start), bench = top.ps.filter(p => !p.start);
  return [{kind: "wx", tone: "sky", i: at(top.ps[0]),
    text: t("teams.brief.wx", {what: esc(top.wx.what.charAt(0) + top.wx.what.slice(1).toLowerCase()), where: esc(top.g.venue)}),
    sub: [start.length ? t("teams.brief.wxStart", {names: briefList(start)}) : "",
          bench.length ? t("teams.brief.wxBench", {names: briefList(bench)}) : ""].filter(Boolean).join("; ")}];
}

/* Matchups: his toughest and softest starter this week, by the page's own ranks. */
function briefMatchups(team, at){
  const ranked = team.roster.filter(p => p.start).map(p => ({p, prof: profileFor(p)}))
    .filter(x => x.prof && x.prof.next && easiestRank(x.prof.next.factor) !== null)
    .map(x => ({...x, n: easiestRank(x.prof.next.factor)})).sort((a, b) => b.n - a.n);
  if (ranked.length < 2) return [];
  const say = x => t("teams.brief.muOne", {name: briefName(x.p), where: whereWord(x.prof.next), opp: esc(x.prof.next.opp), nth: ordinal(x.n)});
  const hard = ranked[0], easy = ranked[ranked.length - 1];
  return [{kind: "mu", tone: "warn", i: at(hard.p), text: t("teams.brief.muHard", {m: say(hard)}), sub: t("teams.brief.muEasy", {m: say(easy)})}];
}

/* The wire: must-claims first, else what is worth a claim, with when the claims clear. */
function briefWire(team){
  if (team.connected || typeof waiverIn !== "function") return [];
  const must = waiverMustIn(team.key), worth = waiverIn(team.key).filter(([r]) => waiverTier(r, team.key) === "worth").length;
  if (!must && !worth) return [];
  const meta = waiverMeta()[team.key], when = meta ? waiverWhen(meta.clears || (WAIVER && WAIVER.clears)) : "";
  return [{kind: "wire", tone: must ? "lime" : "up", go: "waivers",
    text: must ? (must === 1 ? t("teams.brief.mustOne") : t("teams.brief.mustMany", {n: must})) : t("teams.brief.worth", {n: worth}),
    sub: when ? t("waiver.hero.clears", {when}) : ""}];
}

function briefNews(team, at){
  const told = team.roster.filter(p => p.news).sort((a, b) => b.news - a.news || at(a) - at(b));
  if (!told.length) return [];
  return [{kind: "news", tone: "soft", i: at(told[0]),
    text: told.length === 1 ? t("teams.brief.newsOne", {name: briefName(told[0]), n: told[0].news}) : t("teams.brief.newsMany", {names: briefList(told.slice(0, 3))}),
    sub: t("teams.brief.newsSub")}];
}

function briefLines(team){
  const order = briefOrder(team), at = p => order.indexOf(p);
  return [...briefHurt(team, at), ...briefLineup(team, at), ...briefWeather(team, at),
          ...briefMatchups(team, at), ...briefWire(team), ...briefNews(team, at)];
}

/* The kind's mark, drawn in its colour: a cross for health, a checked list for the lineup, a cloud
   for weather, a shield for a matchup, a plus for the wire, a page for news. */
const BRIEF_ICON = {
  hurt: '<path d="M12 4v16M4 12h16"/>',
  lu: '<path d="M4 6h16M4 12h10M4 18h7"/><path d="m15 16 2 2 4-4"/>',
  wx: '<path d="M7 16a4 4 0 1 1 1-7.9A5 5 0 0 1 18 9a3.5 3.5 0 0 1-.5 7z"/><path d="m9 19-1 2M13 19l-1 2M17 19l-1 2"/>',
  mu: '<path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/>',
  wire: '<path d="M12 5v14M5 12h14"/>',
  news: '<path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/>',
};

function briefHTML(team){
  const lines = briefLines(team);
  if (!lines.length) return `<section class="brief" aria-label="${t("teams.brief.title")}">
    <h2 class="brief-h">${t("teams.brief.title")}</h2><p class="brief-quiet">${t("teams.brief.quiet")}</p></section>`;
  const more = lines.length > 3;
  return `<section class="brief${BRIEF_ALL ? " all" : ""}" aria-label="${t("teams.brief.title")}">
    <h2 class="brief-h">${t("teams.brief.title")}<small>${t("teams.brief.count", {n: lines.length, s: lines.length === 1 ? "" : "s"})}</small></h2>
    ${lines.map(l => `<button class="brief-line k-${l.kind} ${l.tone}" ${l.go ? `data-go="${l.go}"` : `data-team="${team.key}" data-i="${l.i}"`}>
        <span class="brief-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${BRIEF_ICON[l.kind]}</svg></span>
        <span class="brief-txt">${l.text}${l.sub ? `<small>${l.sub}</small>` : ""}</span><span class="brief-go" aria-hidden="true">&rsaquo;</span>
      </button>`).join("")}
    ${more ? `<button type="button" class="brief-more" data-briefall aria-expanded="${BRIEF_ALL}">${BRIEF_ALL ? t("teams.brief.fewer") : t("teams.brief.all", {n: lines.length})}</button>` : ""}
  </section>`;
}

/* From 1100px the brief is a sticky column beside the rows, pinned just under the nav -- the same
   measurement Waivers' rail takes (wdesk.js wvRailSide), since the nav's height is not a token. */
function wireBrief(v){
  const rl = v.querySelector(".rl"), nav = document.querySelector(".navbar");
  if (rl && nav) rl.style.setProperty("--rl-stick", `${Math.round((parseFloat(getComputedStyle(nav).top) || 0) + nav.offsetHeight)}px`);
  v.querySelectorAll(".brief-line").forEach(el => el.addEventListener("click", () => {
    if (el.dataset.go) navGo(el.dataset.go);
    else openProfile(findPlayer(el.dataset.team, +el.dataset.i), el);
  }));
  v.querySelector("[data-briefall]")?.addEventListener("click", () => { BRIEF_ALL = !BRIEF_ALL; render(); });
}
