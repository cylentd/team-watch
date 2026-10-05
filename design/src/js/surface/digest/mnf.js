/* ============================== DIGEST: THE LAST GAME ==============================
   2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV (David: "The Monday game
   needs to be its own section."). Once every game before the week's last day is final and one or two
   remain (now.js dgWeek: Monday, or any last standalone game), a card sits above the ticker: the
   game, then for each league my matchup, who is still to play on each side with their projections,
   and one sentence of what the result needs. It stands in for Tonight's card (tonight.js) while it
   shows, and stays through the game with live points. Scores come from the poll (GD_STATS) through
   Live's own scorer (gdSide), so the Digest and Live never disagree. */

/* The late slot itself, dgMnfSlot, is data (data/digest.js): this file only draws it. */

const dgDayName = k => new Date(k).toLocaleDateString("en-US", {weekday: "long"});
const dgMnfName = r => r.pos === "DEF" ? r.n : dgShort(r.n);

/* My matchup in one league: both sides scored, who of each is still to play in the late game(s). */
function dgMnfLeague(lg, late){
  const game = lg.games.find(g => g.includes(lg.me));
  if (!game) return null;
  const stats = GD_STATS.stats, states = GD_STATS.games || {};
  const side = id => gdSide(lg, id, stats, states);
  const mine = side(lg.me), theirs = side(game[0] === lg.me ? game[1] : game[0]);
  const inLate = r => late.some(x => gdSameClub(x.g.home, r.team) || gdSameClub(x.g.away, r.team));
  const toPlay = s => s.rows.filter(r => r.state !== "complete" && inLate(r));
  const median = lg.median ? gdLadder(Object.keys(lg.teams).map(side)).median : null;
  return {lg, mine, theirs, gap: Math.round((mine.total - theirs.total) * 100) / 100, left: [toPlay(mine), toPlay(theirs)], median};
}

/* What it takes, in one sentence. Exact when the side that can still move has one man left; with
   players on both sides the other side's points join in, and the sentence says so. */
function dgMnfSay(L){
  const [mine, theirs] = L.left, n = dgN1(Math.abs(L.gap));
  const yours = () => mine.length === 1 ? esc(dgMnfName(mine[0])) : t("digest.mnf.whoYours", {n: mine.length});
  const their = () => theirs.length === 1 ? esc(dgMnfName(theirs[0])) : t("digest.mnf.whoTheirs", {n: theirs.length});
  if (Math.abs(L.gap) < 0.05) return t("digest.mnf.even");
  if (L.gap > 0){
    if (!theirs.length) return t("digest.mnf.clinched");
    return mine.length ? t("digest.mnf.stayPlus", {who: their(), n}) : t("digest.mnf.stay", {who: their(), n});
  }
  if (!mine.length) return t("digest.mnf.lost");
  return theirs.length ? t("digest.mnf.needPlus", {who: yours(), n}) : t("digest.mnf.need", {who: yours(), n});
}

/* "UP 1.6", "DOWN 9.8", "EVEN": my lead, in my matchup's own words. */
function dgMnfTag(gap){
  if (Math.abs(gap) < 0.05) return `<span class="dg-mnf-lead even">${t("digest.mnf.evenTag")}</span>`;
  const n = dgN1(Math.abs(gap));
  return gap > 0 ? `<span class="dg-mnf-lead up">${t("digest.mnf.up", {n})}</span>` : `<span class="dg-mnf-lead dn">${t("digest.mnf.down", {n})}</span>`;
}

/* One side's players still to play: his name and his projection; mid-game, his points of it. */
function dgMnfList(title, rows){
  const li = r => {
    const p = projFor(r), proj = p === null ? "—" : dgN1(p);
    const num = r.state === "in_game" && r.pts !== null ? t("digest.mnf.pts", {pts: dgN1(r.pts), proj}) : proj;
    const inner = `<span>${esc(dgMnfName(r))}</span><i>${num}</i>`;
    return `<li>${r.pos === "DEF" ? `<span class="dg-mnf-p">${inner}</span>`
      : `<button type="button" class="dg-mnf-p" ${dgLvAttrs(r)}>${inner}</button>`}</li>`;
  };
  return `<div class="dg-mnf-c"><h4>${title}</h4>${rows.length ? `<ul>${rows.map(li).join("")}</ul>` : `<p>${t("digest.mnf.noone")}</p>`}</div>`;
}

