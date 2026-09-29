/* ------------------------------------------------------------------
   PREVIEW's state and reads — This week > Preview (2026-09-29, storyboard option C,
   https://claude.ai/artifact/A5QvueyLecBFdFyYCcZbEH). LIVE_PREVIEW comes from design/preview.py:
   the week's games by kickoff, each with the market's implied score and Claude's take (or null).
------------------------------------------------------------------ */
let PV_I = null;   // the game on screen; null until the view is first drawn, then the next to kick off

const pvGames = () => (LIVE_PREVIEW && LIVE_PREVIEW.games) || [];
const pvDone = g => new Date(g.kickoff).getTime() <= Date.now();
/* The reader's own weekday, since that is what "a Sunday game" means where the reader is. */
const pvDay = g => new Date(g.kickoff).toLocaleDateString([], {weekday: "short"});

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

/* The slate by day, in kickoff order: [{day, idx: [game indexes]}], for the day marker. */
function pvDays(){
  const out = [];
  pvGames().forEach((g, i) => {
    const d = pvDay(g), last = out[out.length - 1];
    if (last && last.day === d) last.idx.push(i); else out.push({day: d, idx: [i]});
  });
  return out;
}
