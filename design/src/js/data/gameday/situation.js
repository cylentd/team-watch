/* ============================== GAMEDAY: THE BALL ==============================
   Who has the ball, the down and distance, and whether it is inside the 20 (U9, 2026-10-05; David: "the
   live scoreboard should show the direction of the ball or team and the redzone").

   ESPN's `situation` object says it, in the game summary (read by the game sheet, espn.js gsNow) and in
   the scoreboard's competition (read by the Games tab, clock.js gdClockShape), so a live card needs no
   request of its own beyond the one Live already makes for every game's clock. Its fields, as the
   summary carries them: possession (a team id), downDistanceText ("3rd & 4 at DET 15"),
   shortDownDistanceText ("3rd & 4"), possessionText (the spot, "DET 15"), isRedZone, yardsToEndzone.
   The scoreboard's copy, read live 2026-10-05 (ATL @ NO, 3rd quarter), carries possession,
   downDistanceText ("3rd & 3 at ATL 8"), shortDownDistanceText, possessionText and isRedZone, but no
   yardsToEndzone; at halftime it carries down, distance and isRedZone with no possession, so no ball
   shows. When a field is missing the card shows less, never a guess.

   gdSitShape is pure: a situation and the id -> club code map in, {ball, dd, red, ytez} out. */

/* Inside the opponent's 20 (the 20 itself counts): the spot's side is the other club's, its yards 1-20. */
function gdSpotInRedZone(spot, ball){
  const m = /^([A-Z]{2,4}) (\d{1,2})$/.exec(String(spot || "").trim());
  return !!m && m[1] !== ball && +m[2] >= 1 && +m[2] <= 20;
}

function gdSitShape(raw, abbrOf){
  if (!raw || raw.possession === undefined || raw.possession === null || raw.possession === "") return null;
  const ball = (abbrOf || {})[raw.possession];
  if (!ball) return null;
  const red = typeof raw.isRedZone === "boolean" ? raw.isRedZone : gdSpotInRedZone(raw.possessionText, ball);
  return {ball, dd: raw.downDistanceText || raw.shortDownDistanceText || "", short: raw.shortDownDistanceText || "", red,
          ytez: typeof raw.yardsToEndzone === "number" ? raw.yardsToEndzone : null};
}

/* A tile's line: the down and distance without the spot ("3rd & 4", the red-zone tag sits beside it),
   or the club with the ball when it is a kickoff or ESPN left the down out. */
function gdSitText(sit){
  return sit.short || sit.dd || t("live.sheet.ball", {club: sit.ball});
}

/* The club's game situation from the scoreboard's last read; null before kickoff, after the final or
   when ESPN sent none. */
function gdSitOf(club){
  const g = gdByCode(GD_CLOCK, club);
  return (g && g.state === "in" && g.sit) || null;
}
