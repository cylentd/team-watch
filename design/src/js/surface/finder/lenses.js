/* ============================== LEAGUE > TRADES: AN OFFER'S LENSES ==============================
   Ledger #44, 2026-10-08 (VISION 2026-10-07, David: "ROS gain is one lens, not the gate"). ff-jarvis 3cf9002 judges each
   side of an offer on the lens its standing weighs most: Now (the next 2 weeks), Push (the next 4), Playoff run or ROS.
   An offer card (lboard/tbcard.js) then shows, in its foot, both sides as equals, You and Them: the gain on the lens that
   judges that side, and the line "For a contender: Playoff run". The partner's number is as big as the reader's, because
   it is the pitch. Above the foot, the nearest bye notes (two at most); in it, All four lenses, the research one tap away.
   Which lens, which gain, which notes: finder/logic.js. Nothing here computes a number. An offer from before the lenses
   draws none of this: the card shows its rest-of-season gain as it did. */

/* Every copy key spelled out: assemble.py --check finds a key only by a literal lookup. */
const tfLensName = lens => ({now: t("finder.lens.now"), push: t("finder.lens.push"), playoffs: t("finder.lens.playoffs"),
  ros: t("finder.lens.ros")})[lens];
const tfTierName = tier => ({contender: t("finder.tier.contender"), bubble: t("finder.tier.bubble"), chaser: t("finder.tier.chaser")})[tier];

/* "For a contender: Playoff run", or the lens alone for a team the league does not place. */
const tfJudgeLine = j => j.tier ? t("finder.judge", {tier: tfTierName(j.tier), lens: tfLensName(j.lens)}) : tfLensName(j.lens);

/* A gain to one decimal with its sign, or the dash for a blank lens. */
const tfGainText = n => n == null ? t("lboard.edit.none") : tfSigned(n);
const tfMood = n => n > 0 ? "up" : n < 0 ? "neg" : "flat";

/* One side: who, the gain on its lens, the judge line. Both sides draw the same markup, so they are the same size. */
const tfSideHTML = (j, who) => `<div class="tf-side" data-testid="finder-side"><p class="tb-h" data-testid="finder-side-who">${who}</p>
  <p class="tb-gain tf-sgain" data-testid="finder-side-gain"><b class="${tfMood(j.gain)}">${tfGainText(j.gain)}</b> <small>${t("finder.side.pts")}</small></p>
  <p class="tf-judge" data-testid="finder-side-judge">${tfJudgeLine(j)}</p></div>`;

/* The weeks a lens covers: the league's `windows` for Now, Push and Playoff run, `weeks_left` for ROS; "" when unknown. */
function tfLensWeeks(lgd, lens){
  const n = lens === "ros" ? lgd.weeks_left : (lgd.windows || {})[lens];
  return typeof n !== "number" ? "" : n === 1 ? t("finder.lens.week", {n}) : t("finder.lens.weeks", {n});
}

/* All four lenses, behind a tap: a row a lens, both sides' gains, the cell that judges each side marked. */
function tfLensTableHTML(o, lgd){
  const cell = (n, on) => `<td class="${on ? "on" : ""}">${tfGainText(n)}</td>`;
  const row = r => `<tr data-testid="finder-lens-row"><th scope="row"><b>${tfLensName(r.lens)}</b><small>${tfLensWeeks(lgd, r.lens)}</small></th>${
    cell(r.me, r.onMe)}${cell(r.them, r.onThem)}</tr>`;
  return `<details class="tf-lenses" data-testid="finder-lenses"><summary>${t("finder.lenses.all")}<svg class="tf-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg></summary>
    <table><thead><tr><th scope="col">${t("finder.lenses.head")}</th><th scope="col">${t("finder.side.me")}</th><th scope="col">${t("finder.side.them")}</th></tr></thead>
    <tbody>${tfLensRows(o).map(row).join("")}</tbody></table></details>`;
}

/* The foot's top: the two sides, then the table. `owner` is the reader's team name, the league's `standing` key. */
function tfLensFootHTML(o, lgd, owner){
  const me = tfJudge(o, "me", tfTier(lgd.standing, owner)), them = tfJudge(o, "them", tfTier(lgd.standing, o.partner));
  return `<div class="tf-sides" title="${t("finder.lenses.mark")}">${tfSideHTML(me, t("finder.side.me"))}${tfSideHTML(them, t("finder.side.them"))}</div>
    ${tfLensTableHTML(o, lgd)}`;
}

/* One bye note in words, by kind and side; `n` above 1 says how many. */
function tfNoteText(n){
  const v = {name: esc(nameInitial(n.player)), week: n.week, n: n.n}, many = n.n > 1, mine = n.side === "me";
  if (n.kind === "covers_bye") return mine ? (many ? t("finder.note.coversMeMany", v) : t("finder.note.coversMe", v))
    : (many ? t("finder.note.coversThemMany", v) : t("finder.note.coversThem", v));
  return mine ? (many ? t("finder.note.doneMeMany", v) : t("finder.note.doneMe", v))
    : (many ? t("finder.note.doneThemMany", v) : t("finder.note.doneThem", v));
}

/* The card's nearest bye notes, quiet lines under the To IR and You drop lines. */
const tfNotesHTML = (o, lgd) => tfNotes(o.notes, lgd.week, lgd.windows)
  .map(n => `<p class="tf-note" data-testid="finder-note">${tfNoteText(n)}</p>`).join("");
