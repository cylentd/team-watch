/* The player profile ff-jarvis writes (LIVE_PROFILES), looked up by slug, and the matchup rank the
   roster row and the profile both show. next.factor.rank is 1 = the toughest defence for his
   position, so "Nth easiest" is of - rank + 1. Colour only at the extremes: the easiest 8 read
   up, the hardest 8 read down, the middle 16 stay plain. */
function profileFor(p){
  if (typeof LIVE_PROFILES === "undefined" || !LIVE_PROFILES || !p) return null;
  return LIVE_PROFILES.players[p.slug || slugOf(p.n)] || null;
}

function ordinal(n){
  const tens = n % 100, ones = n % 10;
  if (tens >= 11 && tens <= 13) return t("common.ordinal.th", {n});
  if (ones === 1) return t("common.ordinal.st", {n});
  if (ones === 2) return t("common.ordinal.nd", {n});
  if (ones === 3) return t("common.ordinal.rd", {n});
  return t("common.ordinal.th", {n});
}

/* 1 = easiest of `of`; null when there is no factor to rank. */
function easiestRank(f){
  return f && f.rank && f.of ? f.of - f.rank + 1 : null;
}

function matchupClass(n, of){
  if (n === null || n === undefined) return "";
  return n <= 8 ? "mu-easy" : n >= of - 7 ? "mu-hard" : "";
}

function whereWord(nx){
  return nx.home ? t("profile.next.home") : t("profile.next.away");
}

/* "9th easiest of 32 for WRs" in the easier half, "13th toughest of 32" past the midpoint --
   "20th easiest" read as easy at a glance when the strip put him on the tough side. The caller
   checks easiestRank first. */
function matchupRankText(prof){
  const f = prof.next.factor, n = easiestRank(f);
  return n <= f.of / 2
    ? t("profile.matchup.rank", {nth: ordinal(n), of: f.of, pos: esc(prof.pos)})
    : t("profile.matchup.rankTough", {nth: ordinal(f.of - n + 1), of: f.of, pos: esc(prof.pos)});
}

/* The same rank as a clause on the row's meta line, shown only at phone width (430.css) where the
   column would crowd the trend line. No rank: no clause at all. */
function matchupMetaHTML(prof){
  const nx = prof && prof.next;
  const n = nx ? easiestRank(nx.factor) : null;
  if (n === null) return "";
  return `<span class="mu-meta"><span class="mu-dot">·</span>${whereWord(nx)} ${esc(nx.opp)} <b class="mu-n ${matchupClass(n, nx.factor.of)}">${ordinal(n)}</b></span>`;
}

/* The roster row's MATCHUP cell: "@ KC  20th", or a muted dash on a bye or with no rank. */
function matchupCellHTML(prof){
  const nx = prof && prof.next;
  const n = nx ? easiestRank(nx.factor) : null;
  if (n === null) return `<span class="mu-none">—</span>`;
  return `<span class="mu-opp">${whereWord(nx)} ${esc(nx.opp)}</span>`
    + `<b class="mu-n ${matchupClass(n, nx.factor.of)}" title="${matchupRankText(prof)}">${ordinal(n)}</b>`;
}
