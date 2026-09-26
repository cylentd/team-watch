/* "This week": the roster's checklist (2026-09-25, from the storyboard David picked; it replaced a
   brief of at most three lines that usually held one). One line per thing to check before
   kickoff, most urgent first: who is hurt, whether the lineup is right, the weather, the
   matchups, the wire, the news. Each line says the fact, a second line says what it touches, and
   a tap opens the player or the view it names. Every fact is read from data the page already
   carries; nothing here computes a verdict of its own. */

let BRIEF_ALL = false;   // a phone shows three lines until "Show all"
let BRIEF_PEEK = false;  // the checked lines are shown again, until "Hide checked" or a reload

/* Checked lines (2026-09-25): the list is read once, then it is in the way, on a phone above the
   whole roster. "Got it" checks every line, a swipe checks one, and a line that is all checked
   folds to one row. Kept per league per week, by what the line says, so a line whose fact changes
   (a new injury, a new swap) comes back. localStorage can refuse: this load still remembers. */
const BRIEF_MEM = new Map();
const briefKey = team => `tw-brief-${team.key}-${packWeek() || 0}`;
function briefId(l){
  let h = 5381;
  for (const ch of `${l.kind}|${l.text}|${l.sub || ""}`) h = (h * 33 ^ ch.charCodeAt(0)) >>> 0;
  return h.toString(36);
}
function briefChecked(team){
  const k = briefKey(team);
  if (!BRIEF_MEM.has(k)){
    let ids = [];
    try { ids = JSON.parse(localStorage.getItem(k) || "[]"); } catch (e) { /* none kept */ }
    BRIEF_MEM.set(k, new Set(Array.isArray(ids) ? ids : []));
  }
  return BRIEF_MEM.get(k);
}
function briefCheck(team, ids){
  const s = briefChecked(team);
  ids.forEach(id => s.add(id));
  try { localStorage.setItem(briefKey(team), JSON.stringify([...s])); } catch (e) { /* kept for this load */ }
}

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
  if (notMine(team) || typeof waiverIn !== "function") return [];
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
  const all = briefLines(team).map(l => ({...l, id: briefId(l)}));
  const head = (small, act) => `<div class="brief-h"><h2>${t("teams.brief.title")}</h2><small>${small}</small>${act}</div>`;
  if (!all.length) return `<section class="brief" aria-label="${t("teams.brief.title")}">
    ${head("", "")}<p class="brief-quiet">${t("teams.brief.quiet")}</p></section>`;
  const checked = briefChecked(team), open = all.filter(l => !checked.has(l.id));
  const lines = BRIEF_PEEK ? all : open, done = all.length - open.length;
  // Every line checked: one row that says so, and the way back to them.
  if (!lines.length) return `<section class="brief done" aria-label="${t("teams.brief.title")}" data-bteam="${team.key}">
    ${head(t("teams.brief.allChecked", {n: all.length}), `<button type="button" class="brief-act" data-briefpeek>${t("teams.brief.show")}</button>`)}</section>`;
  // Every line checked and shown again: the done row keeps its words and its place, "Show" becomes
  // "Hide", and the lines open under it (a "0 things to check" heading read as a fault).
  const peekDone = !open.length, more = lines.length > 3;
  const foot = [
    more ? `<button type="button" class="brief-more" data-briefall aria-expanded="${BRIEF_ALL}">${BRIEF_ALL ? t("teams.brief.fewer") : t("teams.brief.all", {n: lines.length})}</button>` : "",
    done && !peekDone ? `<button type="button" class="brief-more" data-briefpeek>${BRIEF_PEEK ? t("teams.brief.hideChecked") : t("teams.brief.showChecked", {n: done})}</button>` : "",
  ].join("");
  return `<section class="brief${BRIEF_ALL ? " all" : ""}${peekDone ? " done peek" : ""}" aria-label="${t("teams.brief.title")}" data-bteam="${team.key}">
    ${peekDone ? head(t("teams.brief.allChecked", {n: all.length}), `<button type="button" class="brief-act" data-briefpeek>${t("teams.brief.hide")}</button>`)
      : head(t("teams.brief.count", {n: open.length, s: open.length === 1 ? "" : "s"}),
          `<button type="button" class="brief-act" data-briefok>${t("teams.brief.gotIt")}</button>`)}
    ${lines.map(l => `<button class="brief-line k-${l.kind} ${l.tone}${checked.has(l.id) ? " checked" : ""}" data-bid="${l.id}" ${l.go ? `data-go="${l.go}"` : `data-team="${team.key}" data-i="${l.i}"`}>
        <span class="brief-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${BRIEF_ICON[l.kind]}</svg></span>
        <span class="brief-txt">${l.text}${l.sub ? `<small>${l.sub}</small>` : ""}</span><span class="brief-go" aria-hidden="true">&rsaquo;</span>
      </button>`).join("")}
    ${foot ? `<div class="brief-foot">${foot}</div>` : ""}
  </section>`;
}

