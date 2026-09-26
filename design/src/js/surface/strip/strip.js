/* ------------------------------------------------------------------
   STRIP — a drive, acted out. The panel and the paint.

   It takes what /api/game returns and nothing else, which is why the same component serves both
   ways in: Gameday opens it at the drive being played, a game log opens it at a week's game. A
   finished game and a live one arrive in the same shape, so there is no second code path.

   `t` counts finished plays: t = 3 is play 3 just ended, t = 3.5 is halfway through play 4. Every
   paint is a pure function of (t, hold), so the scrubber, the Play button and a resize all reach
   the same picture by the same road.
------------------------------------------------------------------ */

const ST_PLAY_ICON = '<svg class="stic" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 1l8 5-8 5z"/></svg>';
const ST_PAUSE_ICON = '<svg class="stic" viewBox="0 0 12 12" aria-hidden="true"><path d="M2 1.5h3v9H2zM7 1.5h3v9H7z"/></svg>';
const ST_ARC = '<path d="M1 9Q9 -5 17 9"/>';

/* Every copy key below is spelled out in full. assemble.py --check finds an orphaned key by
   scanning for literal lookups, and cannot see one assembled from a template. */
function stripPanelHTML(){
  const arc = cls => `<svg class="${cls}" viewBox="0 0 18 10" aria-hidden="true">${ST_ARC}</svg>`;
  return '<div class="stfilt"></div>'
    + '<div class="stgrid"><div class="stmain">'
    + '<div class="stscorerow"><div class="stscore"></div><div class="stclock"></div></div>'
    + '<div class="stbox"><div class="stview" data-phone="pan"><div class="ststage"></div></div><div class="stslam"></div></div>'
    + '<div class="stcap"></div>'
    + '<div class="stscrub">'
    + `<button type="button" class="stplay" aria-pressed="false"></button>`
    + `<button type="button" class="stprev" aria-label="${esc(t("strip.control.prev"))}">&lsaquo;<span class="stw"> ${t("strip.control.prev")}</span></button>`
    + `<input type="range" class="stslider" min="0" max="1" step="0.01" value="1" aria-label="${esc(t("strip.control.scrub"))}">`
    + `<button type="button" class="stnext" aria-label="${esc(t("strip.control.next"))}"><span class="stw">${t("strip.control.next")} </span>&rsaquo;</button>`
    + `<button type="button" class="stmode" aria-label="${esc(t("strip.control.view"))}">${t("strip.view.pan")}</button>`
    + "</div>"
    + '<div class="stkeyrow"><div class="stkey">'
    + `<span><i class="k-run"></i>${t("strip.key.run")}</span>`
    + `<span><i class="k-loss"></i>${t("strip.key.loss")}</span>`
    + `<span>${arc("k-pass")}${t("strip.key.pass")}</span>`
    + `<span>${arc("k-inc")}${t("strip.key.inc")}</span></div></div>`
    + `</div><div class="stlistbox"><ol class="stlist" aria-label="${esc(t("strip.list.label"))}"></ol></div></div>`;
}

function stUi(host){
  const q = s => host.querySelector(s);
  return {host, filt: q(".stfilt"), list: q(".stlist"), main: q(".stmain"), box: q(".stbox"),
          score: q(".stscore"), clock: q(".stclock"), view: q(".stview"),
          stage: q(".ststage"), slam: q(".stslam"), cap: q(".stcap"), slider: q(".stslider"),
          play: q(".stplay"), mode: q(".stmode")};
}

/* A moment is something the feed states outright -- a score, a pick, a gain of 20 or more -- never
   something inferred. It dims the field and speaks from its centre: tried above the field first,
   where it overlapped the play at a narrow window and had nowhere to go at all on a phone. */
function stMoment(p, dir){
  const gain = (p.to - p.from) * dir;
  if (p.td) return {txt: gain >= 20 ? t("strip.moment.tdLong", {n: gain}) : t("strip.moment.td")};
  if (p.k === "fg") return {txt: p.made ? t("strip.moment.fg") : t("strip.moment.fgMissed"), cls: p.made ? "" : " bad"};
  if (p.k === "int") return {txt: t("strip.moment.int"), cls: " bad"};
  if (p.fum && p.fum.lost) return {txt: t("strip.moment.fumble"), cls: " bad"};
  if (p.k !== "inc" && gain >= 20){
    /* whichever half of the gain is bigger gets named; a tie goes to the air yards, the flashier
       number. One line only -- the band has room for a headline and a tag, not two sentences. */
    let sub = "";
    if (p.k === "pass" && p.yac != null){
      const air = gain - p.yac;
      sub = air >= p.yac ? t("strip.moment.air", {n: air}) : t("strip.moment.yac", {n: p.yac});
    }
    return {txt: t("strip.moment.big", {n: gain}), sub, cls: " minor"};
  }
  return null;
}

