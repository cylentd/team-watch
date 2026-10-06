/* The Digest's state and its reading of LIVE_DIGEST (design/digest.py). ff-jarvis picks the lead,
   ranks every row and writes the same packet the morning Discord post renders; the page only
   decides which one row lies open. */

/* The ticker, top to bottom. Each id is one topic and one row. `recap` is the link to This week > Recap
   (2026-10-05), which replaced the Results row: it shows only while the week's results are fresh. */
/* Starters folded into News on 2026-09-29 (rows.js dgStartNewsHTML): a new #1 is news, and the row
   of its own sat empty most days. */
/* Hurt left the rows on 2026-09-29 for Need to know (surface/digest/need.js), which lies open above
   them; its id stays for dgWaiting's rows. */
const DG_ROWS = ["recap", "mu", "wx", "adds", "t5", "gems", "news"];
const DG_POS = ["QB", "RB", "WR", "TE"];

/* The row the reader opened by hand ("" when he closed it); null until the first tap, and while
   it is null the day picks. Kept across views, so coming back finds the row where it was left. */
let DG_OPEN = null;

/* The signature: the day picks the open row. Claims are Tuesday and Wednesday, so the wire's
   adds lead; Sunday is game day, so the weather; any other day no row opens, since who is hurt already
   lies open in Need to know (2026-09-29). Monday opened the Results row until 2026-10-05, when the
   results moved to Recap. The reader's local day, from Date.now(), which the render suite pins. */
const DG_DAY = {0: ["wx"], 2: ["adds"], 3: ["adds"]};

/* A game's kickoff as the page writes every kickoff (lib/kick.js), in the reader's clock, from the
   packet's ISO `ko`; the Pacific words digest.py wrote (`kick`) stand in for a packet without one. */
const dgKick = g => kickFmt(g.ko) || g.kick || "";

/* A game that has kicked off takes its pre-game rows with it, here in the browser: the packet was
   cut at build time, and a tab stays open across a Sunday. ff-jarvis drops the same rows at build
   (weekly_digest_played); this only catches up with the clock since. */
function dgCut(d, now){
  const gone = ko => !!ko && Date.parse(ko) <= now;
  const c = {...d, hurt: d.hurt.filter(r => !(r.game && gone(r.game.ko))), best: d.best.filter(r => !gone(r.ko)),
             wx: d.wx.filter(r => !gone(r.ko)), near: d.near && gone(d.near.ko) ? null : d.near,
             top5: d.top5.filter(r => !gone(r.ko)), starters: (d.starters || []).filter(r => !gone(r.ko))};
  // The lead is found before tonight's rows move into the card, so a Thursday lead about a player
  // out tonight still leads; lead.js reads its row from these lists, not the ticker's.
  c.leadRows = {hurt: c.hurt, weather: c.wx, news: c.news};
  c.lead = dgLeadAfter(d, c);
  return dgTonightCut(c, now);
}

/* The lead keeps its row, found again by reference in the cut lists. One whose game has started
   gives way to the top headline. The packet's "results" rule (the week's top score once half the week
   was final) is not drawn since 2026-10-05, when the results moved to Recap: it falls to the headline too. */
function dgLeadAfter(d, c){
  const L = d.lead;
  const was = L && ({hurt: d.hurt, weather: d.wx, news: d.news}[L.rule] || [])[L.index];
  const at = was ? (c.leadRows[L.rule] || []).indexOf(was) : -1;
  if (at >= 0) return {rule: L.rule, index: at};
  return c.news.length ? {rule: "news", index: 0} : null;
}

/* Tonight's card (2026-09-28, storyboard JSPwg21i9YaTSzhYqAEnQZ) shows from 18 hours before its
   kickoff until 4 hours after, so a packet cut Friday for Monday night waits for Monday, and a tab
   left open overnight lets it go. While it shows, its teams' rows live in the card, not the ticker;
   when its games are all the week has left (`tonight_last`), the week's preview rows go too. */
