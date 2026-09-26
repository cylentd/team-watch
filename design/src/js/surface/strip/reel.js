/* ------------------------------------------------------------------
   STRIP REEL — which plays the transport runs through, and the list that names them.

   A reader arrives from a game log with one of three questions: show me the game, show me a
   quarter, show me my player. So the unit the transport steps through is not a drive but a reel:
   the plays a selection covers, in game order, as {d, i} (drive, play within it). The field still
   draws one drive at a time -- that is what its geometry is built on -- and changes drive when
   the reel crosses into the next one.

   `T` is the reel's own clock, counted like the drive's `t`: T = 3 is the reel's third play just
   ended. stSeek turns it into (drive, t) and is the only road to the picture.
------------------------------------------------------------------ */

/* the quarter a play belongs to, from its own clock ("Q2 8:58"); 5 is overtime */
const stQuarter = p => +((/^Q(\d)/.exec(p.clock || "") || [0, 0])[1]);
const stInvolves = (p, who) => !!who && (p.who === who || p.qb === who);

function stReelOf(data, sel){
  const out = [];
  data.drives.forEach((dr, d) => dr.plays.forEach((p, i) => {
    if ((!sel.q || stQuarter(p) === sel.q) && (!sel.me || stInvolves(p, sel.who))) out.push({d, i});
  }));
  return out;
}

const stSegAt = (ctl, T) => T <= 0 ? 0 : Math.min(Math.ceil(T) - 1, ctl.reel.length - 1);
const stPlayOf = (ctl, s) => ctl.data.drives[s.d].plays[s.i];

/* Every copy key is spelled out in full, for assemble.py --check. */
const stQName = q => q === 1 ? t("strip.list.q1") : q === 2 ? t("strip.list.q2")
  : q === 3 ? t("strip.list.q3") : q === 4 ? t("strip.list.q4") : t("strip.list.ot");
const stQTab = q => q > 4 ? t("strip.filter.ot") : t("strip.filter.q", {n: q});

/* The one row of controls: the game or one quarter, and the player the reader came from. The
   player chip stacks with a quarter ("his Q2"), which is why it is a toggle and not a sixth tab. */
function stFiltHTML(ctl){
  const qs = [...new Set(ctl.data.drives.flatMap(dr => dr.plays.map(stQuarter)))].filter(Boolean).sort();
  const tab = (q, label) => `<button type="button" data-q="${q}">${label}</button>`;
  const who = ctl.sel.who, mine = who && ctl.data.drives.some(dr => dr.plays.some(p => stInvolves(p, who)));
  const chip = mine ? `<button type="button" class="stme" aria-pressed="false">${stFace(who, ctl.faces[who], " xs")}`
    + `<span>${esc(who)}</span><em></em></button>` : "";
  return `<div class="stqs" role="group" aria-label="${esc(t("strip.filter.label"))}">`
    + tab(0, t("strip.filter.game")) + qs.map(q => tab(q, stQTab(q))).join("") + "</div>" + chip;
}

/* A quarter the player never touched the ball in is greyed rather than hidden, so the row keeps
   its shape when the chip is toggled. */
function stPaintFilt(ctl){
  const {q, me, who} = ctl.sel, all = ctl.data.drives.flatMap(dr => dr.plays);
  ctl.ui.filt.querySelectorAll("[data-q]").forEach(b => {
    const bq = +b.dataset.q;
    b.setAttribute("aria-pressed", String(bq === q));
    b.disabled = !!me && !!bq && !all.some(p => stQuarter(p) === bq && stInvolves(p, who));
  });
  const chip = ctl.ui.filt.querySelector(".stme");
  if (!chip) return;
  chip.setAttribute("aria-pressed", String(!!me));
  chip.querySelector("em").textContent = all.filter(p => (!q || stQuarter(p) === q) && stInvolves(p, who)).length;
}

