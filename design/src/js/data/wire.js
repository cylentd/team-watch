/* ff-jarvis's wire_watch (LIVE_WIRE, design/wire_watch.py): per league, what moved on the wire
   since the claims cleared. The producer decides what is worth an event (a junk drop never
   arrives); this file only orders a league's events for the rail. */
const WIRE = typeof LIVE_WIRE !== "undefined" && LIVE_WIRE ? LIVE_WIRE : null;

/* Rail order: a path opening first (it is a claim to make), then a drop worth a look, then my
   own players' status (the context for both), then the adds. Newest first within a kind, as the
   producer sends them. Adds are context only, so at most three. */
const WIRE_KINDS = ["path", "drop", "status", "adds"];
const WIRE_ADDS_CAP = 3;

function wireEvents(key){
  const lg = WIRE && WIRE.leagues[key];
  if (!lg) return [];
  const by = k => lg.events.filter(e => e.kind === k);
  return WIRE_KINDS.flatMap(k => k === "adds" ? by(k).slice(0, WIRE_ADDS_CAP) : by(k));
}

/* Milliseconds for an event's `at`, or 0 when it will not parse, so it is never "new". */
const wireAt = e => { const n = Date.parse(e.at || ""); return isNaN(n) ? 0 : n; };
