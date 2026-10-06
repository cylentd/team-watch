/* ============================== DIGEST: AFTER KICKOFF ==============================
   2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV ("Digest after kickoff";
   David: "Sometimes something big happens like injury or top scores. The headline should change
   accordingly. Need to know and Highlights become old news on kickoff.").

   The Digest is the packet's until the week's first kickoff. From then it shares Live's poll
   (live.js): the headline is the week's top scorer so far, Right now appears beside Need to know (the
   top five and a touchdown count; Highlights left the Digest on 2026-10-04), Need to know drops what has been played, and the last game of the
   week gets a card of its own (mnf.js). Every number here is GD_STATS.lead, league-wide and half-PPR,
   the same reply Live and the profile read; the page adds nothing to it. A fantasy-relevant player
   (QB/RB/WR/TE projected 8+) who left a game hurt, in any game (data/gameday/hurt.js, from ESPN's play
   text), takes the headline from the top score until he returns. Without that, the packet's
   hurt-starter lead stands only while no game is on and his own has not kicked off.

   Generic by rule (David, 2026-10-04: "The Digest is supposed to be GENERIC for the public. It
   shouldn't hone on to my roster or their roster."): nothing in surface/digest reads a league, a
   roster or a matchup after kickoff. Live is the personal view.

   Live parts repaint in place (paintDigestLive, called by live.js): a poll never rebuilds the page
   under a thumb. Only a change of phase (a new section appears or leaves) renders it again. */

const DG_NOW_TOP = 5;
const DG_TD_KEYS = ["rush_td", "rec_td"];   // a passing TD is the same score as the catch: counted once

const dgN1 = v => (Math.round(v * 10) / 10).toFixed(1);

/* The week's first kickoff has passed: the poll is worth starting (before it, nothing changes). */
const dgKicked = () => dgWeek(Date.now()).started;

/* Every player with a TD plus the week's top 25, best first. */
function dgLeaders(){
  const lead = (GD_STATS && GD_STATS.lead) || {};
  return Object.values(lead).filter(r => r && r.n && typeof r.pts === "number").sort((a, b) => b.pts - a.pts);
}

/* Live mode: games have begun, the week is not over, and the poll has told us who scored. */
function dgLiveMode(now){
  const w = dgWeek(now);
  return w.started && !w.done && dgLeaders().length > 0;
}

const dgLvAttrs = r => `data-dglv data-n="${esc(r.n)}" data-pos="${esc(r.pos)}" data-team="${esc(r.team)}" data-slug="${esc(r.slug || slugOf(r.n))}"`;

/* What the by-line adds to a head that prints his yards, TDs and 10+ catches (2026-10-05): the rest of
   his day (completions, carries, catches and targets, turnovers), never a number the head already
   shows; a part that shares one with the head is dropped. A scorer the head has no numbers for (a
   kicker, a defense) gets Live's whole line. */
function dgTopBy(top){
  const s = top.s || {}, n = k => +(s[k] || 0), head = dgTopLine(s);
  if (!head) return gdLine({pos: top.pos}, s);
  const seen = new Set(head.match(/\d+/g)), pass = n("pass_yd") > n("rush_yd") + n("rec_yd");
  const catches = n("rec_tgt") ? (n("rec") >= DG_BIG.catches ? t("digest.live.by.tgt", {n: n("rec_tgt")}) : t("live.line.rec", {r: n("rec"), g: n("rec_tgt")})) : "";
  const parts = pass ? [n("pass_att") ? t("live.line.cmp", {c: n("pass_cmp"), a: n("pass_att")}) : "",
      n("pass_int") ? t("live.line.int", {n: n("pass_int")}) : "", n("rush_att") ? t("live.line.car", {n: n("rush_att"), y: n("rush_yd")}) : ""]
    : [n("rush_att") ? t("live.line.carries", {n: n("rush_att")}) : "", catches];
  if (n("fum_lost")) parts.push(t("live.line.fl", {n: n("fum_lost")}));
  return parts.filter(p => p && !(p.match(/\d+/g) || []).some(x => seen.has(x))).join(" · ");
}

/* The banner while games are on: the top scorer, called like an announcer would (lead.js dgTopCall),
   what the call leaves out and the game's clock under it. Between windows the same man, in the past tense. */
function dgLeadTop(top, playing){
  const slug = slugOf(top.n), name = esc(dgSurname(top.n));
  const by = [dgTopBy(top), gdClockOf(top.team).label].filter(Boolean).map(esc).join(" · ");
  // Sleeper's code (LAR, WSH) is not always the colour table's (LA, WAS): take whichever spelling it has.
  const team = gdCodes(top.team).find(c => TEAM_COLOURS[c]) || top.team;
  return {tone: "go team", team, slug, name: top.n, live: {...top, slug}, photo: dgPhotoHTML(slug), ghost: esc(top.team),
          head: dgTopCall(top, playing && gdClockOf(top.team).state !== "post", name), fact: by};
}

