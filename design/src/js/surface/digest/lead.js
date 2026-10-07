/* ============================== DIGEST: THE LEAD ==============================
   The banner: the day's label, a headline, one fact line, a 96px face or the game's two team codes, in
   one 128px band on a phone (2026-10-06, Digest by day; it was a 236px panel). Its subject, in order: a
   game in play (now.js: who left hurt, else the top scorer), Claude's story or the top scorer between
   windows (now.js), the day's answer (day.js), then the packet's lead (a hurt starter, a game in bad
   weather, the top headline). No stats row and no "leads because" line (David, 2026-09-26). The week's
   results left the banner on 2026-10-05 (Recap has them); a packet whose `lead` is still "results" falls
   to the top headline (data/digest.js). */

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
          head: t("digest.lead.hurt", {name: esc(dgShort(r.n)), status: `<em class="dg-em ${cls}">${word()}</em>`}),
          fact: [who, r.injury ? esc(r.injury) + "." : "", game].filter(Boolean).join(" ")};
}

/* Rule 2: "SEA @ WAS in 22 mph wind" / "Sun 10:00 AM. 73°F, mostly sunny." */
function dgLeadWx(g){
  const what = dgWxKind(g) === "wind" ? t("digest.lead.wx.wind", {mph: g.wind_mph}) : t("digest.lead.wx.rain", {pct: g.precip_pct});
  const sky = [g.temp_f != null ? t("digest.lead.wx.temp", {f: g.temp_f}) : "", g.short ? esc(g.short) : ""].filter(Boolean).join(", ");
  return {tone: "sky", glyph: dgWxKind(g) === "wind" ? DG_WIND : DG_RAIN,
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

function dgLead(plan){
  const d = dgD();
  if (!d) return {tone: "quiet", photo: "", head: t("digest.empty.head"), fact: t("digest.empty.sub")};
  // Once games are on, the banner is the day's top score (now.js); else the day's answer (day.js), else the
  // packet's own lead. Whichever it is, it never names the Recap banner's subject: the first candidate
  // that does not is the banner (data/leadsplit.js).
  const quiet = {tone: "quiet", photo: "", head: t("digest.lead.quiet.head"), fact: t("digest.lead.quiet.sub")};
  return lspPick([dgLeadLive(d), dgLeadDay(d, plan), ...dgLeadPacket(d), quiet], lspRecapSubject(dgRecapBlock())) || quiet;
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

/* The band's right edge: Weather's mark, the game's two codes ("TB at DAL"), or his 96px face
   (heads/<slug>.webp); nothing when he has no head file, never a broken image. */
function dgBnSide(L){
  if (L.glyph) return `<span class="dg-bn-glyph" aria-hidden="true">${L.glyph}</span>`;
  if (L.vs) return `<span class="dg-bn-vs" data-testid="digest-lead-vs"><b>${esc(L.vs[0])}</b><small>${t("digest.day.at")}</small><b>${esc(L.vs[1])}</b></span>`;
  const src = L.slug && typeof HEADS !== "undefined" ? HEADS[L.slug] : "";
  return src ? `<img class="dg-bn-face" data-testid="digest-lead-face" src="${src}" alt="" decoding="async" onerror="this.remove()">` : "";
}

function dgLeadHTML(){
  const plan = dgDayPlan(Date.now()), L = dgLead(plan);
  /* A lead about one player opens his profile from anywhere on the band (2026-09-29, David: "should
     we be able to click on players to open their profile?"). A button laid over the band, not the
     band made a button, so the headline stays a heading. */
  const who = L.live ? dgLvAttrs(L.live) : `data-dgslug="${esc(L.slug)}"`;   // a live scorer opens through now.js's one listener
  const go = L.slug ? `<button type="button" class="dg-lead-go" data-testid="digest-lead-go" ${who}
    aria-label="${esc(t("digest.lead.open", {n: L.name || ""}))}"></button>` : "";
  const side = dgBnSide(L);
  // An untested call (Saturday's SMASH, Thursday's pick) says so on hover, as every flag does (tests/test_flag_marks.py).
  const mark = s => s ? ` title="${esc(s)}"` : "";
  return `<article class="dg-bn ${L.tone}${side ? " has-side" : ""}${go ? " opens" : ""}" data-testid="digest-lead" data-dgday="${plan.key}"${L.team ? " " + teamColourStyle(L.team) : ""}>
    ${go}<div class="dg-bn-txt"><p class="dg-bn-day" data-testid="digest-day">${dgDayLabel(plan.key)}</p>
      <h2 class="dg-bn-h" data-testid="digest-lead-head"${mark(L.headMark)}>${L.head}</h2>
      <div class="dg-bn-fact" data-testid="digest-lead-fact"${mark(L.factMark)}>${L.fact}</div></div>
    ${side}
  </article>`;
}
