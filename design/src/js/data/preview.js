/* ------------------------------------------------------------------
   PREVIEW's state and reads — This week > Preview. A slate and a dossier since 2026-09-29 (storyboard
   option A, superseding option C of the same morning). LIVE_PREVIEW comes from design/preview.py: the
   week's games by kickoff, each with its window, line, matchup, weather, injuries, rest, travel, the
   flags that say why to open it, and Claude's take (or null).
------------------------------------------------------------------ */
let PV_I = null;     // the game in the dossier; null until first asked, then the next to kick off
let PV_OPEN = false; // a phone shows the dossier instead of the slate (a desktop shows both, always)
let PV_Y = 0;        // the slate's scroll when the dossier opened, put back when it closes
let PV_REC = false;  // Past games is open (in the slate's place on a phone, the dossier's on a desktop)
let PV_ARC_WK = null;   // the week Past games shows; null until first opened (pvArcWeekDefault)
let PV_ARC_G = null;    // an earlier week's game open from Past games: {week, key}; null for this week's games
let PV_ARC = null;      // preview_archive.json once fetched ({season, weeks}); "loading" or "failed" meanwhile

/* Games of another week than the page's are none (schedIsPageWeek), so Preview says its games are not posted. */
const pvGames = () => (LIVE_PREVIEW && schedIsPageWeek(LIVE_PREVIEW.week) && LIVE_PREVIEW.games) || [];
const pvDone = g => new Date(g.kickoff).getTime() <= Date.now();

/* A game is over, so it leaves the slate for Past games (2026-10-05, storyboard 1A,
   https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV): the schedule has its final score, or Live's clock says
   Final, or failing both it kicked off SCHED_GRACE_MS (4 hours) ago. Live's clock is asked only when Live
   has polled; before that its read throws on the missing game-day state, which counts as "not known". */
function pvOver(g){
  const h = schedCode(g.home), a = schedCode(g.away);
  // `final` is the schedule's own (design/schedule.py: both scores are in the games log).
  if (schedGamesOf(LIVE_PREVIEW.week).some(s => s.final && schedCode(s.home) === h && schedCode(s.away) === a)) return true;
  try { if (gdClockOf(h).state === "post") return true; } catch (e) { /* Live has not polled */ }
  return Date.now() - Date.parse(g.kickoff) >= SCHED_GRACE_MS;
}

/* The slate's games: this week's, less the ones that are over. Indexes stay pvGames()'s. */
const pvSlateIdx = () => pvGames().map((g, i) => i).filter(i => !pvOver(pvGames()[i]));
const pvFinalIdx = () => pvGames().map((g, i) => i).filter(i => pvOver(pvGames()[i]));

function pvIndex(){
  const gs = pvGames();
  if (PV_I === null || PV_I >= gs.length){
    const next = gs.findIndex(g => !pvOver(g));
    PV_I = next < 0 ? 0 : next;
  }
  return PV_I;
}

/* An earlier week's games from the fetched archive, [] before it arrives. */
const pvArcGames = wk => (PV_ARC && typeof PV_ARC === "object" && PV_ARC.weeks[String(wk)]) || [];

/* The game in the dossier: an earlier week's when one is open from Past games, else this week's PV_I. */
function pvCurGame(){
  if (PV_ARC_G) return pvArcGames(PV_ARC_G.week).find(g => g.key === PV_ARC_G.key) || null;
  return pvGames()[pvIndex()] || null;
}

/* One game along; false at either end, so a swipe past the last game does nothing. An earlier week's
   game steps through its own week. */
function pvStep(d){
  if (PV_ARC_G){
    const gs = pvArcGames(PV_ARC_G.week), j = gs.findIndex(g => g.key === PV_ARC_G.key) + d;
    if (j < 0 || j >= gs.length) return false;
    PV_ARC_G = {week: PV_ARC_G.week, key: gs[j].key};
    return true;
  }
  const i = pvIndex() + d;
  if (i < 0 || i >= pvGames().length) return false;
  PV_I = i;
  return true;
}

/* The slate by kickoff window, in kickoff order: [{slot, day, times: ["1:00 PM"], idx: [game indexes]}].
   A window is named for the league's own Eastern slots (slot, day: design/preview.py), its times are
   the reader's clock (lib/kick.js), so a Denver reader sees "Sunday early · 11:00 AM". */
