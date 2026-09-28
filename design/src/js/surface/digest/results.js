/* ============================== DIGEST: RESULTS ==============================
   The week so far (2026-09-28): the top scores per position as a 2x2, then who smashed his
   projection, who busted and who left his game hurt. A smashed or busted row says, in one line,
   why: ff-jarvis picks the reason (weekly_digest_played.why_of), the page only words it. On the
   wall the four blocks sit two by two (results.css); a phone stacks them. */

/* "1 game" / "15 games": both spelled out, since assemble.py --check finds a key only as a literal. */
const dgGames = n => n === 1 ? t("digest.res.game") : t("digest.res.games", {n});

/* What a left-hurt player has now: his newest words since ("suffers season-ending torn ACL"),
   after the injury tag when there is one; else just the tag, else "left early". */
function dgLeftWord(r){
  const tag = r.injury ? esc(r.injury) : "";
  if (r.later) return tag ? t("digest.why.tagged", {tag, words: esc(r.later)}) : esc(r.later);
  return tag || t("digest.res.leftEarly");
}

/* The one reason, first rule that fits (the producer already chose `kind`), as HTML: every value
   in it is a number or already escaped. A role that gained also names TD luck when that added five
   points or more. */
function dgWhy(r, left){
  const w = r.why, up = r.diff > 0, abs = n => Math.abs(n);
  if (w.kind === "hurt"){
    const l = left.find(x => x.slug === r.slug);
    return t("digest.why.hurt", {word: l ? dgLeftWord(l) : t("digest.res.leftEarly")});
  }
  if (w.kind === "idle") return t("digest.why.idle", {share: w.share});
  if (w.kind === "luck") return up ? t("digest.why.luckUp", {n: abs(w.luck)}) : t("digest.why.luckDown", {n: abs(w.luck)});
  if (w.kind === "role"){
    const v = {share: w.share, delta: dgSigned(w.delta, 0)};
    const role = {targets: () => t("digest.why.targets", v), carries: () => t("digest.why.carries", v),
                  snaps: () => t("digest.why.snaps", v)}[w.stat]();
    return up && w.luck >= 5 ? role + t("digest.why.andLuck", {n: w.luck}) : role;
  }
  if (w.expected == null) return "";
  return up ? t("digest.why.earnedUp", {n: w.expected}) : t("digest.why.earnedDown", {n: w.expected});
}

/* "proj 2.4 → 17.3", then the gap in its colour when there is one. */
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
  const hurt = r => `<span class="q">${dgLeftWord(r)}</span>`;
  const blocks = dgResTop(d)
    + dgResLines(t("digest.res.smashed"), d.smashed, r => dgWhy(r, d.left), true)
    + dgResLines(t("digest.res.busts"), d.busts, r => r.why.kind === "hurt" ? `<span class="q">${dgWhy(r, d.left)}</span>`
      : dgWhy(r, d.left), true)
    + dgResLines(t("digest.res.left"), d.left, hurt, false, "left");
  const foot = d.pending ? t("digest.foot.resPending", {n: dgGames(d.finals.length), left: d.pending}) : t("digest.foot.res", {n: dgGames(d.finals.length)});
  return (blocks ? `<div class="dg-rs">${blocks}</div>` : "") + dgFootHTML(foot, "", "");
}
