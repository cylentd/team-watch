/* ------------------------------------------------------------------
   LIVE BOARD — the markup, pure. Every function here takes the payload /api/live returned and
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
  if (/\sD\/ST$/.test(s)) return s.replace(/\sD\/ST$/, "");
  const parts = s.split(/\s+/);
  return parts.length > 1 ? `${parts[0][0]}. ${parts.slice(1).join(" ")}` : s;
}

function gdCellHTML(row, side){
  if (!row) return `<div class="gdcell ${side} empty"></div>`;
  const name = row.name || t("live.unnamed");
  return `<div class="gdcell ${side}${row.started ? " played" : ""}">
    <span class="gdname"><span class="gdnametxt">${esc(name)}</span><span
      class="gdnameshort">${esc(gdShort(name))}</span>${gdBadge(row)}</span>
    <span class="gdclub">${esc(row.team || "")}</span>
    <span class="gdnow">${gdNum(row.actual)}</span>
    <span class="gdproj">${gdNum(row.projected)}</span>
  </div>`;
}

/* Both lineups arrive sorted the same way (starters first, then slot, then name) out of the same
   league's settings, so index pairing puts like slot against like slot. When it somehow does not,
   the row says so rather than quietly implying a QB is lined up against a tight end. */
function gdRowHTML(mine, theirs){
  const slot = (mine || theirs || {}).slot || "";
  const other = (theirs || {}).slot || "";
  const label = (mine && theirs && other !== slot) ? `${slot}/${other}` : slot;
  return `<li class="gdrow">
    ${gdCellHTML(mine, "mine")}
    <span class="gdslot">${esc(label)}</span>
    ${gdCellHTML(theirs, "theirs")}
  </li>`;
}

function gdGroupHTML(mine, theirs, heading){
  const n = Math.max(mine.length, theirs.length);
  if (!n) return "";
  const rows = [];
  for (let i = 0; i < n; i++) rows.push(gdRowHTML(mine[i], theirs[i]));
  return `<h3 class="gdgroup">${heading}</h3><ol class="gdrows">${rows.join("")}</ol>`;
}

function gdSideHTML(side, which){
  return `<div class="gdteam ${which}">
    <p class="gdclubname">${esc(side.team)}</p>
    <p class="gdscore">${gdNum(side.live)}</p>
    <p class="gdfinal">${t("live.proj", {pts: gdNum(side.projected)})}</p>
  </div>`;
}

/* The win bar is ESPN's own number, not ours: the payload carries winProbability per side and
   the two sum to 1, so one filled bar shows both. */
function gdWinHTML(me, opp) {
  const mine = gdPct(me.winPct);
  return `<div class="gdwin">
    <span class="gdwinpct mine">${t("live.win", {pct: mine})}</span>
    <div class="gdwinbar"><div class="gdwinfill" style="width:${mine}%"></div></div>
    <span class="gdwinpct theirs">${t("live.win", {pct: gdPct(opp.winPct)})}</span>
  </div>`;
}

const gdClock = ms => new Date(ms).toLocaleTimeString([], {hour: "numeric", minute: "2-digit"});

/* While nothing is being played the board says so, and says when that changes. Otherwise a
   board that has not moved in an hour looks broken rather than correct. */
function gdRestHTML(now){
  if (gdPlaying(now)) return "";
  const next = gdNextKick(now);
  const word = next === undefined
    ? t("live.idle")
    : t("live.next", {when: gdClock(next)});
  return `<span class="gdrest">${esc(word)}</span>`;
}

function gdHeadHTML(d){
  const now = Date.now();
  return `<header class="gdhead">
      ${gdSideHTML(d.me, "mine")}
      <div class="gdvs"><span class="gdweek">${t("live.week", {week: d.week})}</span></div>
      ${gdSideHTML(d.opponent, "theirs")}
    </header>
    ${gdWinHTML(d.me, d.opponent)}
    <p class="gdasof">${t("live.asof", {time: esc(gdClock(Date.parse(d.asof)))})}
      ${gdRestHTML(now)}
      <button class="gdlink" data-gdrefresh>${t("live.refresh")}</button></p>`;
}

/* Bench is sorted by what a player has actually scored, biggest first, and says nothing about
   whether he should have started -- the payload carries no slot eligibility, so any such claim
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
      : `<p class="gdwait">${t("live.loading")}</p>`;
  }

  const d = GD_DATA;
  const start = rows => rows.filter(r => r.starter);
  const bench = rows => rows.filter(r => !r.starter)
    .slice().sort((a, b) => (b.actual || 0) - (a.actual || 0));
  return banner + gdHeadHTML(d)
    + gdGroupHTML(start(d.me.lineup), start(d.opponent.lineup), t("live.starters"))
    + gdGroupHTML(bench(d.me.lineup), bench(d.opponent.lineup), t("live.bench"));
}
