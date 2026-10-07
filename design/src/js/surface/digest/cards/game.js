/* DIGEST CARD: Start in this game (Thursday) / Start tonight (Monday). The calls LIVE_SS3 makes for the day's
   game still to kick off: SMASH first, then the bold STARTs, four rows at most. The answer is the pick word with
   the position rank under it ("WR3"); a tap opens our rank, his season average, his team's total, the main line
   and the TD price, whichever the call carries. The foot is Start/Sit's record with its marks (dgCardRecord);
   more to Matchups. Interface: card.js; returns "" when no call is in that game. */
const DG_GAME_ROWS = 4;

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
  return [[t("digest.card.game.rank"), dgSsRank(r.pos, r.rank)],
    ...(r.avg_rank == null ? [] : [[t("digest.card.game.avg"), dgSsRank(r.pos, r.avg_rank)]]),
    ...(total === null ? [] : [[t("digest.card.game.total"), total]]),
    ...(l ? [[t("digest.card.game.line"), `${l.value.toFixed(1)} ${MU_STAT()[l.stat] || l.stat}`]] : []),
    ...(r.td_price == null ? [] : [[t("digest.card.game.td"), fmtAm(r.td_price)]]),
    ...(r.reasons || []).filter(w => !(total !== null && w.k === "script")).map(w => [t("digest.card.game.why"), w.t])];
}

function dgGameRowHTML(ctx, r, pill){
  return dgRowHTML("game", {slug: r.slug, n: dgShort(r.name), meta: muVs(r), answer: {pill, sub: dgSsRank(r.pos, r.rank)},
    research: dgGameResearch(ctx, r)});
}

function dgCardGame(ctx){
  const g = ctx.schedule && dgPickKickoff(ctx.schedule.games, ctx.now);
  if (!ctx.ss3 || !g) return "";
  const teams = [schedCode(g.away), schedCode(g.home)], inGame = r => teams.includes(schedCode(r.team));
  const rows = [...ctx.ss3.smash.filter(inGame).sort((a, b) => (b.pts || 0) - (a.pts || 0)).map(r => [r, "SMASH"]),
    ...ctx.ss3.takes.filter(r => r.call === "START" && inGame(r)).map(r => [r, "START"])].slice(0, DG_GAME_ROWS);
  if (!rows.length) return "";
  return dgCardHTML({id: "game", title: ctx.day === "mon" ? t("digest.card.game.tonight") : t("digest.card.game.title"),
    more: {leaf: "matchups"}, body: rows.map(([r, pill]) => dgGameRowHTML(ctx, r, pill)).join(""), foot: dgRecordFoot(ctx, "game")});
}