function pvWindows(idx = pvSlateIdx()){
  const out = [];
  idx.forEach(i => {
    const g = pvGames()[i], last = out[out.length - 1], time = kickTime(g.kickoff);
    if (last && last.slot === g.slot && last.day === g.day){
      last.idx.push(i);
      if (!last.times.includes(time)) last.times.push(time);
    } else out.push({slot: g.slot, day: g.day, times: [time], idx: [i]});
  });
  return out;
}

/* 3 -> "3", 2.5 -> "2.5": a line is to the half point, so no trailing ".0". */
const pvNum = n => Number.isInteger(n) ? String(n) : n.toFixed(1);

/* A spread in words, never signed (David, 2026-09-29: "-1.5" read as funky): "ARI by 1.5", or "Even". */
const pvSpread = (fav, by) => fav ? t("preview.line.by", {team: esc(fav), n: pvNum(by)}) : t("preview.line.even");

/* Defense rank colour: a soft matchup (bottom 8 of 32) is --up, a tough one (top 8) --down. */
const pvRankTone = r => r >= 25 ? "pv-soft" : r <= 8 ? "pv-tough" : "";

/* Claude's confidence as a chip: STRONG lime fill, SOLID lime outline, LEAN grey, NO EDGE without one. */
const pvConfHTML = conf => ({
  strong: `<b class="pv-conf strong">${t("preview.conf.strong")}</b>`,
  solid: `<b class="pv-conf solid">${t("preview.conf.solid")}</b>`,
  lean: `<b class="pv-conf lean">${t("preview.conf.lean")}</b>`,
}[conf] || `<b class="pv-conf none">${t("preview.conf.none")}</b>`);

/* What a spread call needs, in points (storyboard 3A, 2026-10-05; David could not tell whose "PIT by 2.5"
   was). The favourite must win by more than the line; the underdog may lose by less. A whole-number line's
   exact margin is a push, so it counts on neither side: by 3, the favourite needs 4, the underdog loses by 2. */
function pvCoverNeeds(team, l){
  if (!l.fav) return "";
  if (team === l.fav) return t("preview.ans.coverFav", {n: Math.floor(l.by) + 1});
  const n = Math.ceil(l.by) - 1;
  return n > 0 ? t("preview.ans.coverDog", {n}) : t("preview.ans.coverWin");
}

/* The same for a total: Under 38.5 is 38 or fewer, Over 50 is 51 or more. */
const pvTotalNeeds = (call, total) => call === "under" ? t("preview.ans.under", {n: Math.ceil(total) - 1})
  : t("preview.ans.over", {n: Math.floor(total) + 1});

/* The answer block at the top of a game's page: Claude's score, then one row per bet (storyboard 3A,
   2026-10-05, https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV; it replaced plan U3's four cells, which said
   "CLE wins" four ways). Each row is {id, vegas, claude, conf, sub, hit}: Vegas's number, Claude's call ("" for
   none), his confidence word, what the call needs in points (the moneyline's is his chance), and with a graded
   record game `rg` the row's hit / miss / push. A row with neither a Vegas number nor a call is left out. */
function pvAnswer(g, rg = null){
  const l = g.line, k = g.take || null, p = k && k.pick ? k.pick : null, mw = g.market_win;
  const rows = [];
  const pair = (w, lo, s) => t("preview.pick.pair", {w: esc(w), a: s[w], l: esc(lo), b: s[lo]});
  const other = w => w === g.home ? g.away : g.home;
  const mfav = mw ? Object.keys(mw).reduce((a, b) => mw[b] > mw[a] ? b : a) : null;
  if (mfav || p){
    const cl = p && k.win ? k.win[p.winner] : null;
    rows.push({id: "ml", vegas: mfav ? `${esc(mfav)} ${Math.round(mw[mfav])}%` : "",
      claude: p ? t("preview.ans.wins", {team: esc(p.winner)}) : "", conf: null,
      sub: cl != null ? t("preview.ans.chance", {n: cl}) : "", hit: rg ? rg.su ?? null : null});
  }
  if (l){
    const side = k && k.ats && k.ats.side;
    rows.push({id: "spread", vegas: pvSpread(l.fav, l.by), claude: side ? t("preview.ans.covers", {team: esc(side)}) : "",
      conf: side ? k.ats.conf : null, sub: side ? pvCoverNeeds(side, l) : "", hit: rg ? rg.hit ?? null : null});
    if (l.total != null){
      const call = k && k.total && k.total.call;
      rows.push({id: "total", vegas: pvNum(l.total),
        claude: call ? (call === "over" ? t("preview.pick.over") : t("preview.pick.under")) : "",
        conf: call ? k.total.conf : null, sub: call ? pvTotalNeeds(call, l.total) : "", hit: rg ? rg.total_hit ?? null : null});
    }
  }
  return {score: p ? pair(p.winner, other(p.winner), p.score) : "", rows};
}

