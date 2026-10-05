/* ============================== DIGEST: PARTS THE RECAP VIEW DRAWS ==============================
   The week's results left the Digest on 2026-10-05 (David: "we probably need a recap section for the
   week instead of dumping it into the Digest ... not just a results section that stays there for the
   whole week and quickly become stale"). The Results row, its banner rule and the Waiting card are gone;
   This week > Recap (surface/recap/) draws the week. What it draws with is here, under the names the
   Digest gave them, so nothing was copied: a call, a box line, a board, a reason, a left-hurt pill.
   Nothing in the Digest itself calls dgBoardHTML, dgWhy, dgLeftPills or dgResRow any more; the Recap
   view does (and dgCall, dgBoxPills, dgTopLine in lead.js). Their styles are results.css and
   headlines.css, fenced to both views (scope.json). */

/* "1 game" / "15 games": both spelled out, since assemble.py --check finds a key only as a literal. */
const dgGames = n => n === 1 ? t("digest.res.game") : t("digest.res.games", {n});

/* A player's day in one short line: a passer's yards and TDs, a back's rushing and receiving yards,
   a receiver's catches for yards. Every word is a copy key, spelled out for assemble.py --check. */
function dgStatLine(r){
  const b = r.line;
  if (!b) return "";
  const td = n => n ? t("digest.stat.td", {n}) : "";
  const parts = b.att >= 10
    ? [t("digest.stat.pass", {y: b.pass_yd}), td(b.pass_td), b.int ? t("digest.stat.int", {n: b.int}) : "",
       b.rush_yd >= 20 ? t("digest.stat.rush", {y: b.rush_yd}) : ""]
    : b.car >= 5
      ? [t("digest.stat.rush", {y: b.rush_yd}), b.rec_yd > 0 ? t("digest.stat.recYd", {y: b.rec_yd}) : "", td(b.td)]
      : [b.rec ? t("digest.stat.catches", {n: b.rec, y: b.rec_yd}) : "", b.car ? t("digest.stat.rush", {y: b.rush_yd}) : "", td(b.td)];
  return parts.filter(Boolean).join(" · ");
}

/* Each position's top three, as a table: the position as a heading, then name over his day, points at
   the right (2026-09-29, storyboard https://claude.ai/artifact/Ms6FbdvynVPoRTKEidPGAz, 1B). No faces: a
   list scans by name, and a kicker or a defense has none to show. Two positions a row on a phone, four
   on a wide screen. `d.stars` is a list of rows with `line`; the Recap's own `stars` has the same shape. */
function dgBoardHTML(d){
  const pos = DG_POS.map(p => {
    const rows = d.stars.filter(r => r.pos === p);
    return rows.length ? `<div class="dg-bd-pos"><h4 class="dg-bd-p">${p}</h4><span class="dg-bd-ns">${rows.map(r =>
      `<button type="button" class="dg-bd-r" data-dgslug="${esc(r.slug)}">
        <b>${esc(dgShort(r.n))}</b><span class="dg-bd-s">${dgStatLine(r)}</span><i>${r.actual.toFixed(1)}</i></button>`).join("")}</span></div>` : "";
  }).join("");
  return pos ? `<div class="dg-bd">${pos}</div>` : "";
}

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

/* One list row: name over its reason pills, points over projection. Opens the profile. */
const dgResRow = (r, pills, num) => `<button type="button" class="dg-rr" data-dgslug="${esc(r.slug)}">
    <span class="dg-rr-n"><b>${esc(dgShort(r.n))}</b>${pills ? `<span>${pills}</span>` : ""}</span>${num}</button>`;
