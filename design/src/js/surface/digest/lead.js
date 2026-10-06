/* ============================== DIGEST: THE LEAD ==============================
   One fact leads the week: a headline, one fact line, a photo. ff-jarvis picks it by rule (the
   packet's `lead`: a hurt starter first, then a game in bad weather, then the top headline); this
   file only writes it. No stats row and no "leads because" line (David, 2026-09-26): the fact is the
   lead, and the rows under it carry the numbers. The week's results left the banner on 2026-10-05
   (Recap has them); a packet whose `lead` is still "results" falls to the top headline (data/digest.js). */

const DG_STATUS = {
  Out: ["out", () => t("digest.status.out")], IR: ["out", () => t("digest.status.ir")],
  Doubtful: ["out", () => t("digest.status.doubtful")], Questionable: ["q", () => t("digest.status.questionable")],
};

/* The big photo: the 256px head where ff-jarvis cut one, faded into the panel at its foot. */
function dgPhotoHTML(slugs){
  const lg = typeof HEADS_LG !== "undefined" && HEADS_LG ? HEADS_LG : {};
  const slug = [].concat(slugs || []).find(s => lg[s] || HEADS[s]);
  if (!slug) return "";
  const set = headSrcset(slug);
  return `<img class="dg-photo" src="${lg[slug] || HEADS[slug]}"${set ? ` srcset="${set}" sizes="(min-width:1100px) 460px, (min-width:960px) 260px, 168px"` : ""}
    alt="" decoding="async" onerror="this.remove()">`;
}

/* Rule 1: "Puka Nacua is doubtful" / "The WR2 this week. Hip. LA @ DEN, Sun 5:20 PM." A player
   with no rank led on how widely he is rostered, so that number takes the rank's place. */
function dgLeadHurt(r){
  const [cls, word] = DG_STATUS[r.status] || ["q", () => esc(r.status)];
  const who = r.rank != null ? t("digest.lead.rank", {pos: esc(r.pos), rank: r.rank})
    : r.rostered != null ? t("digest.lead.rostered", {pct: dgPct(r.rostered)}) : "";
  const game = r.game ? t("digest.lead.game", {game: dgGame(r.game) + (dgKick(r.game) ? ", " + esc(dgKick(r.game)) : "")}) : "";
  return {tone: cls, slug: r.slug, name: r.n, photo: dgPhotoHTML(r.slug), ghost: r.rank != null ? esc(r.pos) + r.rank : "",
          head: t("digest.lead.hurt", {name: esc(r.n), status: `<em class="dg-em ${cls}">${word()}</em>`}),
          fact: [who, r.injury ? esc(r.injury) + "." : "", game].filter(Boolean).join(" ")};
}

/* Rule 2: "SEA @ WAS in 22 mph wind" / "Sun 10:00 AM. 73°F, mostly sunny." */
function dgLeadWx(g){
  const what = dgWxKind(g) === "wind" ? t("digest.lead.wx.wind", {mph: g.wind_mph}) : t("digest.lead.wx.rain", {pct: g.precip_pct});
  const sky = [g.temp_f != null ? t("digest.lead.wx.temp", {f: g.temp_f}) : "", g.short ? esc(g.short) : ""].filter(Boolean).join(", ");
  return {tone: "sky", photo: `<span class="dg-photo dg-glyph">${dgWxKind(g) === "wind" ? DG_WIND : DG_RAIN}</span>`,
          ghost: dgWxKind(g) === "wind" ? t("digest.wx.mph", {n: g.wind_mph}) : t("digest.wx.pct", {n: g.precip_pct}),
          head: t("digest.lead.wx.head", {game: dgGame(g), what: `<em class="dg-em sky">${what}</em>`}),
          fact: [dgKick(g) ? esc(dgKick(g)) + "." : "", sky ? sky + "." : ""].filter(Boolean).join(" ")};
}

/* The week's top score, called like a game (David, 2026-09-29, storyboard
   https://claude.ai/artifact/BvceuqtTkqyvzgjiHPGK7g): "Gibbs rumbles for 164 yards and 3 TDs", his
   box line as pills. It was the banner's rule 3 once half the week was final, until 2026-10-05; it is
   now Recap's banner, which calls dgCall and dgBoxPills (the Digest's live banner is dgTopCall, below).
   The headline celebrates: no projection, no luck, nothing the lists under it already say. */
