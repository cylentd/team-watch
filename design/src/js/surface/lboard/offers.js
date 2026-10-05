/* ============================== LEAGUE > TEAMS: TRADE OFFERS, THE DATA ==============================
   2026-10-05. ff-jarvis's trade_offers.json (design/trade_offers.py writes it beside the page): for every
   owner in every league, up to three bold and three fair offers to each partner. ~650 KB, so it is not in
   the page: it is fetched the first time a reader opens the builder (tbpage.js) and kept in memory for the
   session. From file:// or offline the fetch fails and the page says so, with a button to try again. An offer
   is what each side sends, the owner's one number, `gain`, and who the owner drops to stay at the roster cap.
   The page scores nothing but the reader's own packages (Edit, tbedit.js, with tbscore.js's port of the rule).

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

/* What a team's page offers (lbpage.js): "find" (Find trades, the reader's own team is in this league and is
   another), "set" (This is my team: the reader has no team in this league), "own" (it is the reader's team: nothing
   to trade with) or "" (a team the page cannot make the reader's, which TEAMS does not list). */
function tbGate(tm){
  const lg = tbLeagueOf(tm.key), me = tbMine(lg);
  return !lg ? "" : !me ? (TEAMS[tm.key] ? "set" : "") : me.key === tm.key ? "own" : "find";
}

/* {bold: [offer], fair: [offer]} for this pair, or null when the file has nothing for it. */
const tbPair = (lg, me, tm) => ((((TB_DATA || {}).leagues || {})[lg.key] || {}).teams || {})[me.name]?.[tm.name] || null;

/* ---- Edit's guard (2026-10-05): the page re-scores the offers it loads with tbscore.js and shuts Edit when it
   cannot reproduce them. The file is ff-jarvis's, the port is the page's, and a rule that changed on one side
   only would otherwise show the reader a wrong number on a card they built themselves. Fails closed: a missing
   field, a player the roster does not list, a gain more than 0.15 off or a different drop shuts Edit and Make
   your own for the session (the offers still show), and the console names the offer. ---- */
const TB_TOL = 0.15;
let TB_GUARD = {data: null, shut: false, seen: {}};   // per file in memory: a shut guard stays shut, a pair is checked once

const tbLeagueData = lg => ((TB_DATA || {}).leagues || {})[lg.key] || null;

/* The K/DST/other non-IR players a team holds, which count toward the cap but are not in `values`: the league's
   `other` map, team name to count (a league with no entry for the team holds none). */
const tbOther = (lgd, team) => ((lgd || {}).other || {})[team] || 0;

/* The offer's players, as the roster lists them (with `proj` and `ir`), or null when one is not on it. */
function tbResolve(list, roster){
  const rows = (list || []).map(p => roster.find(r => tbKey(r) === tbKey(p)));
  return rows.every(Boolean) ? rows : null;
}

/* The reason this pair cannot be scored, or "" when every offer of it re-scores to its gain and its drop. */
function tbMismatch(lgd, me, tm, pair){
  const lu = lgd && lgd.lineup, mine = lgd && lgd.values && lgd.values[me.name], theirs = lgd && lgd.values && lgd.values[tm.name];
  if (!lu || !mine || !theirs) return "no lineup or values for this pair";
  for (const kind of ["bold", "fair"]) for (const [i, o] of ((pair || {})[kind] || []).entries()){
    const send = tbResolve(o.send, mine), get = tbResolve(o.get, theirs);
    if (!send || !get || !Array.isArray(o.drop)) return `${kind}[${i}] has a player the roster does not list, or no drop`;
    const r = tbGain(mine, send, get, lu, tbOther(lgd, me.name));
    const same = r.ok && r.drop.map(tbKey).join("|") === o.drop.map(tbKey).join("|");   // the producer's order is the rule's
    if (!(Math.abs(r.gain - o.gain) <= TB_TOL) || !same) return `${kind}[${i}] scores ${r.gain}${same ? "" : " and drops another player"}, the file says ${o.gain}`;
  }
  return "";
}

/* True when Edit and Make your own may show for the open pair. */
function tbEditOk(){
  if (!TB_DATA || !TB) return false;
  if (TB_GUARD.data !== TB_DATA) TB_GUARD = {data: TB_DATA, shut: false, seen: {}};
  if (TB_GUARD.shut) return false;
  const k = `${TB.lg.key}|${TB.me.name}|${TB.tm.name}`;
  if (!(k in TB_GUARD.seen)){
    const why = tbMismatch(tbLeagueData(TB.lg), TB.me, TB.tm, tbPair(TB.lg, TB.me, TB.tm));
    TB_GUARD.seen[k] = !why;
    if (why){ TB_GUARD.shut = true; console.warn(`trade builder: Edit is off, ${TB.me.name} to ${TB.tm.name}: ${why}`); }
  }
  return TB_GUARD.seen[k];
}

/* ---- the message the reader pastes to the other manager: only true season averages, "seen" ---- */
const tbSurname = n => { const p = String(n).trim().split(/\s+/); return p.length < 2 || /D\/ST$/.test(n) ? String(n) : p.slice(1).join(" "); };
const tbJoin = list => list.length === 2 ? list.join(t("lboard.offer.and")) : list.join(", ");

/* "Trade? I send Purdy (28.8 a game), Higgins (14.4) for Smith-Njigba (25.3) and Brown (11.4)." The first
   player carries the unit. */
function tbText(o){
  const one = (p, unit) => `${tbSurname(p.name)} (${unit ? t("lboard.offer.game", {n: lbNum(p.seen)}) : lbNum(p.seen)})`;
  return t("lboard.offer.text", {send: tbJoin(o.send.map((p, i) => one(p, i === 0))), get: tbJoin(o.get.map(p => one(p, false)))});
}
