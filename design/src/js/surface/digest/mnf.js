/* ============================== DIGEST: THE LAST GAME ==============================
   2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV (David: "The Monday game
   needs to be its own section."). Once every game before the week's last day is final and one or two
   remain (data/digest.js dgWeek: Monday, or any last standalone game), a card sits above the ticker:
   the game itself. Before kickoff each side's two best projections; while it is on, the score, the
   clock and the game's top scorers; after it, the final. It stands in for Tonight's card (tonight.js)
   while it shows.

   Generic by rule (David, 2026-10-04: "The Digest is supposed to be GENERIC for the public. It
   shouldn't hone on to my roster or their roster."): nothing here reads a league, a roster or a
   matchup. The first version of this card (2bf04c6) drew the reader's matchup per league and is
   superseded. Numbers are the league-wide ones every view shares: LIVE_RANKS (projections) and the
   poll's GD_STATS (scores, GD_STATS.lead). */

/* The late slot itself, dgMnfSlot, is data (data/digest.js): this file only draws it. */

const DG_MNF_PROJ = 2;      // projected players per side, before kickoff
const DG_MNF_SCORERS = 3;   // top scorers of the game, once it is on

const dgDayName = k => new Date(k).toLocaleDateString("en-US", {weekday: "long"});
const dgMnfIn = (g, r) => gdSameClub(g.home, r.team) || gdSameClub(g.away, r.team);

/* One player: his name and a number, a tap opens his profile. */
const dgMnfPlayer = (r, num) => `<li><button type="button" class="dg-mnf-p" ${dgLvAttrs(r)}>
  <span>${esc(dgShort(r.n))}</span><i>${num}</i></button></li>`;

const dgMnfCol = (title, rows, num) => `<div class="dg-mnf-c"><h4>${esc(title)}</h4>${rows.length
  ? `<ul>${rows.map(r => dgMnfPlayer(r, num(r))).join("")}</ul>` : `<p>${t("digest.mnf.none")}</p>`}</div>`;

/* Before kickoff: each side's best projections, LIVE_RANKS' own rows (QB, RB, WR, TE). */
function dgMnfProj(g){
  const rows = typeof LIVE_RANKS !== "undefined" && LIVE_RANKS ? LIVE_RANKS.rows : [];
  const side = club => rows.filter(r => gdSameClub(club, r.team)).sort((a, b) => b.pts - a.pts).slice(0, DG_MNF_PROJ);
  return `<div class="dg-mnf-cols">${[g.away, g.home].map(c => dgMnfCol(c, side(c), r => dgN1(r.pts))).join("")}</div>`;
}

/* While it is on and after it: the score (Sleeper's, nflnow.js gdClubScore) and the game's best scorers
   from the poll's league-wide list. Neither draws until the poll has said something about the game. */
function dgMnfPlay(g){
  const a = gdClubScore(g.away, g.home), h = gdClubScore(g.home, g.away);
  const club = (code, s) => `<span><span class="dg-mnf-nm">${esc(code)}</span><b>${s}</b></span>`;
  const score = a !== null && h !== null ? `<p class="dg-mnf-score">${club(g.away, a)}${club(g.home, h)}</p>` : "";
  const top = dgLeaders().filter(r => dgMnfIn(g, r)).slice(0, DG_MNF_SCORERS);
  return score + (top.length ? `<div class="dg-mnf-cols one">${dgMnfCol(t("digest.mnf.scorers"), top, r => dgN1(r.pts))}</div>` : "");
}

/* The line over a game: its time before kickoff, its clock while on, "Final" after; then the matchup. */
function dgMnfWhen(x){
  if (x.st === "final") return t("live.clock.final");
  if (x.st === "live") return gdClockOf(x.g.home).label;
  return new Date(x.k).toLocaleTimeString("en-US", {hour: "numeric", minute: "2-digit"});
}

function dgMnfGame(x){
  return `<div class="dg-mnf-lg" data-st="${x.st}">
    <p class="dg-mnf-sub"><time>${esc(dgMnfWhen(x))}</time><i aria-hidden="true"> · </i><span>${esc(x.g.away)} @ ${esc(x.g.home)}</span></p>
    ${x.st === "pre" ? dgMnfProj(x.g) : dgMnfPlay(x.g)}</div>`;
}

/* The card: "Monday night", then each of the slot's games. "" when there is no slot. */
function dgMnfHTML(){
  const late = dgMnfSlot(Date.now());
  if (!late) return "";
  return `<section class="dg-tn dg-mnf" data-dgmnf aria-label="${t("digest.mnf.label")}">
    <header class="dg-mnf-h"><b>${t("digest.mnf.head", {day: dgDayName(late[0].k)})}</b></header>
    ${late.map(dgMnfGame).join("")}
    <div class="dg-foot"><span></span><button type="button" class="dg-go" data-dgmgo>${t("digest.go.live")}${DG_ARROW}</button></div></section>`;
}
