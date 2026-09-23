/* ff-jarvis's waiver packet (LIVE_WAIVER, design/waiver.py): one row per candidate, each with
   its tier and a view per league, and `leagues_meta` in the order the cards draw leagues. Every
   verdict, margin and drop is the packet's own. Nothing here re-derives one; it only groups,
   counts and formats. */
const WAIVER = typeof LIVE_WAIVER !== "undefined" && LIVE_WAIVER ? LIVE_WAIVER : null;

function waiverPlayers(){ return WAIVER ? WAIVER.players : []; }
function waiverMeta(){ return WAIVER ? WAIVER.leagues_meta : {}; }

/* A league row only where he can be had there. Rostered and mine collapse to the grey note. */
const waiverOpen = lg => !!lg && (lg.status === "fa" || lg.status === "waiver");

/* His league views in leagues_meta order, never a hardcoded espn/yahoo. */
function waiverLeagues(r){
  return Object.keys(waiverMeta()).filter(k => r.leagues && r.leagues[k]).map(k => [k, r.leagues[k]]);
}

/* The swap the headline states: the best verdict among the leagues he is available in, a start
   before a bench, then the bigger margin. Null when no league has one. */
function waiverBestVerdict(r){
  const rank = v => (v.kind === "start" ? 1000 : 0) + (v.margin || 0);
  return waiverLeagues(r).filter(([, lg]) => waiverOpen(lg) && lg.verdict)
    .map(([, lg]) => lg.verdict).sort((a, b) => rank(b) - rank(a))[0] || null;
}

/* Must-claims open in one league: the hero's count is per league, like its FAAB. */
function waiverMustIn(key){
  return waiverPlayers().filter(r => r.tier === "must" && waiverOpen(r.leagues[key])).length;
}

const WAIVER_DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
/* "2026-09-24T03:00:00-04:00" -> "Thu 3:00 AM". Parsed by hand, as the packet states it, so the
   label never shifts with the viewer's zone or locale: the league's clock is the one that counts. */
function waiverWhen(iso){
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}))?/.exec(iso || "");
  if (!m) return null;
  const day = WAIVER_DAYS[new Date(Date.UTC(+m[1], +m[2]-1, +m[3])).getUTCDay()];
  if (m[4] === undefined) return day;
  const h = +m[4] % 12 || 12;
  return `${day} ${h}:${m[5]} ${+m[4] < 12 ? "AM" : "PM"}`;
}