/* "BUF 38" from a point on the absolute 0-100 field. Which side of 50 it is on decides the name,
   and the number counts back down from midfield the way the painted ones do. */
function stSpot(yl, home, away){
  const n = Math.round(yl);
  return n < 50 ? `${home} ${n}` : n > 50 ? `${away} ${100 - n}` : t("strip.spot.fifty");
}

/* ESPN opens a lot of play texts with a formation note or a substitution, and both are noise here:
   the strip already shows the passer dropping back, and nobody is reading a drive replay to learn
   who reported in as eligible. Dropping them is worth a wrapped line on a phone, which the caption
   box pays for twice -- once in the line itself, and once in the floor every other play then sits
   above. (api/game.py strips the same prefixes for a different reason: to find the name.) */
const ST_PREFIX = /^\((?:Shotgun|No Huddle|No Huddle, Shotgun|Field Goal formation|Punt formation)\)\s*/;
const ST_ELIGIBLE = /^[^.]*reported in as eligible\.\s*/;
const stPlayText = tx => String(tx || "").replace(ST_ELIGIBLE, "").replace(ST_PREFIX, "");

function stCaption(ctl, p, over, dr = ctl.drive){
  const c = over ? dr.end : p;
  const who = p.who || t("strip.unnamed");
  const from = p.qb ? ` <small>${t("strip.caption.from", {qb: esc(p.qb)})}</small>` : "";
  const yac = !over && p.k === "pass" && p.yac != null
    ? `<span class="styac">${t("strip.caption.caught",
        {spot: stSpot(p.to - p.yac * dr.dir, ctl.home, ctl.away), n: p.yac})}</span>` : "";
  return `<span class="stfaces">${p.qb ? stFace(p.qb, ctl.faces[p.qb], " sm") : ""}${stFace(who, ctl.faces[p.who])}</span>`
    + `<span class="stnm">${esc(who)}${from}</span><span class="stdd">${esc(c.dd || "")}</span>`
    + `<span class="sttx">${esc(stPlayText(c.tx))}</span>${yac}`;
}

/* The caption box's floor: the tallest caption of THIS reel, laid out at the real width in the
   real fonts, measured in the reader's own browser. A hardcoded pixel floor was right in one
   headless Chromium and wrong on the phone it was meant for. The whole reel, not the drive on
   the field: a replay that crosses drives would otherwise jump at every change of possession. */
function stFitCap(ctl){
  const cap = ctl.ui.cap, probe = cap.cloneNode(false);
  probe.style.cssText = `position:absolute;visibility:hidden;pointer-events:none;min-height:0;width:${cap.clientWidth}px`;
  cap.parentNode.appendChild(probe);
  let h = 0;
  const fit = html => { probe.innerHTML = html; h = Math.max(h, probe.offsetHeight); };
  const reel = ctl.reel || ctl.plays.map((p, i) => ({d: ctl.at, i}));
  reel.forEach(s => {
    const dr = ctl.data.drives[s.d], p = dr.plays[s.i];
    fit(stCaption(ctl, p, false, dr));
    if (s.i === dr.plays.length - 1) fit(stCaption(ctl, p, true, dr));
  });
  probe.remove();
  cap.style.minHeight = h + "px";
}

function stScoreHTML(ctl, score, turned){
  /* the words sit in their own element so a phone can take them out of the flow entirely and
     leave a 7px lime square -- hiding a text node in place leaves its width behind */
  const poss = side => side ? ` <span class="stposs"><i>${t("strip.score.hasBall")}</i></span>` : "";
  const home = ctl.drive.dir > 0;
  return `<span><strong class="sthome">${esc(ctl.home)} ${score[0]}</strong>${poss(home !== turned)}</span>`
    + `<span><strong class="staway">${esc(ctl.away)} ${score[1]}</strong>${poss(home === turned)}</span>`;
}

/* One drive onto the field. Rebuilds the stage, so anything cached against the old layout goes.
   `quiet` is the reel changing drive under a seek, which paints the frame itself; without it the
   drive is shown finished, the way it was opened before there was a reel. */
