/* ============================== LEAGUE: THE LEAD AND THE BRIEFS (Yahoo back page) ==============================
   2026-09-27, storyboard https://claude.ai/artifact/5Sj3BRZqyfaVWkvCXCjgFV; rows and tags 2026-10-06 (back.js).
   The game the week is about as one big story with Blip reacting to it (never a player's headshot since
   2026-10-06: the recap is the whole league's board, not one roster's), the other games as rows of a score line, its tags and the joke, and
   the standings in agate. Managers carry the score lines; team names appear inside the jokes, where the
   puns need them. A row's facts and box score open in the modal, so no card ever grows. */

/* Winner and score, "beat", loser and score: the loser dimmed. Given the week, each award is a stamp in its
   team's half, after its score, and the Nail-biter, the game's own, closes the line (David, 2026-10-06: a row of
   tags under the line put Jon's Dumpster fire under Phillip). The sheet passes no week and draws none. */
const lgStampHTML = x => `<span class="lg-stamp ${x.tone}">${x.label}</span>`;
function lgScoreLineHTML(g, wk){
  const aWon = g.win !== "away";
  const [w, l] = aWon ? [[g.a, g.ap], [g.b, g.bp]] : [[g.b, g.bp], [g.a, g.ap]];
  const tie = g.win === "tie", tags = wk ? lgGameTags(wk, g) : [];
  const of = id => tags.filter(x => x.k !== "close" && x.id === id).map(lgStampHTML).join("");
  return `<span class="bp2-w"><b>${lgMgr(w[0])}</b> <span class="bp2-n">${lgPts(w[1])}</span>${of(w[0])}</span>
    <span class="bp2-d">${tie ? t("league.lead.tied") : t("league.lead.def")}</span>
    <span class="bp2-l"><b>${lgMgr(l[0])}</b> <span class="bp2-n">${lgPts(l[1])}</span>${of(l[0])}</span>${
    tags.filter(x => x.k === "close").map(lgStampHTML).join("")}`;
}

/* A game card's score as a scoreboard (David, 2026-10-06: in three-across cards "Chanel 146.98 [TOP DOG] beat"
   ended a line and the loser wrapped under it): the winner's row over the loser's, name, score, its own stamps;
   the Nail-biter, the game's, spans both rows at their end. A tie dims neither row. */
function lgScoreRowsHTML(g, wk){
  const aWon = g.win !== "away", tie = g.win === "tie", tags = lgGameTags(wk, g);
  const [w, l] = aWon ? [[g.a, g.ap], [g.b, g.bp]] : [[g.b, g.bp], [g.a, g.ap]];
  const row = ([id, pts], cls) => `<span class="bp2-sr ${cls}"><b>${lgMgr(id)}</b><span class="bp2-n">${lgPts(pts)}</span><span class="bp2-st">${
    tags.filter(x => x.k !== "close" && x.id === id).map(lgStampHTML).join("")}</span></span>`;
  const game = tags.filter(x => x.k === "close").map(lgStampHTML).join("");
  return `<span class="bp2-sb">${row(w, "bp2-w")}${row(l, tie ? "bp2-w" : "bp2-l")}${game ? `<span class="bp2-sgame">${game}</span>` : ""}</span>`;
}

/* A team's own Yahoo avatar (design/avatars.py, 2026-10-06), else its manager's initial in the same circle, so a
   card keeps its shape. The page draws the winner's only: on each game card and by the lead's score. */
