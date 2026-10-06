/* THE ONE KICKOFF FORMAT (2026-10-05): "Sun 1:00 PM", in the reader's own clock, everywhere a kickoff is
   printed. Before it the page wrote four: "Mon 8:15 PM ET" (Preview, Eastern), "5:15p" (Bets and News,
   Pacific, cut in Python), "Sun 10:00 AM" (Start/Sit and the profile, Pacific) and the browser's
   "Sun, 1:00 PM" (Ranks, Weather, Live). A page read in Denver now says Denver's time, and no zone
   letters: the reader's clock is the only one they need.

   Every function takes the time as it arrives: an ISO string (Z or an offset), the props' zoneless
   "YYYY-MM-DD HH:MM:SS" (UTC, as BettingPros and ff-jarvis write it), or epoch ms. A time it cannot read
   comes back "" so a caller falls back to the label it already has. A test sets KICK_TZ to pin the zone;
   the page leaves it unset. Pure: no document, no copy, nothing to escape. */
const kickZone = () => typeof KICK_TZ === "string" ? KICK_TZ : undefined;
const KICK_FMT = {};

/* ms since the epoch, or NaN. A zoneless stamp is UTC, never the reader's clock. */
function kickMs(x){
  if (typeof x === "number") return x;
  if (typeof x !== "string" || !x) return NaN;
  const s = /^\d{4}-\d\d-\d\d[ T]\d\d:\d\d(:\d\d)?$/.test(x) ? x.replace(" ", "T") + "Z" : x;
  return Date.parse(s);
}

function kickParts(ms, tz){
  const key = tz || "";
  const f = KICK_FMT[key] || (KICK_FMT[key] = new Intl.DateTimeFormat("en-US",
    {timeZone: tz, weekday: "short", hour: "numeric", minute: "2-digit", hour12: true}));
  const p = {};
  f.formatToParts(new Date(ms)).forEach(x => { p[x.type] = x.value; });
  return {day: p.weekday, time: `${p.hour}:${p.minute} ${p.dayPeriod.toUpperCase()}`};
}

/* "Sun 1:00 PM". */
function kickFmt(x, tz){
  const ms = kickMs(x);
  if (isNaN(ms)) return "";
  const p = kickParts(ms, tz || kickZone());
  return `${p.day} ${p.time}`;
}

/* "1:00 PM": for a heading that already names the day. */
function kickTime(x, tz){
  const ms = kickMs(x);
  return isNaN(ms) ? "" : kickParts(ms, tz || kickZone()).time;
}

/* "Sep 14": the date a played week's row carries, in the same clock as its neighbours' kickoffs. */
function kickDate(x, tz){
  const ms = kickMs(x);
  if (isNaN(ms)) return "";
  const zone = tz || kickZone(), key = "day:" + (zone || "");
  const f = KICK_FMT[key] || (KICK_FMT[key] = new Intl.DateTimeFormat("en-US", {timeZone: zone, month: "short", day: "numeric"}));
  return f.format(new Date(ms));
}

/* "13:25" -> "1:25 PM": a clock that is not the reader's (a team's body clock), in the same words. */
function kickClock(hm){
  const [h, m] = String(hm).split(":").map(Number);
  return `${h % 12 || 12}:${String(m).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`;
}

/* Has it kicked off by `now` (ms)? A row with no kickoff is not called played. */
function kickPast(x, now){
  const ms = kickMs(x);
  return !isNaN(ms) && ms <= now;
}

/* Rewrites each row's `kick` label from its own ISO time (`key`); a row without one keeps the label it
   came with. The Bets rows arrive with Pacific labels cut in Python (design/slate.py): this puts them in
   the reader's clock without a Python change per consumer. */
function kickLabel(rows, key, tz){
  rows.forEach(r => { r.kick = kickFmt(r[key], tz) || r.kick; });
}
