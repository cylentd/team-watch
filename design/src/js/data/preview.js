/* ------------------------------------------------------------------
   PREVIEW's state and reads — This week > Preview. A slate and a dossier since 2026-09-29 (storyboard
   option A, superseding option C of the same morning). LIVE_PREVIEW comes from design/preview.py: the
   week's games by kickoff, each with its window, line, matchup, weather, injuries, rest, travel, the
   flags that say why to open it, and Claude's take (or null).
------------------------------------------------------------------ */
let PV_I = null;     // the game in the dossier; null until first asked, then the next to kick off
let PV_OPEN = false; // a phone shows the dossier instead of the slate (a desktop shows both, always)
let PV_Y = 0;        // the slate's scroll when the dossier opened, put back when it closes

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
