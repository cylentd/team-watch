/* ------------------------------------------------------------------
   PREVIEW's state and reads — This week > Preview. A slate and a dossier since 2026-09-29 (storyboard
   option A, superseding option C of the same morning). LIVE_PREVIEW comes from design/preview.py: the
   week's games by kickoff, each with its window, line, matchup, weather, injuries, rest, travel, the
   flags that say why to open it, and Claude's take (or null).
------------------------------------------------------------------ */
let PV_I = null;     // the game in the dossier; null until first asked, then the next to kick off
let PV_OPEN = false; // a phone shows the dossier instead of the slate (a desktop shows both, always)
let PV_Y = 0;        // the slate's scroll when the dossier opened, put back when it closes
let PV_REC = false;  // the every-week record is open (in the slate's place on a phone, the dossier's on a desktop)

const pvGames = () => (LIVE_PREVIEW && LIVE_PREVIEW.games) || [];
const pvDone = g => new Date(g.kickoff).getTime() <= Date.now();

function pvIndex(){
  const gs = pvGames();
  if (PV_I === null || PV_I >= gs.length){
    const next = gs.findIndex(g => !pvDone(g));
    PV_I = next < 0 ? 0 : next;
  }
  return PV_I;
}

/* One game along; false at either end, so a swipe past the last game does nothing. */
function pvStep(d){
  const i = pvIndex() + d;
  if (i < 0 || i >= pvGames().length) return false;
  PV_I = i;
  return true;
}

/* The slate by kickoff window, in kickoff order: [{slot, day, times: ["1:00 PM"], idx: [game indexes]}].
   A window is named for the league's own Eastern slots (slot, day: design/preview.py), its times are
   the reader's clock (lib/kick.js), so a Denver reader sees "Sunday early · 11:00 AM". */
function pvWindows(){
  const out = [];
  pvGames().forEach((g, i) => {
    const last = out[out.length - 1], time = kickTime(g.kickoff);
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

/* A side against the spread in words, never signed (David, 2026-09-29): "CLE getting 2.5",
   "IND giving 3.5", "CLE, even". `spread` is that team's own line: below 0 it gives points. */
const pvSideWords = (team, spread) => spread < 0 ? t("preview.side.giving", {team: esc(team), n: pvNum(-spread)})
  : spread > 0 ? t("preview.side.getting", {team: esc(team), n: pvNum(spread)}) : t("preview.side.even", {team: esc(team)});

/* A team's own line from a game's {fav, by}: the favourite gives `by`, the other side gets it. */
const pvTeamSpread = (g, team) => !g.line || !g.line.fav ? 0 : g.line.fav === team ? -g.line.by : g.line.by;

/* Claude's confidence as a chip: STRONG lime fill, SOLID lime outline, LEAN grey, NO EDGE without one. */
const pvConfHTML = conf => ({
  strong: `<b class="pv-conf strong">${t("preview.conf.strong")}</b>`,
  solid: `<b class="pv-conf solid">${t("preview.conf.solid")}</b>`,
  lean: `<b class="pv-conf lean">${t("preview.conf.lean")}</b>`,
}[conf] || `<b class="pv-conf none">${t("preview.conf.none")}</b>`);

/* A take's side, chip first-class: "JAX getting 3 [STRONG]", or the NO EDGE chip alone. */
const pvAtsHTML = (g, a) => a && a.side
  ? `<span class="pv-side">${pvSideWords(a.side, pvTeamSpread(g, a.side))}</span>${pvConfHTML(a.conf)}` : pvConfHTML(null);

/* The answer block at the top of a game's page (plan U3, 2026-10-05; the audit found the line and the pick
   under five paragraphs): Claude's pick, the line, the total, the win chance, in that order, as data the
   surface draws. A cell with nothing behind it is left out, so a game with no take still gives its line,
   total and the market's win chance, and a game with nothing gives []. `sub` is the market's own number
   beside Claude's, or where a line opened when it moved; `ats` and `call` are Claude's sides, drawn as chips. */
function pvAnswer(g){
  const l = g.line, k = g.take && g.take.ats ? g.take : null, p = g.take && g.take.pick ? g.take.pick : null;
  const out = [];
  const pair = (w, lo, s) => t("preview.pick.pair", {w: esc(w), a: s[w], l: esc(lo), b: s[lo]});
  const other = w => w === g.home ? g.away : g.home;
  if (p){
    const w = p.winner, imp = l && l.implied;
    out.push({id: "pick", main: pair(w, other(w), p.score), sub: imp ? t("preview.ans.market", {what: pair(w, other(w), imp)}) : "",
      ats: k ? k.ats : null});
  }
  if (l){
    const o = l.open, moved = o && (o.fav !== l.fav || o.by !== l.by);
    out.push({id: "line", main: pvSpread(l.fav, l.by), sub: moved ? t("preview.line.opened", {line: pvSpread(o.fav, o.by)}) : ""});
    if (l.total != null){
      const tMoved = o && o.total != null && o.total !== l.total;
      out.push({id: "total", main: pvNum(l.total), sub: tMoved ? t("preview.line.openedn", {n: pvNum(o.total)}) : "",
        call: k && k.total ? {call: k.total.call, conf: k.total.conf} : null});
    }
  }
  const mw = g.market_win, w = p ? p.winner : mw ? Object.keys(mw).reduce((a, b) => mw[b] > mw[a] ? b : a) : null;
  const cl = k && k.win && w ? k.win[w] : null, mk = mw && w ? mw[w] : null;
  if (w && (cl != null || mk != null)){
    out.push({id: "win", main: `${esc(w)} ${cl != null ? cl : Math.round(mk)}%`,
      sub: cl != null && mk != null ? t("preview.ans.market", {what: `${Math.round(mk)}%`}) : "",
      claude: cl != null, bar: cl != null && mk != null ? {mk, cl} : null});
  }
  return out;
}

/* The graded season (design/preview.py _record); null without ff-jarvis's preview_record. */
const pvRecord = () => (LIVE_PREVIEW && LIVE_PREVIEW.record) || null;

/* "25-21-2" -> "25–21–2", a push count of 0 dropped ("7–3"); null -> "0–0". */
const pvWL = s => { const [w = 0, l = 0, p = 0] = String(s || "0-0").split("-").map(Number); return p ? `${w}–${l}–${p}` : `${w}–${l}`; };

/* Hit % of a W-L-P record, pushes out; null before a decided game. */
const pvHit = s => { const [w = 0, l = 0] = String(s || "0-0").split("-").map(Number); return w + l ? Math.round(100 * w / (w + l)) : null; };
