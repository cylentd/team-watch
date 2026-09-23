/* ff-jarvis's waiver packet (LIVE_WAIVER, design/waiver.py): one row per candidate, each with
   its tier and a view per league, and `leagues_meta` in the order the cards draw leagues. Every
   tier, verdict, margin and drop is the packet's own. Nothing here re-derives one; it only
   filters to the league on screen (VIEW), groups, counts and formats. */
const WAIVER = typeof LIVE_WAIVER !== "undefined" && LIVE_WAIVER ? LIVE_WAIVER : null;

function waiverPlayers(){ return WAIVER ? WAIVER.players : []; }
function waiverMeta(){ return WAIVER ? WAIVER.leagues_meta : {}; }

/* A league row only where he can be had there. Rostered and mine collapse to the grey note. */
const waiverOpen = lg => !!lg && (lg.status === "fa" || lg.status === "waiver");
/* A card in a league: he can be had there, or nobody knows ("unknown": the roster scrape could not
   tell). The unknown one is drawn and says so; it is never passed off as a free agent. */
const waiverListed = lg => waiverOpen(lg) || (!!lg && lg.status === "unknown");

/* His league views in leagues_meta order, never a hardcoded espn/yahoo. */
function waiverLeagues(r){
  return Object.keys(waiverMeta()).filter(k => r.leagues && r.leagues[k]).map(k => [k, r.leagues[k]]);
}

/* His tier in one league: the packet's per-league tier, else the row's own (a packet from before
   ff-jarvis wrote per-league tiers). Read, never derived: the rule lives in ff-jarvis. */
const waiverTier = (r, key) => (r.leagues[key] && r.leagues[key].tier) || r.tier;

const WAIVER_TIERS = ["must", "worth", "watch", "spec", "stash"];
/* One league's wire: [row, index into waiverPlayers()] for everyone he can be had in there,
   grouped by that league's tier, packet order within a tier. The index is what the profile
   button carries, so it stays the global one. */
function waiverIn(key){
  const at = k => { const i = WAIVER_TIERS.indexOf(k); return i < 0 ? WAIVER_TIERS.length : i; };
  return waiverPlayers().map((r, i) => [r, i]).filter(([r]) => waiverListed(r.leagues[key]))
    .map((x, n) => [x, n]).sort(([a, n], [b, m]) => at(waiverTier(a[0], key)) - at(waiverTier(b[0], key)) || n - m)
    .map(([x]) => x);
}

/* Must-claims open in one league: the hero's count is per league, like its FAAB. */
function waiverMustIn(key){
  return waiverIn(key).filter(([r]) => waiverTier(r, key) === "must").length;
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
