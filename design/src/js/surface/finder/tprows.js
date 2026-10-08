/* ============================== LEAGUE > TRADES: A PLAYER'S TRADE PAGE, ITS ROWS ==============================
   2026-10-08 (ledger #51, storyboard trades-pin draft B, frames 2-5). One row per package (Get) or per team (Send):
   what moves on the left, the reader's gain over the partner's on the right. A tap opens today's offer card under the
   row (lboard/tbcard.js, with Copy offer and Edit), one at a time. Send folds the teams with no offer into one line.
   A player with no row says why in one line. Nothing here is computed: the rows are data/tradepage.js's. */

/* "+38.4", "−1.2", "0.0", or a dash for a blank lens cell. */
const tpNum = g => g === null ? t("lboard.edit.none") : tbSigned(g);
const tpMood = g => g === null || g === 0 ? "flat" : g > 0 ? "up" : "neg";

/* Surnames for what the reader sends ("Pollard, Kittle, Goff"); initials for the rest, as the cards do. */
const tpSurnames = list => list.map(p => tbSurname(p.name)).join(", ");
const tpInitials = list => list.map(p => nameInitial(p.name)).join(", ");

/* Get: what the reader sends, then whoever else comes with him, or the shape of the deal when he comes alone. */
function tpGetWhat(o, slug){
  const also = o.get.filter(p => p.slug !== slug);
  const sub = also.length ? t("tradepage.get.also", {names: esc(tpInitials(also))}) : t("tradepage.get.for", {n: o.send.length});
  return {main: esc(tpSurnames(o.send)), sub};
}

/* Send: the team, then what the reader gets and what he adds to the shopped players. */
function tpSendWhat(o, slugs){
  const add = o.send.filter(p => !slugs.includes(p.slug));
  const sub = esc(tpInitials(o.get)) + (add.length ? ` · ${t("tradepage.send.add", {names: esc(tpSurnames(add))})}` : "");
  return {main: esc(o.partner), sub};
}

function tpRowHTML(o, i, ctx){
  const what = ctx.side === "get" ? tpGetWhat(o, ctx.slugs[0]) : tpSendWhat(o, ctx.slugs), g = tpGains(o), open = i === ctx.open;
  return `<li class="tpg-li${open ? " open" : ""}"><button type="button" class="tpg-row" data-tprow="${i}" aria-expanded="${open}" data-testid="tpg-row">
      <span class="tpg-what"><b data-testid="tpg-main">${what.main}</b><small data-testid="tpg-sub">${what.sub}</small></span>
      <span class="tpg-num" data-testid="tpg-gains"><b class="${tpMood(g.me)}">${tpNum(g.me)}</b><small>${tpNum(g.them)}</small></span>
      <svg class="tpg-chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg></button>
    ${open ? `<div class="tpg-card">${tbCardHTML(o, i, ctx.lg, ctx.edit)}</div>` : ""}</li>`;
}

/* The teams with no offer, as one line under the rows (David 2a). */
const tpNoneHTML = (names, two) => names.length ? `<li class="tpg-none" data-testid="tpg-none"><b>${esc(names.join(", "))}</b>
  <small>${two ? t("tradepage.none.two") : t("tradepage.none.one")}</small></li>` : "";

/* The list: its column heads, the rows, the folded line. */
function tpListHTML(found, ctx){
  const head = ctx.side === "get" ? t("tradepage.head.send") : t("tradepage.head.team");
  return `<div class="tpg-list" data-testid="tpg-list"><p class="tpg-lh"><span>${head}</span><span>${t("tradepage.head.gains")}</span></p>
    <ul>${found.rows.map((o, i) => tpRowHTML(o, i, ctx)).join("")}${tpNoneHTML(found.none || [], ctx.slugs.length > 1)}</ul></div>`;
}

/* The one line for a player with nothing: the pinned search's reason, or tonight's search missed him. Every key is
   spelled out: assemble --check finds keys by their literal lookups. */
function tpWhy(code, side, owner, two){
  const o = {owner: esc(owner || "")};
  const get = {namesake: () => t("tradepage.why.namesake", o), unpriced: () => t("tradepage.why.unpriced"),
    no_gain_for_you: () => t("tradepage.why.youLose"), no_gain_for_him: () => t("tradepage.why.heLoses", o),
    lens_gate: () => t("tradepage.why.lens"), no_legal_drop: () => t("tradepage.why.noDrop"), today: () => t("tradepage.why.getToday")};
  const send = {...get, namesake: () => t("tradepage.why.sendNamesake"), no_gain_for_him: () => t("tradepage.why.theyLose"),
    today: () => two ? t("tradepage.why.sendTodayTwo") : t("tradepage.why.sendToday")};
  const line = (side === "get" ? get : send)[code] || (side === "get" ? get : send).today;
  return `<div class="state-empty tb-empty tpg-why" data-testid="tpg-why"><b>${line()}</b></div>`;
}

/* Shapes where the rows will be while the files load, so the page is the size it will be. */
const tpSkelHTML = () => `<p class="tb-line" role="status">${t("lboard.offer.loading")}</p><div class="tpg-list tpg-skel" aria-hidden="true"><ul>${
  [0, 1, 2].map(() => `<li class="tpg-li"><span class="tpg-row"><i></i><i></i></span></li>`).join("")}</ul></div>`;
