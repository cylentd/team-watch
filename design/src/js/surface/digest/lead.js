/* ============================== DIGEST: THE LEAD ==============================
   One fact leads the week: a headline, one fact line, a photo. ff-jarvis picks it by rule (the
   packet's `lead`: a hurt starter first, then a game in bad weather, then the top headline); this
   file only writes it. No stats row and no "leads because" line (David, 2026-09-26): the fact is
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
  return `<img class="dg-photo" src="${lg[slug] || HEADS[slug]}"${set ? ` srcset="${set}" sizes="(min-width:960px) 260px, 168px"` : ""}
    alt="" decoding="async" onerror="this.remove()">`;
}

/* Rule 1: "Puka Nacua is doubtful" / "The WR2 this week. Hip. LA @ DEN, Sun 5:20 PM." A player
   with no rank led on how widely he is rostered, so that number takes the rank's place. */
function dgLeadHurt(r){
  const [cls, word] = DG_STATUS[r.status] || ["q", () => esc(r.status)];
  const who = r.rank != null ? t("digest.lead.rank", {pos: esc(r.pos), rank: r.rank})
    : r.rostered != null ? t("digest.lead.rostered", {pct: dgPct(r.rostered)}) : "";
  const game = r.game ? t("digest.lead.game", {game: dgGame(r.game) + (r.game.kick ? ", " + esc(r.game.kick) : "")}) : "";
  return {tone: cls, photo: dgPhotoHTML(r.slug),
          head: t("digest.lead.hurt", {name: esc(r.n), status: `<em class="dg-em ${cls}">${word()}</em>`}),
          fact: [who, r.injury ? esc(r.injury) + "." : "", game].filter(Boolean).join(" ")};
}

/* Rule 2: "SEA @ WAS in 22 mph wind" / "Sun 10:00 AM. 73°F, mostly sunny." */
function dgLeadWx(g){
  const what = dgWxKind(g) === "wind" ? t("digest.lead.wx.wind", {mph: g.wind_mph}) : t("digest.lead.wx.rain", {pct: g.precip_pct});
  const sky = [g.temp_f != null ? t("digest.lead.wx.temp", {f: g.temp_f}) : "", g.short ? esc(g.short) : ""].filter(Boolean).join(", ");
  return {tone: "sky", photo: `<span class="dg-photo dg-glyph">${dgWxKind(g) === "wind" ? DG_WIND : DG_RAIN}</span>`,
          head: t("digest.lead.wx.head", {game: dgGame(g), what: `<em class="dg-em sky">${what}</em>`}),
          fact: [g.kick ? esc(g.kick) + "." : "", sky ? sky + "." : ""].filter(Boolean).join(" ")};
}

/* Rule 3: the headline itself, a size down because it is a sentence, not a name. */
function dgLeadNews(it){
  return {tone: it.kind === "out" ? "out" : it.kind === "injury" ? "q" : "", photo: dgPhotoHTML(it.slugs), long: true,
          head: esc(it.headline), fact: it.when ? t("digest.lead.news.fact", {when: esc(it.when)}) : t("digest.lead.news.src")};
}

function dgLead(){
  const d = dgD();
  if (!d) return {tone: "quiet", photo: "", head: t("digest.empty.head"), fact: t("digest.empty.sub")};
  const l = d.lead;
  const row = l && {hurt: d.hurt, weather: d.wx, news: d.news}[l.rule] ? {hurt: d.hurt, weather: d.wx, news: d.news}[l.rule][l.index] : null;
  if (!row) return {tone: "quiet", photo: "", head: t("digest.lead.quiet.head"), fact: t("digest.lead.quiet.sub")};
  return l.rule === "hurt" ? dgLeadHurt(row) : l.rule === "weather" ? dgLeadWx(row) : dgLeadNews(row);
}

function dgLeadHTML(){
  const L = dgLead();
  return `<article class="dg-lead ${L.tone}${L.photo ? " has-photo" : ""}">
    <div class="dg-lead-txt"><h2 class="dg-lead-h${L.long ? " long" : ""}">${L.head}</h2>
      <p class="dg-lead-fact">${L.fact}</p></div>
    ${L.photo}
  </article>`;
}
