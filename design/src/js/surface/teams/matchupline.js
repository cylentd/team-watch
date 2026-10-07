/* The matchup line, drawn (2026-10-07). data/matchupline.js says who he faces; this prints it the same
   way on the Sheet's row and on a card's back: "vs BUF 29th" with the stadium's roof, the kickoff on the
   line under it, in the reader's clock (lib/kick.js). A bye is one word. */

/* A flat mark, solid for a dome, an outline for a retractable roof (the data does not say whether it is
   open), nothing outdoors. */
function mlRoofHTML(roof){
  if (!roof) return "";
  const label = roof === "dome" ? t("teams.line.dome") : t("teams.line.retractable");
  const shape = roof === "dome"
    ? `<path d="M1 10 A6 6 0 0 1 13 10 Z" fill="currentColor"/>`
    : `<path d="M1.7 10 A5.3 5.3 0 0 1 12.3 10" fill="none" stroke="currentColor" stroke-width="1.4"/>`;
  return `<svg class="ml-roof ${roof}" viewBox="0 0 14 11" role="img" aria-label="${label}" data-testid="roster-roof">${shape}<rect x="0" y="9.6" width="14" height="1.4" fill="currentColor"/></svg>`;
}

/* The first line's parts: where and who ("vs BUF"), the rank in its band's colour, the roof. */
function mlGameHTML(m, p){
  const rank = m.rank
    ? ` <span class="ml-rk ml-${m.tone}" data-testid="roster-rank" title="${t("teams.line.rankTip", {nth: ordinal(m.rank), of: m.of, pos: esc(p.pos)})}">${ordinal(m.rank)}</span>` : "";
  return `<span class="ml-vs">${whereWord(m)} ${esc(m.opp)}</span>${rank}${mlRoofHTML(m.roof)}`;
}

/* The kickoff, with his position in front where the row does not already show it ("RB · Sun 1:05 PM"). */
function mlKickText(m, p, saysPos){
  const when = m.bye ? t("teams.line.bye") : kickFmt(m.kickoff);
  return saysPos && when ? t("teams.line.posWhen", {pos: esc(p.pos), when}) : when;
}

/* The Sheet's two lines under a name. A bye is one line; with no schedule the old "RB · LA". */
function mlRowHTML(p){
  const m = matchupLine(p);
  if (!m) return `<div class="ml-1" data-testid="roster-row-game">${t("teams.line.posTeam", {pos: esc(p.pos), team: esc(p.team)})}</div>`;
  const pos = mlSaysPos(p);
  if (m.bye) return `<div class="ml-1" data-testid="roster-row-game">${mlKickText(m, p, pos)}</div>`;
  return `<div class="ml-1" data-testid="roster-row-game">${mlGameHTML(m, p)}</div>
        <div class="ml-2" data-testid="roster-row-kick">${mlKickText(m, p, pos)}</div>`;
}
