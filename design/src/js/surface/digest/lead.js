/* ============================== DIGEST: THE LEAD ==============================
   One fact leads the week: a headline, one fact line, a photo. ff-jarvis picks it by rule (the
   packet's `lead`: a hurt starter first, then a game in bad weather, then the week's results once
   half of it is final, then the top headline); this file only writes it. No stats row and no "leads because" line (David, 2026-09-26): the fact is
   the lead, and the rows under it carry the numbers. */

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
  const game = r.game ? t("digest.lead.game", {game: dgGame(r.game) + (r.game.kick ? ", " + esc(r.game.kick) : "")}) : "";
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
          fact: [g.kick ? esc(g.kick) + "." : "", sky ? sky + "." : ""].filter(Boolean).join(" ")};
}

/* Rule 3 (2026-09-28): once half the week is final, the week's top score among the recap's
   standouts, called like a game (David, 2026-09-29, storyboard
   https://claude.ai/artifact/BvceuqtTkqyvzgjiHPGK7g): "Gibbs rumbles for 164 yards and 3 TDs", his
   box line as pills, the banner washed in his team's colour with its code huge behind him. The
   headline celebrates: no projection, no luck, nothing the Results list under it already says. */
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

/* His box line, once each: the points, then passing, rushing and receiving where he had any. */
function dgBoxPills(r){
  const b = r.line || {}, pill = s => `<span class="dg-lpill">${s}</span>`;
  return [pill(t("digest.call.pts", {n: r.actual.toFixed(1)})),
    b.att >= 10 ? pill(t("digest.call.passLine", {c: b.cmp, a: b.att, y: b.pass_yd})) : "",
    b.car ? pill(t("digest.call.rushLine", {n: b.car, y: b.rush_yd})) : "",
    b.rec ? pill(t("digest.call.recLine", {n: b.rec, y: b.rec_yd})) : ""].join("");
}

function dgLeadRes(d){
  const r = [...d.stars].sort((a, b) => b.actual - a.actual)[0];
  if (!r) return {tone: "go", photo: "", head: t("digest.lead.res.none", {week: d.week}), fact: ""};
  return {tone: "go team", team: r.team, slug: r.slug, name: r.n, photo: dgPhotoHTML(r.slug), ghost: esc(r.team),
          head: dgCall(r, d.week), fact: `<span class="dg-lead-pills">${dgBoxPills(r)}</span>`};
}

/* Rule 4: the headline itself, a size down because it is a sentence, not a name. */
function dgLeadNews(it){
  return {tone: it.kind === "out" ? "out" : it.kind === "injury" ? "q" : "", photo: dgPhotoHTML(it.slugs), long: true, slug: [].concat(it.slugs || [])[0], name: it.n,
          head: esc(it.headline), fact: it.when ? t("digest.lead.news.fact", {when: esc(it.when)}) : t("digest.lead.news.src")};
}

function dgLead(){
  const d = dgD();
  if (!d) return {tone: "quiet", photo: "", head: t("digest.empty.head"), fact: t("digest.empty.sub")};
  const l = d.lead;
  if (l && l.rule === "results") return dgLeadRes(d);
  const row = l && d.leadRows[l.rule] ? d.leadRows[l.rule][l.index] : null;
  if (!row) return {tone: "quiet", photo: "", head: t("digest.lead.quiet.head"), fact: t("digest.lead.quiet.sub")};
  return l.rule === "hurt" ? dgLeadHurt(row) : l.rule === "weather" ? dgLeadWx(row) : dgLeadNews(row);
}

function dgLeadHTML(){
  const L = dgLead(), d = dgD();
  /* The ghost is the reason he leads (his rank, the wind), set huge and faint behind the photo on
     a wide screen; aria-hidden, since the fact line already says it. The stamp above the head says
     which week and how old the packet is, so a stale page reads as stale (2026-09-28). */
  const stamp = d && d.asof_words ? `<p class="dg-lead-when">${t("digest.lead.when", {week: d.week, when: esc(d.asof_words)})}</p>` : "";
  /* A lead about one player opens his profile from anywhere on the band (2026-09-29, David: "should
     we be able to click on players to open their profile?"). A button laid over the band, not the
     band made a button, so the headline stays a heading. */
  const go = L.slug ? `<button type="button" class="dg-lead-go" data-dgslug="${esc(L.slug)}"
    aria-label="${esc(t("digest.lead.open", {n: L.name || ""}))}"></button>` : "";
  return `<article class="dg-lead ${L.tone}${L.photo ? " has-photo" : ""}${go ? " opens" : ""}"${L.team ? " " + teamColourStyle(L.team) : ""}>
    ${go}${L.ghost ? `<span class="dg-ghost" aria-hidden="true">${L.ghost}</span>` : ""}
    <div class="dg-lead-txt">${stamp}<h2 class="dg-lead-h${L.long ? " long" : ""}">${L.head}</h2>
      <div class="dg-lead-fact">${L.fact}</div></div>
    ${L.photo}
  </article>`;
}