/* A player left a game hurt and is not back (data/gameday/hurt.js): "B. Purdy left the game hurt"
   outranks the top score while games are on (2026-10-04). Any QB/RB/WR/TE the projections rate 8+, in
   any game. Several: the best projection. When he returns, GD_HURT clears him and the banner is the
   top scorer again. By-line: his club and the game's clock. */
function dgLeadLeft(){
  const h = gdHurtNow()[0];
  if (!h) return null;
  const by = [h.team, gdClockOf(h.team).label].filter(Boolean).map(esc).join(" · ");
  return {tone: "out", slug: h.slug, name: h.n, live: {n: h.n, pos: h.pos, team: h.team, slug: h.slug}, photo: dgPhotoHTML(h.slug),
          head: t("digest.hurt.head", {name: esc(dgShort(h.n)), hurt: `<em class="dg-em out">${t("digest.hurt.word")}</em>`}), fact: by};
}

/* The banner's order (2026-10-04): a game in play leads with the live hurt or top scorer; with no game
   on, Claude's story (lead.js dgLeadStory) when it is newer than the packet; else the rules below and
   then the packet's own lead. null leaves the packet's lead alone. */
function dgLeadLive(d){
  const now = Date.now(), w = dgWeek(now), on = w.started && !w.done;
  const top = on ? dgLeaders()[0] : null, playing = on && gdPlaying(now);
  if (playing){
    const left = dgLeadLeft();
    return left || (top ? dgLeadTop(top, true) : null);
  }
  const story = dgLeadStory(d);
  if (story) return story;
  if (!top) return null;
  // The packet's hurt starter (dgLeadAfter already dropped one whose game began) holds the banner
  // until a game is on: nothing live knows who got hurt since.
  if (d.lead && d.lead.rule === "hurt") return null;
  return dgLeadTop(top, false);
}

/* ---------------------------------------------------------------- Right now */

const dgTdCount = () => dgLeaders().reduce((n, r) => n + DG_TD_KEYS.reduce((m, k) => m + (+((r.s || {})[k]) || 0), 0), 0);

function dgNowRow(r){
  const slug = slugOf(r.n), line = gdLine({pos: r.pos}, r.s), clock = gdClockOf(r.team).label;
  return `<li><button type="button" class="dg-now-r" ${dgLvAttrs({...r, slug})}>
    <span class="dg-hd">${avatarHTML({n: r.n, slug})}</span>
    <span class="dg-now-t"><b>${esc(dgShort(r.n))}</b>
      <span class="dg-now-m"><span class="dg-now-pos">${esc(r.pos)}</span> ${esc(r.team)}${clock ? ` · ${esc(clock)}` : ""}</span>
      ${line ? `<span class="dg-now-s">${esc(line)}</span>` : ""}</span>
    <i class="dg-now-p">${dgN1(r.pts)}</i></button></li>`;
}

/* One who left the game hurt, in --down: the same row, "Hurt" where the points go. */
function dgHurtRow(h){
  const line = [h.pos, h.team, gdClockOf(h.team).label].filter(Boolean).map(esc).join(" · ");
  return `<li><button type="button" class="dg-now-r hurt" ${dgLvAttrs({n: h.n, pos: h.pos, team: h.team, slug: h.slug})}>
    <span class="dg-hd">${avatarHTML({n: h.n, slug: h.slug})}</span>
    <span class="dg-now-t"><b>${esc(dgShort(h.n))}</b><span class="dg-now-m">${line}</span></span>
    <i class="dg-now-p">${t("digest.hurt.row")}</i></button></li>`;
}

/* From the first kickoff to the week's last final: the top five and the day's touchdowns,
   which open Live's TDs tab. "" outside live mode, where nothing takes its place. Players who
   left a game hurt lead it, the best projections first (their own rows, so none is in the five as well). */
const DG_HURT_ROWS = 3;
/* Three rows, then More (2026-10-05, storyboard https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP): the
   rest opens in place, because the reader asked for it with a tap (STYLE.md "Layout"). The touchdown
   count already goes to Live's TDs tab, so More does not. The choice is kept while the page is open. */
const DG_NOW_SHOW = 3;
let DG_NOW_MORE = false;

