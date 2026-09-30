/* ============================== LEAGUE: THE LEAD AND THE BRIEFS (Yahoo back page) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5Sj3BRZqyfaVWkvCXCjgFV. A newspaper back page: the
   game the headline is about as one big story with the photo of the player its joke is about (faded
   like an OUT headshot when the player flopped), the other games as briefs of one line and the joke, and the
   standings in agate. Managers carry the score lines; team names appear inside the jokes, where the
   puns need them. A brief's facts and box score open in the modal, so no card ever grows. */

/* Winner and score, "def.", loser and score: the loser dimmed. */
function lgScoreLineHTML(g){
  const aWon = g.win !== "away";
  const [w, l] = aWon ? [[g.a, g.ap], [g.b, g.bp]] : [[g.b, g.bp], [g.a, g.ap]];
  const tie = g.win === "tie";
  return `<span class="bp2-w"><b>${lgMgr(w[0])}</b> <span class="bp2-n">${lgPts(w[1])}</span></span>
    <span class="bp2-d">${tie ? t("league.lead.tied") : t("league.lead.def")}</span>
    <span class="bp2-l"><b>${lgMgr(l[0])}</b> <span class="bp2-n">${lgPts(l[1])}</span></span>`;
}

const lgBeatsHTML = g => g.beats.length ? `<ul class="bp2-beats">${g.beats.map(b => `<li>${lgBeatHTML(b)}</li>`).join("")}</ul>` : "";

/* The headshot: the biggest cut ff-jarvis made of the player; nothing when there is none. */
function lgPhotoHTML(p){
  if (!p) return "";
  const src = (typeof HEADS_LG !== "undefined" && HEADS_LG[p.slug]) || (typeof HEADS !== "undefined" && HEADS[p.slug]);
  if (!src) return "";
  return `<figure class="bp2-photo${p.flop ? " flop" : ""}">${headImgHTML(src, initials(p.name), p.slug, 170)}
    <figcaption>${esc(nameInitial(p.name))} <b>${lgPts(p.pts)}</b></figcaption></figure>`;
}

/* No player to picture: Blip in the photo's place, reacting once to the game (w.blip, blip_of). */
const LG_BLIP_LABEL = {wince: () => t("league.lead.blip.wince"), flatline: () => t("league.lead.blip.flatline"),
  ko: () => t("league.lead.blip.ko"), sweat: () => t("league.lead.blip.sweat"), laugh: () => t("league.lead.blip.laugh")};
function lgBlipHTML(pose, stamped){
  if (!LG_BLIP_LABEL[pose]) return "";
  // A stamped game reacts as the stamp lands (back.css slams it at .75s), an unstamped one sooner.
  return `<figure class="bp2-photo bp2-blip${stamped ? " late" : ""}">${blipReactSVG(LG_BLIP_LABEL[pose](), pose)}</figure>`;
}

/* The lead: the week's biggest game (w.lead), drawn big. Its joke is the page's one headline (since
   2026-09-27; the roast's own headline told the same game twice), else the roast's headline. */
function lgLeadHTML(w){
  const g = w.games.find(x => lgKey(x) === w.lead) || w.games[0];
  const photo = lgPhotoHTML(w.photo) || lgBlipHTML(w.blip, !!g.stamp), hl = g.punch || w.head;
  return `<article class="bp2-lead${photo ? " has-photo" : ""}">
    ${photo}
    <div class="bp2-lbody">
      <div class="bp2-score">${lgScoreLineHTML(g)}</div>
      ${hl ? `<h2 class="bp2-punch">${esc(hl)}</h2>` : ""}
      ${lgBeatsHTML(g)}
      ${g.box ? `<button class="bp2-more" data-lgsheet="${lgKey(g)}">${t("league.box.show")}</button>` : ""}
    </div>
    ${g.stamp ? `<span class="bp-stamp bp2-stamp">${esc(g.stamp)}</span>` : ""}
  </article>`;
}

/* A brief: one line of names and scores, the joke under it; the whole brief opens its sheet. */
function lgBriefHTML(g, i){
  return `<button class="bp2-brief" data-lgsheet="${lgKey(g)}" style="--i:${i}">
    <span class="bp2-bl">${lgScoreLineHTML(g)}</span>
    ${g.punch ? `<span class="bp2-bp">${esc(g.punch)}</span>` : ""}
    ${g.stamp ? `<span class="bp2-tag">${esc(g.stamp)}</span>` : ""}
  </button>`;
}

/* Every game but the lead, in the slate's story order (stamped first, then by margin). */
function lgBriefsHTML(w){
  const margin = g => Math.abs(g.ap - g.bp);
  const rest = w.games.filter(g => lgKey(g) !== w.lead).sort((x, y) => (!!y.stamp - !!x.stamp) || margin(y) - margin(x));
  return `<section class="bp2-briefs" aria-label="${t("league.lead.also")}">
    <h3 class="bp-hd">${t("league.lead.also")}<span>${t("league.back.games", {n: rest.length})}</span></h3>
    ${rest.map(lgBriefHTML).join("")}
  </section>`;
}

/* The standings in agate: rank, manager, record, two columns of six; the team on screen in lime. */
function lgAgateHTML(w, id){
  const half = Math.ceil(w.table.length / 2);
  const row = (r, i) => `<span class="${r.id === id ? "me" : ""}"><i>${i + 1}</i>${lgMgr(r.id)}<em>${r.t ? `${r.w}–${r.l}–${r.t}` : `${r.w}–${r.l}`}</em></span>`;
  const cells = w.table.slice(0, half).flatMap((r, i) => [row(r, i), w.table[i + half] ? row(w.table[i + half], i + half) : ""]);
  return `<section class="lg-sec bp2-agate" aria-label="${t("league.table.title")}">
    <h3 class="bp-hd">${t("league.table.title")}<span>${t("league.table.after", {n: w.week})}</span></h3>
    <div class="bp2-ag">${cells.join("")}</div>
  </section>`;
}

/* A game's facts and box score in the modal, grown out of the brief that was tapped. */
function lgOpenGameSheet(g, originEl){
  const d = document.getElementById("modal");
  d.innerHTML = `<div class="dr-head">
      <button type="button" class="dr-close" aria-label="${t("common.action.close")}">✕</button>
      <h3 id="lg-sheet-title" class="bp2-sheet-t">${g.punch ? esc(g.punch) : t("league.box.show")}</h3>
      <div class="lbl">${t("league.recap.wk", {n: lgWeek().week})}</div>
    </div><div class="dr-body bp2-sheet">
      <div class="bp2-score">${lgScoreLineHTML(g)}</div>
      ${lgBeatsHTML(g)}
      ${g.box ? lgBoxHTML(g) : ""}
    </div>`;
  showModal(d, originEl, "lg-sheet-title");
}