const dgSurname = n => n.replace(/\s+(Jr\.?|Sr\.?|II|III|IV|V)$/i, "").split(" ").slice(1).join(" ") || n;

/* The announcer's call, picked by what his day was made of, never invented: a passer (10+ throws),
   a runner (more rushing than receiving yards), a catcher, or a day of short scores (3+ TDs on under
   80 yards). Each kind has four phrasings (David, 2026-09-29: "a couple of words or phrases"); which
   one is fixed by his name and the week, so a reload never reshuffles it and next week reads fresh.
   The touchdowns ride at the end in lime. Without a box line (play-by-play not out yet) it says the
   score. */
const dgPick = (list, seed) => list[[...seed].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7) % list.length];
function dgCall(r, week){
  const b = r.line, name = esc(dgSurname(r.n));
  if (!b) return t("digest.call.scores", {name, pts: `<em class="dg-em go">${r.actual.toFixed(1)}</em>`});
  const yds = b.rush_yd + b.rec_yd, pass = b.att >= 10, tds = b.td + (pass ? b.pass_td || 0 : 0);
  const td = `<em class="dg-em go">${tds === 1 ? t("digest.call.td1") : t("digest.call.tds", {n: tds})}</em>`;
  const seed = `${r.n}|${week || ""}`;
  if (!pass && b.td >= 3 && yds < 80) return dgPick([
    t("digest.call.punches", {name, td}), t("digest.call.plunges", {name, td}),
    t("digest.call.cashes", {name, td}), t("digest.call.goalLine", {name, td})], seed);
  const v = {name, yds: pass ? b.pass_yd : yds, rec: b.rec};
  const call = dgPick(pass ? [t("digest.call.slings", v), t("digest.call.airs", v), t("digest.call.carves", v), t("digest.call.lights", v)]
    : b.car && b.rush_yd >= b.rec_yd ? [t("digest.call.rumbles", v), t("digest.call.runsWild", v), t("digest.call.bulldozes", v), t("digest.call.churns", v)]
    : [t("digest.call.hauls", v), t("digest.call.reels", v), t("digest.call.torches", v), t("digest.call.racks", v)], seed);
  return tds ? t("digest.call.and", {call, td}) : call;
}

/* The top scorer's call, scaled by the size of his day (2026-10-04, David on "McMillan leads the week with
   38.2 points": "38.2 is insane number in fantasy... use more excited wording. This is the headline
   afterall. Should be like NFL announcer to build the hype."). Only what the page has: his points, his
   stat line (GD_STATS.lead `s`), whether his game is on, and the gap to the week's second score.
   Big: 30+ points, 3+ touchdowns, 150+ yards (300+ passing); with a 10-point gap to the second score
   he "laps the field". Solid: 20+ points. Under that, the plain count. Each tier has two phrasings in
   the present (his game is on) and the past (it is not), picked by his slug so a poll never reshuffles
   them. Superseded in part 2026-10-05 (David: the headline "should use yards and TDs", every league
   scores differently): the tier is still chosen by his points, but the points never print; the head
   carries his real line (dgTopLine), yards and TDs first, catches only for a receiver with 10+. */
const DG_BIG = {pts: 30, tds: 3, yds: 150, passYds: 300, lap: 10, solid: 20, catches: 10};

/* "14 catches, 192 yards, 2 TDs": a passer's yards are his passing yards, anyone else's his rushing
   plus receiving; a passer's TDs are his passing and rushing ones, anyone else's rushing and
   receiving (a passing TD is the same score as the catch, counted once). Empty when there is
   nothing to count (a kicker, a defense): the caller says it without a number. */
function dgTopLine(s){
  const n = k => +(s[k] || 0), pass = n("pass_yd") > n("rush_yd") + n("rec_yd");
  const yds = pass ? n("pass_yd") : n("rush_yd") + n("rec_yd");
  const tds = n("rush_td") + (pass ? n("pass_td") : n("rec_td"));
  return [!pass && n("rec") >= DG_BIG.catches ? t("digest.live.line.catches", {n: n("rec")}) : "",
    yds > 0 ? t("digest.live.line.yds", {n: Math.round(yds)}) : "",
    tds ? (tds === 1 ? t("digest.live.line.td1") : t("digest.live.line.tds", {n: tds})) : ""].filter(Boolean).join(", ");
}