function dgNowHTML(){
  if (!dgLiveMode(Date.now())) return "";
  const n = dgTdCount(), hurt = gdPlaying(Date.now()) ? gdHurtNow().slice(0, DG_HURT_ROWS) : [], out = new Set(hurt.map(h => h.slug));
  const top = dgLeaders().filter(r => !out.has(slugOf(r.n))).slice(0, DG_NOW_TOP);
  const rows = [...hurt.map(dgHurtRow), ...top.map(dgNowRow)], more = rows.length > DG_NOW_SHOW;
  return `<section class="dg-facts dg-now" data-dgnow aria-labelledby="dg-now-h">
    <h3 class="dg-sec" id="dg-now-h">${t("digest.live.title")}</h3>
    <ol class="dg-now-l">${(more && !DG_NOW_MORE ? rows.slice(0, DG_NOW_SHOW) : rows).join("")}</ol>
    <div class="dg-now-f">${more ? `<button type="button" class="dg-go dg-now-more" data-dgmore aria-expanded="${DG_NOW_MORE}">${DG_NOW_MORE ? t("digest.now.less") : t("digest.now.more")}</button>` : ""}
    ${n ? `<button type="button" class="dg-go dg-now-td" data-dgtds>${n === 1 ? t("digest.live.td1") : t("digest.live.tds", {n})}${DG_ARROW}</button>` : ""}</div></section>`;
}

/* Need to know is empty once games are on and nobody unplayed is hurt or new: it is not drawn. */
function dgNeedEmpty(d){
  if (!dgLiveMode(Date.now())) return false;
  const lead = d.lead && d.lead.rule === "hurt" && !dgLeadLive(d) ? d.hurt[d.lead.index] : null;
  return !d.starters.length && !d.hurt.some(r => r !== lead);
}

/* ---------------------------------------------------------------- painting */

/* What the page drew last, so a poll replaces a part only when its words changed. */
let DG_LAST = {};
let DG_DRAWN = "";
let DG_RENDERING = false;

/* The sections that exist; when it changes the view renders again, once. */
function dgPhaseKey(){
  const d = dgD();
  if (!d) return "";
  // The live lead is part of the key: the band is a data-dgslug button (wired once, at render) or a
  // data-dglv one (the page's one listener), so a swap between them must render again.
  // Tonight's card turns into the game's block at its kickoff (tonight.js), so each one's kickoff is part of the key too.
  const on = (d.tn || []).map(g => Date.parse(g.ko) <= Date.now() ? 1 : 0).join("");
  return [dgLiveMode(Date.now()), dgMnfSlot(Date.now()) !== null, dgLeadLive(d) !== null, dgNeedEmpty(d), d.hurt.length + d.starters.length, on].join("|");
}

function dgSwap(el, key, html){
  if (!el || !html || DG_LAST[key] === html) return;
  el.outerHTML = html;
  DG_LAST[key] = html;
}

/* live.js calls this after every poll. A no-op unless the Digest is the view on screen. */
function paintDigestLive(){
  if (SURFACE !== "digest") return;
  const host = document.querySelector("#view .dg");
  if (!host) return;
  if (dgPhaseKey() !== DG_DRAWN){
    if (DG_RENDERING) return;
    DG_RENDERING = true;
    const y = window.scrollY;
    try { render(); } finally { DG_RENDERING = false; }
    window.scrollTo(0, y);
    return;
  }
  dgSwap(host.querySelector(":scope > .dg-lead"), "lead", dgLeadHTML());
  dgSwap(host.querySelector("[data-dgnow]"), "now", dgNowHTML());
  // Each game's block (the last game's card, or Tonight's once it is on) repaints on its own, by its home club.
  const games = gdWeekGames();
  host.querySelectorAll("[data-dgblk]").forEach(el => {
    const g = games.find(x => x.home === el.dataset.dgblk);
    if (g) dgSwap(el, "blk." + g.home, dgMnfFor(g));
  });
}

/* One listener on the Digest's root, so a part replaced in place needs no wiring of its own. */
function dgLiveClick(e){
  const p = e.target.closest("[data-dglv]");
  if (p) return openProfile({n: p.dataset.n, pos: p.dataset.pos, team: p.dataset.team, slug: p.dataset.slug}, p);
  if (e.target.closest("[data-dgtds]")){
    gdSetTab("tds");    // Live's own setter: it keeps the tab in memory when localStorage will not answer
    morphLogo(); navGo("live"); window.scrollTo({top: 0});
    return;
  }
  const more = e.target.closest("[data-dgmore]");
  if (more){
    DG_NOW_MORE = !DG_NOW_MORE;
    const host = more.closest("[data-dgnow]"), html = dgNowHTML();
    DG_LAST.now = html; host.outerHTML = html;
    document.querySelector("[data-dgmore]")?.focus({preventScroll: true});
    return;
  }
  const blk = e.target.closest("[data-dgblk]");   // a game's block opens its sheet, the one Live's Games tab opens
  if (blk) gsOpen({event: blk.dataset.event, away: blk.dataset.away, home: blk.dataset.home}, blk);
}
