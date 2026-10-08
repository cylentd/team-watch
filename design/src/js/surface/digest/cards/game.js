/* DIGEST CARD: Tonight (Thursday and Monday; 2026-10-08, Home draft B). The day's game still to kick off, one card:
   the kickoff and its sky, Vegas beside Claude per bet (vegas.js, the dossier's rows), then our two best starts in the
   game, SMASH first, then the bold STARTs, and a foot counting the rest with a link to Start/Sit. It supersedes three
   blocks of one game: the projected-points card (tonight.js), Claude vs Vegas and Start in this game. A start's
   answer is the pick word over Ranks' own rank ("WR4"); a tap opens our rank, his season average, his team's total,
   the main line and the TD price, whichever the call carries. The header link opens Preview on the game. Once it
   kicks off the card goes, and the live block (tonight.js, mnf.js) has the game. Interface: card.js; returns ""
   without a game today or with neither a line nor a start to show. */
const DG_TONIGHT_ROWS = 2;

/* "WR3": the position and the rank under it, "" for a missing rank. */
const dgSsRank = (pos, n) => n == null ? "" : `${pos}${n}`;

/* The team total the books put on a player's club in his game (LIVE_PREVIEW line.implied), or null. */
function dgGameTotal(ctx, r){
  const g = ((ctx.preview && ctx.preview.games) || []).find(x => [x.home, x.away].map(schedCode).includes(schedCode(r.team))
    && [x.home, x.away].map(schedCode).includes(schedCode(r.opp)));
  const v = g && g.line && g.line.implied && g.line.implied[r.team];
  return v == null ? null : pvNum(v);
}

/* [[label, value]]: our rank, his season average, the team total, the main line, the TD price, then the
   reasons a bold call carries (the team total among them only when the books gave none). */
function dgGameResearch(ctx, r){
  const total = dgGameTotal(ctx, r), l = r.line;
  return [[t("digest.card.game.rank"), dgRankOf(r, ctx.ranks) || dgSsRank(r.pos, r.rank)],
    ...(r.avg_rank == null ? [] : [[t("digest.card.game.avg"), dgSsRank(r.pos, r.avg_rank)]]),
    ...(total === null ? [] : [[t("digest.card.game.total"), total]]),
    ...(l ? [[t("digest.card.game.line"), `${l.value.toFixed(1)} ${MU_STAT()[l.stat] || l.stat}`]] : []),
    ...(r.td_price == null ? [] : [[t("digest.card.game.td"), fmtAm(r.td_price)]]),
    ...(r.reasons || []).filter(w => !(total !== null && w.k === "script")).map(w => [t("digest.card.game.why"), w.t])];
}

/* "DAL · WR4": his club and Ranks' rank (the storyboard's row), the pick word alone at the right. */
function dgGameRowHTML(ctx, r, pill){
  const rank = dgRankOf(r, ctx.ranks) || dgSsRank(r.pos, r.rank);
  return dgRowHTML("tonight", {slug: r.slug, n: dgShort(r.name), meta: [esc(r.team || ""), esc(rank)].filter(Boolean).join(" · "),
    answer: {pill}, research: dgGameResearch(ctx, r)});
}

/* [[row, pill]]: every call in the game, SMASH by points, then the bold STARTs. */
function dgGameStarts(ss3, g){
  if (!ss3) return [];
  const teams = [schedCode(g.away), schedCode(g.home)], inGame = r => teams.includes(schedCode(r.team));
  return [...(ss3.smash || []).filter(inGame).sort((a, b) => (b.pts || 0) - (a.pts || 0)).map(r => [r, "SMASH"]),
    ...(ss3.takes || []).filter(r => r.call === "START" && inGame(r)).map(r => [r, "START"])];
}

/* {i, game}: the same game in LIVE_PREVIEW (its lines, Claude's take, the index Preview opens on), or null. */
function dgGamePreview(ctx, g){
  const games = ctx.preview && schedIsPageWeek(ctx.preview.week) ? ctx.preview.games : [];
  const i = games.findIndex(x => gdSameClub(x.home, g.home) && gdSameClub(x.away, g.away));
  return i < 0 ? null : {i, game: games[i]};
}

/* "5:15 PM · 82°F · 5 mph wind · Clear": the kickoff, then the packet's sky for the game when it has one. */
function dgGameSky(ctx, g){
  const tn = ((ctx.d && ctx.d.tn) || []).find(x => gdSameClub(x.home, g.home));
  const sky = tn && tn.wx ? dgTnSky(tn.wx) : "";
  return [esc(kickTime(g.kickoff)), sky].filter(Boolean).join(" · ");
}

/* {i, game}: today's first preview game still to kick off, for a day whose schedule lacks it. */
function dgTonightPreview(ctx){
  const games = ctx.preview && schedIsPageWeek(ctx.preview.week) ? ctx.preview.games : [];
  const hits = games.map((game, i) => ({i, game})).filter(x => dgToday(x.game.kickoff, ctx.now) && Date.parse(x.game.kickoff) > ctx.now);
  return hits.sort((a, b) => Date.parse(a.game.kickoff) - Date.parse(b.game.kickoff))[0] || null;
}

function dgCardTonight(ctx){
  const sched = ctx.schedule && dgPickKickoff(ctx.schedule.games, ctx.now);
  const pv = sched ? dgGamePreview(ctx, sched) : dgTonightPreview(ctx), g = sched || (pv && pv.game);
  if (!g) return "";
  const bets = pv ? dgVegasTableHTML(pv.game) : "";
  const starts = dgGameStarts(ctx.ss3, g), rows = starts.slice(0, DG_TONIGHT_ROWS), rest = starts.length - rows.length;
  if (!bets && !rows.length) return "";
  const body = `<p class="dg-vg-game" data-testid="digest-tonight-sky">${dgGameSky(ctx, g)}</p>${bets}`
    + rows.map(([r, pill]) => dgGameRowHTML(ctx, r, pill)).join("");
  return dgCardHTML({id: "tonight", title: t("digest.card.tonight.title", {game: dgGame(g)}),
    more: pv ? {leaf: "preview", game: pv.i} : {leaf: "preview"},
    body, foot: rest > 1 ? t("digest.card.tonight.more", {n: rest}) : rest ? t("digest.card.tonight.moreOne") : "", footGo: rows.length ? {leaf: "matchups"} : null});
}