/* My median gap in words, as a tag-sized element ("" when the league has no median). */
function dgMnfMed(L, tag){
  if (L.median === null) return "";
  const gap = L.mine.total - L.median, v = {n: dgN1(Math.abs(gap)), line: dgN1(L.median)};
  return `<${tag} class="dg-mnf-med">${gap >= 0 ? t("digest.mnf.medUp", v) : t("digest.mnf.medDown", v)}</${tag}>`;
}

/* A league with nobody left on either side is decided: one line, its name, the score, won or lost
   (and the median gap when it has one). The full block is only for a league with someone to play. */
function dgMnfDoneHTML(L){
  const word = Math.abs(L.gap) < 0.05 ? ["even", t("digest.mnf.tiedTag")] : L.gap > 0 ? ["up", t("digest.mnf.wonTag")] : ["dn", t("digest.mnf.lostTag")];
  return `<div class="dg-mnf-lg done"><b class="dg-mnf-nm">${esc(L.lg.name)}</b>
    <span class="dg-mnf-fin">${dgN1(L.mine.total)} – ${dgN1(L.theirs.total)}</span><span class="dg-mnf-res ${word[0]}">${word[1]}</span>${dgMnfMed(L, "span")}</div>`;
}

function dgMnfLeagueHTML(L){
  if (!L.left[0].length && !L.left[1].length) return dgMnfDoneHTML(L);
  const med = dgMnfMed(L, "p");
  return `<div class="dg-mnf-lg">
    <div class="dg-mnf-top"><b>${esc(L.lg.name)}</b>${dgMnfTag(L.gap)}</div>
    <p class="dg-mnf-score"><span><span class="dg-mnf-nm">${esc(L.mine.name)}</span><b>${dgN1(L.mine.total)}</b></span><span><span class="dg-mnf-nm">${esc(L.theirs.name)}</span><b>${dgN1(L.theirs.total)}</b></span></p>
    <div class="dg-mnf-cols">${dgMnfList(t("digest.mnf.yours"), L.left[0])}${dgMnfList(t("digest.mnf.theirs"), L.left[1])}</div>
    <p class="dg-mnf-say">${dgMnfSay(L)}</p>${med}</div>`;
}

/* The card: "Monday night" over "5:15 PM · ATL @ NO" (the clock once it is on). "" when there is none. */
function dgMnfHTML(){
  const now = Date.now(), late = dgMnfSlot(now);
  if (!late) return "";
  const leagues = GD.leagues.map(lg => dgMnfLeague(lg, late)).filter(Boolean);
  if (!leagues.length) return "";
  const cur = late.find(x => x.st !== "final") || late[0];
  const when = cur.st === "live" ? gdClockOf(cur.g.home).label
    : new Date(cur.k).toLocaleTimeString("en-US", {hour: "numeric", minute: "2-digit"});
  const games = late.map(x => `${esc(x.g.away)} @ ${esc(x.g.home)}`).join(", ");
  return `<section class="dg-tn dg-mnf" data-dgmnf aria-label="${t("digest.mnf.label")}">
    <header class="dg-mnf-h"><b>${t("digest.mnf.head", {day: dgDayName(late[0].k)})}</b>
      <p class="dg-mnf-sub"><time>${esc(when)}</time><i aria-hidden="true"> · </i><span>${games}</span></p></header>
    ${leagues.map(dgMnfLeagueHTML).join("")}
    <div class="dg-foot"><span></span><button type="button" class="dg-go" data-dgmgo>${t("digest.go.live")}${DG_ARROW}</button></div></section>`;
}

/* The banner before the game: "You're up 1.6 going into Monday night", for the first league. null
   once it is on (the top scorer takes the banner back) or when no league can be scored. */
function dgLeadMnf(now){
  const late = dgMnfSlot(now);
  if (!late || late.some(x => x.st !== "pre")) return null;
  const L = dgMnfLeague(GD.leagues[0], late);
  if (!L) return null;
  const day = dgDayName(late[0].k), up = L.gap > 0, even = Math.abs(L.gap) < 0.05;
  const n = `<em class="dg-em ${up ? "go" : "q"}">${dgN1(Math.abs(L.gap))}</em>`;
  return {tone: up ? "go" : "q", photo: "", ghost: even ? "0.0" : (up ? "+" : "−") + dgN1(Math.abs(L.gap)),
          head: even ? t("digest.mnf.headEven", {day}) : up ? t("digest.mnf.headUp", {n, day}) : t("digest.mnf.headDown", {n, day}),
          fact: dgMnfSay(L)};
}
