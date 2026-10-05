/* ============================== DIGEST: AFTER KICKOFF ==============================
   2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV ("Digest after kickoff";
   David: "Sometimes something big happens like injury or top scores. The headline should change
   accordingly. Need to know and Highlights become old news on kickoff.").

   The Digest is the packet's until the week's first kickoff. From then it shares Live's poll
   (live.js): the headline is the week's top scorer so far, Highlights becomes Right now (the top
   five and a touchdown count), Need to know drops what has been played, and the last game of the
   week gets a card of its own (mnf.js). Every number here is GD_STATS.lead, league-wide and half-PPR,
   the same reply Live and the profile read; the page adds nothing to it. No live injury source
   exists yet, so the packet's hurt-starter lead stands only while no game is on and his own has not
   kicked off.

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

/* The banner while games are on: the top scorer, "Gibbs has 31.4 points", his line and the game's clock
   under it. Between windows the same man, in the past of the week. */
function dgLeadTop(top, playing){
  const slug = slugOf(top.n), name = esc(dgSurname(top.n));
  const pts = `<em class="dg-em go">${dgN1(top.pts)}</em>`;
  const by = [gdLine({pos: top.pos}, top.s), gdClockOf(top.team).label].filter(Boolean).map(esc).join(" · ");
  // Sleeper's code (LAR, WSH) is not always the colour table's (LA, WAS): take whichever spelling it has.
  const team = gdCodes(top.team).find(c => TEAM_COLOURS[c]) || top.team;
  return {tone: "go team", team, slug, name: top.n, live: {...top, slug}, photo: dgPhotoHTML(slug), ghost: esc(top.team),
          head: playing ? t("digest.live.has", {name, pts}) : t("digest.live.leads", {name, pts}), fact: by};
}

/* null leaves the packet's lead alone. */
function dgLeadLive(d){
  const now = Date.now(), w = dgWeek(now);
  if (!w.started || w.done) return null;
  const mnf = dgLeadMnf(now);
  if (mnf) return mnf;
  const top = dgLeaders()[0], playing = gdPlaying(now);
  if (!top) return null;
  // The packet's hurt starter (dgLeadAfter already dropped one whose game began) holds the banner
  // until a game is on: nothing live knows who got hurt since.
  if (!playing && d.lead && d.lead.rule === "hurt") return null;
  return dgLeadTop(top, playing);
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

/* Highlights from the first kickoff to the week's last final: the top five and the day's touchdowns,
   which open Live's TDs tab. "" outside live mode, so the packet's Highlights draws instead. */
function dgNowHTML(){
  if (!dgLiveMode(Date.now())) return "";
  const n = dgTdCount();
  return `<section class="dg-facts dg-now" data-dgnow aria-labelledby="dg-now-h">
    <h3 class="dg-sec" id="dg-now-h">${t("digest.live.title")}</h3>
    <ol class="dg-now-l">${dgLeaders().slice(0, DG_NOW_TOP).map(dgNowRow).join("")}</ol>
    ${n ? `<button type="button" class="dg-go dg-now-td" data-dgtds>${n === 1 ? t("digest.live.td1") : t("digest.live.tds", {n})}${DG_ARROW}</button>` : ""}</section>`;
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
  return [dgLiveMode(Date.now()), dgMnfSlot(Date.now()) !== null, dgLeadLive(d) !== null, dgNeedEmpty(d), d.hurt.length + d.starters.length].join("|");
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
  dgSwap(host.querySelector("[data-dgmnf]"), "mnf", dgMnfHTML());
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
  if (e.target.closest("[data-dgmgo]")){ morphLogo(); navGo("live"); window.scrollTo({top: 0}); }
}
