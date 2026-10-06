/* The profile strip's cells as data (plan U3, 2026-10-05). The strip under the head used to open with
   "WR3" and "26.2 PPG", which read as this week's projection and was last season to date. The headline
   is now this week's projection (ui/player.js projFor, the one projection source since U1), and season
   points per game comes second under its own label. surface/profile/lede.js only draws what this returns.

   Input is already resolved by the caller: `proj` {pts, out, done} or null (projFor, projOut, projDone),
   `ppg` a number or null, `rank` the position rank text ("WR3") or null, `share` {id, pct} for carries
   or targets, `snaps` a percent text. A cell with no source is left out; an empty strip is []. An injured
   player's headline is the reason he has no number (Out), a finished or idle week says Played or Bye.
   `range` (ui/player.js rangeFor, plan U5) is the floor and ceiling beside the projection: the projection
   cell carries its text when it shows a number, never beside Out, Played or Bye. */
function ledeCells({proj, ppg, rank, share, snaps, range}){
  const out = [];
  if (proj){
    const value = proj.out ? t("profile.lede.out") : proj.done === "played" ? t("teams.card.played")
      : proj.done === "bye" ? t("teams.card.bye") : typeof proj.pts === "number" ? proj.pts.toFixed(1) : null;
    if (value !== null){
      const cell = {id: "proj", value, label: t("profile.lede.proj")};
      if (range && range.text && !proj.out && !proj.done && typeof proj.pts === "number") cell.range = range.text;
      out.push(cell);
    }
  }
  if (typeof ppg === "number") out.push({id: "ppg", value: ppg.toFixed(1), label: t("profile.lede.ppg")});
  if (rank) out.push({id: "rank", value: rank, label: t("profile.lede.rank")});
  if (share && share.pct) out.push({id: "share", value: share.pct, label: share.id === "carries" ? t("profile.lede.carries") : t("profile.lede.targets")});
  if (snaps) out.push({id: "snaps", value: snaps, label: t("profile.lede.snaps")});
  return out;
}