/* What a row says happened: the result a drive chart would print, in the colour the field uses. */
function stResult(p, dir){
  if (p.td) return [t("strip.result.td"), "good"];
  if (p.k === "fg") return p.made ? [t("strip.result.fg"), "good"] : [t("strip.result.fgMissed"), "bad"];
  if (p.k === "int") return [t("strip.result.int"), "bad"];
  if (p.fum && p.fum.lost) return [t("strip.result.fumble"), "bad"];
  if (p.k === "inc") return [t("strip.result.inc"), "none"];
  const g = Math.round((p.to - p.from) * dir);
  return [g > 0 ? `+${g}` : String(g), g > 0 ? "gain" : g < 0 ? "bad" : "none"];
}

function stPaintList(ctl){
  let q = -1, html = "";
  ctl.reel.forEach((s, k) => {
    const dr = ctl.data.drives[s.d], p = dr.plays[s.i], pq = stQuarter(p);
    if (pq !== q){ q = pq; html += `<li class="stqh">${stQName(pq)}</li>`; }
    const [res, cls] = stResult(p, dr.dir);
    const mine = !ctl.sel.me && stInvolves(p, ctl.sel.who) ? " mine" : "";
    html += `<li><button type="button" class="strow${mine}" data-k="${k}">`
      + `<span class="stclk">${esc((p.clock || "").replace(/^Q\d\s*/, ""))}</span>`
      + `<span class="stteam">${esc(dr.team || "")}</span>`
      + `<span class="stwho">${esc(p.who || t("strip.unnamed"))}</span>`
      + `<span class="stres ${cls}">${esc(res)}</span></button></li>`;
  });
  ctl.ui.list.innerHTML = html;
  ctl.row = -1;
}

/* The lit row follows the play. The list only scrolls itself when it is its own scroller (the
   desktop column); on a phone it is part of the page, and moving the page under a reader who is
   watching the field is the one thing the motion rules forbid. */
function stMarkRow(ctl, k){
  const list = ctl.ui.list, was = list.querySelector(".strow.cur"), row = list.querySelector(`[data-k="${k}"]`);
  ctl.row = k;
  if (was) was.classList.remove("cur");
  if (!row) return;
  row.classList.add("cur");
  if (list.scrollHeight <= list.clientHeight + 1) return;
  const top = row.offsetTop, bottom = top + row.offsetHeight;
  if (top < list.scrollTop + 24 || bottom > list.scrollTop + list.clientHeight - 24){
    list.scrollTo({top: top - list.clientHeight / 3, behavior: ST_REDUCED ? "auto" : "smooth"});
  }
}

/* One point on the reel onto the field. Crossing into another drive rebuilds the stage first. */
function stSeek(ctl, T, hold = 1){
  ctl.T = T;
  const k = stSegAt(ctl, T), s = ctl.reel[k], f = T <= 0 ? 0 : T - k;
  if (s.d !== ctl.at) stShowDrive(ctl, s.d, true);
  stRender(ctl, s.i + f, hold);
  ctl.ui.slider.value = T;
  if (k !== ctl.row) stMarkRow(ctl, k);
}

/* A new selection keeps the reader's place when it can: the play on the field if the new reel
   holds it, else the next play it holds, else the top. */
function stSelect(ctl, patch){
  const cur = ctl.reel ? ctl.reel[stSegAt(ctl, ctl.T)] : null, done = ctl.T > 0 && Number.isInteger(ctl.T);
  Object.assign(ctl.sel, patch);
  ctl.reel = stReelOf(ctl.data, ctl.sel);
  if (!ctl.reel.length){ ctl.sel.q = 0; ctl.reel = stReelOf(ctl.data, ctl.sel); }
  stStop(ctl);
  if (ctl.pose) ctl.pose.mark(ctl.sel.me ? ctl.sel.who : null);
  stPaintFilt(ctl);
  stPaintList(ctl);
  ctl.ui.slider.max = ctl.reel.length;
  stFitCap(ctl);
  let T = 0;
  if (cur){
    const k = ctl.reel.findIndex(s => s.d > cur.d || (s.d === cur.d && s.i >= cur.i));
    const same = k >= 0 && ctl.reel[k].d === cur.d && ctl.reel[k].i === cur.i;
    T = k < 0 ? 0 : same && done ? k + 1 : k;
  }
  stSeek(ctl, T);
}
