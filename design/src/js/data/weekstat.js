/* The stat line on a Week plays card (2026-10-07, David: "7-25-0 · 10-68" reads as a date). A week's box
   score row in words: yards with their unit, the biggest kind first ("25 rush yds · 68 rec yds"), then the
   touchdowns of every kind summed ("· 2 TD"), only when there is one. No counts (carries, catches, targets,
   attempts) and no turnovers: the line is a highlight. A kind with no yards is left out, so a week of one
   touchdown and no yards says "1 TD" and a week of nothing says nothing.

   The card is narrow, so the line comes as candidates, the whole line first, each next one without the
   smallest yardage kind that is left, and the touchdowns last of all to go: wsLine picks the first that fits.
   `fit` is a width budget in characters (tests) or a function that measures the card (surface/teams/reel.js);
   without one the whole line is kept. A line that fits nowhere is the shortest, never cut with an ellipsis.
   The page computes no stats; the row is LIVE_GAMELOG's box score. */

/* {kinds: [{k, yds}] biggest first (a tie keeps pass, rush, rec), td: touchdowns of every kind}. */
function wsParts(pos, r){
  const n = k => (r && Number(r[k])) || 0;
  const kinds = [{k: "pass", yds: n("pass_yds")}, {k: "rush", yds: n("rush_yds")}, {k: "rec", yds: n("rec_yds")}]
    .filter(x => x.yds > 0).sort((a, b) => b.yds - a.yds);
  return {kinds, td: n("pass_td") + n("rush_td") + n("rec_td")};
}

/* One kind's words, every key spelled out so the copy check can see it. */
function wsKind(x){
  return x.k === "pass" ? t("teams.clips.stat.pass", {n: x.yds})
    : x.k === "rush" ? t("teams.clips.stat.rush", {n: x.yds}) : t("teams.clips.stat.rec", {n: x.yds});
}

/* The lines from the whole to the shortest: [] when there is nothing to say. */
function wsCandidates(parts){
  const words = parts.kinds.map(wsKind), td = parts.td > 0 ? [t("teams.clips.stat.td", {n: parts.td})] : [];
  const out = [];
  for (let k = words.length; k >= 1; k--) out.push([...words.slice(0, k), ...td].join(t("teams.clips.stat.sep")));
  if (td.length) out.push(td[0]);
  return out;
}

/* The first of `all` that fits, else the last (the shortest); "" for none. */
function wsPick(all, fit){
  const ok = typeof fit === "number" ? s => s.length <= fit : typeof fit === "function" ? fit : () => true;
  return all.find(ok) ?? all[all.length - 1] ?? "";
}

function wsLine(pos, r, fit){ return wsPick(wsCandidates(wsParts(pos, r)), fit); }
