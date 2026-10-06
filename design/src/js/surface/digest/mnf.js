/* ============================== DIGEST: THE LAST GAME ==============================
   2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV (David: "The Monday game
   needs to be its own section."). Once every game before the week's last day is final and one or two
   remain (data/digest.js dgWeek: Monday, or any last standalone game), a card sits above the ticker:
   the game itself. It stands in for Tonight's card (tonight.js) while it shows.

   One compact block per game (2026-10-05, storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP):
   about 80px at 360px where the card was 300-450px. Line 1 the day and the clock ("MON · Q3 4:12", or
   before kickoff "MON 8:15 PM · ATL @ NO"), line 2 the score in mono ("ATL 17 · NO 21"), line 3 the
   game's top performer in yards and touchdowns, never fantasy points (David, 2026-10-05: every league
   scores differently). Before kickoff there is no score and no line 3. A tap opens the game's sheet
   (live/gamesheet.js, the one the Games tab opens). Tonight's card uses the same block once its game
   is on (tonight.js dgTnCard), so a Thursday game reads like a Monday one.

   Generic by rule (David, 2026-10-04: "The Digest is supposed to be GENERIC for the public. It
   shouldn't hone on to my roster or their roster."): nothing here reads a league, a roster or a
   matchup. Numbers are the poll's GD_STATS (scores, GD_STATS.lead), the same reply Live reads. */

/* The late slot itself, dgMnfSlot, is data (data/digest.js): this file only draws it. */

const dgMnfIn = (g, r) => gdSameClub(g.home, r.team) || gdSameClub(g.away, r.team);

/* His yards and touchdowns: a passer's yards are his passing yards, anyone else's rushing plus
   receiving; a passing TD is the same score as the catch, counted once (dgTopLine says the same in the
   headline, in its own words). A scorer with neither (a kicker, a defense) gets Live's whole line. */
function dgMnfNums(r){
  const s = r.s || {}, n = k => +(s[k] || 0), pass = n("pass_yd") > n("rush_yd") + n("rec_yd");
  return {yds: Math.round(pass ? n("pass_yd") : n("rush_yd") + n("rec_yd")), tds: n("rush_td") + (pass ? n("pass_td") : n("rec_td"))};
}

function dgMnfLine(r){
  const {yds, tds} = dgMnfNums(r);
  const line = [yds > 0 ? t("digest.mnf.yds", {n: yds}) : "", tds ? t("digest.mnf.td", {n: tds}) : ""].filter(Boolean).join(", ");
  return line || gdLine({pos: r.pos}, r.s || {});
}

/* The game's best performer in the poll's league-wide list: the best scorer who has yards or a
   touchdown, else just the best scorer. */
function dgMnfTop(g){
  const rows = dgLeaders().filter(r => dgMnfIn(g, r));
  return rows.find(r => { const m = dgMnfNums(r); return m.yds > 0 || m.tds > 0; }) || rows[0] || null;
}

/* "MON · Q3 4:12" once on, "MON · Final" after; before kickoff "MON 8:15 PM · ATL @ NO". */
function dgMnfWhen(x){
  const fmt = kickFmt(x.k), day = fmt.split(" ")[0].toUpperCase();
  if (x.st === "final") return t("digest.mnf.on", {day, clock: t("live.clock.final")});
  if (x.st === "live") return t("digest.mnf.on", {day, clock: gdClockOf(x.g.home).label});
  return t("digest.mnf.pre", {day, time: kickTime(x.k), game: `${x.g.away} @ ${x.g.home}`});
}

/* One game's block: the whole of it is one button. `x` is {g, k, st} (dgWeek's row). */
function dgMnfGame(x){
  const g = x.g, played = x.st !== "pre";
  const a = played ? gdClubScore(g.away, g.home) : null, h = played ? gdClubScore(g.home, g.away) : null;
  const score = a !== null && h !== null
    ? `<span class="dg-mnf-s">${esc(g.away)} <b>${a}</b><i aria-hidden="true"> · </i>${esc(g.home)} <b>${h}</b></span>` : "";
  const top = played ? dgMnfTop(g) : null;
  const by = top ? `<span class="dg-mnf-t">${esc(dgShort(top.n))} ${esc(dgMnfLine(top))}</span>` : "";
  return `<button type="button" class="dg-mnf-g" data-testid="digest-mnf-block" data-dgblk="${esc(g.home)}" data-event="${esc(g.espn || "")}"
    data-away="${esc(g.away)}" data-home="${esc(g.home)}" data-st="${x.st}">
    <span class="dg-mnf-w" data-testid="digest-mnf-when">${esc(dgMnfWhen(x))}</span>${score}${by}${DG_ARROW}</button>`;
}

/* The block for a game of the week's schedule, in the state the clock puts it in. Both the late slot and
   Tonight's card (tonight.js) draw it, and a poll repaints it in place by its club (now.js). */
const dgMnfFor = g => dgMnfGame({g, k: Date.parse(g.kickoff), st: dgGameState(g, Date.now())});

/* The card: each of the slot's games as a block. "" when there is no slot. */
function dgMnfHTML(){
  const late = dgMnfSlot(Date.now());
  if (!late) return "";
  return `<section class="dg-tn dg-mnf" data-testid="digest-tn" data-dgmnf aria-label="${t("digest.mnf.label")}">${late.map(dgMnfGame).join("")}</section>`;
}
