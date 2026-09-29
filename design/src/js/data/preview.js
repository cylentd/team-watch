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

/* The slate by kickoff window, in kickoff order: [{slot, day, times: ["1:00 PM"], idx: [game indexes]}]. */
function pvWindows(){
  const out = [];
  pvGames().forEach((g, i) => {
    const last = out[out.length - 1];
    if (last && last.slot === g.slot && last.day === g.day){
      last.idx.push(i);
      if (!last.times.includes(g.et)) last.times.push(g.et);
    } else out.push({slot: g.slot, day: g.day, times: [g.et], idx: [i]});
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

/* The graded season (design/preview.py _record); null without ff-jarvis's preview_record. */
const pvRecord = () => (LIVE_PREVIEW && LIVE_PREVIEW.record) || null;

/* "25-21-2" -> "25–21–2", a push count of 0 dropped ("7–3"); null -> "0–0". */
const pvWL = s => { const [w = 0, l = 0, p = 0] = String(s || "0-0").split("-").map(Number); return p ? `${w}–${l}–${p}` : `${w}–${l}`; };

/* Hit % of a W-L-P record, pushes out; null before a decided game. */
const pvHit = s => { const [w = 0, l = 0] = String(s || "0-0").split("-").map(Number); return w + l ? Math.round(100 * w / (w + l)) : null; };
