/* ============================== GAMEDAY: EVERY GAME'S CLOCK ==============================
   The quarter and time left in every game of the week (2026-10-04, storyboard
   https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV). Sleeper says only whether a game is on; ESPN's
   public scoreboard says where it is. The reader's browser asks it, the way the game sheet asks for a
   summary (espn.js): ESPN answers a browser and refuses servers, so no api/ function can.

   One request per Live poll covers every game. When ESPN does not answer, every reader still gets
   Sleeper's word ("Live" / "Final") and the kickoff, never a guessed clock.

   gdClockOf(club) is the one read the views use. It returns
     {state: "pre"|"in"|"post", label, live}
   label is "Q3 4:12", "Half", "OT 2:01", "Final", "Final/OT", or the kickoff ("Sun 1:25 PM").
   live is true while the game is being played, halftime included. */

const GD_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard";
let GD_CLOCK = {};       /* club code (ESPN's) -> {state, q, clock, half, detail} */
let GD_CLOCK_AT = 0;

/* One competition of the scoreboard to what a row needs. */
function gdClockShape(ev){
  const comp = (ev.competitions || [])[0] || {};
  const st = comp.status || ev.status || {}, type = st.type || {};
  return {state: type.state || "pre", q: st.period || 0, clock: st.displayClock || "",
          half: /HALFTIME/.test(type.name || ""), detail: type.shortDetail || "",
          clubs: (comp.competitors || []).map(c => (c.team || {}).abbreviation).filter(Boolean)};
}

async function gdClockFetch(){
  const week = (GD.leagues[0] || {}).week;
  if (!week) return;
  const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), GS_TIMEOUT_MS);
  try {
    const res = await fetch(`${GD_SCOREBOARD}?seasontype=2&week=${week}&dates=${GD.season}`, {signal: ctl.signal});
    const body = res.ok ? await res.json() : null;
    if (!body || !Array.isArray(body.events)) return;
    const next = {};
    for (const ev of body.events){
      const g = gdClockShape(ev);
      for (const c of g.clubs) next[c] = g;
    }
    GD_CLOCK = next; GD_CLOCK_AT = Date.now();
  } catch (e) { /* ESPN down or slow: Sleeper's state below */ }
  finally { clearTimeout(timer); }
}

/* "Q3 4:12" from ESPN's period and clock; a fifth period is overtime. */
function gdClockLabel(g){
  if (g.state === "post") return g.q > 4 ? t("live.clock.finalOt") : t("live.clock.final");
  if (g.half) return t("live.clock.half");
  const q = g.q > 4 ? t("live.clock.ot") : t("live.clock.q", {n: g.q});
  return g.clock ? `${q} ${g.clock}` : q;
}

function gdClockOf(club){
  const g = gdByCode(GD_CLOCK, club);
  if (g && g.state !== "pre") return {state: g.state, label: gdClockLabel(g), live: g.state === "in"};
  /* Sleeper's state and the schedule's kickoff, when ESPN has nothing (yet) for this club. */
  const st = gdByCode((GD_STATS && GD_STATS.games) || {}, club);
  if (st === "complete") return {state: "post", label: t("live.clock.final"), live: false};
  if (st === "in_game") return {state: "in", label: t("live.clock.live"), live: true};
  const gm = gdGameOf(club), k = gm ? Date.parse(gm.kickoff) : gdKickOf(club);
  return {state: "pre", label: k === undefined || isNaN(k) ? "" : gdClock(k), live: false};
}
