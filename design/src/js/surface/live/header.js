/* ------------------------------------------------------------------
   LIVE HEADER — the part you read from across the room.

   The board below is a table and reads like one. This is the opposite: four facts, each big
   enough to take in without focusing, answering the only questions worth asking mid-game.

     the spine    who is ahead, as a length rather than a number
     the trace    how today got here -- ESPN's win probability, one point per reply
     left to play the tension. A 20-point lead with one starter left and the same lead with five
                  left are opposite situations, and a scoreboard alone cannot tell them apart
     the catch-up what moved while you were not looking

   Pure markup, like board.js: everything here reads state and returns a string.
------------------------------------------------------------------ */

/* A starter who has not kicked off yet. Bench never scores, so it never counts as "to come" --
   counting it would promise points no lineup can deliver. */
const gdToCome = side => side.lineup.filter(r => r.starter && !r.started);

function gdSideHTML(side, which){
  return `<div class="gdteam ${which}">
    <p class="gdclubname">${esc(side.team)}</p>
    <p class="gdscore">${gdNum(side.live)}</p>
    <p class="gdfinal">${t("live.proj", {pts: gdNum(side.projected)})}</p>
  </div>`;
}

/* One bar, both sides: ESPN's own winProbability, and the two sum to 1 so a single fill says
   everything. It is the one element on the page meant to be legible at arm's length. */
function gdSpineHTML(me){
  return `<div class="gdspine">
    <div class="gdspinetrack"><div class="gdspinefill" style="width:${gdPct(me.winPct)}%"></div></div>
  </div>`;
}

function gdTallyHTML(side, which){
  const rest = gdToCome(side);
  const pts = rest.reduce((n, r) => n + (r.projected || 0), 0);
  return `<div class="gdtally ${which}">
    <span class="gdwinpct">${t("live.win", {pct: gdPct(side.winPct)})}</span>
    <span class="gdpair">
      <span class="gdleft">${t("live.left", {n: rest.length})}</span>
      <span class="gddot">${GD_DOT}</span>
      <span class="gdtocome">${t("live.tocome", {pts: gdNum(Math.round(pts * 10) / 10)})}</span>
    </span>
  </div>`;
}

/* The day's shape. x is real time, so a stretch when the tab was closed draws as one straight
   run rather than pretending points were collected through it -- this is this browser's view of
   the day, not a record of it, and the straight segment is the honest way to say so.
   The box is drawn even when there is nothing in it yet, so the header never changes height
   under someone who is reading it. */
function gdTraceHTML(){
  const pts = GD_WP, w = 100, h = 30;
  let path = "";
  if (pts.length >= 2){
    const t0 = pts[0][0], span = Math.max(1, pts[pts.length - 1][0] - t0);
    path = pts.map(([at, p], i) =>
      `${i ? "L" : "M"}${((at - t0) / span * w).toFixed(2)},${((1 - p) * h).toFixed(2)}`).join("");
  }
  /* The area under the line, not just the line. Without it the trace is a squiggle that could
     mean anything; filled, the height IS the win probability and "more lime is better" needs no
     legend to explain it. The dashed midline is the coin flip. */
  const area = path ? `${path}L${w},${h}L0,${h}Z` : "";
  return `<div class="gdtrace">
    <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
      ${area ? `<path class="gdtracefill" d="${area}"/>` : ""}
      <line class="gdtracemid" x1="0" y1="${h / 2}" x2="${w}" y2="${h / 2}"/>
      ${path ? `<path class="gdtraceline" vector-effect="non-scaling-stroke" d="${path}"/>` : ""}
    </svg>
  </div>`;
}

/* Shown after time away, and only then: a dozen rows each wearing a chip is not news. It stays
   until dismissed rather than fading, because the whole point is that nobody was watching. */
function gdCatchupHTML(){
  if (!GD_CATCHUP) return "";
  const {movers, swing} = GD_CATCHUP;
  /* Mine in lime, his in plain ink -- the same shorthand the rest of the board uses, so which
     number is whose needs no word to say it. */
  const sum = swing
    ? `<span class="gdswing"><b class="mine">${esc(gdSign(swing.me))}</b>
        <span class="gddot">${GD_DOT}</span>${esc(gdSign(swing.opp))}</span>`
    : "";
  const who = movers.map(m =>
    `<span class="gdmover">${esc(gdShort(m.name))}
      <b class="${m.delta < 0 ? "down" : "up"}">${esc(gdSign(m.delta))}</b></span>`).join("");
  return `<div class="gdcatch">
    <span class="gdcatchtitle">${t("live.away.title")}</span>
    ${sum}${who}
    <button class="gdlink" data-gdseen>${t("live.seen")}</button>
  </div>`;
}

const gdClock = ms => new Date(ms).toLocaleTimeString([], {hour: "numeric", minute: "2-digit"});

/* While nothing is being played the board says so, and says when that changes. Otherwise a
   board that has not moved in an hour looks broken rather than correct. */
function gdRestHTML(now){
  if (gdPlaying(now)) return "";
  const next = gdNextKick(now);
  const word = next === undefined ? t("live.idle") : t("live.next", {when: gdClock(next)});
  return `<span class="gdrest">${esc(word)}</span>`;
}

function gdHeadHTML(d){
  return gdCatchupHTML()
    + `<header class="gdhead">
      ${gdSideHTML(d.me, "mine")}
      <div class="gdvs"><span class="gdweek">${t("live.week", {week: d.week})}</span></div>
      ${gdSideHTML(d.opponent, "theirs")}
    </header>
    ${gdSpineHTML(d.me)}
    <div class="gdtallies">${gdTallyHTML(d.me, "mine")}${gdTallyHTML(d.opponent, "theirs")}</div>
    ${gdTraceHTML()}
    <p class="gdasof">${t("live.asof", {time: esc(gdClock(Date.parse(d.asof)))})}
      ${gdRestHTML(Date.now())}
      <button class="gdlink" data-gdrefresh>${t("live.refresh")}</button></p>`;
}
