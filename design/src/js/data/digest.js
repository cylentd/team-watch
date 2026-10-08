/* The Digest's state and its reading of LIVE_DIGEST (design/digest.py). ff-jarvis writes the packet; the page
   decides which subject leads it. Which day's job it shows is the day plan, data/dayplan.js. */

const DG_POS = ["QB", "RB", "WR", "TE"];

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

/* Tonight's game (2026-09-28, storyboard JSPwg21i9YaTSzhYqAEnQZ) is held from 18 hours before its kickoff until
   4 hours after. Since 2026-10-08 (Home draft B) its rows stay in the lists: the card of its own players left Home,
   so Injury watch and the rest rank them with everyone else until kickoff, when dgCut drops them. */
const DG_TN_BEFORE = 18 * 3600e3, DG_TN_AFTER = 4 * 3600e3;
function dgTonightCut(c, now){
  const tn = (c.tonight || []).filter(g => { const k = Date.parse(g.ko); return now >= k - DG_TN_BEFORE && now < k + DG_TN_AFTER; });
  return {...c, tn, tnLast: tn.length ? !!c.tonight_last : false};
}

/* Cut once per half minute, not once per row: every row asks dgD() several times a render. */
let DG_CUT = null, DG_CUT_AT = 0;
function dgD(){
  if (typeof LIVE_DIGEST === "undefined" || !LIVE_DIGEST) return null;
  const now = Date.now();
  if (!DG_CUT || Math.abs(now - DG_CUT_AT) > 30000){ DG_CUT = dgCut(LIVE_DIGEST, now); DG_CUT_AT = now; }
  return DG_CUT;
}

/* Every game of the packet's week has kicked off (LIVE_SCHEDULE): its injury list is moot (2026-09-29). */
function dgWeekDone(d){
  const games = typeof LIVE_SCHEDULE !== "undefined" && LIVE_SCHEDULE ? LIVE_SCHEDULE.games.filter(g => g.week === d.week) : [];
  const now = Date.now();
  return games.length > 0 && games.every(g => Date.parse(g.kickoff) <= now);
}

/* The week Need to know names: the page's (2026-10-05); after its last kickoff, the next one's. */
const dgRowWeek = d => schedWeek() === d.week && dgWeekDone(d) ? d.week + 1 : schedWeek() ?? d.week;

/* Weather is the Weather view's own reading (2026-09-29): only a forecast that meets a condition the
   backtest proved (data/weather.js wtRows), for a game still to come. The Weather card reads it. */
const dgWxMoves = () => wtRows().moves.filter(r => !r.done);

/* The Recap chip's rule (2026-10-05; a ticker row until 2026-10-06): LIVE_RECAP's week, from half its games
   final until the end of the first Wednesday after its last kickoff, in the reader's own day. No kickoff, no chip. */
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

/* Whether the week's preview lists wait on next week: every game has kicked off and tonight's card is
   gone (Need to know then says the report is still to come). The last game's card (surface/digest/mnf.js)
   is a card of the week, so the wait does not start under it. */
const dgWaiting = d => !!d && !d.tn.length && dgWeekDone(d) && dgMnfSlot(Date.now()) === null;

const DG_SUFFIX = /^(jr\.?|sr\.?|ii|iii|iv|v)$/i;

/* A big count as the eye reads it: 4,039,301 -> "4.0M", 832,977 -> "833K", 950 -> "950". */
const dgBig = n => n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "K" : String(n);

/* "4.0M adds": a Sleeper-sourced add's number (2026-09-28), Waivers' Most added. */
const dgAddCount = a => t("digest.adds.count", {n: dgBig(a.count)});

/* A signed number with a true minus: +3.7, −4.3. */
const dgSigned = (v, dp) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(dp);
/* A percentage as a whole number, except that 99.9 stays 99.9: "100% rostered" would be false. */
const dgPct = v => (v >= 99.5 && v < 100 ? v.toFixed(1) : Math.round(v).toFixed(0));
/* "LA @ DEN", escaped: the game as every row writes it. */
const dgGame = g => `${esc(g.away)} @ ${esc(g.home)}`;
/* "D. Smith", "A. St. Brown": the first initial and every word after it, suffix dropped. A short form two
   players on one NFL team share keeps the first name: ATL's Bijan and Brian Robinson (David, 2026-09-29). */
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

/* Which bar a game crossed, wind or rain: the packet's own `bar`, so no threshold is copied here. */
const dgWxKind = g => g.bar;
