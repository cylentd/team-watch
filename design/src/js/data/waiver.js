/* ff-jarvis's waiver packet (LIVE_WAIVER, design/waiver.py) for one league. Every number on the
   Waivers sub-tab is the packet's own: `role_pts` is his price moved toward last week's work,
   `starts.margin` is that against the weakest starter he could replace. Nothing here re-derives
   either; it only counts and formats. */
function waiverFor(key){
  return (typeof LIVE_WAIVER !== "undefined" && LIVE_WAIVER && LIVE_WAIVER.leagues[key]) || null;
}

/* Wire rows whose forward number clears the starter they would replace. */
function waiverStarters(lg){
  return lg ? lg.wire.filter(r => r.starts && r.starts.margin >= 0).length : 0;
}

const WAIVER_DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
const WAIVER_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
/* "2026-09-23T00:00" (local, no zone) -> ["Wed", "Sep 23"]. Parsed by hand so the label never
   shifts with the viewer's zone or locale; the packet already states local time. */
function waiverClears(iso){
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || "");
  if (!m) return null;
  const d = new Date(Date.UTC(+m[1], +m[2]-1, +m[3]));
  return [WAIVER_DAYS[d.getUTCDay()], `${WAIVER_MONTHS[+m[2]-1]} ${+m[3]}`];
}
