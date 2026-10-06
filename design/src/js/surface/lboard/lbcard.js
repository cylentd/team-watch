/* ============================== LEAGUE > TEAMS: ONE TEAM'S CARD ==============================
   2026-10-06 (trade finder, unit U3). One card per team in the league, drawn from design/teams.py's
   LIVE_TEAMS: the header (name, record, lineup total), the strength strip (QB RB WR TE FLX, tinted against
   the league's median, a lime "+" for a spare starter), the starters one row each (slot, name as initials,
   projected points), the bench as one wrapped line, and a foot. A card is not a button: nothing opens from a
   tap on it (its foot's link opens the trade finder on that team; the team page, lbpage.js, is gone). The board
   (lboard.js) sorts and places the cards; this file draws one. */

/* A projected 0 is BYE when his NFL club has no game in the page week (design/teams.py sets `bye`), else a
   dash: he is hurt, unprojected or already played. */
const lbPts = r => r.pts ? lbNum(r.pts) : r.bye ? t("lboard.card.bye") : t("lboard.card.dash");

/* One strip cell: the column's label over the team's sum there, green or red 8% off the league's median. */
function lbCellHTML(tm, lg, c){
  const plus = tm.spare.includes(c) ? `<i class="lb-plus" title="${t("lboard.spare.title")}">+</i>` : "";
  return `<span class="lb-c ${lbTone(tm.cols[c], lg.median[c])}" data-testid="teams-cell" data-col="${c}">
    <i class="lb-cl">${c}</i><b data-testid="teams-cell-v">${lbNum(tm.cols[c])}</b>${plus}</span>`;
}

function lbStarterHTML(r){
  return `<li class="lb-s" data-testid="teams-starter"><span class="lb-pos" data-pos="${esc(r.pos)}" data-testid="teams-slot">${esc(r.slot)}</span>
    <span class="lb-n" data-testid="teams-player">${esc(nameInitial(r.n))}</span>
    <b class="lb-pts" data-testid="teams-pts">${lbPts(r)}</b></li>`;
}

/* The bench is one line that wraps: position, name as initials, points, a gap between players. */
function lbBenchHTML(tm){
  const one = r => `<span class="lb-bi" data-testid="teams-bench-item"><i data-pos="${esc(r.pos)}" data-testid="teams-slot">${esc(r.pos)}</i>
    <span data-testid="teams-player">${esc(nameInitial(r.n))}</span> <b data-testid="teams-pts">${lbPts(r)}</b></span>`;
  return `<p class="lb-bench" data-testid="teams-bench"><span class="lb-bh">${t("lboard.card.bench")}</span>${
    tm.bench.length ? tm.bench.map(one).join("") : `<em>${t("lboard.card.nobench")}</em>`}</p>`;
}

/* What the card's foot holds, "" for nothing (then the card draws no foot). The reader's own card says so; a
   reader with no team in this league is offered the card as theirs by a quiet text link (pickTeam, the team switch's
   own function; lime is for the one primary action on a screen, 2026-10-06); a card of another team, for a reader who
   has one here, ends in "Trades with them ›", which opens the finder filtered to that team (finder/finder.js). */
function lbCardFoot(lg, tm, mine){
  if (mine) return `<span class="lb-yours" tabindex="-1" data-testid="teams-yours">${t("lboard.team.yours")}</span>`;
  const gate = tbGate(tm);
  return gate === "set" ? `<button type="button" class="lb-mine" data-lbmine="${esc(tm.key)}" data-testid="teams-mine">${t("lboard.team.mine")}</button>`
    : gate === "find" ? `<button type="button" class="lb-trade" data-lbtrade="${esc(tm.key)}" aria-label="${t("lboard.team.tradesAria", {name: esc(tm.name)})}"
      data-testid="teams-trades">${t("lboard.team.trades")}</button>` : "";
}

function lbCardHTML(tm, lg, cols){
  const rec = lbRecord(tm), mine = tm.key === myTeamLoad(), foot = lbCardFoot(lg, tm, mine);
  return `<article class="lb-card${mine ? " mine" : ""}" data-lbcard="${esc(tm.key)}" data-testid="teams-card">
    <header class="lb-ch"><div class="lb-id"><h3 class="lb-name" data-testid="teams-name">${esc(tm.name)}</h3>${
      rec ? `<small class="lb-rec" data-testid="teams-record">${rec}</small>` : ""}</div>
      <b class="lb-tot" data-testid="teams-total">${lbNum(tm.tot)}</b></header>
    <div class="lb-strip">${cols.map(c => lbCellHTML(tm, lg, c)).join("")}</div>
    <ol class="lb-starters">${tm.lineup.map(lbStarterHTML).join("")}</ol>
    ${lbBenchHTML(tm)}${foot ? `<footer class="lb-foot" data-testid="teams-foot">${foot}</footer>` : ""}</article>`;
}
