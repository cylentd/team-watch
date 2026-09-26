/* Player search: one list of every player the page carries, joined by slug, and the matcher that
   ranks it against a query. Built on first use rather than at load: hydrate.js fills the rosters
   first, and a reader who never searches never pays for the index. The sheet is chrome/search.js.

   Sample fallbacks are left out on purpose. A search that found an invented prop row would tell
   the reader a player is in this week's data when he is not. */
const SEARCH_TIER = {roster: 3, market: 2, grid: 1};
let SEARCH_INDEX = null;

/* [row, tier, league] for every player row the page holds, rosters first so a rostered player's
   own row (slot, note) is the one the profile opens with. A leaguemate's team (data/mates.js)
   counts as rostered only when it is the one on screen: the other 21 are not the reader's, and
   their 240 players would all read as "on your team". A team switch drops the index (teamswitch.js). */
function searchSources(){
  const mine = Object.values(TEAMS).filter(tm => !tm.mate || tm.key === VIEW)
    .flatMap(tm => (tm.roster || []).map(p => [p, "roster", tm.key]));
  const live = (on, rows) => on ? rows.map(p => [p, "market"]) : [];
  const grid = USAGE_LIVE ? [...USAGE.rows, ...((USAGE.sheet && USAGE.sheet.rows) || [])] : [];
  return [
    ...mine,
    ...live(!!LIVE_MARKET, PROPS),
    ...live(!!LIVE_YAHOO_DFS, DFSPOOL_YAHOO),
    ...live(!!WAIVER, waiverPlayers()),
    ...live(typeof LIVE_POOL !== "undefined" && !!LIVE_POOL, POOL),
    ...grid.map(p => [p, "grid"]),
  ];
}

function searchIndex(){
  if (SEARCH_INDEX) return SEARCH_INDEX;
  const by = new Map();
  for (const [p, src, league] of searchSources()){
    if (!p || !p.n) continue;
    const slug = p.slug || slugOf(p.n);
    let e = by.get(slug);
    if (!e){
      e = {n: p.n, slug, pos: p.pos, team: p.team, tier: 0, leagues: [], row: p, words: searchWords(p.n)};
      by.set(slug, e);
    }
    // A prop row has no team; the grid's row for the same player does.
    e.pos = e.pos || p.pos;
    e.team = e.team || p.team;
    e.tier = Math.max(e.tier, SEARCH_TIER[src]);
    if (league && !e.leagues.includes(league)) e.leagues.push(league);
  }
  SEARCH_INDEX = [...by.values()];
  return SEARCH_INDEX;
}

/* What openProfile gets: the richest row seen, with the joined identity over it. */
const searchPlayer = e => Object.assign({}, e.row, {n: e.n, slug: e.slug, pos: e.pos, team: e.team});

/* Lowercase with accents folded. Punctuation is dropped rather than turned into a space, so
   "Ja'Marr" is one word and "st. brown" still reads as two. */
const searchFold = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const searchKey = s => searchFold(s).replace(/[^a-z0-9]/g, "");

/* Every key a name answers to, as [key, unit, offset]. A unit is one space-separated part of the
   name as written; a hyphenated unit also answers to its later halves, so Amon-Ra St. Brown is
   found by "amonra" and by "ra", Smith-Njigba by "njigba". The offset counts letters and digits
   into the unit, which is what searchNameHTML walks to bold the match. */
function searchWords(n){
  const out = [];
  n.split(/\s+/).forEach((unit, u) => {
    const whole = searchKey(unit);
    if (whole) out.push([whole, u, 0]);
    let off = 0;
    unit.split("-").forEach((part, i) => {
      const k = searchKey(part);
      if (k && i > 0) out.push([k, u, off]);
      off += k.length;
    });
  });
  return out;
}

/* At most one edit (insert, delete, substitute, or swap two neighbours) between a and b. */
function searchNear1(a, b){
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) i++;
  const tail = (x, y) => a.slice(x) === b.slice(y);
  return tail(i + 1, i + 1) || tail(i + 1, i) || tail(i, i + 1)
    || (a[i] === b[i + 1] && a[i + 1] === b[i] && tail(i + 2, i + 2));
}

/* How many letters of `key` a typo'd query word covers, or 0: the query against the key's own
   start, at the query's length and one either side. */
function searchNear(w, key){
  for (const len of [w.length, w.length + 1, w.length - 1]){
    if (len > 0 && len <= key.length && searchNear1(w, key.slice(0, len))) return len;
  }
  return 0;
}

const SEARCH_POS = ["qb", "rb", "wr", "te", "k", "dst"];

/* One query word against one player: 4 a whole word of his name, 3 the start of one, 2 his
   position or team, 1 the start of a word with one typo. A typo counts only from 4 letters: at
   2 or 3, one edit away matches half the league. Returns [score, mark] or null; mark is the
   [unit, offset, length] to bold, null for a position or team match. */
function searchTerm(w, e){
  let best = null;
  for (const [key, u, off] of e.words){
    let s = 0, len = w.length;
    if (key === w) s = 4;
    else if (key.startsWith(w)) s = 3;
    else if (w.length >= 4 && (len = searchNear(w, key))) s = 1;
    if (s && (!best || s > best[0])) best = [s, [u, off, len]];
  }
  const tag = (SEARCH_POS.includes(w) && (e.pos || "").toLowerCase() === w)
    || (e.team || "").toLowerCase() === w;
  if (tag && (!best || best[0] < 2)) best = [2, null];
  return best;
}

/* Every query word must match something. Ranked by match quality, then by how much the page
   has to say about him (SEARCH_TIER), then by name so a tie always lands the same way. */
function searchFind(q, limit){
  const ws = searchFold(q).replace(/[^a-z0-9\s]/g, "").split(/\s+/).filter(Boolean);
  if (!ws.length) return [];
  const out = [];
  for (const e of searchIndex()){
    let score = 0;
    const marks = [];
    const ok = ws.every(w => {
      const m = searchTerm(w, e);
      if (!m) return false;
      score += m[0];
      if (m[1]) marks.push(m[1]);
      return true;
    });
    if (ok) out.push({e, score, marks});
  }
  out.sort((a, b) => b.score - a.score || b.e.tier - a.e.tier || a.e.n.localeCompare(b.e.n));
  return out.slice(0, limit);
}

/* The name as written, with the letters that matched in bold. */
function searchNameHTML(n, marks){
  return n.split(/\s+/).map((unit, u) => {
    const ms = marks.filter(m => m[0] === u);
    let i = 0, html = "";
    for (const ch of unit){
      const k = searchKey(ch).length;
      // Punctuation inside a match is bold with it, so "Ja'Mar" reads as one run, not two.
      const on = ms.some(([, off, len]) => k > 0 ? i >= off && i < off + len : i > off && i < off + len);
      html += on ? `<b>${esc(ch)}</b>` : esc(ch);
      i += k;
    }
    return html.replace(/<\/b><b>/g, "");
  }).join(" ");
}
