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

/* "RB9" -- the head line, where the position is the point.

   No tie marker, from 2026-09-22. rankAmong already handles a tie the honest way: two players
   level are both 9th and the next is 11th. An asterisk on top of that only said "someone else
   has this number too", which changes no decision a reader of this page is making, and six of
   them ringing the radar at the size the rank is set read as damage on the glyphs. */
function rankText(pos, rk){
  return t("profile.rank.plain", {pos: esc(pos), n: rk[0]});
}

/* "#9" -- the radar, where six of them have to fit. */
function rankMark(rk){
  return t("profile.rank.mark", {n: rk[0]});
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

/* "WR · DET · WR28 · BYE 9" under the name: what he is, who he plays for, his fantasy rank at
   his position the way a fantasy reader says it, and the one week he cannot be started. Any
   clause with no source drops out rather than dashing.

   The bye is here rather than on a line of its own because it is the only static fact about him
   that changes a decision -- everything else the head used to carry (age, size, years) is
   reference, and reference belongs in the Bio block, not in chrome that is paid for on every
   screen of a phone scroll.

   One separator for the whole page: " · ". Never a mixture, and never a vertical bar as a second
   kind of divider -- there is no second meaning for it to carry, and the page already spells
   this separator 26 times in copy and 13 more in joins like this one. The line groups itself by
   weight instead: the rank is the bright thing, the bye the quiet one. */
function identityHTML(p, prof){
  const pos = prof ? prof.pos : p.pos;
  const rk = ppgRank({slug: p.slug, pos});
  const b = pedigreeFor(p);
  return [esc(pos), esc(prof ? prof.team : p.team),
    rk ? `<b class="pf-id-rank">${rankText(pos, rk)}</b>` : "",
    b && pedHas(b.bye) ? `<span class="pf-id-bye">${t("profile.bio.bye", {n: b.bye})}</span>` : "",
  ].filter(Boolean).join(" · ");
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
    .map(k => [esc(TEAMS[k].name), leaguePickText(fd[k], TEAMS[k].name)])
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

const pedHas = v => v !== null && v !== undefined && v !== "";

/* Everything about the man rather than the week: how old, how big, how long he has been doing
   this, and where the NFL and each of my leagues took him. Its own pane since 2026-09-22 (the
   Bio tab), because none of it decides anything this Sunday -- it qualifies the numbers in the
   other three. No heading of its own: the tab is the heading.

   It was an unheaded grid under the chart before that, which is where the eye had already
   stopped, with his age beside a dynasty pick from three years ago as though the two were the
   same kind of fact. The one fact in it that does decide something, the bye, is on the identity
   line under his name instead.

   Measurables take the two-column half of the grid, draft rows the full width: "Rd 1.12 · 2023"
   and a league name are long, and "Age 27" is not. */
function bioBlockHTML(p){
  const b = pedigreeFor(p);
  if (!b) return "";
  const size = [inchesText(b.height), pedHas(b.weight) ? t("profile.fact.lb", {n: b.weight}) : null]
    .filter(Boolean).join(" · ");
  const nfl = pedHas(b.draft_round) && pedHas(b.draft_slot)
    ? t("profile.fact.nflRound", {r: b.draft_round, s: String(b.draft_slot).padStart(2, "0"), yr: b.entry_year ?? "—"})
    : pedHas(b.draft_number) ? t("profile.fact.nflPick", {n: b.draft_number, yr: b.entry_year ?? "—"}) : null;
  const half = [
    [t("profile.fact.age"), pedHas(b.age) ? b.age : null],
    [t("profile.fact.size"), size || null],
    [t("profile.fact.exp"), pedHas(b.years_exp)
      ? (b.years_exp === 0 ? t("profile.fact.rookie") : t("profile.fact.years", {n: b.years_exp})) : null],
  ].filter(c => c[1] !== null);
  const wide = (nfl ? [[t("profile.fact.nfl"), nfl]] : []).concat(leagueFactRows(b.fantasy_draft || {}));
  if (!half.length && !wide.length) return "";
  const cell = (k, v, cls) => `<div${cls ? ` class="${cls}"` : ""}><dt>${k}</dt><dd>${v}</dd></div>`;
  return `<dl class="pf-facts">${half.map(([k, v]) => cell(k, v)).join("")}${wide.map(([k, v]) => cell(k, v, "wide")).join("")}</dl>`;
}
