/* Player tags (2026-10-08, ledger #41): which tags a player has, in what order, and the plain line each says. The data
   is LIVE_PLAYER_TAGS (design/player_tags.py), numbers only, already cut to the tags the page shows (its SHOWN list);
   the words are content.json's `tags.*`, keyed by tag and kind, each spelled out literally so assemble.py --check can
   find it. ui/tags.js draws what this returns.

   ff-jarvis's POTENTIAL is named Sleeper here (David, 2026-10-08). No Fact or Tested word is drawn (David, "show not
   tell"): a tested kind changes the line itself, which then says what the test found. */
const TAG_ORDER = ["RISING", "POTENTIAL", "TRENDING"];
const TAG_CLS = {RISING: "rising", POTENTIAL: "sleeper", TRENDING: "trending"};

/* His entries: the plain slug, else `<slug>-<team>` (ff-jarvis keys two players who share a name that way), in the
   page's team spelling, then in nflverse's (the block's `alias` maps nflverse -> page). Never a merge of two people. */
function tagEntries(block, p){
  if (!block || !p || !p.slug) return [];
  const pl = block.players, team = String(p.team || "");
  if (pl[p.slug]) return pl[p.slug];
  const nfl = Object.keys(block.alias || {}).find(k => block.alias[k] === team);
  for (const code of [team, nfl]) {
    if (code && pl[`${p.slug}-${code.toLowerCase()}`]) return pl[`${p.slug}-${code.toLowerCase()}`];
  }
  return [];
}

/* [{tag, kind, nums}] in TAG_ORDER, POTENTIAL's entries merged into one {tag, kind, signals} in the file's order. */
function tagsFor(block, p){
  const es = tagEntries(block, p), out = [];
  for (const tag of TAG_ORDER) {
    const mine = es.filter(e => e.tag === tag);
    if (!mine.length) continue;
    out.push(tag === "POTENTIAL" ? {tag, kind: mine[0].kind, signals: mine.map(e => e.nums.signal)}
      : {tag, kind: mine[0].kind, nums: mine[0].nums});
  }
  return out;
}

const tagN = v => Number(v).toFixed(1);
const TAG_SIGNAL_LINE = {
  VACATED: () => t("tags.sleeper.vacated"), ROOKIE_RAMP: () => t("tags.sleeper.rookieRamp"),
  ROUTES_FIRST: () => t("tags.sleeper.routesFirst"), EFFICIENT_PARTTIMER: () => t("tags.sleeper.partTimer"),
};

/* The Sleeper lines: each signal's reason; the effect once, right after the signals it belongs to (never VACATED's). */
function tagSleeperLines(block, signals){
  const has = s => block.effect != null && (block.effect_signals || []).includes(s);
  const withEffect = signals.filter(has), rest = signals.filter(s => !has(s));
  const line = s => TAG_SIGNAL_LINE[s] ? TAG_SIGNAL_LINE[s]() : "";
  return [...withEffect.map(line), ...(withEffect.length ? [t("tags.sleeper.effect", {pts: block.effect.toFixed(2)})] : []),
    ...rest.map(line)].filter(Boolean);
}

/* One tag as the page says it: {tag, cls, label, lines, tip}. Only Rising has tested words; a tested kind on another tag
   reads as its plain fact, so the page claims nothing it cannot source. */
function tagView(block, x){
  const n = x.nums || {};
  let label, lines;
  if (x.tag === "RISING") {
    label = t("tags.label.rising");
    const v = {n: block.last_n, last: tagN(n.last), earlier: tagN(n.earlier)};
    lines = [x.kind === "tested" ? t("tags.rising.tested", v) : t("tags.rising.fact", v)];
  } else if (x.tag === "TRENDING") {
    label = t("tags.label.trending");
    lines = [t("tags.trending.fact", {rank: n.rank, hours: block.hours, adds: Number(n.adds).toLocaleString("en-US")})];
  } else {
    label = t("tags.label.sleeper");
    lines = tagSleeperLines(block, x.signals || []);
  }
  return {tag: x.tag, cls: TAG_CLS[x.tag], label, lines, tip: lines.join(" ")};
}

const tagViews = (block, p) => tagsFor(block, p).map(x => tagView(block, x));
/* The row's one pill: the first tag in TAG_ORDER, or null. */
function tagRowView(block, p){
  const all = tagsFor(block, p);
  return all.length ? tagView(block, all[0]) : null;
}
/* Watch's verdict word gives way in the profile head when a tag of the same name fires (only RISING overlaps). */
const tagCovers = (block, p, verdict) => tagsFor(block, p).some(x => x.tag === verdict);
