/* ============================== DIGEST: A ROW ==============================
   2026-10-06, storyboard "Digest by Day"; STYLE.md "Answer first, research one tap away". Every card's
   row: a 34px face (a team tile for a defense or a game), the name over one meta line, the answer at
   the right. No position tag: the meta line says what matters. The answer is a pick word in a pill
   (SMASH, START, SIT where a model makes the call; START and SIT are bold calls, takes, with no mark; Q, D, OUT and IR, the official status) or a number with
   its change. A row with research opens it in place under itself, one open at a time across the
   Digest; a row without opens the player's profile.

     dgRowHTML(card, r) -> HTML
       card       the card's id ("adds"), so two cards can hold one player
       r.slug     the player (his face, his profile); r.n his name (drawn escaped)
       r.tile     a team or game code drawn instead of a face ("DET", "TEN")
       r.meta     one line of HTML under the name: the card escapes what it puts there
       r.mid      optional HTML between the name and the answer (a sparkline, practice marks)
       r.answer   {pill: "SMASH" | "START" | "SIT" | "Q" | "D" | "OUT" | "IR", sub} or {num, unit, change, dir: "up" | "down" | "flat"}
                  (`unit`: the word for what the number counts, small beside it: "78% snaps")
       r.research [[label, value], ...], drawn escaped; r.foot one line under them, escaped

   A pick word carries what its model has been through in its tooltip (tests/test_flag_marks.py). */

let DG_ROW_OPEN = null;   // the open row's key, kept across repaints

const DG_PILL = {
  SMASH: ["smash", () => t("digest.card.pill.smash"), () => t("matchups.takes.markSmash")],
  START: ["start", () => t("digest.card.pill.start"), () => ""],     // a bold call is a take: no test-status label
  SIT: ["sit", () => t("digest.card.pill.sit"), () => ""],
  Q: ["q", () => t("digest.card.pill.q"), () => ""],
  OUT: ["out", () => t("digest.card.pill.out"), () => ""],
  D: ["d", () => t("digest.card.pill.d"), () => ""],
  IR: ["ir", () => t("digest.card.pill.ir"), () => ""],
};

function dgAnswerHTML(a){
  if (!a) return "";
  if (a.pill){
    const [cls, word, mark] = DG_PILL[a.pill] || ["", () => esc(a.pill), () => ""];
    return `<span class="dg-ans ${cls}" data-testid="digest-r-pill"${mark() ? ` title="${esc(mark())}"` : ""}>${word()}</span>`
      + (a.sub ? `<small class="dg-r-d flat">${esc(a.sub)}</small>` : "");
  }
  return `<span class="dg-r-num" data-testid="digest-r-num">${esc(a.num)}${a.unit ? ` <small class="dg-r-u">${esc(a.unit)}</small>` : ""}</span>`
    + (a.change ? `<small class="dg-r-d ${["up", "down"].includes(a.dir) ? a.dir : "flat"}">${esc(a.change)}</small>` : "");
}

const dgRowKey = (card, r) => `${card}:${r.slug || r.tile || r.n || ""}`;
const dgRowId = key => "dg-r-" + key.replace(/[^a-z0-9-]/gi, "-");

function dgRowHTML(card, r){
  const key = dgRowKey(card, r), res = (r.research || []).length > 0, open = res && DG_ROW_OPEN === key;
  const face = r.tile ? `<span class="dg-r-tile">${esc(r.tile)}</span>`
    : `<span class="dg-hd dg-r-face">${avatarHTML({n: r.n || "", slug: r.slug})}</span>`;
  const act = res ? `aria-expanded="${open}" aria-controls="${dgRowId(key)}" data-dgr="${esc(key)}"` : r.slug ? `data-dgslug="${esc(r.slug)}"` : "";
  const body = res ? `<div class="dg-r-res" id="${dgRowId(key)}" data-testid="digest-r-research"${open ? "" : " hidden"}>
      <dl>${r.research.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("")}</dl>
      ${r.foot ? `<p class="dg-r-foot">${esc(r.foot)}</p>` : ""}
      ${r.slug ? `<button type="button" class="dg-go" data-testid="digest-r-profile" data-dgslug="${esc(r.slug)}">${t("digest.card.profile")}${DG_ARROW}</button>` : ""}</div>` : "";
  const tag = res || r.slug ? "button" : "div";
  return `<div class="dg-r${open ? " open" : ""}" data-testid="digest-r">
    <${tag}${tag === "button" ? ' type="button"' : ""} class="dg-r-b" data-testid="digest-r-btn" ${act}>${face}
      <span class="dg-r-t"><b data-testid="digest-r-name">${esc(r.n || "")}</b><span class="dg-r-m">${r.meta || ""}</span></span>
      ${r.mid ? `<span class="dg-r-mid">${r.mid}</span>` : ""}<span class="dg-r-a" data-testid="digest-r-answer">${dgAnswerHTML(r.answer)}</span></${tag}>
    ${body}</div>`;
}

/* Open a row's research in place and close any other: no re-render, so nothing moves under the thumb but
   the row itself. A second tap closes it. */
function dgRowToggle(b, root){
  const key = b.dataset.dgr;
  DG_ROW_OPEN = DG_ROW_OPEN === key ? null : key;
  root.querySelectorAll(".dg-r-b[data-dgr]").forEach(x => {
    const on = x.dataset.dgr === DG_ROW_OPEN, res = document.getElementById(x.getAttribute("aria-controls"));
    x.setAttribute("aria-expanded", String(on));
    x.parentElement.classList.toggle("open", on);
    if (res) res.hidden = !on;
  });
}
