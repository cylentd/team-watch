/* ============================== LEAGUE > TRADES: TRADE OFFERS, THE DATA ==============================
   2026-10-05; v2 2026-10-06. ff-jarvis's trade_offers.json (design/trade_offers.py writes it beside the page): for
   every owner in every league one flat list of offers ranked by gain, each with its `partner`: per position the best
   offers whose `get` holds a player there, and per partner his best. ~360 KB, so it is not in the page: it is
   fetched the first time a reader opens the finder (finder/finder.js) and kept in memory for the session. From
   file:// or offline the fetch fails and the page says so, with a button to try again. An offer is what each side
   sends, the owner's one number, `gain`, and who the owner moves to IR (`ir_moves`) or drops to stay at the roster
   cap. The page scores nothing but the reader's own packages (Edit, tbedit.js, with tbscore.js's port of the rule).

   An owner and a partner are the teams' names as the League board has them (LIVE_TEAMS), which are the names
   in ff-jarvis's roster files, the same ones the offers are keyed by. */
const TB_URL = "trade_offers.json";
let TB_DATA = null;     // the file, once fetched
let TB_ERR = false;     // the last fetch failed
let TB_BUSY = null;     // the fetch in flight, so two opens share one request

/* True when the file is in TB_DATA. Always resolves, never throws: the page paints what it has. */
function tbLoad(){
  if (TB_DATA) return Promise.resolve(true);
  if (TB_BUSY) return TB_BUSY;
  TB_ERR = false;
  TB_BUSY = (async () => {
    try {
      const r = await fetch(TB_URL);
      if (!r.ok) throw new Error(String(r.status));
      const d = await r.json();
      if (!d || typeof d.leagues !== "object") throw new Error("shape");   // an HTML page where the file should be
      TB_DATA = d;
    } catch (e) { TB_ERR = true; }
    TB_BUSY = null;
    return !!TB_DATA;
  })();
  return TB_BUSY;
}

/* The league a team is in, and the reader's own team there (null when they picked none or one elsewhere). */
const tbLeagueOf = key => ((lbData() || {}).leagues || []).find(l => l.teams.some(x => x.key === key)) || null;
const tbMine = lg => { const k = myTeamLoad(); return lg && k ? lg.teams.find(x => x.key === k) || null : null; };

/* What a Teams card's foot offers: "find" (the reader's own team is in this league and is another: "Trades with
   them"), "set" (This is my team: the reader has no team in this league), "own" (it is the reader's team: nothing to
   trade with) or "" (a team the page cannot make the reader's, which TEAMS does not list). */
function tbGate(tm){
  const lg = tbLeagueOf(tm.key), me = tbMine(lg);
  return !lg ? "" : !me ? (TEAMS[tm.key] ? "set" : "") : me.key === tm.key ? "own" : "find";
}

/* The owner's offers in this league, as the file ranks them (best gain first); [] when it has none for him. */
const tbOffersOf = (lg, me) => ((((TB_DATA || {}).leagues || {})[lg.key] || {}).teams || {})[me.name] || [];

/* ---- Edit's guard (2026-10-05): the page re-scores the offers it loads with tbscore.js and shuts Edit when it
   cannot reproduce them. The file is ff-jarvis's, the port is the page's, and a rule that changed on one side
   only would otherwise show the reader a wrong number on a card they built themselves. Fails closed: a missing
   field (an offer's `their` too, since option B), a player the roster does not list, a gain more than 0.15 off or a
   different drop, IR move or `their` shuts Edit and Make
   your own for the session (the offers still show), and the console names the offer. Since v2 (2026-10-06) the
   guard checks every offer of the owner, each against its own partner's values, once per owner. ---- */
const TB_TOL = 0.15;
let TB_GUARD = {data: null, shut: false, seen: {}};   // per file in memory: a shut guard stays shut, an owner is checked once

const tbLeagueData = lg => ((TB_DATA || {}).leagues || {})[lg.key] || null;

/* The K/DST/other non-IR players a team holds, which count toward the cap but are not in `values`: the league's
   `other` map, team name to count (a league with no entry for the team holds none). */
const tbOther = (lgd, team) => ((lgd || {}).other || {})[team] || 0;

/* The offer's players, as the roster lists them (with `proj` and `ir`), or null when one is not on it. */
function tbResolve(list, roster){
  const rows = (list || []).map(p => roster.find(r => tbKey(r) === tbKey(p)));
  return rows.every(Boolean) ? rows : null;
}

/* True when a roster carries what the drop rule reads: a `keep` number and the two flags on every player. A file
   from before the rule (2026-10-05) has none, and the page cannot score it. */
const tbRuled = rows => rows.every(p => typeof p.keep === "number" && typeof p.ir_ok === "boolean" && typeof p.protect === "boolean");

/* True when an offer's `their` (the partner's room after the trade, option B) is there: both lists, possibly empty. */
const tbTheirOk = th => !!th && Array.isArray(th.ir_moves) && Array.isArray(th.drop);

/* The reason this owner's offers cannot be scored, or "" when every one re-scores to its gain, its IR moves and its
   drop. `list` is the owner's offers (tbOffersOf), each with its partner's name. */