const DG_TN_BEFORE = 18 * 3600e3, DG_TN_AFTER = 4 * 3600e3;
/* Starters stays: a change after a team's game is next week's news, not this slot's preview. */
const DG_TN_ROWS = ["hurt", "mu", "wx", "t5"];
function dgTonightCut(c, now){
  const tn = (c.tonight || []).filter(g => { const k = Date.parse(g.ko); return now >= k - DG_TN_BEFORE && now < k + DG_TN_AFTER; });
  if (!tn.length) return {...c, tn: [], tnLast: false};
  const teams = new Set(tn.flatMap(g => [g.away, g.home]));
  const off = r => !teams.has(r.team), offGame = g => !teams.has(g.home) && !teams.has(g.away);
  return {...c, tn, tnLast: !!c.tonight_last, hurt: c.hurt.filter(off),
          best: c.best.filter(off), top5: c.top5.filter(off), wx: c.wx.filter(offGame), near: c.near && offGame(c.near) ? c.near : null};
}

/* Cut once per half minute, not once per row: every row asks dgD() several times a render. */
let DG_CUT = null, DG_CUT_AT = 0;
function dgD(){
  if (typeof LIVE_DIGEST === "undefined" || !LIVE_DIGEST) return null;
  const now = Date.now();
  if (!DG_CUT || Math.abs(now - DG_CUT_AT) > 30000){ DG_CUT = dgCut(LIVE_DIGEST, now); DG_CUT_AT = now; }
  return DG_CUT;
}

/* Every game of the packet's week has kicked off (LIVE_SCHEDULE): its injury list is moot and next
   week's is not written until Tuesday's run, so an empty Hurt row says so (David, 2026-09-29). */
function dgWeekDone(d){
  const games = typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE ? LIVE_SCHEDULE.games.filter(g => g.week === d.week) : [];
  const now = Date.now();
  return games.length > 0 && games.every(g => Date.parse(g.kickoff) <= now);
}

/* The week a Digest row names: the page's, never the packet's plus one on the reader's clock (2026-10-05);
   between the last kickoff and the turn that week is over, and the row waits for the next one's. */
const dgRowWeek = d => schedWeek() === d.week && dgWeekDone(d) ? d.week + 1 : schedWeek() ?? d.week;

/* Top 5 is Ranks' own rows (2026-09-29, storyboard https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz,
   5A; David: "it's supposed to be forward looking"). The packet's top5 is cut from the week the
   digest was written, so it emptied once that week's games began, and the wait card said
   "projections land Tuesday" while Ranks already showed next week's. Reading LIVE_RANKS, the two can
   never disagree. A game under way leaves, and so do tonight's teams, whose card holds them. */
const DG_T5_POS = ["QB", "RB", "WR", "TE", "FLEX"];
function dgTop5(d, pos){
  const now = Date.now(), tn = new Set((d.tn || []).flatMap(g => [g.away, g.home]));
  return rkList(pos).filter(r => !(r.kick && Date.parse(r.kick) <= now) && !tn.has(r.team)).slice(0, 5);
}

/* Weather is the Weather view's own reading (2026-09-29, the same storyboard, 6A; David: "the next
   tab over is the weather and it's actually already live"): only a forecast that meets a condition
   the backtest proved (data/weather.js wtRows), and only for a game still to come. The packet's
   15 mph / 50% list was a second rule that disagreed with the tab beside it. */
const dgWxMoves = () => wtRows().moves.filter(r => !r.done);

/* The Recap row's rule (2026-10-05; David: the Digest is "a curated list of content ... not just a
   results section that stays there for the whole week and quickly become stale"). LIVE_RECAP is the
   week This week > Recap shows, the newest with half its games final. The row points at it from that
   half-way mark until the end of the first Wednesday after the week's last kickoff, in the reader's
   own day; then the Digest is next week's alone. Without a kickoff to count from, no row. */
