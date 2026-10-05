/* ============================== LEAGUE > TEAMS: TRADE OFFERS, THE DATA ==============================
   2026-10-05. ff-jarvis's trade_offers.json (design/trade_offers.py writes it beside the page): for every
   owner in every league, up to three bold and three fair offers to each partner. ~650 KB, so it is not in
   the page: it is fetched the first time a reader opens the builder (tbsheet.js) and kept in memory for the
   session. From file:// or offline the fetch fails and the sheet says so, with a button to try again. The
   page computes nothing: an offer is what each side sends and the owner's one number, `gain`.

   An owner and a partner are the teams' names as the League board has them (LIVE_TEAMS), which are the names
   in ff-jarvis's roster files, the same ones the offers are keyed by. */
const TB_URL = "trade_offers.json";
let TB_DATA = null;     // the file, once fetched
let TB_ERR = false;     // the last fetch failed
let TB_BUSY = null;     // the fetch in flight, so two opens share one request

/* True when the file is in TB_DATA. Always resolves, never throws: the sheet paints what it has. */
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

/* What the roster sheet's foot holds: "find" (the button), "pick" (a line asking the reader for their team)
   or "" (it is the reader's own team: nothing to trade with). */
function tbGate(tm){
  const lg = tbLeagueOf(tm.key), me = tbMine(lg);
  return !lg ? "" : !me ? "pick" : me.key === tm.key ? "" : "find";
}

/* {bold: [offer], fair: [offer]} for this pair, or null when the file has nothing for it. */
const tbPair = (lg, me, tm) => ((((TB_DATA || {}).leagues || {})[lg.key] || {}).teams || {})[me.name]?.[tm.name] || null;

/* ---- the message the reader pastes to the other manager: only true season averages, "seen" ---- */
const tbSurname = n => { const p = String(n).trim().split(/\s+/); return p.length < 2 || /D\/ST$/.test(n) ? String(n) : p.slice(1).join(" "); };
const tbJoin = list => list.length === 2 ? list.join(t("lboard.offer.and")) : list.join(", ");

/* "Trade? I send Purdy (28.8 a game), Higgins (14.4) for Smith-Njigba (25.3) and Brown (11.4)." The first
   player carries the unit. */
function tbText(o){
  const one = (p, unit) => `${tbSurname(p.name)} (${unit ? t("lboard.offer.game", {n: lbNum(p.seen)}) : lbNum(p.seen)})`;
  return t("lboard.offer.text", {send: tbJoin(o.send.map((p, i) => one(p, i === 0))), get: tbJoin(o.get.map(p => one(p, false)))});
}
