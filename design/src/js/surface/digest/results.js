/* ============================== DIGEST: RESULTS ==============================
   The week so far (2026-09-28): four headline tiles and each position's top three (headlines.js,
   since 2026-09-29), then who smashed his projection, who busted and who left his game hurt, folded.
   A smashed or busted row says why as a pill: ff-jarvis picks the reason
   (weekly_digest_played.why_of), the page only labels it. */

/* "1 game" / "15 games": both spelled out, since assemble.py --check finds a key only as a literal. */
const dgGames = n => n === 1 ? t("digest.res.game") : t("digest.res.games", {n});

/* Reasons are short coloured words, not sentences (2026-09-28, DESIGN.md "Say it in a shape"; boxes
   dropped 2026-09-29, only how long he is out keeps one). One colour, one meaning: green = TD luck
   that helped, red = TD luck that hurt, amber = an injury, filled red = how long he is out, grey =
   his role. Tapping the row opens the profile with the full news. */
const dgPill = (text, cls) => `<i class="dg-pill${cls ? " " + cls : ""}">${text}</i>`;
const dgCap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;

/* How long he is out, read from his newest headline by a short list of phrases; first match wins,
   and a headline that names none gives no pill. */
const DG_WORD_N = {one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8};
const DG_OUT = [
  [/season-ending|for the season|rest of the season/i, () => dgPill(t("digest.out.season"), "out")],
  [/injured reserve|\bIR\b/, () => dgPill(t("digest.out.ir"), "out")],
  [/\b(\d+|one|two|three|four|five|six|seven|eight)(?:[- ]to[- ]\w+)? weeks?\b/i,
    m => dgPill(t("digest.out.weeks", {n: DG_WORD_N[m[1].toLowerCase()] || m[1]}), "out")],
  [/extended time|multiple weeks|several weeks/i, () => dgPill(t("digest.out.long"), "out")],
  [/week-to-week/i, () => dgPill(t("digest.out.wtw"))],
  [/day-to-day/i, () => dgPill(t("digest.out.dtd"))],
  [/could play|expected to play|avoids serious/i, () => dgPill(t("digest.out.could"))],
  [/questionable/i, () => dgPill(t("digest.out.q"))],
];
function dgOutPill(text){
  if (!text) return "";
  for (const [re, pill] of DG_OUT){ const m = text.match(re); if (m) return pill(m); }
  return "";
}

/* A left-hurt player: his injury, then how long he is out; "Left early" when nothing is known. */
function dgLeftPills(r){
  const tag = r.injury ? dgPill(esc(dgCap(r.injury)), "hurt") : "";
  const out = dgOutPill(r.later);
  return tag || out ? tag + out : dgPill(t("digest.res.leftEarly"));
}

/* The one reason the producer chose (`kind`), as pills. A role that gained also shows TD luck when
   that added five points or more. */
function dgWhy(r, left){
  const w = r.why, up = r.diff > 0, abs = n => Math.abs(n);
  if (w.kind === "hurt"){
    const l = left.find(x => x.slug === r.slug);
    return dgPill(l && l.injury ? t("digest.pill.hurtTag", {tag: esc(dgCap(l.injury))}) : t("digest.pill.hurt"), "hurt");
  }
  if (w.kind === "idle") return dgPill(t("digest.pill.snaps", {share: w.share}));
  if (w.kind === "luck") return dgPill(t("digest.pill.luck", {n: dgSigned(up ? abs(w.luck) : -abs(w.luck), 0)}), up ? "luck" : "unlucky");
  if (w.kind === "role"){
    const v = {share: w.share, delta: dgSigned(w.delta, 0)};
    const role = dgPill({targets: () => t("digest.pill.targets", v), carries: () => t("digest.pill.carries", v),
                         snaps: () => t("digest.pill.roleSnaps", v)}[w.stat]());
    return up && w.luck >= 5 ? role + dgPill(t("digest.pill.luck", {n: dgSigned(w.luck, 0)}), "luck") : role;
  }
  if (w.expected == null) return "";
  return dgPill(up ? t("digest.pill.earned", {n: w.expected}) : t("digest.pill.expected", {n: w.expected}));
}

/* Points over his projection, the stack Live's rows use (2026-09-29, storyboard
   https://claude.ai/artifact/7gsPHebT4xTdo36N1QqqWD, option B). The gap is not printed: the list's
   name says which way he went and the pill says why, so a row carries two things. */
const dgResNum = r => `<span class="dg-rv"><b>${r.actual != null ? r.actual.toFixed(1) : ""}</b>`
  + `${r.proj != null ? `<span>${r.proj.toFixed(1)}</span>` : ""}</span>`;

/* A face cropped to the head, drawn at 150% so it fills the circle instead of the chest-up frame;
   `96` asks the srcset for a file sharp at that size. The tiles and the wall's board wear it
   (headlines.js); a list row is text. */
const dgResFace = r => HEADS[r.slug] ? headImgHTML(HEADS[r.slug], initials(r.n), r.slug, 96)
  : `<div class="fallback">${esc(initials(r.n))}</div>`;
/* One list row: name over its reason pills, points over projection. Opens the profile. */
const dgResRow = (r, pills, num) => `<button type="button" class="dg-rr" data-dgslug="${esc(r.slug)}">
    <span class="dg-rr-n"><b>${esc(dgShort(r.n))}</b>${pills ? `<span>${pills}</span>` : ""}</span>${num}</button>`;

/* A folded list (Smashed, Busts, Left hurt; 2026-09-29, 80px rows made the phone's card ~3,400px)
   heads with a button, its name, count and chevron; its rows show once tapped open (digest.js). On the
   wall too since the headlines (2026-09-29): the tiles already tell the week, the lists are the detail. */
const DG_FOLD = new Set();
const dgResCol = (title, rows, row, cls) => {
  if (!rows.length) return "";
  const key = cls || title;
  return `<div class="dg-rcol ${cls} fold"${DG_FOLD.has(key) ? " data-open" : ""}>
    <button type="button" class="dg-rsum" data-dgfold="${esc(key)}" aria-expanded="${DG_FOLD.has(key)}">
      <span>${title}</span><span class="dg-rcount">${rows.length}</span>${DG_CHEV}</button>${rows.map(row).join("")}</div>`;
};

/* The four tiles, each position's top three, then the three lists folded. */
function dgResBody(d){
  const why = r => dgResRow(r, dgWhy(r, d.left), dgResNum(r));
  const low = dgResCol(t("digest.res.smashed"), d.smashed, why, "smashed") + dgResCol(t("digest.res.busts"), d.busts, why, "busts")
    + dgResCol(t("digest.res.left"), d.left, r => dgResRow(r, dgLeftPills(r), dgResNum(r)), "left");
  const blocks = dgTilesHTML(d) + dgBoardHTML(d) + (low ? `<div class="dg-rlow">${low}</div>` : "");
  const foot = d.pending ? t("digest.foot.resPending", {n: dgGames(d.finals.length), left: d.pending}) : t("digest.foot.res", {n: dgGames(d.finals.length)});
  return (blocks ? `<div class="dg-rs">${blocks}</div>` : "") + dgFootHTML(foot, "", "");
}
