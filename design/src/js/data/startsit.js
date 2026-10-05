/* Start/Sit's shared pieces (leaf `matchups`): the one open bold call, the kickoff and matchup words
   a row prints, and the record's own reading. Every call is ff-jarvis's, frozen there at its game's
   kickoff and graded there (LIVE_SS3, design/startsit_v3.py); the page only shows them. */

/* The one open bold call ("t:<slug>"), "" for none. */
let MU_OPEN = "";

/* The kickoff, from the call's own ISO time, in Pacific wall-clock words, "Sun 1:25 PM", as the Digest
   writes them. Null when ff-jarvis gave none; the row then names the matchup alone. */
const MU_KICK_FMT = new Intl.DateTimeFormat("en-US", {timeZone: "America/Los_Angeles", weekday: "short",
  hour: "numeric", minute: "2-digit"});
const muKick = r => r.kick ? MU_KICK_FMT.format(new Date(r.kick)).replace(",", "") : null;

/* "DAL vs BAL" / "LAC @ BUF", the call's own club first. */
const muVs = r => !r.opp ? esc(r.team) : r.home ? t("matchups.vs.home", {team: esc(r.team), opp: esc(r.opp)})
  : t("matchups.vs.away", {team: esc(r.team), opp: esc(r.opp)});

/* "CIN @ PIT · Sun 10:00 AM", or the game alone when the call carries no kickoff. */
function muGame(r){
  const kick = muKick(r);
  return kick ? t("matchups.row.meta", {game: muVs(r), kick: esc(kick)}) : muVs(r);
}

/* A record's hit-miss ("5-2"); a week counts once any of its calls is graded. */
const ss3Wl = c => `${c.hit}-${c.miss}`;
const ss3Graded = rec => rec.weeks.length > 0 || ["smash", "start", "sit"].some(k => rec[k].hit + rec[k].miss + rec[k].void > 0);