const DG_RECAP_DAY = 3;      // Wednesday, as Date.getDay() says it
function dgRecapEnd(r){
  const sched = typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE ? LIVE_SCHEDULE.games.filter(g => g.week === r.week) : [];
  const ks = [...r.games, ...sched].map(g => Date.parse(g.kickoff)).filter(k => !isNaN(k));
  if (!ks.length) return null;
  const last = new Date(Math.max(...ks));
  const ahead = (DG_RECAP_DAY - last.getDay() + 7) % 7 || 7;   // days to the first Wednesday after his day
  return new Date(last.getFullYear(), last.getMonth(), last.getDate() + ahead + 1).getTime();   // that day's midnight, its end
}
function dgRecap(){
  const r = typeof LIVE_RECAP !== "undefined" ? LIVE_RECAP : null;
  if (!r || !r.n_games || r.n_final * 2 < r.n_games) return null;
  const end = dgRecapEnd(r);
  return end !== null && Date.now() < end ? r : null;
}

/* Does the section hold anything at all. An empty one says "nothing new" and cannot open. */
function dgHas(id){
  const d = dgD();
  if (!d) return false;
  return {recap: dgRecap(), hurt: d.hurt.length, mu: d.best.length || d.calls,
          wx: dgWxMoves().length, adds: d.adds.length, t5: dgTop5(d, "QB").length,
          gems: d.gems.length, news: d.news.length}[id] ? true : false;
}

/* Is there news in it, which is what earns the day's open: anything at all. */
const dgNew = id => dgHas(id);

/* Where the week stands (2026-10-04; lived in surface/digest until the model-to-view direction was
   restored). One game of the week is "pre", "live" or "final", from the clock the views share (ESPN's,
   else Sleeper's) and then the time: past kickoff plus the padding live.js keeps for a game's length
   with no word from either. */
const DG_LATE_MAX = 2;      // a last day with more games than this is the main slate, not a standalone slot
function dgGameState(g, now){
  const c = gdClockOf(g.home).state;
  if (c === "post") return "final";
  if (c === "in") return "live";
  const k = Date.parse(g.kickoff);
  if (isNaN(k) || k > now) return "pre";
  return now < k + GD_GAME_MS ? "live" : "final";
}

const dgDayKey = k => { const d = new Date(k); return d.getFullYear() * 10000 + d.getMonth() * 100 + d.getDate(); };

/* `mnf` is the standalone last slot (Monday, or any last game on a day of its own) once every game
   before its day is final and it is not: [{g, k, st}], else null. */
function dgWeek(now){
  const rows = gdWeekGames().map(g => ({g, k: Date.parse(g.kickoff), st: dgGameState(g, now)})).filter(r => !isNaN(r.k));
  if (!rows.length) return {rows, started: false, done: false, mnf: null};
  const last = Math.max(...rows.map(r => dgDayKey(r.k)));
  const late = rows.filter(r => dgDayKey(r.k) === last), early = rows.filter(r => dgDayKey(r.k) < last);
  const done = rows.every(r => r.st === "final");
  const mnf = !done && early.length && late.length <= DG_LATE_MAX && early.every(r => r.st === "final")
    && late.some(r => r.st !== "final") ? late : null;
  return {rows, started: rows.some(r => r.st !== "pre"), done, mnf};
}

/* The late slot, once the poll has said where everyone stands: [{g, k, st}] or null. */
function dgMnfSlot(now){
  if (!GD_STATS) return null;
  return dgWeek(now).mnf;
}

/* The week's preview rows, and whether they are waiting on next week: every game has kicked off
   and tonight's card is gone. They then leave the ticker (the card that stood in for them, "Waiting on
   week N", left on 2026-10-05; Need to know says the report is still to come).
   Weather and Top 5 no longer wait (2026-09-29): both read next week's data the page already has. */
const DG_WAIT_ROWS = ["hurt", "mu"];
/* The last game's card (surface/digest/mnf.js) is a card of the week, so the wait does not start under it. */
const dgWaiting = d => !!d && !d.tn.length && dgWeekDone(d) && dgMnfSlot(Date.now()) === null;