const lgWinnerId = g => g.win === "away" ? g.b : g.a;
function lgAvatarHTML(id){
  const tm = LG && LG.teams.find(x => x.id === id);
  return tm && tm.avatar ? `<img class="lg-av" src="${esc(tm.avatar)}" alt="" loading="lazy" decoding="async">`
    : `<span class="lg-av lg-av-i" aria-hidden="true">${esc(String(lgMgr(id) || "").charAt(0))}</span>`;
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

/* The lead: the week's biggest game (w.lead), the full width above the other games, and the page's one
   headline (2026-10-06, "it looks like two headlines": Claude's headline sat above the card and the game's
   line inside it in the same face). Blip with the page's one stamp under it; the headline, else the game's
   line in its place; the score with its stamps, then the report and Box score. The report is one paragraph,
   the game's line then the dek on the rest of the week (David, 2026-10-06: the line, the dek and the facts were
   three scraps, "a bit random"; a newspaper runs the headline, then the report). The facts live in the sheet. */
function lgLeadHTML(w, g){
  const fig = lgBlipHTML(w.blip, !!g.stamp);
  const stamp = g.stamp ? `<span class="bp-stamp bp2-stamp">${esc(g.stamp)}</span>` : "";
  const title = w.head || g.punch, line = g.punch && g.punch !== title ? g.punch : "";
  const report = [line, w.head ? w.dek : ""].filter(Boolean).map(esc).join(" ");
  return `<article class="bp2-lead${fig ? " has-fig" : ""}">
    ${fig ? `<div class="bp2-fig">${fig}${stamp}</div>` : ""}
    <div class="bp2-lbody">
      ${title ? `<h2 class="lg-hl">${esc(title)}</h2>` : ""}
      <div class="bp2-score">${lgAvatarHTML(lgWinnerId(g))}${lgScoreLineHTML(g, w)}</div>
      ${fig ? "" : stamp}
      ${report ? `<p class="bp2-report">${report}</p>` : ""}
      ${g.box ? `<button class="bp2-more" data-lgsheet="${lgKey(g)}">${t("league.box.more")}</button>` : ""}
    </div>
  </article>`;
}

/* Every game but the lead as one card: the score as a scoreboard with its award stamps, the line. The whole
   card is the button that opens its sheet. No card carries the lead's big stamp. */
function lgRowHTML(w, g, i){
  return `<button type="button" class="lg-row" data-lgsheet="${lgKey(g)}" style="--i:${i}">
    ${lgAvatarHTML(lgWinnerId(g))}${lgScoreRowsHTML(g, w)}
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

/* Luck so far (David, 2026-10-06, the bottom row's gap): every team, luckiest first, by its luck in wins
   (league_back.add_standings: real wins minus the wins its points earned against everyone), drawn as a bar
   from a zero line, so it reads as a chart beside the standings' table ("looks the same", 2026-10-06): its
   length against the week's biggest luck, right and green when lucky, left and red when not. The table's tags
   name the two most extreme each side, Lucky and Unlucky (Snakebit until David asked what it meant; the week's
   unluckiest loss says Unlucky too since 2026-10-06, Robbed before: one word for bad luck). */
const lgLuckRows = w => [...w.table].sort((a, b) => b.luck - a.luck);
const lgSignedLuck = n => n > 0 ? `+${n.toFixed(1)}` : n < 0 ? `−${(-n).toFixed(1)}` : "0.0";
function lgLuckHTML(w){
  const rows = lgLuckRows(w);
  if (!rows.length) return "";
  const most = Math.max(...rows.map(r => Math.abs(r.luck))) || 1;
  const tag = r => r.tag === "lucky" ? lgStampHTML({tone: "g", label: t("league.luck.lucky")})
    : r.tag === "robbed" ? lgStampHTML({tone: "r", label: t("league.luck.unlucky")}) : "";
  const bar = r => `<span class="lg-lucktrack"><span class="lg-luckbar ${r.luck > 0 ? "up" : r.luck < 0 ? "dn" : "zero"}" style="--w:${
    +(Math.abs(r.luck) / most * 100).toFixed(1)}%"></span></span>`;
  return `<section class="lg-sec lg-luck" aria-label="${t("league.luck.title")}">
    <h3 class="bp-hd">${t("league.luck.title")}<span>${t("league.luck.sub")}</span></h3>
    <ul class="lg-luck-l">${rows.map(r => `<li><b>${lgMgr(r.id)}</b>${bar(r)}<i>${lgSignedLuck(r.luck)}</i>${tag(r)}</li>`).join("")}</ul>
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
