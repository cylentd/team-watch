/* ------------------------------------------------------------------
   LIVE BOARD — the rows, pure. Every function here takes the payload /api/live returned and
   gives back a string; nothing fetches, nothing touches the DOM.

   Globals are GD_*, never LIVE_*. The assembler injects the build-time data blocks as
   LIVE_TEAMS, LIVE_NEWS, LIVE_MARKET and friends (order.js.txt, line 2), so a surface that also
   owned LIVE_* names would read as if it were one of them. GD is for gameday.
------------------------------------------------------------------ */

/* ESPN sends no actual stat row at all for a player whose game has not kicked off, which is the
   only game-state signal in the payload. A dot says "nothing yet" where a 0.0 would claim he
   played and scored nothing. */
const GD_DOT = "·";
const GD_HEALTHY = ["ACTIVE", "NORMAL"];

const gdNum = v => (v === null || v === undefined) ? GD_DOT : (Math.round(v * 10) / 10).toFixed(1);
const gdPct = v => Math.round((v || 0) * 100);
/* A movement, always signed. A stat correction that takes points away is stated as readily as a
   touchdown -- it moved, and hiding the direction would be the only dishonest option. */
const gdSign = n => (n > 0 ? "+" : "") + n.toFixed(1);

function gdBadge(row){
  const s = String(row.injury || "").toUpperCase();
  if (!s || GD_HEALTHY.includes(s)) return "";
  return `<span class="gdbadge ${s === "OUT" ? "out" : "q"}">${esc(s[0])}</span>`;
}

/* Two spellings of a name, the same full/abbr swap the nav tabs and topbar pills use: at 430px
   two lineups share the width and "De'Von Achane" truncates to "De'Von …", which names nobody.
   A defence loses its suffix instead of its surname -- the slot column already says D/ST. */
function gdShort(name){
  const s = String(name);
  return /\sD\/ST$/.test(s) ? s.replace(/\sD\/ST$/, "") : nameInitial(s);
}

/* Three states, not two. "9.2" against a name means something different depending on whether
   his game is over, underway, or has not started, and until now the board drew all three the
   same way. `started` comes from the payload; the rest comes from the kickoff we already hold. */
function gdState(row, now){
  if (!row.started) return "waiting";
  const kick = gdKickOf(row.team);
  return (kick !== undefined && now > kick + GD_GAME_MS) ? "final" : "playing";
}

function gdCellHTML(row, side, now){
  if (!row) return `<div class="gdcell ${side} empty"></div>`;
  const name = row.name || t("live.unnamed");
  const moved = GD_PULSE[name];
  /* The delta takes the projection's place rather than sitting beside it. Same grid cell, so
     nothing shifts under the reader when it arrives or leaves -- and for those few seconds the
     projection is the least interesting number on the row. */
  const trailing = moved === undefined
    ? `<span class="gdproj">${gdNum(row.projected)}</span>`
    : `<span class="gddelta ${moved < 0 ? "down" : "up"}">${esc(gdSign(moved))}</span>`;
  /* Tapping a name opens his club's game at the drive he was last on the field for -- the first
     of the drive strip's two ways in. Only when the schedule has an ESPN id for that game; a
     player on a bye, or a game whose history row predates the id, stays a plain row. */
  const game = typeof stGameFor === "function" ? stGameFor(row.team) : null;
  const opens = game
    ? ` role="button" tabindex="0" data-gdopen="${esc(row.team)}" data-gdname="${esc(name)}"`
      + ` aria-label="${esc(t("strip.open.player", {name}))}"`
    : "";
  return `<div class="gdcell ${side} ${gdState(row, now)}${moved === undefined ? "" : " moved"}${game ? " opens" : ""}"${opens}>
    <span class="gdname"><span class="gdnametxt">${esc(name)}</span><span
      class="gdnameshort">${esc(gdShort(name))}</span>${gdBadge(row)}</span>
    <span class="gdclub">${esc(row.team || "")}</span>
    <span class="gdnow">${gdNum(row.actual)}</span>
    ${trailing}
  </div>`;
}

/* Both lineups arrive sorted the same way (starters first, then slot, then name) out of the same
   league's settings, so index pairing puts like slot against like slot. When it somehow does not,
   the row says so rather than quietly implying a QB is lined up against a tight end. */
function gdRowHTML(mine, theirs, now){
  const slot = (mine || theirs || {}).slot || "";
  const other = (theirs || {}).slot || "";
  const label = (mine && theirs && other !== slot) ? `${slot}/${other}` : slot;
  return `<li class="gdrow">
    ${gdCellHTML(mine, "mine", now)}
    <span class="gdslot">${esc(label)}</span>
    ${gdCellHTML(theirs, "theirs", now)}
  </li>`;
}

function gdGroupHTML(mine, theirs, heading, now){
  const n = Math.max(mine.length, theirs.length);
  if (!n) return "";
  const rows = [];
  for (let i = 0; i < n; i++) rows.push(gdRowHTML(mine[i], theirs[i], now));
  return `<h3 class="gdgroup">${heading}</h3><ol class="gdrows">${rows.join("")}</ol>`;
}

/* Only a first-ever visit reaches this: after one reply there is always a board in memory to
   paint. Nine rows because that is this league's starting lineup, and the point is to hold the
   space the numbers are about to land in -- reserving it is the whole job, so nothing jumps
   when they do. It claims nothing; every cell is empty. */
const GD_SKELETON_ROWS = 9;

function gdSkeletonHTML(){
  const rows = [];
  for (let i = 0; i < GD_SKELETON_ROWS; i++){
    rows.push(`<li class="gdrow">
      <div class="gdcell mine skel"></div>
      <span class="gdslot skel"></span>
      <div class="gdcell theirs skel"></div>
    </li>`);
  }
  return `<p class="gdwait">${t("live.loading")}</p>
    <ol class="gdrows">${rows.join("")}</ol>`;
}

/* Bench is sorted by what a player actually scored, biggest first, and says nothing about
   whether he should have started: the payload carries no slot eligibility, so any such claim
   would be a guess dressed as advice. The number is the point. */
function gdBoardHTML(){
  /* A failed poll is a banner over the last good board, never a replacement for it. Games do
     not stop because the connection did, and blanking a scoreboard someone is reading loses
     more than the stale numbers were costing. */
  const banner = GD_ERR ? `<p class="gderr">${esc(GD_ERR)}</p>` : "";
  if (!GD_DATA){
    /* Nothing to fall back to. The retry still has to be here, or an expired cookie leaves the
       page with no way out but a reload. */
    return banner
      ? banner + `<p class="gdasof">${gdRestHTML(Date.now())}
          <button class="gdlink" data-gdrefresh>${t("live.refresh")}</button></p>`
      : gdSkeletonHTML();
  }

  const d = GD_DATA, now = Date.now();
  const start = rows => rows.filter(r => r.starter);
  const bench = rows => rows.filter(r => !r.starter)
    .slice().sort((a, b) => (b.actual || 0) - (a.actual || 0));
  return banner + gdHeadHTML(d)
    + gdGroupHTML(start(d.me.lineup), start(d.opponent.lineup), t("live.starters"), now)
    + gdGroupHTML(bench(d.me.lineup), bench(d.opponent.lineup), t("live.bench"), now);
}