/* Is the row drawn at all: Recap while the week's results are fresh, and the week's preview rows unless
   tonight's card holds everything the week has left, or the week is over and they wait. */
function dgShown(id){
  const d = dgD();
  if (id === "recap") return dgHas(id);
  if (dgWaiting(d) && DG_WAIT_ROWS.includes(id)) return false;
  return !(d && d.tnLast && DG_TN_ROWS.includes(id));
}

const dgDayRow = () => (DG_DAY[new Date(Date.now()).getDay()] || []).find(id => dgShown(id) && dgNew(id)) || null;
const dgOpenRow = () => DG_OPEN === null ? dgDayRow() : DG_OPEN;

/* A surname for the one-line rows ("Smith-Njigba", "Walker"): the last word that is not a suffix. */
const DG_SUFFIX = /^(jr\.?|sr\.?|ii|iii|iv|v)$/i;
function dgLast(name){
  const w = String(name || "").split(/\s+/).filter(Boolean);
  while (w.length > 1 && DG_SUFFIX.test(w[w.length - 1])) w.pop();
  return w[w.length - 1] || "";
}

/* A big count as the eye reads it: 4,039,301 -> "4.0M", 832,977 -> "833K", 950 -> "950". */
const dgBig = n => n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "K" : String(n);

/* "4.0M adds": a Sleeper-sourced add's number (2026-09-28), shared by the Digest row and Waivers'
   Most added. The ESPN fallback keeps each reader's own % wording. */
const dgAddCount = a => t("digest.adds.count", {n: dgBig(a.count)});

/* A signed number with a true minus: +3.7, −4.3. */
const dgSigned = (v, dp) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(dp);
/* A percentage as a whole number, except that 99.9 stays 99.9: "100% rostered" would be false. */
const dgPct = v => (v >= 99.5 && v < 100 ? v.toFixed(1) : Math.round(v).toFixed(0));
/* "LA @ DEN", escaped: the game as every row writes it. */
const dgGame = g => `${esc(g.away)} @ ${esc(g.home)}`;
/* "D. Smith", "A. St. Brown": the first initial and the whole surname, suffix dropped; the Q list
   and the Results lists. The surname is every word after the first, not the last one alone. A short
   form two players on one NFL team share keeps the first name: ATL has Bijan and Brian Robinson, and
   "B. Robinson" could be either (David, 2026-09-29). */
function dgShort(name){
  const w = String(name || "").split(/\s+/).filter(Boolean);
  while (w.length > 2 && DG_SUFFIX.test(w[w.length - 1])) w.pop();
  if (w.length < 2) return name;
  const short = `${w[0][0]}. ${w.slice(1).join(" ")}`;
  return dgClashes().has(short) ? w.join(" ") : short;
}

/* The short forms two players on one team share, from every player the page carries (search.js's
   index, joined by slug). Read once: the teams do not change while the page is open. */
let DG_CLASH = null;
function dgClashes(){
  if (DG_CLASH) return DG_CLASH;
  const seen = new Map(), clash = new Set();
  for (const e of searchIndex()){
    const w = String(e.n || "").split(/\s+/).filter(Boolean);
    while (w.length > 2 && DG_SUFFIX.test(w[w.length - 1])) w.pop();
    if (w.length < 2 || !e.team) continue;
    const short = `${w[0][0]}. ${w.slice(1).join(" ")}`, key = `${short}|${e.team}`;
    const first = seen.get(key);
    if (first && first !== e.slug) clash.add(short);
    else seen.set(key, e.slug);
  }
  DG_CLASH = clash;
  return clash;
}

/* Which bar a game crossed, wind or rain, for the word a row leads with: the packet's own `bar`, so
   no threshold is copied here (ff-jarvis weekly_digest_schema owns them, in LIVE_DIGEST.rules). */
const dgWxKind = g => g.bar;
