/* ============================== DIGEST: RESULTS ==============================
   The week so far (2026-09-28): the top scores per position as a 2x2, then who smashed his
   projection, who busted and who left his game hurt. A smashed or busted row says why as a pill:
   ff-jarvis picks the reason (weekly_digest_played.why_of), the page only labels it. On the
   wall the four blocks sit two by two (results.css); a phone stacks them. */

/* "1 game" / "15 games": both spelled out, since assemble.py --check finds a key only as a literal. */
const dgGames = n => n === 1 ? t("digest.res.game") : t("digest.res.games", {n});

/* Reasons are pills, not sentences (2026-09-28, DESIGN.md "Say it in a shape"). One colour, one
   meaning: green = TD luck that helped, red = TD luck that hurt, amber = an injury, filled red =
   how long he is out, grey = his role. Tapping the row opens the profile with the full news. */
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

/* "2.4 → 17.3", then the gap in its colour when there is one. */
function dgProjTo(r, diff){
  const from = r.proj != null ? `<small>${t("digest.res.proj", {n: r.proj.toFixed(1)})}</small>` : "";
  const to = r.actual != null ? r.actual.toFixed(1) : "";
  const gap = diff ? `<em class="${r.diff > 0 ? "up" : "dn"}">${dgSigned(r.diff, 1)}</em>` : "";
  return `<span class="dg-rn">${from}<b>${to}</b>${gap}</span>`;
}

function dgResLines(title, rows, meta, diff, cls){
  if (!rows.length) return "";
  return `<div class="dg-rl${cls ? " " + cls : ""}"><h4>${title}</h4>`
    + rows.map(r => dgLnHTML({...r, n: dgShort(r.n)}, meta(r), dgProjTo(r, diff))).join("") + `</div>`;
}

function dgResTop(d){
  const pos = DG_POS.map(p => {
    const rows = d.stars.filter(r => r.pos === p);
    return rows.length ? `<div><h4>${p}</h4><ol>${rows.map(r => `<li><span class="dg-hd sm">${avatarHTML(r)}</span>`
      + `<span>${esc(dgShort(r.n))}</span><em>${r.actual.toFixed(1)}</em></li>`).join("")}</ol></div>` : "";
  }).join("");
  return pos ? `<div class="dg-rtop">${pos}</div>` : "";
}

function dgResBody(d){
  const blocks = dgResTop(d)
    + dgResLines(t("digest.res.smashed"), d.smashed, r => dgWhy(r, d.left), true)
    + dgResLines(t("digest.res.busts"), d.busts, r => dgWhy(r, d.left), true)
    + dgResLines(t("digest.res.left"), d.left, dgLeftPills, false, "left");
  const foot = d.pending ? t("digest.foot.resPending", {n: dgGames(d.finals.length), left: d.pending}) : t("digest.foot.res", {n: dgGames(d.finals.length)});
  return (blocks ? `<div class="dg-rs">${blocks}</div>` : "") + dgFootHTML(foot, "", "");
}
