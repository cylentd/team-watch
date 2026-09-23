/* Who the player is: the identity line under his name and the facts table in the modal's left
   column (LIVE_PEDIGREE), plus the ranking helpers the whole profile shares. Nothing here reads
   the usage grid. LIVE_POOL and TEAMS are declared after this file but only read inside a
   function body, at click time, when every top-level const in the page has already run. */
function pedigreeFor(p){
  return typeof LIVE_PEDIGREE !== "undefined" && LIVE_PEDIGREE ? LIVE_PEDIGREE.players[p.slug] || null : null;
}

/* Competition ranking over {slug: value}: equal values share the rank above them (two tied for
   first are both 1st, the next is 3rd), never split by sort order. [rank, of, tied], or null
   when `slug` has no value. */
function rankAmong(by, slug){
  if (!(slug in by)) return null;
  const mine = by[slug];
  let above = 0, same = 0;
  for (const v of Object.values(by)){ if (v > mine) above += 1; else if (v === mine) same += 1; }
  return [above + 1, Object.keys(by).length, same > 1];
}

/* "RB9", or "RB9*" when he shares it -- the head line, where the position is the point.
   Two literal t() calls, for assemble.py --check. */
function rankText(pos, rk){
  return rk[2] ? t("profile.rank.tie", {pos: esc(pos), n: rk[0]}) : t("profile.rank.plain", {pos: esc(pos), n: rk[0]});
}

/* "#9", or "#9*" on a tie -- the radar, where six of them have to fit. */
function rankMark(rk){
  return rk[2] ? t("profile.rank.markTie", {n: rk[0]}) : t("profile.rank.mark", {n: rk[0]});
}

/* "#9 of 120" -- the card, which has room for the denominator and needs it: each axis has its
   own, since a receiver ranks among everyone with a target but only among those with routes. */
function rankMarkOf(rk){
  return rk[2] ? t("profile.rank.markOfTie", {n: rk[0], of: rk[1]}) : t("profile.rank.markOf", {n: rk[0], of: rk[1]});
}

/* Small-type names lose the first name to an initial: "X. Worthy" (lib/escape.js nameInitial),
   escaped for markup. A red-zone key with five full names has no room for them. */
const shortName = n => esc(nameInitial(n));

/* His fantasy rank at his position by points per game, season to date: LIVE_POOL (every player
   who logged a snap, ff-jarvis's ppg), one {slug: ppg} map per position. */
const PPG_BY = {};
function ppgRank(p){
  if (typeof LIVE_POOL === "undefined" || !LIVE_POOL || !p.slug) return null;
  const pos = p.pos;
  if (!PPG_BY[pos]){
    PPG_BY[pos] = {};
    LIVE_POOL.players.filter(r => r.pos === pos && r.ppg !== null && r.ppg !== undefined)
      .forEach(r => { PPG_BY[pos][r.slug] = r.ppg; });
  }
  return rankAmong(PPG_BY[pos], p.slug);
}

/* "WR · DET · WR28" under the name: his fantasy rank at his position, the way a fantasy reader
   already says it. No rank, no clause. */
function identityHTML(p, prof){
  const pos = prof ? prof.pos : p.pos;
  const rk = ppgRank({slug: p.slug, pos});
  return [esc(pos), esc(prof ? prof.team : p.team), rk ? rankText(pos, rk) : ""].filter(Boolean).join(" · ");
}

/* "Rd 2.02", plus "· by X" when someone other than my team in that league took him. Round and
   pick are both 1-based, so a 0 in either reads as unset. */
function leaguePickText(fd, mine){
  if (!fd || !fd.round || !fd.pick) return null;
  const pick = `${fd.round}.${String(fd.pick).padStart(2, "0")}`;
  return fd.drafted_by && fd.drafted_by !== mine ? t("profile.fact.leaguePickBy", {pick, by: esc(fd.drafted_by)}) : t("profile.fact.leaguePick", {pick});
}

/* One facts row per league I have a team in (TEAMS), labelled by that team's name, at most
   three: a reader with five leagues gets his first three here, not a wall of picks. */
function leagueFactRows(fd){
  return Object.keys(TEAMS).slice(0, 3)
    .map(k => [esc(TEAMS[k].name), leaguePickText(fd[k], TEAMS[k].name), "wide"])
    .filter(c => c[1] !== null);
}

/* Sleeper stores height as bare inches in a string ("73"). Nobody reads a receiver's height in
   inches, so it goes out as feet and inches; anything that is not a plain number passes through
   unchanged, in case a record ever carries the formatted form instead. */
function inchesText(h){
  if (h === null || h === undefined || h === "") return null;
  const n = Number(h);
  return Number.isFinite(n) && n > 12 ? t("profile.fact.height", {ft: Math.floor(n / 12), in: n % 12}) : esc(h);
}

function factsHTML(p){
  const b = pedigreeFor(p);
  if (!b) return "";
  const has = v => v !== null && v !== undefined && v !== "";
  const fd = b.fantasy_draft || {};
  const nfl = has(b.draft_round) && has(b.draft_slot)
    ? t("profile.fact.nflRound", {r: b.draft_round, s: String(b.draft_slot).padStart(2, "0"), yr: b.entry_year ?? "—"})
    : has(b.draft_number) ? t("profile.fact.nflPick", {n: b.draft_number, yr: b.entry_year ?? "—"}) : null;
  const size = [inchesText(b.height), has(b.weight) ? t("profile.fact.lb", {n: b.weight}) : null].filter(Boolean).join(" · ");
  const cells = [
    [t("profile.fact.age"), has(b.age) ? b.age : null],
    [t("profile.fact.size"), size || null],
    [t("profile.fact.exp"), has(b.years_exp) ? (b.years_exp === 0 ? t("profile.fact.rookie") : t("profile.fact.years", {n: b.years_exp})) : null],
    [t("profile.fact.bye"), has(b.bye) ? t("profile.fact.week", {n: b.bye}) : null],
    [t("profile.fact.nfl"), nfl, "wide"],
  ].filter(c => c[1] !== null).concat(leagueFactRows(fd));
  if (!cells.length) return "";
  return `<dl class="pf-facts">${cells.map(([k, v, cls]) => `<div${cls ? ` class="${cls}"` : ""}><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>`;
}
