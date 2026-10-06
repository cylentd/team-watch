/* ============================== RECAP: PLAYERS ==============================
   The Players tab, three cards (Material's rule, DESIGN.md "Cards": one card per subject, rows inside):
   Leaders (each position's top three, then K and DST), Smashed / Busts / Left hurt (ff-jarvis's own
   picks, the Digest's lists), and Touchdowns. A row is two things: the name over his day, and the
   points. Faces stay in the banner; a list scans by name. */

const WR_POS = ["QB", "RB", "WR", "TE"];

/* One leader: name over his day, points at the right. A kicker's day is his box line, a defense's
   too; a defense has no page to open. */
function wrLeaderRow(r){
  const day = r.line !== undefined ? dgStatLine(r) : esc(r.box || "");
  const body = `<b class="wr-n">${esc(r.pos === "DST" ? r.n : dgShort(r.n))}</b><i class="wr-pts">${r.actual.toFixed(1)}</i>
    <span class="wr-day" data-testid="recap-day">${day}</span>`;
  return wrCanOpen(r.slug) ? `<button type="button" class="wr-r" data-testid="recap-leader" data-wrslug="${esc(r.slug)}">${body}</button>`
    : `<div class="wr-r" data-testid="recap-leader">${body}</div>`;
}

function wrLeadersHTML(d){
  const blocks = [...WR_POS.map(p => [p, d.stars.filter(r => r.pos === p)]), ["K", d.k], ["DST", d.dst]]
    .filter(([, rows]) => rows.length);
  if (!blocks.length) return "";
  return `<section class="wr-card wr-leaders" data-testid="recap-leaders"><h3 class="wr-ch">${t("weekrecap.leaders.title")}</h3>
    <div class="wr-board" data-testid="recap-board">${blocks.map(([p, rows]) =>
      `<div class="wr-bp" data-testid="recap-pos"><h4 data-testid="recap-pos-head">${p}</h4>${rows.map(wrLeaderRow).join("")}</div>`).join("")}</div></section>`;
}

/* The two numbers of a row: what he scored over what we projected, the projection dim. A player hurt
   before he scored has only the projection (the Digest's lists do the same). */
const wrNums = r => `<span class="wr-nums">${r.actual != null ? `<b>${r.actual.toFixed(1)}</b>` : ""}${
  r.proj != null ? `<span>${r.proj.toFixed(1)}</span>` : ""}</span>`;

function wrListRow(r, left){
  const day = left
    ? [esc(r.team), r.injury ? esc(r.injury.charAt(0).toUpperCase() + r.injury.slice(1)) : "", esc(r.later || r.rest || "")]
    : [esc(r.team), dgStatLine(r)];
  return `<button type="button" class="wr-lr" data-wrslug="${esc(r.slug)}"><span class="wr-ln"><b>${esc(dgShort(r.n))}</b>
    <span>${day.filter(Boolean).join(" · ")}</span></span>${wrNums(r)}</button>`;
}

/* Three lists. A phone shows one under a tab bar (the count in the list's colour); from 960px all three
   sit side by side under their headings and the bar is gone (players.css). A list with nobody in it
   draws no tab and no column. */
function wrListsHTML(d){
  const lists = [["smashed", t("weekrecap.lists.smashed"), d.smashed, "up", false],
    ["busts", t("weekrecap.lists.busts"), d.busts, "dn", false],
    ["left", t("weekrecap.lists.left"), d.left_hurt, "am", true]].filter(l => l[2].length);
  if (!lists.length) return "";
  const on = lists.some(l => l[0] === WR_LIST) ? WR_LIST : lists[0][0];
  const tab = ([k, label, rows, tone]) => `<button type="button" class="wr-lt" data-testid="recap-list-tab" data-wrlist="${k}" aria-pressed="${k === on}">${label}
    <em class="${tone}" data-testid="recap-list-count">${rows.length}</em></button>`;
  const panel = ([k, label, rows, tone, left]) => `<div class="wr-lp" data-testid="recap-list-panel" data-wrpanel="${k}"${k === on ? "" : " data-off"}>
    <h4 class="wr-lh ${tone}" data-testid="recap-list-head">${label}<em>${rows.length}</em></h4>${rows.map(r => wrListRow(r, left)).join("")}</div>`;
  return `<section class="wr-card wr-lists" data-testid="recap-lists"><div class="wr-ltabs" data-testid="recap-list-tabs" role="group" aria-label="${t("weekrecap.lists.label")}">${lists.map(tab).join("")}</div>
    <div class="wr-lps">${lists.map(panel).join("")}</div></section>`;
}

/* Touchdowns: a dot per rushing, receiving or return score, the top five then Show all. Passing TDs
   are one line under the list, since a pass and its catch are the same score. */
const wrTdN = n => n === 1 ? t("weekrecap.td.n1") : t("weekrecap.td.n", {n});

function wrPassNote(d){
  const most = Math.max(0, ...d.tds.map(r => r.pass_td || 0));
  const names = d.tds.filter(r => most && r.pass_td === most).map(r => esc(dgShort(r.n)));
  if (!names.length) return "";
  return names.length === 1 ? t("weekrecap.td.pass1", {name: names[0], n: most}) : t("weekrecap.td.pass", {names: names.join(", "), n: most});
}

function wrTdsHTML(d){
  const rows = wrTdRows(d);
  if (!rows.length) return "";
  const shown = WR_TDS_ALL ? rows : rows.slice(0, 5), note = wrPassNote(d);
  const row = r => `<button type="button" class="wr-lr" data-testid="recap-td-row" data-wrslug="${esc(r.slug)}"><span class="wr-ln"><b>${esc(dgShort(r.n))}</b>
    <span>${esc(r.pos)} · ${esc(r.team)}</span></span><span class="wr-dots" data-testid="recap-td-dots" role="img" aria-label="${wrTdN(wrDots(r))}">${"<i></i>".repeat(wrDots(r))}</span></button>`;
  return `<section class="wr-card wr-tds" data-testid="recap-tds"><h3 class="wr-ch">${t("weekrecap.td.title")}</h3>
    <div class="wr-tdl" data-testid="recap-td-list">${shown.map(row).join("")}</div>
    ${rows.length > 5 ? `<button type="button" class="wr-more" data-testid="recap-td-more" data-wrtds aria-expanded="${WR_TDS_ALL}">${
      WR_TDS_ALL ? t("weekrecap.td.fewer") : t("weekrecap.td.all", {n: rows.length})}</button>` : ""}
    ${note ? `<p class="wr-foot" data-testid="recap-td-note">${note}</p>` : ""}</section>`;
}

const wrPlayersHTML = d => wrLeadersHTML(d) + wrListsHTML(d) + wrTdsHTML(d);
