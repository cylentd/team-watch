/* ============================== LEAGUE > TRADES: AN OFFER CARD ==============================
   2026-10-05 (storyboard https://claude.ai/artifact/BXCJdmWfC87Z7VCAgdVC3Y, frames 1-3); the card since
   2026-10-06 sits in the finder (finder/finder.js; tbpage.js, the per-partner page with its Bold and Fair tabs,
   is gone). A card is one offer: the partner's name and record on top, two columns, YOU SEND and YOU GET, and one
   number, the reader's gain in rest-of-season points (a week's, until 2026-10-06). "Copy offer" puts a message on the clipboard for the other manager: season
   averages (a Hot player's last 2) and one sentence on the partner's roster room (`their`). An offer that drops a
   player says so in one line. "Edit" on a card and "Make your own offer" under the list open the edit state
   (tbedit.js) on its own page, its own history entry, so Back returns to the finder. The data is offers.js's;
   nothing here is computed. */
let TB = null;            // {lg, me, tm} while the edit state is open: the league, the reader's team and the partner's
let TB_EDIT = null;       // the reader's own package while the edit state is open (tbedit.js), else null

/* The four codes a status is shortened to; any other status shows its first letters. */
const tbInjCode = s => ({Out: t("lboard.inj.o"), IR: t("lboard.inj.ir"), Questionable: t("lboard.inj.q"),
  Doubtful: t("lboard.inj.d")})[s] || String(s).slice(0, 3).toUpperCase();

/* The amber pill: the status where one is set, else IR for a player in an IR slot (the rosters in Edit say so). */
const tbPillHTML = p => p.injury || p.ir
  ? `<i class="tb-inj" title="${esc(p.injury || "IR")}">${esc(tbInjCode(p.injury || "IR"))}</i>` : "";

/* The perceived-value chips (option B, 2026-10-05): how the other manager is likely to price a player. Hot and Cold
   follow his last 2 games, Early pick is a round 1-3 draft pick. Small and flat, in tokens (--heat, --sky, neutral); a
   chip the file adds that the page does not know is left out. */
const tbChipsHTML = p => (p.chips || []).map(c => c === "Hot" ? `<i class="tb-chip hot" title="${t("lboard.chip.mark")}">${t("lboard.chip.hot")}</i>`
  : c === "Cold" ? `<i class="tb-chip cold" title="${t("lboard.chip.mark")}">${t("lboard.chip.cold")}</i>`
  : c === "Early pick" ? `<i class="tb-chip early">${t("lboard.chip.early")}</i>` : "").join("");

const tbWrapTags = s => s ? `<span class="tb-tags">${s}</span>` : "";

/* A roster row (Edit): the status pill, then the chips, after the name; nothing when there is neither. */
const tbTagsHTML = p => tbWrapTags(tbPillHTML(p) + tbChipsHTML(p));

/* An offer card's row: the pill beside the name as ever, and the chips on a line of their own under it, because a card's
   column is ~140px at 360px and a name plus two chips does not fit one line. The package in Edit shows no chips: the
   rosters under it do. */
function tbPlayerHTML(p){
  return `<li class="tb-p"><span class="lbp-pos" data-pos="${esc(p.pos)}">${esc(p.pos)}</span>
    <span class="tb-n" title="${esc(p.name)}">${esc(nameInitial(p.name))}</span>${tbPillHTML(p)}${tbWrapTags(tbChipsHTML(p))}</li>`;
}

/* "You drop: O. Gordon II": who the reader releases to stay at the roster cap, one quiet line. Nothing about the
   partner's roster: their room is theirs to manage. Initials, comma-separated. */
const tbNames = list => esc(list.map(p => nameInitial(p.name)).join(", "));
const tbDropHTML = drop => drop && drop.length ? `<p class="tb-drop">${t("lboard.offer.drop", {names: tbNames(drop)})}</p>` : "";

/* "To IR: C. Williams": who moves into an IR slot instead of being dropped, its own quiet line above the drop line. */
const tbIrHTML = moves => moves && moves.length ? `<p class="tb-ir">${t("lboard.offer.ir", {names: tbNames(moves)})}</p>` : "";

/* Both lines of an offer, IR first, each only when there is one. */
const tbRoomHTML = o => tbIrHTML(o.ir_moves) + tbDropHTML(o.drop);