/* "CLE 27, PIT 24", the winner first, from a graded record game; "" without one. */
function pvFinal(g, rg){
  const r = rg && rg.result;
  if (!r || r.home == null) return "";
  const hw = r.home >= r.away;
  return t("preview.pick.pair", {w: esc(hw ? g.home : g.away), a: hw ? r.home : r.away, l: esc(hw ? g.away : g.home), b: hw ? r.away : r.home});
}

/* The graded season (design/preview.py _record); null without ff-jarvis's preview_record. */
const pvRecord = () => (LIVE_PREVIEW && LIVE_PREVIEW.record) || null;

/* A game's graded row in the record, by its key; null before it is graded. */
function pvRecGameOf(g){
  const r = pvRecord();
  if (!r || !g) return null;
  for (const w of r.weeks) for (const x of w.games) if (x.key && x.key === g.key) return x;
  return null;
}

/* The record's week, or null before that week is graded. */
const pvRecWeek = wk => (pvRecord() && pvRecord().weeks.find(w => w.week === wk)) || null;

/* Every week Past games has something for: graded weeks, fetched archive weeks, and this week once a game
   is over. Ascending. */
function pvArcWeeks(){
  const s = new Set((pvRecord() ? pvRecord().weeks : []).map(w => w.week));
  if (PV_ARC && typeof PV_ARC === "object") Object.keys(PV_ARC.weeks).forEach(w => s.add(+w));
  if (pvFinalIdx().length) s.add(LIVE_PREVIEW.week);
  return [...s].sort((a, b) => a - b);
}

/* The week Past games opens on: this week's finals when there are any, else the newest earlier week. */
const pvArcWeekDefault = () => { const ws = pvArcWeeks(); return ws.length ? ws[ws.length - 1] : LIVE_PREVIEW.week; };

/* Past games' stepper runs from week 1 to this week (when a game of it is over) or the week before. */
const pvArcLast = () => pvFinalIdx().length ? LIVE_PREVIEW.week : LIVE_PREVIEW.week - 1;

/* One week's rows: {g, i, key, rg}. This week's come from the page (i opens the live dossier); an earlier
   week's from the fetched archive in kickoff order, or before it arrives from the record's graded games. */
function pvArcRows(wk){
  const fin = wk === LIVE_PREVIEW.week ? pvFinalIdx() : [];
  if (fin.length) return fin.map(i => ({g: pvGames()[i], i, key: null, rg: pvRecGameOf(pvGames()[i])}));
  const arc = pvArcGames(wk);
  if (arc.length) return arc.map(g => ({g, i: null, key: g.key, rg: pvRecGameOf(g)}));
  const rw = pvRecWeek(wk);
  return rw ? rw.games.map(x => ({g: {key: x.key, away: x.away, home: x.home, take: null}, i: null, key: x.key, rg: x})) : [];
}

/* A row's three calls, {ml, spread, total} each {pick, hit} or null: the graded record's when there is one,
   else the take's own. */
function pvArcCalls(g, rg){
  if (rg) return {ml: rg.pick ? {pick: rg.pick, hit: rg.su} : null, spread: rg.side ? {pick: rg.side, hit: rg.hit} : null,
    total: rg.total_call ? {pick: rg.total_call, hit: rg.total_hit} : null};
  const k = g.take;
  if (!k) return {ml: null, spread: null, total: null};
  return {ml: k.pick ? {pick: k.pick.winner, hit: null} : null, spread: k.ats && k.ats.side ? {pick: k.ats.side, hit: null} : null,
    total: k.total && k.total.call ? {pick: k.total.call, hit: null} : null};
}

/* "25-21-2" -> "25–21–2", a push count of 0 dropped ("7–3"); null -> "0–0". */
const pvWL = s => { const [w = 0, l = 0, p = 0] = String(s || "0-0").split("-").map(Number); return p ? `${w}–${l}–${p}` : `${w}–${l}`; };

/* Hit % of a W-L-P record, pushes out; null before a decided game. */
const pvHit = s => { const [w = 0, l = 0] = String(s || "0-0").split("-").map(Number); return w + l ? Math.round(100 * w / (w + l)) : null; };
