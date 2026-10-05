/* ============================== GAMEDAY: FRESH TD CLIPS ==============================
   Live > TDs' TD clips reel (2026-10-05, storyboard https://claude.ai/artifact/5GZZ3GCcsp9znxzjiNrjKB)
   names a clip of each scorer the minute YouTube has it. The page's own LIVE_CLIPS is the finished week's,
   matched by Claude; on game day the reel also asks our function for fresh ones:

     GET /api/clips?ch=<code>  ->  {"ch", "clips": [{id, title, posted, secs, shape, embed}]}

   One request per channel (an nflverse team code, or NFL), at most TD_CLIPS_FLIGHT at once. The channels
   are the clubs whose game is on or ended less than TD_CLIPS_AFTER ago, plus NFL while there is one; a
   page opened fresh asks, once, for the games that ended less than TD_CLIPS_OPEN ago too, so a reader
   who arrives after the last whistle still gets the day's clips. It asks only while the TDs tab (Feed) is
   on screen and the tab is visible, and never sooner than TD_CLIPS_MS after the last round: tdcEnsure()
   is called when the tab paints, and live.js's own 30 s poll repaints it while a game is on.

   A channel's reply is merged into what the channel already held, by id (TDC), and clips posted more than
   TD_CLIPS_HOURS ago are dropped: the NFL channel posts 35-43 uploads an hour on a Sunday, so its 50 newest
   reach back barely two hours, and the 1 pm clips would be gone by the 4 pm window. A request that fails
   keeps that channel's clips. Who a clip is of is tdcmatch.js. */

const TD_CLIPS_MS = 300000;
const TD_CLIPS_HOURS = 30;
const TD_CLIPS_FLIGHT = 4;
const TD_CLIPS_LEN = 11700000;       /* a game's usual length, 3 h 15 min: a final's end is guessed from the kickoff */
const TD_CLIPS_AFTER = 3600e3;       /* a game's channels are asked for until this long after it ended */
const TD_CLIPS_OPEN = 6 * 3600e3;    /* the first round of a page asks for games that ended this recently */
let TDC = {by: {}, at: 0, busy: false, rounds: 0, over: {}};   /* by: channel code -> its clips, newest first; over: game -> when it was first seen final */

/* Function declarations, so a test can stand in for the page's origin and the build's names. */
function tdcServed(){ return PAGE_SERVED(); }
function tdcNameRow(slug){ return (typeof LIVE_NAMES !== "undefined" && LIVE_NAMES && LIVE_NAMES[slug]) || null; }

/* A club's channel code: nflverse's spelling (LA, WAS), whichever one the caller holds. */
function tdcCode(club){
  const alias = (typeof LIVE_CLIPS !== "undefined" && LIVE_CLIPS && LIVE_CLIPS.alias) || GD_ALIAS;
  return gdCodes(club).find(c => alias[c]) || club;
}

/* The games whose clips are worth asking for: on now, or ended less than `slack` ago. A final's end is the
   kickoff plus a usual game, or the moment this page first saw it final, whichever is sooner; a game
   neither ESPN nor Sleeper has a word on is taken for the schedule's. */
function tdcGames(now, slack){
  return GD_GAMES.filter(g => {
    const k = Date.parse(g.kickoff), age = now - k;
    if (isNaN(k) || age < 0 || age >= GD_GAME_MS + slack) return false;
    const a = gdClockOf(g.home).state, state = a !== "pre" ? a : gdClockOf(g.away).state, key = `${g.home}@${g.away}`;
    if (state === "in") return age < GD_GAME_MS;
    if (state !== "post") return age < TD_CLIPS_LEN + TD_CLIPS_AFTER;
    TDC.over[key] = Math.min(TDC.over[key] === undefined ? Infinity : TDC.over[key], now);
    return now - Math.min(k + TD_CLIPS_LEN, TDC.over[key]) < slack;
  });
}

/* The clubs of those games, then NFL. */
function tdcChannels(games){
  const out = new Set();
  for (const g of games) out.add(tdcCode(g.home)).add(tdcCode(g.away));
  return [...out, "NFL"];
}

const tdcSig = () => JSON.stringify(Object.keys(TDC.by).sort().map(ch => [ch, TDC.by[ch].map(c => c.id)]));

/* A reply into the channel's clips: by id (the newer wins), none older than TD_CLIPS_HOURS, newest first. */
function tdcMerge(ch, clips, now){
  const all = new Map(), cut = now - TD_CLIPS_HOURS * 3600e3;
  for (const c of [...(TDC.by[ch] || []), ...clips]) if (c && c.id) all.set(c.id, c);
  TDC.by[ch] = [...all.values()].filter(c => Date.parse(c.posted) >= cut).sort((a, b) => Date.parse(b.posted) - Date.parse(a.posted));
}

async function tdcOne(ch){
  try {
    const res = await fetch(`/api/clips?ch=${encodeURIComponent(ch)}`, {headers: {"Accept": "application/json"}});
    const body = res.ok ? await res.json().catch(() => null) : null;
    if (body && Array.isArray(body.clips)) tdcMerge(ch, body.clips, Date.now());
  } catch (e) { /* this channel keeps its clips */ }
}

async function tdcRound(now, games){
  TDC.busy = true; TDC.at = now; TDC.rounds++;
  const todo = tdcChannels(games), before = tdcSig();
  const lane = async () => { while (todo.length) await tdcOne(todo.shift()); };
  try { await Promise.all(Array.from({length: Math.min(TD_CLIPS_FLIGHT, todo.length)}, () => lane())); }
  finally { TDC.busy = false; }
  if (tdcSig() !== before) paintLive();
}

function tdcEnsure(){
  const now = Date.now();
  if (TDC.busy || now - TDC.at < TD_CLIPS_MS || !tdcServed()) return;
  if (SURFACE !== "live" || !gdOnScreen() || gdTab() !== "tds" || tdMode() !== "feed") return;
  const games = tdcGames(now, TDC.rounds ? TD_CLIPS_AFTER : TD_CLIPS_OPEN);
  if (games.length) tdcRound(now, games);
}
