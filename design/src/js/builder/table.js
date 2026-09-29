/* The deal table (2026-09-29, storyboard option C; it replaced the gallery of one card per kickoff
   and category, "Deal me 3" and the TD board). David builds several slips a kickoff: TD parlays
   from a pool of ten-plus scorers, safer yards slips to balance them, 3 to 6 legs, 5 when sure.
   So the page deals one slip at a time from the kickoff's good-% pool, he locks the picks he
   likes, deals again, and keeps the ones he wants in a list.

   The pool is looser than the old gallery's backtested gates (TD 50%+, receptions lower at 65%+,
   which left 15 legs of 268 on 2026-09-29): a TD at 30%+ P(score), a yards leg called lower at
   58%+. David chose those floors from the storyboard. The chance printed on a slip is still the
   graded one (legHit, grade.js), so a looser pool never reads better than it grades. */
const TABLE_TD = 30, TABLE_SAFE = 58;
const TABLE_KINDS = ["td", "safe", "mix"];
const TABLE_LEGS = [3, 4, 5, 6];
/* legs and locks are PROPS indexes; sig is the book, kickoff, kind and length the legs were dealt
   for, so a change of any of them deals afresh (locks that still fit stay). */
let TABLE = {kind: "td", n: 5, legs: [], locks: [], sig: ""};
let TABLE_FRESH = false;   // drop the unlocked legs in after the next render
let TABLE_POOL_ALL = false;

/* The kickoff the table deals for: the chosen one, or the first still to come. */
function tableWin(){
  return GAL_WINDOWS.find(w => w.k === GAL_WIN) || GAL_WINDOWS.find(w => !w.wins) || null;
}
const tableIsTD = p => p.mkt === "TD";
/* A leg for the pool: to come, on the field, 8+ games of his own, not stale, then the kind's floor.
   Underdog: a TD at its model P(score); a yards leg at Underdog's own line, called lower (higher
   picks graded 42.3%, ff-jarvis 12.51), and a receptions line of 2.5+ (1.5 is priced as a lock).
   DraftKings: its own price and the model's chance of the over. */
function tableLegOK(p, kind, book){
  if (!upcoming(p) || !playing(p) || (p.games || 0) < 8) return false;
  const td = tableIsTD(p);
  if ((kind === "td" && !td) || (kind === "safe" && td)) return false;
  if (book === "underdog"){
    const u = udPick(p);
    if (!u || u.stale) return false;
    if (td) return u.conf >= TABLE_TD;
    return !u.synthetic && u.pick === "lower" && u.conf >= TABLE_SAFE && (p.mkt !== "RECS" || u.line >= 2.5);
  }
  if (p.book !== "DraftKings" || overPrice(p) === null || typeof p.model !== "number") return false;
  return p.model >= (td ? TABLE_TD : TABLE_SAFE);
}
/* The number a pick shows: Underdog's confidence, DK's model chance. */
const tableConf = p => PARLAY_BOOK === "underdog" ? udPick(p).conf : p.model;
function tablePool(kind = TABLE.kind){
  const w = tableWin();
  if (kind === "mix"){
    // Yards legs run 58-76%, TDs 30-62%, so one ranking would bury every TD; alternate them.
    const td = tablePool("td"), safe = tablePool("safe");
    return Array.from({length: Math.max(td.length, safe.length)}, (_, k) => [td[k], safe[k]]).flat().filter(i => i !== undefined);
  }
  return PROPS.map((p, i) => [p, i]).filter(([p]) => tableLegOK(p, kind, PARLAY_BOOK) && inWin(p, w))
    .sort((a, b) => tableConf(b[0]) - tableConf(a[0])).map(([, i]) => i);
}

/* Fill to n around the locks: one leg per player; a game of its own for each leg while games last,
   then any game (Thursday is one game); Mix splits TDs and yards evenly, the TDs rounding down.
   Underdog wants two teams on an entry, so a one-team deal swaps its last free leg for another team's. */
