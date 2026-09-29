/* ============================== GAMEDAY: ONE GAME FROM ESPN ==============================
   The game sheet's scoreboard and plays (2026-09-28, storyboard
   https://claude.ai/artifact/7dtFfrweZG7mYE6oWSjmFb). The reader's browser asks ESPN's public game
   summary directly: it answers a browser (200, checked 2026-09-28) and refuses servers and headless
   browsers (403), so neither api/game.py nor the tests can ask for it. The tests shape the saved
   game in tests/fixtures/data/espn_summary.json instead.

   gsShape is pure: the summary in, what the sheet draws out. Nothing here touches the page. */

const GS_ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=";
const GS_TIMEOUT_MS = 12000;
/* Rows that are not plays: the end of a quarter or half, a timeout, the two-minute warning. */
const GS_NOT_PLAY = /^(end |timeout|two-minute|official timeout)/i;

async function gsFetchSummary(event){
  const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), GS_TIMEOUT_MS);
  try {
    const res = await fetch(GS_ESPN + encodeURIComponent(event), {signal: ctl.signal});
    return res.ok ? await res.json() : null;
  } finally { clearTimeout(timer); }
}

const gsOrd = n => ["", "1st", "2nd", "3rd", "4th"][n] || `${n}th`;

/* "2nd & 6 at PHI 38" from a play's start or end: the yards to the end zone are the side with the
   ball's, so more than 50 is its own half. A kickoff or an extra point has no down and says nothing. */
function gsWhere(spot, abbrOf, other){
  if (!spot || !(spot.down >= 1) || !(spot.yardsToEndzone > 0)) return "";
  const own = abbrOf[(spot.team || {}).id] || "", ytez = spot.yardsToEndzone;
  const at = ytez === 50 ? "50" : ytez > 50 ? `${own} ${100 - ytez}` : `${other(own)} ${ytez}`;
  const dist = spot.distance >= ytez ? "Goal" : spot.distance;
  return t("live.sheet.where", {d: gsOrd(spot.down), n: dist, at});
}

function gsSide(c){
  const tm = c.team || {};
  return {id: tm.id, abbr: tm.abbreviation, name: tm.shortDisplayName || tm.name || tm.abbreviation,
          score: c.score === undefined || c.score === "" ? null : +c.score};
}

/* A drive's one line: "8 plays · 65 yds · 0:39". */
function gsDriveLine(d){
  if (d.offensivePlays !== undefined && d.yards !== undefined)
    return t("live.sheet.drive", {p: d.offensivePlays, y: d.yards, tm: (d.timeElapsed || {}).displayValue || ""});
  return (d.description || "").replace(/,\s*/g, " · ").replace(/ yards/, " yds");
}

function gsShape(summary){
  const comp = (((summary || {}).header || {}).competitions || [])[0];
  if (!comp) return null;
  const cs = comp.competitors || [];
  const home = gsSide(cs.find(c => c.homeAway === "home") || {}), away = gsSide(cs.find(c => c.homeAway === "away") || {});
  const abbrOf = {[home.id]: home.abbr, [away.id]: away.abbr};
  const other = a => a === home.abbr ? away.abbr : home.abbr;
  const st = (comp.status || {}).type || {};
  const dr = summary.drives || {};
  const chrono = [...(dr.previous || []), ...(dr.current ? [dr.current] : [])];
  /* The drive in progress is ESPN's `current`, or the last one while the game is on. */
  const onDrive = st.state === "in" ? chrono.length - 1 : -1;
  const drives = chrono.map((d, i) => {
    const plays = (d.plays || []).filter(p => !GS_NOT_PLAY.test((p.type || {}).text || "") && !GS_NOT_PLAY.test(p.text || ""))
      .map(p => ({q: (p.period || {}).number, clock: (p.clock || {}).displayValue || "", text: p.text || "",
                  dd: (p.start || {}).downDistanceText || gsWhere(p.start, abbrOf, other), sc: !!p.scoringPlay}));
    const res = d.result || d.displayResult || "";
    return {team: abbrOf[(d.team || {}).id] || (d.team || {}).abbreviation || "", line: gsDriveLine(d),
            res, sc: !!d.isScore || /^(TD|FG|touchdown|field goal)/i.test(res), on: i === onDrive, plays: plays.reverse()};
  }).filter(d => d.plays.length).reverse();
  return {state: st.state || "pre", detail: st.shortDetail || st.detail || "", home, away,
          now: st.state === "in" ? gsNow(summary, chrono, abbrOf, other) : null, drives};
}

/* Where the ball is now: ESPN's `situation` when the summary carries one, else the end of the last
   play. `ytez` places the ball on the strip under the scoreboard. */
function gsNow(summary, chrono, abbrOf, other){
  const s = summary.situation;
  if (s && s.possession) return {ball: abbrOf[s.possession] || "", dd: s.downDistanceText || "", ytez: s.yardsToEndzone};
  const last = [...chrono].reverse().flatMap(d => [...(d.plays || [])].reverse()).find(p => p.end && p.end.down);
  if (!last) return null;
  return {ball: abbrOf[(last.end.team || {}).id] || "", dd: gsWhere(last.end, abbrOf, other), ytez: last.end.yardsToEndzone};
}
