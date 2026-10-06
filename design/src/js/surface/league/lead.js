/* ============================== LEAGUE: THE LEAD AND THE BRIEFS (Yahoo back page) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5Sj3BRZqyfaVWkvCXCjgFV; rows and tags 2026-10-06 (back.js).
   The game the week is about as one big story with Blip reacting to it (never a player's headshot since
   2026-10-06: the recap is the whole league's board, not one roster's), the other games as rows of a score line, its tags and the joke, and
   the standings in agate. Managers carry the score lines; team names appear inside the jokes, where the
   puns need them. A row's facts and box score open in the modal, so no card ever grows. */

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

/* Blip on the lead, reacting once to the game (w.blip, blip_of). */
const LG_BLIP_LABEL = {wince: () => t("league.lead.blip.wince"), flatline: () => t("league.lead.blip.flatline"),
  ko: () => t("league.lead.blip.ko"), sweat: () => t("league.lead.blip.sweat"), laugh: () => t("league.lead.blip.laugh")};
function lgBlipHTML(pose, stamped){
  if (!LG_BLIP_LABEL[pose]) return "";
  // A stamped game reacts as the stamp lands (back.css slams it at .75s), an unstamped one sooner.
  return `<figure class="bp2-photo bp2-blip${stamped ? " late" : ""}">${blipReactSVG(LG_BLIP_LABEL[pose](), pose)}</figure>`;
}

/* The lead: the week's biggest game (w.lead), drawn big, the full width above the other games: Blip with the
   page's one stamp under it, the score, the award tags, the game's line, its facts and its box score. */
function lgLeadHTML(w, g){
  const fig = lgBlipHTML(w.blip, !!g.stamp);
  const stamp = g.stamp ? `<span class="bp-stamp bp2-stamp">${esc(g.stamp)}</span>` : "";
  return `<article class="bp2-lead${fig ? " has-fig" : ""}">
    ${fig ? `<div class="bp2-fig">${fig}${stamp}</div>` : ""}
    <div class="bp2-lbody">
      <div class="bp2-score">${lgScoreLineHTML(g)}</div>
      ${fig ? "" : stamp}
      ${lgTagsHTML(w, g)}
      ${g.punch ? `<p class="bp2-punch">${esc(g.punch)}</p>` : ""}
      ${lgBeatsHTML(g)}
      ${g.box ? `<button class="bp2-more" data-lgsheet="${lgKey(g)}">${t("league.box.show")}</button>` : ""}
    </div>
  </article>`;
}

/* A game's award tags (back.js lgGameTags): flat, in the row's flow, each with the team it names. */
function lgTagsHTML(w, g){
  const tags = lgGameTags(w, g);
  return tags.length ? `<span class="lg-tags">${tags.map(x => `<span class="lg-tag ${x.tone}">${x.label} <small>${lgMgr(x.id)}</small></span>`).join("")}</span>` : "";
}

/* Every game but the lead as one row: the score line, up to two tags, the line. The whole row is the
   button that opens its sheet. No row carries a stamp. */
function lgRowHTML(w, g, i){
  return `<button type="button" class="lg-row" data-lgsheet="${lgKey(g)}" style="--i:${i}">
    <span class="bp2-bl">${lgScoreLineHTML(g)}</span>
    ${lgTagsHTML(w, g)}
    ${g.punch ? `<span class="bp2-bp">${esc(g.punch)}</span>` : ""}
  </button>`;
}

/* The standings in agate: rank, manager, record, then the run each team is on going into next week
   (league_back.add_streaks; two games or more). The same for every reader: no row is lit. */
const LG_STREAK_MIN = 2;
function lgAgateHTML(w){
  const half = Math.ceil(w.table.length / 2), run = {};
  (w.streaks || []).forEach(r => { run[r.id] = r; });
  const sk = id => {
    const r = run[id], cls = r && r.n >= LG_STREAK_MIN ? (r.w ? " hot" : " cold") : "";
    return `<span class="lg-sk${cls}">${cls ? (r.w ? t("league.streak.w", {n: r.n}) : t("league.streak.l", {n: r.n})) : ""}</span>`;
  };
  const row = (r, i) => `<span><i>${i + 1}</i><b>${lgMgr(r.id)}</b><em>${r.t ? `${r.w}–${r.l}–${r.t}` : `${r.w}–${r.l}`}</em>${sk(r.id)}</span>`;
  const cells = w.table.slice(0, half).flatMap((r, i) => [row(r, i), w.table[i + half] ? row(w.table[i + half], i + half) : ""]);
  return `<section class="lg-sec bp2-agate" aria-label="${t("league.table.title")}">
    <h3 class="bp-hd">${t("league.going.title", {n: w.week + 1})}</h3>
    <div class="bp2-ag">${cells.join("")}</div>
  </section>`;
}

/* Luck so far (David, 2026-10-06, the bottom row's gap): a ladder of every team, luckiest first, by its luck
   in wins (league_back.add_standings: real wins minus the wins its points earned against everyone); the
   table's own tag names a whole win either way. "Robbed" is the week's award, so the unlucky side is Snakebit.
   Kept simple: record, the signed number, the tag, one caption; the method stays in the code. */
const lgLuckRows = w => [...w.table].sort((a, b) => b.luck - a.luck);
const lgSignedLuck = n => n > 0 ? `+${n.toFixed(1)}` : n < 0 ? `−${(-n).toFixed(1)}` : "0.0";
function lgLuckHTML(w){
  const rows = lgLuckRows(w);
  if (!rows.length) return "";
  const tag = r => r.tag === "lucky" ? `<span class="lg-tag g">${t("league.luck.lucky")}</span>`
    : r.tag === "robbed" ? `<span class="lg-tag r">${t("league.luck.snakebit")}</span>` : "";
  return `<section class="lg-sec lg-luck" aria-label="${t("league.luck.title")}">
    <h3 class="bp-hd">${t("league.luck.title")}<span>${t("league.luck.sub")}</span></h3>
    <ul class="lg-luck-l">${rows.map(r => `<li${r.tag ? ` class="${r.tag === "lucky" ? "up" : "dn"}"` : ""}><b>${lgMgr(r.id)}</b>
      <em>${r.t ? `${r.w}–${r.l}–${r.t}` : `${r.w}–${r.l}`}</em><i>${lgSignedLuck(r.luck)}</i>${tag(r)}</li>`).join("")}</ul>
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
