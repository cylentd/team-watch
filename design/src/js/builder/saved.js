/* SAVED SLIPS (2026-10-03). David enters his slips on Underdog; Save keeps a copy here for tracking,
   on this device, one list per slate week, newest first. It replaced the deal table's Kept list.
   A leg is saved as slug, market, side, name and line, so a rebuild that reorders PROPS still finds
   it, and a leg whose line has left the board still reads in the list. Storage can throw (a private
   window, blocked site data): every read and write is guarded, and the page works without it. */
const SAVED_KEY = `tw.slips.saved.${SLATE_WEEK || schedWeek() || 0}`;

function savedRead(){
  try {
    const raw = JSON.parse(localStorage.getItem(SAVED_KEY) || "[]");
    return Array.isArray(raw) ? raw.filter(s => s && Array.isArray(s.legs) && s.legs.length) : [];
  } catch (e) { return []; }
}
let SAVED = savedRead();
function savedWrite(){
  try { localStorage.setItem(SAVED_KEY, JSON.stringify(SAVED)); } catch (e) {}
}

const savedLeg = i => ({slug: slSlug(PROPS[i]), mkt: PROPS[i].mkt, side: slipSide(i), n: PROPS[i].n, line: slLine(PROPS[i])});
const savedSig = legs => legs.map(l => `${l.slug}|${l.mkt}|${l.side}`).sort().join(",");
/* The slip in the tray is already in the list, leg for leg. */
const slipIsSaved = () => SLIP.length > 0 && SAVED.some(s => savedSig(s.legs) === savedSig(SLIP.map(savedLeg)));

/* Save the tray's slip; the same legs twice is one slip. Returns whether it was added. */
function slipSave(){
  if (!SLIP.length || slipIsSaved()) return false;
  SAVED.unshift({at: new Date(Date.now()).toISOString(), legs: SLIP.map(savedLeg)});
  savedWrite();
  return true;
}
function savedDrop(k){ SAVED.splice(k, 1); savedWrite(); }

/* A saved slip back into the tray, each leg at its side; a leg gone from the board stays out. */
function savedLoad(k){
  const s = SAVED[k];
  if (!s) return 0;
  SLIP = []; SLIP_SIDE = {}; SLIP_MODE = "custom";
  s.legs.forEach(l => {
    const i = PROPS.findIndex(p => slSlug(p) === l.slug && p.mkt === l.mkt);
    if (i >= 0 && !SLIP.includes(i)){ SLIP.push(i); SLIP_SIDE[i] = l.side; }
  });
  return SLIP.length;
}

/* Every player on a saved slip or on the slip being built: the "on slip" marker on the board and
   in Preview. */
function onSlipSlugs(){
  return new Set([...SAVED.flatMap(s => s.legs.map(l => l.slug)), ...SLIP.map(i => slSlug(PROPS[i]))]);
}