/* The card's head: who the offer is with, and his record where the league has standings. */
function tbHeadHTML(o, lg){
  const tm = lg.teams.find(x => x.name === o.partner), rec = tm ? lbRecord(tm) : "";
  return `<header class="tb-ph"><b class="tb-pn" data-testid="finder-partner">${esc(o.partner)}</b>${
    rec ? `<small data-testid="finder-record">${rec}</small>` : ""}</header>`;
}

/* `i` is the card's place in the offers on screen (finder.js TF_SHOWN): Copy and Edit address it by that. An offer with
   lenses (2026-10-08, finder/lenses.js) shows both sides' judged gains and its nearest bye notes in place of the one
   rest-of-season gain; one without shows that gain, as it did. */
function tbCardHTML(o, i, lg, canEdit){
  const col = (label, rows) => `<div class="tb-col"><p class="tb-h">${label}</p><ul>${rows.map(tbPlayerHTML).join("")}</ul></div>`;
  const edit = canEdit ? `<button type="button" class="tb-copy" data-tbedit="${i}" data-testid="finder-edit">${t("lboard.offer.edit")}</button>` : "";
  const lgd = tbLeagueData(lg), lensed = !!(o.lenses && o.lens && lgd), me = lensed && tbMine(lg);
  const gain = lensed ? tfLensFootHTML(o, lgd, me ? me.name : null)
    : `<p class="tb-gain" data-testid="finder-gain" title="${t("lboard.offer.mark")}">${t("lboard.offer.gain", {n: `<b>+${lbNum(o.gain)}</b>`})}</p>`;
  return `<article class="tb-card" data-testid="finder-card">${tbHeadHTML(o, lg)}
    <div class="tb-cols">${col(t("lboard.offer.send"), o.send)}${col(t("lboard.offer.get"), o.get)}</div>${tbRoomHTML(o)}${lensed ? tfNotesHTML(o, lgd) : ""}
    <div class="tb-foot">${gain}
      <div class="tb-acts">${edit}<button type="button" class="tb-copy" data-tbcopy="${i}" data-testid="finder-copy">${t("lboard.offer.copy")}</button></div></div></article>`;
}

/* Shapes where the cards will be, so the page is the size it will be: a head, two columns of three bars, three cards. */
const tbSkelHTML = () => `<p class="tb-line" role="status">${t("lboard.offer.loading")}</p>` + [0, 1, 2].map(() =>
  `<div class="tb-card tb-skel" aria-hidden="true"><header class="tb-ph"><i></i></header><div class="tb-cols">${[0, 1].map(() =>
    `<div class="tb-col"><i></i><i></i><i></i></div>`).join("")}</div></div>`).join("");

const tbEmptyHTML = line => `<div class="state-empty tb-empty" data-testid="finder-empty"><b>${line}</b></div>`;

/* The date the offers were made, as "Oct 5": bookkeeping, at the bottom. */
const tbUpdated = () => t("lboard.offer.updated", {date: new Date(`${String(TB_DATA.updated).slice(0, 10)}T12:00:00`)
  .toLocaleDateString("en-US", {month: "short", day: "numeric"})});

/* The offer, as a message. The clipboard call is made inside the click, as browsers insist; where it is refused
   (an in-app browser, file://) the text shows in a box, selected, for the reader to copy by hand: in `host`, at
   its `where` ("beforeend" of a card, "afterbegin" of the edit state's foot). */
async function tbCopyText(btn, text, host, where){
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { /* the box below */ }
  if (!ok){
    let box = host.querySelector(".tb-box");
    if (!box) host.insertAdjacentHTML(where, `<textarea class="tb-box" readonly rows="5" aria-label="${t("lboard.offer.copyBox")}">${esc(text)}</textarea>`);
    box = host.querySelector(".tb-box");
    box.focus(); box.select();
    return;
  }
  btn.textContent = t("lboard.offer.copied");
  btn.classList.add("done");
  setTimeout(() => { if (btn.isConnected){ btn.textContent = t("lboard.offer.copy"); btn.classList.remove("done"); } }, 1600);
}
const tbCopy = btn => tbCopyText(btn, tbText(TF_SHOWN[+btn.dataset.tbcopy]), btn.closest(".tb-card"), "beforeend");
