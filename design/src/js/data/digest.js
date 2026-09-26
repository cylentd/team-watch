/* The Digest's state and its reading of LIVE_DIGEST (design/digest.py). ff-jarvis picks the lead,
   ranks every row and writes the same packet the morning Discord post renders; the page only
   decides which one row lies open. */

/* The ticker, top to bottom. Each id is one topic and one row. */
const DG_ROWS = ["hurt", "mu", "wx", "adds", "t5", "st", "gems", "news"];
const DG_POS = ["QB", "RB", "WR", "TE"];

/* The row the reader opened by hand ("" when he closed it); null until the first tap, and while
   it is null the day picks. Kept across views, so coming back finds the row where it was left. */
let DG_OPEN = null;

/* The signature: the day picks the open row. Claims are Tuesday and Wednesday, so the wire's
   adds lead; Sunday is game day, so who is hurt, then the weather if nobody new is; every other
   day, who is hurt. The reader's local day, from Date.now(), which the render suite pins. */
const DG_DAY = {0: ["hurt", "wx"], 2: ["adds"], 3: ["adds"]};

const dgD = () => (typeof LIVE_DIGEST !== "undefined" ? LIVE_DIGEST : null);

/* Does the section hold anything at all. An empty one says "nothing new" and cannot open. */
function dgHas(id){
  const d = dgD();
  if (!d) return false;
  return {hurt: d.hurt.length, mu: d.best.length || d.calls, wx: d.wx.length || d.near, adds: d.adds.length,
          t5: d.top5.length, st: d.up.length || d.down.length, gems: d.gems.length, news: d.news.length}[id] ? true : false;
}

/* Is there news in it, which is what earns the day's open: a hurt row changed in the last 24
   hours, a game past the weather bar; any other section, anything at all. */
function dgNew(id){
  const d = dgD();
  if (id === "hurt") return !!d && d.hurt.some(r => r.new);
  if (id === "wx") return !!d && d.wx.length > 0;
  return dgHas(id);
}

const dgDayRow = () => (DG_DAY[new Date(Date.now()).getDay()] || ["hurt"]).find(dgNew) || null;
const dgOpenRow = () => DG_OPEN === null ? dgDayRow() : DG_OPEN;

/* A surname for the one-line rows ("Smith-Njigba", "Walker"): the last word that is not a suffix. */
const DG_SUFFIX = /^(jr\.?|sr\.?|ii|iii|iv|v)$/i;
function dgLast(name){
  const w = String(name || "").split(/\s+/).filter(Boolean);
  while (w.length > 1 && DG_SUFFIX.test(w[w.length - 1])) w.pop();
  return w[w.length - 1] || "";
}

/* A signed number with a true minus: +3.7, −4.3. */
const dgSigned = (v, dp) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(dp);
/* A percentage as a whole number, except that 99.9 stays 99.9: "100% rostered" would be false. */
const dgPct = v => (v >= 99.5 && v < 100 ? v.toFixed(1) : Math.round(v).toFixed(0));
/* "LA @ DEN", escaped: the game as every row writes it. */
const dgGame = g => `${esc(g.away)} @ ${esc(g.home)}`;
/* "D. Smith": the Q list and other one-line name runs. */
const dgShort = name => { const w = String(name || "").split(/\s+/); return w.length > 1 ? `${w[0][0]}. ${dgLast(name)}` : name; };

/* Which bar a game crossed, wind or rain, for the word a row leads with: the packet's own `bar`, so
   no threshold is copied here (ff-jarvis weekly_digest_schema owns them, in LIVE_DIGEST.rules). */
const dgWxKind = g => g.bar;
