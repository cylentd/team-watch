/* A kicker's and a defense's card back (2026-10-07, David: the same back as every other card, not a squeezed
   table). Pure and DOM-free, so Node tests it (tests/test_js_supportback.py). A K or D/ST has no weekly fantasy
   points on the page or in ff-jarvis's data (the box score holds QB RB WR TE only), so there are no bars:
   two facts and this week's projection, each a whole label and a value. The numbers are the page's own
   (LIVE_LINES, LIVE_WEATHER, LIVE_DST); nothing is computed here but a sign.

   `f` is {roof, windMph, team, opp, spread, proj}: the stadium's roof ("dome", "retractable", "outdoor" or ""),
   the forecast wind in mph, the club's implied points, the opponent's, the club's spread and the projection;
   any may be null. A row's `v` is null when the page has no number for it (drawn as a dash). */

/* The rows a back draws, in order. A kicker's first fact is the roof when it is a dome, else the wind (a
   retractable roof counts as open air: the data does not say it is shut); the projection row exists only
   when there is one (ESPN has no K slot, a bye has no cell). */
function supportFacts(pos, f){
  const rows = pos === "K"
    ? [f.roof === "dome" ? {key: "roof", v: "dome"} : {key: "wind", v: f.windMph}, {key: "team", v: f.team}]
    : [{key: "opp", v: f.opp}, {key: "spread", v: f.spread}];
  if (typeof f.proj === "number") rows.push({key: "proj", v: f.proj});
  return rows.map(r => ({key: r.key, v: r.v === undefined ? null : r.v}));
}

/* A spread with a real minus and a plus for the underdog; a pick'em is "0", no line a dash. */
function spreadText(n){
  if (typeof n !== "number") return "—";
  return n > 0 ? "+" + n : n < 0 ? "−" + Math.abs(n) : "0";
}