function dgTopCall(top, on, name){
  const s = top.s || {}, n = k => +(s[k] || 0), seed = slugOf(top.n);
  const second = dgLeaders()[1], gap = second ? top.pts - second.pts : 0;
  const big = top.pts >= DG_BIG.pts || n("rush_td") + n("rec_td") + n("pass_td") >= DG_BIG.tds
    || n("rush_yd") + n("rec_yd") >= DG_BIG.yds || n("pass_yd") >= DG_BIG.passYds;
  const text = dgTopLine(s), line = text && `<em class="dg-em go">${text}</em>`, v = {name, line};
  if (!line) return on ? t("digest.live.bare.on", {name}) : t("digest.live.bare.fin", {name});
  if (big && gap >= DG_BIG.lap) return on ? t("digest.live.lap.on", v) : t("digest.live.lap.fin", v);
  if (big) return dgPick(on ? [t("digest.live.big1.on", v), t("digest.live.big2.on", v)]
                            : [t("digest.live.big1.fin", v), t("digest.live.big2.fin", v)], seed);
  if (top.pts >= DG_BIG.solid) return dgPick(on ? [t("digest.live.solid1.on", v), t("digest.live.solid2.on", v)]
                                                : [t("digest.live.solid1.fin", v), t("digest.live.solid2.fin", v)], seed);
  return t("digest.live.plain", v);
}

/* His box line, once each: passing, rushing and receiving where he had any. No fantasy points
   (David, 2026-10-05: a headline shows yards and TDs, never points, since every league scores differently). */
function dgBoxPills(r){
  const b = r.line || {}, pill = s => `<span class="dg-lpill">${s}</span>`;
  return [b.att >= 10 ? pill(t("digest.call.passLine", {c: b.cmp, a: b.att, y: b.pass_yd})) : "",
    b.car ? pill(t("digest.call.rushLine", {n: b.car, y: b.rush_yd})) : "",
    b.rec ? pill(t("digest.call.recLine", {n: b.rec, y: b.rec_yd})) : ""].join("");
}

/* Rule 3: the headline itself, a size down because it is a sentence, not a name. */
function dgLeadNews(it){
  return {tone: it.kind === "out" ? "out" : it.kind === "injury" ? "q" : "", photo: dgPhotoHTML(it.slugs), long: true, slug: [].concat(it.slugs || [])[0], name: it.n,
          head: esc(it.headline), fact: it.when ? t("digest.lead.news.fact", {when: esc(it.when)}) : t("digest.lead.news.src")};
}

/* Claude's pick between games (2026-10-04, David: "claude should determine what is the best headline
   from Sunday's results, Injuries, etc"): the packet's `story` (design/digest.py), written by ff-jarvis's
   digest_headline step after the packet it follows. It takes the banner only while no game is on and
   only when it is newer than the packet; an older one is a leftover of last week's run. Its words are
   Claude's and number-checked upstream, so they are drawn as they come, escaped. The stamps are Pacific
   wall clock both ("YYYY-MM-DD HH:MM[:SS]"), so a string compare orders them. */
const dgStamp = s => { const x = String(s || "").replace("T", " ").slice(0, 19); return x.length === 16 ? x + ":00" : x; };
const DG_STORY_TONE = {result: "go", injury: "out"};

/* The story, or null when it is not newer than the packet (a leftover of an earlier run). */
const dgStoryFresh = d => {
  const s = d && d.story;
  return s && s.head && s.fact && s.asof && dgStamp(s.asof) > dgStamp(d.asof) ? s : null;
};
const dgRecapBlock = () => (typeof LIVE_RECAP !== "undefined" ? LIVE_RECAP : null);

/* A result story about the Recap's week and top scorer is Recap's banner, not this one (2026-10-05, David:
   "they should never be the same content"; data/leadsplit.js says which). With no game on the Digest
   then leads with the coming week, the packet's own lead. */
