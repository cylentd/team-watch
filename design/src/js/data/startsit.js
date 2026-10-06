/* Start/Sit's shared pieces (leaf `matchups`): the one open bold call, the kickoff and matchup words
   a row prints, and the record's own reading. Every call is ff-jarvis's, frozen there at its game's
   kickoff and graded there (LIVE_SS3, design/startsit_v3.py); the page only shows them. */

/* The one open bold call ("t:<slug>"), "" for none. */
let MU_OPEN = "";

/* The kickoff, from the call's own ISO time, in the page's one kickoff format (lib/kick.js), "Sun 1:25 PM".
   Null when ff-jarvis gave none; the row then names the matchup alone. */
const muKick = r => kickFmt(r.kick) || null;

/* "DAL vs BAL" / "LAC @ BUF", the call's own club first. */
const muVs = r => !r.opp ? esc(r.team) : r.home ? t("matchups.vs.home", {team: esc(r.team), opp: esc(r.opp)})
  : t("matchups.vs.away", {team: esc(r.team), opp: esc(r.opp)});

/* "CIN @ PIT · Sun 10:00 AM", or the game alone when the call carries no kickoff. */
function muGame(r){
  const kick = muKick(r);
  return kick ? t("matchups.row.meta", {game: muVs(r), kick: esc(kick)}) : muVs(r);
}

/* The picker's opening state (plan U3, 2026-10-05). Picks kept for this week win, an empty kept list
   included (he cleared the card on purpose). Else an owner opens on his closest call with the list
   shut, and anyone else, or an owner with no close call, on an empty card with the search open: the
   audit's first-time visitor was handed a pair he never chose, 8 taps from his own. */
function ssOpening({team, kept, closest}){
  if (Array.isArray(kept)) return {picks: kept, open: kept.length === 0};
  const picks = team ? closest || [] : [];
  return {picks, open: picks.length === 0};
}

/* Does FantasyPros' expert rank (ECR, lower is better) back our START? `fp` is {slug: {pos, ecr}}.
   Only one list compares: same position, a rank for the winner and for the man he beat. A coin flip
   has no winner to contradict. {kind: "contradicts", ours, theirs} names the loser FantasyPros has
   ahead; {kind: "agrees"}; null when the two cannot be set side by side. */
function ssFpCheck(cols, verdict, fp){
  if (!verdict || verdict.flip || !verdict.win || !fp) return null;
  const w = verdict.win, me = fp[w.p.slug];
  if (!me || me.ecr == null) return null;
  const rivals = cols.filter(c => c.p.slug !== w.p.slug && c.p.pos === w.p.pos && fp[c.p.slug] && fp[c.p.slug].ecr != null
    && fp[c.p.slug].pos === me.pos);
  if (!rivals.length) return null;
  const best = rivals.reduce((a, b) => fp[b.p.slug].ecr < fp[a.p.slug].ecr ? b : a);
  return fp[best.p.slug].ecr < me.ecr ? {kind: "contradicts", ours: w.p.slug, theirs: best.p.slug}
    : {kind: "agrees", ours: w.p.slug, theirs: null};
}

/* The one sentence that explains a contradiction, in plain words; "" when there is nothing to explain. */
const ssFpNote = (check, names) => !check || check.kind !== "contradicts" ? ""
  : t("startsit.fp.contradicts", {theirs: esc(names[check.theirs]), ours: esc(names[check.ours])});

/* A record's hit-miss ("5-2"); a week counts once any of its calls is graded. */
const ss3Wl = c => `${c.hit}-${c.miss}`;
const ss3Graded = rec => rec.weeks.length > 0 || ["smash", "start", "sit"].some(k => rec[k].hit + rec[k].miss + rec[k].void > 0);
