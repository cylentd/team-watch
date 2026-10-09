/* ============================== MATCHUPS: THE LINEUP CARD ==============================
   The view's first card (ledger #94, draft A, David 2026-10-09: the first card has to answer the reader's
   question, "who do I start?"). His own starters and bench, each with our projection and our call on him, and
   our one swap on top, worded as our call ("We'd start ..."), never an order: the page is not linked to his
   fantasy app (David, 2026-10-09). The swap is the picker's own verdict on the pair the roster brief names
   (ssClosest, ssVerdict), so the card and Compare the two never disagree. data/lineup.js shapes it; this draws.
   A reader with no team picked gets a card that asks for one, with Compare two beside it. */

/* His lineup and our swap, or null when he has no team (or a team with no roster we can read). */
function muLineupNow(){
  const team = ssTeam();
  if (!team) return null;
  const roster = ssRoster(team);
  const pts = Object.fromEntries(roster.map(p => [p.slug, ssPts(p.slug)]));
  const off = (typeof LIVE_RANKS !== "undefined" && LIVE_RANKS && LIVE_RANKS.off) || [];
  const lineup = muLineup(roster, pts, LIVE_SS3.calls || {}, off);
  const pair = ssClosest().map(p => p.slug);
  return {lineup, pair, swap: muSwap(pair, pair.length === 2 ? ssVerdict(ssColsOf(pair)) : null)};
}

/* Every copy key spelled out: assemble.py --check finds a key only as a literal lookup. */
const muSwapWord = (kind, who) => kind === "swap" ? t("matchups.lineup.swap", who) : kind === "flip" ? t("matchups.lineup.flip", who) : t("matchups.lineup.keep");
const muCallWord = c => c === "SMASH" ? t("matchups.call.smash") : c === "SIT" ? t("matchups.call.sit") : t("matchups.call.start");

/* The answer: one line of our call, the gain beside it, and the way into the two side by side. */
function muSwapHTML(now){
  const s = now.swap, all = [...now.lineup.starters, ...now.lineup.bench];
  const name = slug => esc(nameInitial((all.find(r => r.slug === slug) || {n: slug}).n));
  const cmp = `<button type="button" class="mu-sw-cmp" data-testid="matchups-swap-compare" data-mucmp>${s ? t("matchups.lineup.compare") : t("matchups.compare.link")}</button>`;
  if (!s) return `<div class="mu-sw keep" data-testid="matchups-swap" data-muswap="none"><span class="mu-sw-w">
    <b data-testid="matchups-swap-word">${t("matchups.lineup.keep")}</b></span><span class="mu-sw-g" data-testid="matchups-swap-gain"></span>${cmp}</div>`;
  const who = {a: name(s.in), b: name(s.out)};
  const sub = s.kind === "keep" ? `<span data-testid="matchups-swap-sub">${t("matchups.lineup.keepSub", who)}</span>` : "";
  const gain = s.kind === "flip" ? `<b>${s.gap.toFixed(1)}</b><span>${t("matchups.lineup.apart")}</span>`
    : s.gap > 0 ? `<b>${t("startsit.pick.gap", {n: s.gap.toFixed(1)})}</b><span>${t("matchups.lineup.pts")}</span>` : "";
  const face = all.find(r => r.slug === s.in);
  return `<div class="mu-sw ${s.kind}" data-testid="matchups-swap" data-muswap="${s.kind}">
    <span class="xf-head mu-sw-hd">${avatarHTML({n: face ? face.n : s.in, slug: s.in})}</span>
    <span class="mu-sw-w"><b data-testid="matchups-swap-word">${muSwapWord(s.kind, who)}</b>${sub}</span>
    <span class="mu-sw-g" data-testid="matchups-swap-gain">${gain}</span>${cmp}</div>`;
}

/* One 52px row: the slot, a head, the name over his game, our call, our points. On a swap the one we'd start
   is tinted green and the one he'd sit for dimmed; the swap line above names both. */
function muLineupRowHTML(r, s){
  const mark = s && s.kind === "swap" ? (r.slug === s.in ? "in" : r.slug === s.out ? "out" : "") : "";
  const rk = ssRank(r.slug);
  const game = rk && rk.opp ? muVs(rk) : esc(r.team || "");
  const pts = r.bye ? t("matchups.lineup.bye") : r.pts === null ? "—" : r.pts.toFixed(1);
  const tag = r.call ? `<span class="mu-tag ${r.call.toLowerCase()}">${muCallWord(r.call)}</span>` : "";
  return `<li><button type="button" class="mu-lu${mark ? " " + mark : ""}" data-testid="matchups-lineup-row" data-mulu="${esc(r.slug)}"${mark ? ` data-mumark="${mark}"` : ""}>
    <span class="mu-lu-slot">${esc(r.slot === "BN" ? r.pos : slotLabel(r.slot))}</span><span class="xf-head mu-hd">${avatarHTML({n: r.n, slug: r.slug})}</span>
    <span class="mu-nm"><b>${esc(nameInitial(r.n))}</b><span>${game}</span></span>
    <span class="mu-lu-tag">${tag}</span><span class="mu-lu-pts${r.bye || r.pts === null ? " dim" : ""}">${pts}</span></button></li>`;
}

function muLineupHTML(){
  const now = muLineupNow();
  if (!now || !now.lineup.starters.length) return muNoTeamHTML();
  const wk = schedWeek();
  const rows = (g, list) => `<ul class="mu-lu-l" data-mugroup="${g}">${list.map(r => muLineupRowHTML(r, now.swap)).join("")}</ul>`;
  return `<section class="mu-card mu-lineup" data-testid="matchups-lineup" aria-label="${t("matchups.lineup.title")}">
    <h3 class="mu-ch"><span>${t("matchups.lineup.title")}</span><span class="mu-ck">${wk ? t("startsit.pick.week", {n: wk}) + " · " : ""}${t("matchups.lineup.cols")}</span></h3>
    ${muSwapHTML(now)}${rows("starters", now.lineup.starters)}
    ${now.lineup.bench.length ? `<h4 class="mu-grp">${t("matchups.lineup.bench")}</h4>${rows("bench", now.lineup.bench)}` : ""}</section>`;
}

/* No team picked: what the card would answer, the way to pick one, and Compare two for any pair. */
function muNoTeamHTML(){
  return `<section class="mu-card mu-lineup none" data-testid="matchups-noteam" aria-label="${t("matchups.lineup.title")}">
    <h3 class="mu-ch"><span>${t("matchups.lineup.title")}</span></h3>
    <p class="mu-nt" data-testid="matchups-noteam-line">${t("matchups.lineup.none")}</p>
    <div class="mu-nt-b"><button type="button" class="mu-nt-pick" data-testid="matchups-noteam-pick" data-mupick>${t("matchups.lineup.pick")}</button>
    <button type="button" class="mu-sw-cmp" data-testid="matchups-noteam-compare" data-sscmp>${t("matchups.compare.link")}</button></div></section>`;
}

/* Compare the two: the picker opens on the card's pair, whatever was picked before. */
function muCompareSwap(){
  const now = muLineupNow();
  if (now && now.pair.length === 2){ SS_PICKS = now.pair; SS_OPEN = false; SS_Q = ""; ssSave(); }
  ssCmpOpen();
}

/* Pick your team: the team switch on screen (the header bar's on a phone, the bar's on a desktop) opens. */
function muOpenSwitch(){
  const btn = [...document.querySelectorAll("[data-tsbtn]")].find(b => b.offsetParent !== null);
  if (btn) btn.click();
}