/* A line swiped sideways past a third of its width is checked: it slides out the way it went and
   its row closes up. Short of that it springs back, and it is still a tap. Vertical drags scroll. */
const BRIEF_SWIPE = 1 / 3;
function wireBriefSwipe(el, team){
  let x0 = null, y0 = 0, dx = 0, moved = false;
  el.addEventListener("pointerdown", e => { x0 = e.clientX; y0 = e.clientY; dx = 0; moved = false; });
  el.addEventListener("pointermove", e => {
    if (x0 === null) return;
    dx = e.clientX - x0;
    if (!moved && Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(e.clientY - y0)){ moved = true; el.setPointerCapture?.(e.pointerId); el.classList.add("swiping"); }
    if (moved){ el.style.translate = `${dx}px 0`; el.style.opacity = String(1 - Math.min(.7, Math.abs(dx) / el.offsetWidth)); }
  });
  const end = async () => {
    if (x0 === null) return;
    x0 = null; el.classList.remove("swiping");
    if (!moved) return;
    el.dataset.swiped = "1";                          // the click this release fires is not a tap
    setTimeout(() => delete el.dataset.swiped, 0);
    if (Math.abs(dx) < el.offsetWidth * BRIEF_SWIPE){ el.style.translate = ""; el.style.opacity = ""; return; }
    briefCheck(team, [el.dataset.bid]);
    if (!REDUCED()){
      await el.animate([{translate: `${dx}px 0`, opacity: el.style.opacity}, {translate: `${Math.sign(dx) * el.offsetWidth}px 0`, opacity: 0}],
        {duration: 180, easing: "ease-in", fill: "forwards"}).finished;
      await el.animate([{height: `${el.offsetHeight}px`}, {height: "0px", paddingTop: 0, paddingBottom: 0, borderWidth: 0}],
        {duration: 200, easing: getComputedStyle(el).getPropertyValue("--spring").trim() || "ease-out", fill: "forwards"}).finished;
    }
    render();
  };
  el.addEventListener("pointerup", end);
  el.addEventListener("pointercancel", end);
}

/* From 1100px the brief is a sticky column beside the rows, pinned just under the nav -- the same
   measurement Waivers' rail takes (wdesk.js wvRailSide), since the nav's height is not a token. */
function wireBrief(v){
  const rl = v.querySelector(".rl"), nav = document.querySelector(".navbar");
  if (rl && nav) rl.style.setProperty("--rl-stick", `${Math.round((parseFloat(getComputedStyle(nav).top) || 0) + nav.offsetHeight)}px`);
  const box = v.querySelector(".brief[data-bteam]"), team = box && TEAMS[box.dataset.bteam];
  v.querySelectorAll(".brief-line").forEach(el => {
    el.addEventListener("click", () => {
      if (el.dataset.swiped) return;
      if (el.dataset.go) navGo(el.dataset.go);
      else openProfile(findPlayer(el.dataset.team, +el.dataset.i), el);
    });
    if (team && !el.classList.contains("checked")) wireBriefSwipe(el, team);
  });
  v.querySelector("[data-briefall]")?.addEventListener("click", () => { BRIEF_ALL = !BRIEF_ALL; render(); });
  v.querySelector("[data-briefpeek]")?.addEventListener("click", () => { BRIEF_PEEK = !BRIEF_PEEK; render(); });
  v.querySelector("[data-briefok]")?.addEventListener("click", () => {
    briefCheck(team, [...v.querySelectorAll(".brief-line[data-bid]:not(.checked)")].map(el => el.dataset.bid));
    BRIEF_PEEK = false; BRIEF_ALL = false;
    render();
  });
}