function tbMismatch(lgd, me, list){
  const lu = lgd && lgd.lineup, mine = lgd && lgd.values && lgd.values[me.name];
  if (!lu || !mine) return "no lineup or values for this owner";
  if (typeof lu.ir !== "number" || !tbRuled(mine)) return "no IR slots, keep, ir_ok or protect: the file predates the drop rule";
  for (const [i, o] of (list || []).entries()){
    const theirs = lgd.values[o.partner];
    if (!theirs || !tbRuled(theirs)) return `offers[${i}] is with ${o.partner}, who has no values the drop rule reads`;
    const send = tbResolve(o.send, mine), get = tbResolve(o.get, theirs);
    if (!send || !get || !Array.isArray(o.drop) || !Array.isArray(o.ir_moves) || !tbTheirOk(o.their)) return `offers[${i}] has a player the roster does not list, or no drop, ir_moves or their`;
    const r = tbGain(mine, send, get, lu, tbOther(lgd, me.name)), th = tbTheir(theirs, send, get, lu, tbOther(lgd, o.partner));
    const names = list => list.map(tbKey).join("|");      // the producer's order is the rule's
    const same = r.ok && names(r.drop) === names(o.drop) && names(r.irMoves) === names(o.ir_moves);
    const sameTheirs = names(th.irMoves) === names(o.their.ir_moves) && names(th.drop) === names(o.their.drop);
    if (!(Math.abs(r.gain - o.gain) <= TB_TOL) || !same || !sameTheirs) return `offers[${i}] scores ${r.gain}${same && sameTheirs ? "" : " and moves, drops or makes room for them differently"}, the file says ${o.gain}`;
  }
  return "";
}

/* True when Edit and Make your own may show for this owner. */
function tbEditOk(lg, me){
  if (!TB_DATA || !lg || !me) return false;
  if (TB_GUARD.data !== TB_DATA) TB_GUARD = {data: TB_DATA, shut: false, seen: {}};
  if (TB_GUARD.shut) return false;
  const k = `${lg.key}|${me.name}`;
  if (!(k in TB_GUARD.seen)){
    const why = tbMismatch(tbLeagueData(lg), me, tbOffersOf(lg, me));
    TB_GUARD.seen[k] = !why;
    if (why){ TB_GUARD.shut = true; console.warn(`trade finder: Edit is off, ${me.name}: ${why}`); }
  }
  return TB_GUARD.seen[k];
}

/* ---- the message the reader pastes to the other manager: true points a game, "seen", except a Hot player the
   reader SENDS, who is quoted on his last 2 (option B, 2026-10-05: managers price a hot streak, so the reader sells
   high); a Hot player the reader gets stays on his season average ---- */
const tbSurname = n => { const p = String(n).trim().split(/\s+/); return p.length < 2 || /D\/ST$/.test(n) ? String(n) : p.slice(1).join(" "); };
const tbJoin = list => list.length === 2 ? list.join(t("lboard.offer.and")) : list.join(", ");

/* A Hot player carries his last 2 games' average (`last2`), which the file sets for every Hot player. */
const tbHot = p => (p.chips || []).includes("Hot") && typeof p.last2 === "number";

/* "Higgins (14.4 a game)" or, when he is Hot and the reader sends him (`sells`), "McMillan (20.5 a game his last 2)". `unit` puts "a game" on a season average. */
const tbOne = (p, unit, sells) => `${tbSurname(p.name)} (${sells && tbHot(p) ? t("lboard.offer.last2", {n: lbNum(p.last2)})
  : unit ? t("lboard.offer.game", {n: lbNum(p.seen)}) : lbNum(p.seen)})`;

/* One side of the message. Only the side the reader SENDS (`sells`) quotes a Hot player on his last 2, selling high; every
   player the reader GETS is quoted on his season average, Hot or not, so the ask is never inflated. `unit` goes on the
   side's first season average, so a Hot player ahead of it says his own unit. */
function tbSide(list, unit, sells){
  const at = unit ? list.findIndex(p => !(sells && tbHot(p))) : -1;
  return tbJoin(list.map((p, i) => tbOne(p, i === at, sells)));
}

/* The partner's room, one or two sentences, from a `their` ({ir_moves, drop}, as the file has it): "D. Smith can go to
   your IR slot, so you don't cut anyone." or "You'd only need to cut K. Johnson." and, with both, the two one after the
   other. Empty when there is nothing to say. Initials, plain text: it goes on the clipboard. */
function tbTheirText(th){
  const ir = (th || {}).ir_moves || [], cut = (th || {}).drop || [], plain = list => tbJoin(list.map(p => nameInitial(p.name)));
  const names = {names: plain(ir)}, many = ir.length > 1;      // every key literal: assemble --check cannot see a built one
  const first = !ir.length ? "" : cut.length
    ? (many ? t("lboard.offer.theirIrCutMany", names) : t("lboard.offer.theirIrCut", names))
    : (many ? t("lboard.offer.theirIrMany", names) : t("lboard.offer.theirIr", names));
  return [first, cut.length ? t("lboard.offer.theirCut", {names: plain(cut)}) : ""].filter(Boolean).join(" ");
}

/* "Trade? I send Purdy (28.8 a game), Higgins (14.4) for Smith-Njigba (25.3) and Brown (11.4). D. Smith can go to your
   IR slot, so you don't cut anyone." The first season average carries the unit; `o.their` is the partner's room. */
function tbText(o){
  const room = tbTheirText(o.their);
  return t("lboard.offer.text", {send: tbSide(o.send, true, true), get: tbSide(o.get, false, false)}) + (room ? " " + room : "");
}