function stShowDrive(ctl, i, quiet){
  if (!quiet) stStop(ctl);
  const was = ctl.at;
  ctl.at = i;
  ctl.drive = ctl.data.drives[i];
  ctl.plays = ctl.drive.plays;
  ctl.n = ctl.plays.length;
  ctl.shown = -2; ctl.fired = -1; ctl.lastScore = "";
  ctl.ui.stage.className = "ststage" + (ctl.drive.dir < 0 ? " rev" : "");
  ctl.ui.stage.innerHTML = stStageHTML(ctl.drive, "s" + i, ctl.data.home.abbr, ctl.data.away.abbr);
  ctl.pose = stBind(ctl.ui.stage, ctl.drive, "s" + i, ctl.faces);
  ctl.pose.mark(ctl.sel && ctl.sel.me ? ctl.sel.who : null);
  ctl.ahead = ctl.ui.stage.querySelector(".stahead");
  ctl.ltg = ctl.ui.stage.querySelector(".stltg");
  ctl.turf = ctl.ui.stage.querySelector(".stturf");
  ctl.ui.slam.className = "stslam";
  /* a new possession while playing arrives from the side it will attack from, so the change of
     drive reads as one; a scrub rebuilds in place, since the hand is already saying where it is */
  if (quiet && ctl.playing && was != null && was !== i && !ST_REDUCED){
    ctl.ui.stage.animate([{opacity: 0, translate: `${-4 * ctl.drive.dir}% 0`}, {opacity: 1, translate: "0 0"}],
      {duration: 460, easing: getComputedStyle(ctl.ui.stage).getPropertyValue("--spring").trim() || "ease-out"});
  }
  if (!quiet){ ctl.ui.slider.max = ctl.n; stFitCap(ctl); stRender(ctl, ctl.n); }
}

/* One frame. Everything below reads (t, hold) and nothing else, so scrubbing and playing agree. */
function stRender(ctl, tm, hold = 1){
  const n = ctl.n, i = tm <= 0 ? 0 : Math.min(Math.ceil(tm) - 1, n - 1);
  const f = tm <= 0 ? 0 : tm - i, p = ctl.plays[i], done = f >= 1, over = tm >= n && hold >= 1;
  /* the clock every loop on the field is positioned by (field.css, --clock) */
  ctl.ui.stage.style.setProperty("--ph", (performance.now() / 1000).toFixed(3));
  const x = ctl.pose(i, f, hold, over);
  /* the chevrons fill the ground between the ball and the end zone this drive is heading for --
     which is the LEFT one on an away drive, because the field never flips */
  const back = ctl.drive.dir < 0;
  ctl.ahead.style.left = back ? "0" : `calc(${x}% + 20px)`;
  ctl.ahead.style.right = back ? `calc(${100 - x}% + 20px)` : "0";
  stKeepInView(ctl, x);
  /* possession has changed hands: the chevrons go and the threat is at the other end */
  const turned = done && (p.k === "int" || (!!p.fum && p.fum.lost && hold >= .55) || (!!p.turnover && p.k !== "fg"));
  ctl.ltg.style.left = (p.line == null ? 0 : p.line) + "%";
  ctl.ltg.style.display = p.line != null && p.line < 100 && p.line > 0 && !(over && p.td) && !turned ? "" : "none";
  const tgt = ctl.ui.stage.querySelector(".stez.tgt");
  if (tgt) tgt.classList.toggle("scored", (!!p.td || (p.k === "fg" && p.made)) && done);
  ctl.ui.stage.classList.toggle("turnover", turned);
  stSlam(ctl, p, i, done, hold);
  stScore(ctl, p, done, over, turned);
  const key = over ? -1 : i;
  if (key !== ctl.shown){ ctl.shown = key; ctl.ui.cap.innerHTML = stCaption(ctl, p, over); }
}

/* The moment fires once, on the beat after the play it belongs to, and is cut short by leaving
   that play rather than being allowed to run on over the next one. */
function stSlam(ctl, p, i, done, hold){
  const slam = ctl.ui.slam, m = stMoment(p, ctl.drive.dir);
  if (m && done && hold < 1 && ctl.fired !== i && !ST_REDUCED){
    ctl.fired = i;
    slam.innerHTML = `<span>${esc(m.txt)}${m.sub ? `<small>· ${esc(m.sub)}</small>` : ""}</span>`;
    slam.className = "stslam" + (m.cls || "");
    void slam.offsetWidth;
    slam.classList.add("on");
  }
  if (!(done && ctl.fired === i)) slam.classList.remove("on");
  if (!done && ctl.fired === i) ctl.fired = -1;
}

function stScore(ctl, p, done, over, turned){
  const was = ctl.drive.score, sc = (p.td && done) || over ? ctl.drive.end.score : was;
  const scoreKey = sc.join("-") + turned, key = scoreKey + "@" + (p.clock || ctl.drive.clock);
  if (key === ctl.lastScore) return;
  /* only the score's own part of the key decides the pop: a clock tick after a score has already
     landed must not replay the animation on every later play */
  const moved = ctl.lastScore && scoreKey !== ctl.lastScore.split("@")[0];
  ctl.lastScore = key;
  ctl.ui.score.innerHTML = stScoreHTML(ctl, sc, turned);
  /* whichever side's number actually changed is the one that pops -- an away drive scores too */
  const side = sc[0] !== was[0] ? ".sthome" : sc[1] !== was[1] ? ".staway" : null;
  if (moved && side) ctl.ui.score.querySelector(side).classList.add("bumped");
  ctl.ui.clock.textContent = p.clock || ctl.drive.clock || "";
}