function tableShuffle(pool){
  const a = pool.slice();
  for (let k = a.length - 1; k > 0; k--){ const j = Math.floor(Math.random() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; }
  return a;
}
function tableFill(pool, locks, n, kind){
  const legs = locks.slice(0, n), order = tableShuffle(pool);
  const players = new Set(legs.map(i => PROPS[i].n)), games = new Set(legs.map(i => PROPS[i].game));
  const tds = Math.floor(n / 2), count = td => legs.filter(i => tableIsTD(PROPS[i]) === td).length;
  const room = i => kind !== "mix" || count(tableIsTD(PROPS[i])) < (tableIsTD(PROPS[i]) ? tds : n - tds);
  [[true, true], [false, true], [false, false]].forEach(([ownGame, quota]) => order.forEach(i => {
    const p = PROPS[i];
    if (legs.length >= n || players.has(p.n) || (ownGame && games.has(p.game)) || (quota && !room(i))) return;
    legs.push(i); players.add(p.n); games.add(p.game);
  }));
  const teams = new Set(legs.map(i => PROPS[i].team));
  const free = legs.findLastIndex(i => !locks.includes(i));
  if (PARLAY_BOOK === "underdog" && legs.length > 1 && teams.size < 2 && free >= 0){
    const other = order.find(i => PROPS[i].team !== PROPS[legs[0]].team && !players.has(PROPS[i].n));
    if (other !== undefined) legs[free] = other;
  }
  return legs;
}

const tableSig = () => [PARLAY_BOOK, (tableWin() || {}).k, TABLE.kind, TABLE.n].join("|");
function tableDeal(){
  const pool = tablePool();
  TABLE.locks = TABLE.locks.filter(i => pool.includes(i));
  TABLE.legs = tableFill(pool, TABLE.locks, TABLE.n, TABLE.kind);
  TABLE.sig = tableSig();
  TABLE_FRESH = true;
}
/* Called by the render: a first visit, or a book or kickoff changed from the bar, deals afresh. */
function tableEnsure(){ if (TABLE.sig !== tableSig()){ tableDeal(); TABLE_FRESH = false; } }

/* A locked pick stays through every deal. A pool pick not on the slip takes the last free leg's
   place, or adds a leg when every leg is locked (up to 6). */
function tableLock(i){
  if (TABLE.locks.includes(i)){ TABLE.locks = TABLE.locks.filter(x => x !== i); return; }
  TABLE.locks.push(i);
  if (TABLE.legs.includes(i)) return;
  const free = TABLE.legs.findLastIndex(x => !TABLE.locks.includes(x));
  const clash = TABLE.legs.findIndex(x => x !== i && PROPS[x].n === PROPS[i].n && !TABLE.locks.includes(x));
  if (clash >= 0) TABLE.legs[clash] = i;
  else if (free >= 0) TABLE.legs[free] = i;
  else if (TABLE.n < TABLE_LEGS[TABLE_LEGS.length - 1]){ TABLE.n++; TABLE.legs.push(i); TABLE.sig = tableSig(); }
  else TABLE.locks.pop();
}

/* The chance all legs hit: Underdog's graded chance (udChance), DK's model chance. */
function tableChance(legs, book = PARLAY_BOOK){
  const ps = legs.map(i => PROPS[i]);
  return book === "underdog" ? udChance(ps) : ps.reduce((a, p) => a * p.model / 100, 1);
}

/* Kept slips: this device only, one list per slate week, newest first. A leg is kept as
   slug|market, so a rebuild that reorders PROPS still finds it; a leg gone from the board drops. */
const KEPT_KEY = `tw.slips.kept.${SLATE_WEEK || 0}`;
const keptLegKey = i => `${PROPS[i].slug}|${PROPS[i].mkt}`;
function keptLoad(){
  try {
    const raw = JSON.parse(localStorage.getItem(KEPT_KEY) || "[]");
    return raw.map(s => ({...s, legs: s.legs.map(k => PROPS.findIndex(p => `${p.slug}|${p.mkt}` === k)).filter(i => i >= 0)}))
      .filter(s => s.legs.length);
  } catch (e) { return []; }
}
let KEPT = keptLoad();
function keptSave(){
  try { localStorage.setItem(KEPT_KEY, JSON.stringify(KEPT.map(s => ({...s, legs: s.legs.map(keptLegKey)})))); } catch (e) {}
}
const keptSame = (a, b) => a.length === b.length && a.every(i => b.includes(i));
/* Keep the slip on the table; the same legs twice is one slip. Returns whether it was added. */
function tableKeep(){
  if (!TABLE.legs.length || KEPT.some(s => s.book === PARLAY_BOOK && keptSame(s.legs, TABLE.legs))) return false;
  KEPT.unshift({book: PARLAY_BOOK, kind: TABLE.kind, win: (tableWin() || {}).k || "", legs: TABLE.legs.slice()});
  keptSave();
  return true;
}
function keptDrop(k){ KEPT.splice(k, 1); keptSave(); }
