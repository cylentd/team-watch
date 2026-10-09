/* ============================== DIGEST: THE DAY'S BANNER ==============================
   2026-10-06, storyboard "Digest by Day" (option B). The banner's headline is the day's answer, never a
   news line: Tuesday the top add, Wednesday the top usage mover, Thursday night's game in Claude's words,
   Friday the top status change, Saturday the SMASH with the softest matchup, Sunday the first kickoff,
   Monday tonight's game. data/digest.js picks each subject (dgPick*); this file writes it as a lead
   (lead.js draws every lead the same way). A day whose block has nothing returns null and the banner
   falls to the packet's lead. Generic by rule: nothing here reads a league or a roster. */

/* Every label spelled out: assemble.py --check finds a copy key only as a literal lookup. */
const dgDayLabel = key => ({tue: t("digest.day.tue.label"), wed: t("digest.day.wed.label"), thu: t("digest.day.thu.label"),
  fri: t("digest.day.fri.label"), sat: t("digest.day.sat.label"), sun: t("digest.day.sun.label"),
  mon: t("digest.day.mon.label")})[key] || "";

const dgBlock = name => ({
  LIVE_USAGE_MOVERS: typeof LIVE_USAGE_MOVERS !== "undefined" ? LIVE_USAGE_MOVERS : null,
  LIVE_PREVIEW: typeof LIVE_PREVIEW !== "undefined" ? LIVE_PREVIEW : null,
  LIVE_SS3: typeof LIVE_SS3 !== "undefined" ? LIVE_SS3 : null,
  LIVE_DEFENSE: typeof LIVE_DEFENSE !== "undefined" ? LIVE_DEFENSE : null,
  LIVE_SCHEDULE: typeof LIVE_SCHEDULE !== "undefined" ? LIVE_SCHEDULE : null,
  LIVE_RANKS: typeof LIVE_RANKS !== "undefined" ? LIVE_RANKS : null,
})[name] || null;

/* Tuesday: "K. Coleman is the top waiver add" over his number, Sleeper's adds or ESPN's % rostered. */
function dgDayAdds(d){
  const a = dgPickAdd(d);
  if (!a) return null;
  const fact = d.adds_source === "sleeper" && a.count != null ? t("digest.day.tue.factSleeper", {n: dgBig(a.count), h: d.adds_hours})
    : a.was != null && a.now != null ? t("digest.day.tue.factEspn", {was: dgPct(a.was), now: dgPct(a.now)}) : "";
  return {tone: "go", slug: a.slug, name: a.n, head: t("digest.day.tue.head", {name: esc(dgShort(a.n))}), fact};
}

/* Wednesday: the week's biggest role change (LIVE_USAGE_MOVERS, ff-jarvis) as a short head from his own numbers
   ("B. Robinson's snap share hit 78%"); Claude's whole line stays in his row. It is an untested change, so the head
   carries the card's mark. */
function dgDayUsage(){
  const r = dgPickUsage(dgBlock("LIVE_USAGE_MOVERS"));
  if (!r) return dgDayDefense();
  const v = {name: esc(dgShort(r.name)), pct: dgPct(r.now)};
  return {tone: "go", slug: r.slug, name: r.name || "", fact: t("digest.day.wed.fact"), headMark: t("digest.card.usage.mark"),
          head: r.metric === "snap" ? t("digest.day.wed.headSnaps", v) : t("digest.day.wed.headTargets", v)};
}

/* Wednesday with no usage movers: the Softest defenses card's top row, in a line of its own. */
function dgDayDefense(){
  const top = dgPickDefense(dgBlock("LIVE_DEFENSE"));
  return top ? {tone: "", head: t("digest.day.wed.headDef", {team: esc(dgCityName(top.team)), pos: esc(dgDefPosWord(top.pos))}),
                fact: t("digest.day.wed.factDef", {pts: top.pts.toFixed(1), of: top.of}), headMark: t("digest.card.defenses.foot")} : null;
}

/* Thursday: the game's take in Claude's words, its kickoff and Claude's score, the two codes at the side. */
function dgDayTnf(now){
  const g = dgPickTnf(dgBlock("LIVE_PREVIEW"), now);
  if (!g) return null;
  const time = esc(kickTime(g.kickoff)), pick = dgTakePick(g.take);
  return {tone: "", vs: [g.away, g.home], head: esc(g.take.head), factMark: t("preview.call.mark"), take: g.take,
          fact: pick ? t("digest.day.thu.fact", {time, pick: esc(pick)}) : t("digest.day.thu.factTime", {time})};
}

/* Saturday: the SMASH play against the defense that gives his position the most. */
function dgDaySmash(){
  const smash = dgBlock("LIVE_SS3"), p = dgPickSmash(smash, dgBlock("LIVE_DEFENSE"));
  if (!p) return null;
  const r = p.row, v = {name: esc(dgShort(r.name)), pos: esc(r.pos), opp: esc(r.opp || "")};
  const head = p.most === 1 ? t("digest.day.sat.headSoftest", v) : t("digest.day.sat.head", v);
  const fact = p.allow && p.allow.pts_pg != null
    ? t("digest.day.sat.fact", {...v, pts: p.allow.pts_pg.toFixed(1), n: p.most, of: p.of})
    : t("digest.day.sat.factNone", {n: smash.smash.length});
  return {tone: "go", slug: r.slug, name: r.name, head, fact, headMark: t("matchups.takes.markSmash")};
}

const dgSchedGames = () => { const s = dgBlock("LIVE_SCHEDULE"); return (s && s.games) || []; };

/* Claude's call on a scheduled game, from Preview's slate, for the hero's Blip to react to. Only the pick: this
   banner's headline is the kickoff, not the take, so the take's players are not what it is about. */
function dgTakeFor(g){
  const p = dgBlock("LIVE_PREVIEW"), m = ((p && p.games) || []).find(x => x.away === g.away && x.home === g.home);
  return m && m.take ? {pick: m.take.pick} : undefined;
}

/* Sunday: the first kickoff still to come today. */
function dgDayKickoff(now){
  const g = dgPickKickoff(dgSchedGames(), now);
  return g ? {tone: "", vs: [g.away, g.home], take: dgTakeFor(g), head: t("digest.day.sun.head", {time: esc(kickTime(g.kickoff))}),
              fact: t("digest.day.sun.fact", {game: dgGame(g)})} : null;
}

/* Monday: tonight's game. */
function dgDayTonight(now){
  const g = dgPickTonight(dgSchedGames(), now);
  return g ? {tone: "", vs: [g.away, g.home], take: dgTakeFor(g), head: t("digest.day.mon.head", {game: dgGame(g)}),
              fact: t("digest.day.mon.fact", {time: esc(kickTime(g.kickoff))})} : null;
}

/* The day's lead, or null. Friday's is the packet's own hurt line for the hurt player the page projects highest. */
function dgLeadDay(d, plan){
  const now = Date.now(), hurt = dgPickStatus(d, dgBlock("LIVE_RANKS"));
  return ({adds: () => dgDayAdds(d), usage: dgDayUsage, tnf: () => dgDayTnf(now), status: () => hurt && dgLeadHurt(hurt),
           smash: dgDaySmash, kickoff: () => dgDayKickoff(now), tonight: () => dgDayTonight(now)}[plan.banner] || (() => null))();
}
