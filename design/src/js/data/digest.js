/* The Digest's state and its reading of LIVE_DIGEST (design/digest.py). ff-jarvis picks the lead,
   ranks every row and writes the same packet the morning Discord post renders; the page only
   decides which one row lies open. */

/* The ticker, top to bottom. Each id is one topic and one row. Results shows only once a game is
   final (2026-09-28): an empty "Results" row all week would be noise. */
const DG_ROWS = ["res", "hurt", "start", "mu", "wx", "adds", "t5", "st", "gems", "news"];
const DG_POS = ["QB", "RB", "WR", "TE"];

/* The row the reader opened by hand ("" when he closed it); null until the first tap, and while
   it is null the day picks. Kept across views, so coming back finds the row where it was left. */
let DG_OPEN = null;

/* The signature: the day picks the open row. Claims are Tuesday and Wednesday, so the wire's
   adds lead; Sunday is game day, so who is hurt, then the weather if nobody new is; Monday, the
   week's results; every other day, who is hurt. The reader's local day, from Date.now(), which
   the render suite pins. */
const DG_DAY = {0: ["hurt", "wx"], 1: ["res", "hurt"], 2: ["adds"], 3: ["adds"]};

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
   gives way to the week's results, then to the top headline: the packet's own order of rules. */
function dgLeadAfter(d, c){
  const L = d.lead;
  if (L && L.rule === "results") return c.finals.length ? L : null;
  const was = L && ({hurt: d.hurt, weather: d.wx, news: d.news}[L.rule] || [])[L.index];
  const at = was ? (c.leadRows[L.rule] || []).indexOf(was) : -1;
  if (at >= 0) return {rule: L.rule, index: at};
  return c.finals.length ? {rule: "results", index: 0} : c.news.length ? {rule: "news", index: 0} : null;
}

/* Tonight's card (2026-09-28, storyboard JSPwg21i9YaTSzhYqAEnQZ) shows from 18 hours before its
   kickoff until 4 hours after, so a packet cut Friday for Monday night waits for Monday, and a tab
   left open overnight lets it go. While it shows, its teams' rows live in the card, not the ticker;
   when its games are all the week has left (`tonight_last`), the week's preview rows go too. */
const DG_TN_BEFORE = 18 * 3600e3, DG_TN_AFTER = 4 * 3600e3;
/* Starters stays: a change after a team's game is next week's news, not this slot's preview. */
const DG_TN_ROWS = ["hurt", "mu", "wx", "t5", "st"];
function dgTonightCut(c, now){
  const tn = (c.tonight || []).filter(g => { const k = Date.parse(g.ko); return now >= k - DG_TN_BEFORE && now < k + DG_TN_AFTER; });
  if (!tn.length) return {...c, tn: [], tnLast: false};
  const teams = new Set(tn.flatMap(g => [g.away, g.home]));
  const off = r => !teams.has(r.team), offGame = g => !teams.has(g.home) && !teams.has(g.away);
  return {...c, tn, tnLast: !!c.tonight_last, hurt: c.hurt.filter(off),
          best: c.best.filter(off), top5: c.top5.filter(off),
          up: c.up.filter(off), down: c.down.filter(off), wx: c.wx.filter(offGame), near: c.near && offGame(c.near) ? c.near : null};
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

/* Does the section hold anything at all. An empty one says "nothing new" and cannot open. */
function dgHas(id){
  const d = dgD();
  if (!d) return false;
  return {res: d.finals.length || d.stars.length, hurt: d.hurt.length, start: d.starters.length, mu: d.best.length || d.calls,
          wx: d.wx.length || d.near, adds: d.adds.length, t5: d.top5.length, st: d.up.length || d.down.length,
          gems: d.gems.length, news: d.news.length}[id] ? true : false;
}

/* Is there news in it, which is what earns the day's open: a hurt row changed in the last 24
   hours, a game past the weather bar; any other section, anything at all. */
function dgNew(id){
  const d = dgD();
  if (id === "hurt") return !!d && d.hurt.some(r => r.new);
  if (id === "wx") return !!d && d.wx.length > 0;
  return dgHas(id);
}

/* The week's preview rows, and whether they are waiting on next week: every game has kicked off
   and tonight's card is gone. They then leave the ticker for one card (surface/digest/wait.js). */
const DG_WAIT_ROWS = ["hurt", "mu", "wx", "t5"];
const dgWaiting = d => !!d && !d.tn.length && dgWeekDone(d);

/* Is the row drawn at all: Results once a game is final, and the week's preview rows unless
   tonight's card holds everything the week has left, or the week is over and they wait. */
function dgShown(id){
  const d = dgD();
  if (id === "res") return dgHas(id);
  if (dgWaiting(d) && DG_WAIT_ROWS.includes(id)) return false;
  return !(d && d.tnLast && DG_TN_ROWS.includes(id));
}

const dgDayRow = () => (DG_DAY[new Date(Date.now()).getDay()] || ["hurt"]).find(id => dgShown(id) && dgNew(id)) || null;
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
   and the Results lists. The surname is every word after the first, not the last one alone. */
function dgShort(name){
  const w = String(name || "").split(/\s+/).filter(Boolean);
  while (w.length > 2 && DG_SUFFIX.test(w[w.length - 1])) w.pop();
  return w.length > 1 ? `${w[0][0]}. ${w.slice(1).join(" ")}` : name;
}

/* Which bar a game crossed, wind or rain, for the word a row leads with: the packet's own `bar`, so
   no threshold is copied here (ff-jarvis weekly_digest_schema owns them, in LIVE_DIGEST.rules). */
const dgWxKind = g => g.bar;