function dgLeadStory(d){
  const s = lspDigestStory(dgStoryFresh(d), d.week, dgRecapBlock());
  if (!s) return null;
  const p = s.player, club = (p && p.team) || s.club || "";
  // Sleeper's code (LAR, WSH) is not always the colour table's (LA, WAS): take whichever spelling it has.
  const team = club ? gdCodes(club).find(c => TEAM_COLOURS[c]) || "" : "";
  const photo = p ? dgPhotoHTML(p.slug) : "";
  const base = DG_STORY_TONE[s.kind] || "";
  const tone = team ? `${base} team`.trim() : base || (photo ? "" : "quiet");
  return {tone, team: team || undefined, long: true, photo, ghost: team ? esc(team) : "",
          head: esc(s.head), fact: esc(s.fact),
          ...(p ? {slug: p.slug, name: p.n, live: {n: p.n, pos: p.pos || "", team: p.team || "", slug: p.slug}} : {})};
}

function dgLead(){
  const d = dgD();
  if (!d) return {tone: "quiet", photo: "", head: t("digest.empty.head"), fact: t("digest.empty.sub")};
  // Once games are on, the banner is the day's top score (now.js), or the last game's matchup (mnf.js);
  // else the packet's own lead. Whichever it is, it never names the Recap banner's subject: the first
  // candidate that does not is the banner (data/leadsplit.js).
  const quiet = {tone: "quiet", photo: "", head: t("digest.lead.quiet.head"), fact: t("digest.lead.quiet.sub")};
  return lspPick([dgLeadLive(d), ...dgLeadPacket(d), quiet], lspRecapSubject(dgRecapBlock())) || quiet;
}

/* The packet's lead, then the other headlines behind it, written as banners: the candidates after a lead
   the Recap banner already names. */
function dgLeadPacket(d){
  const l = d.lead, row = l && d.leadRows[l.rule] ? d.leadRows[l.rule][l.index] : null;
  if (!row) return [];
  const first = l.rule === "hurt" ? dgLeadHurt(row) : l.rule === "weather" ? dgLeadWx(row) : dgLeadNews(row);
  return [first, ...d.leadRows.news.filter(r => r !== row).slice(0, 3).map(dgLeadNews)];
}

/* The ghost one character to a box, each knowing its place (--i), so a hover can flip them in turn
   like a scoreboard's split-flap (wall.css). The ghost arrives escaped: an entity stays one box. */
const dgGhostChars = s => (s.match(/&[^;\s]+;|\s|./gu) || [])
  .map((c, i) => c.trim() ? `<i style="--i:${i}">${c}</i>` : c).join("");

function dgLeadHTML(){
  const L = dgLead(), d = dgD();
  /* The ghost is the reason he leads (his rank, the wind), set huge and faint behind the photo on
     a wide screen; aria-hidden, since the fact line already says it. The stamp above the head says
     which week and how old the packet is, so a stale page reads as stale (2026-09-28). */
  const stamp = d && d.asof_words ? `<p class="dg-lead-when" data-testid="digest-lead-when">${t("digest.lead.when", {week: d.week, when: esc(d.asof_words)})}</p>` : "";
  /* A lead about one player opens his profile from anywhere on the band (2026-09-29, David: "should
     we be able to click on players to open their profile?"). A button laid over the band, not the
     band made a button, so the headline stays a heading. */
  const who = L.live ? dgLvAttrs(L.live) : `data-dgslug="${esc(L.slug)}"`;   // a live scorer opens through now.js's one listener
  const go = L.slug ? `<button type="button" class="dg-lead-go" data-testid="digest-lead-go" ${who}
    aria-label="${esc(t("digest.lead.open", {n: L.name || ""}))}"></button>` : "";
  return `<article class="dg-lead ${L.tone}${L.photo ? " has-photo" : ""}${go ? " opens" : ""}" data-testid="digest-lead"${L.team ? " " + teamColourStyle(L.team) : ""}>
    ${go}${L.ghost ? `<span class="dg-ghost" data-testid="digest-ghost" aria-hidden="true">${dgGhostChars(L.ghost)}</span>` : ""}
    <div class="dg-lead-txt">${stamp}<h2 class="dg-lead-h${L.long ? " long" : ""}" data-testid="digest-lead-head">${L.head}</h2>
      <div class="dg-lead-fact" data-testid="digest-lead-fact">${L.fact}</div></div>
    ${L.photo}
  </article>`;
}
