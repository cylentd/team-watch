/* ------------------------------------------------------------------
   THE BOARD — the view: which position, who is on it, and who leads.

   One component does three jobs, which is why it is the whole surface. With nobody picked each
   lane names its own leader, so the board arrives as a leaderboard. With one pick it is that
   player against the field. With two it is a duel, and the distance between the dots is the
   answer on that stat.

   NO COMPOSITE SCORE. "Overall" here is a count of lanes, not a rating: six stats ff-jarvis
   publishes separately, weighted into one number by this page, would be this page inventing a
   model — and nothing on it is backtested. Counting the lanes each player is ahead on says the
   same thing out of numbers already on the screen, and a reader can check it by looking.
------------------------------------------------------------------ */
const BD_POSITIONS = ["QB", "RB", "WR", "TE"];
let BD_POS = "RB";
let BD_PICKS = [];   // slugs, newest last, at most two
let BD_NOTE = "";    // why the last pick did not land, cleared by the next render

const bdPicked = () => BD_PICKS.map(s => bdRows(BD_POS).find(r => r.slug === s)).filter(Boolean);

/* Lanes won, counted only where both players have a number: an unmeasured stat is not a stat he
   lost. A tie is comparable and belongs in the denominator, so "leads 3 of 6" can sit against an
   opponent on 2 without the pair adding to 6. */
function bdTally(pos, axes, picks){
  const out = {a: 0, b: 0, of: 0};
  axes.forEach(x => {
    const by = sheetValues(pos, x.id);
    const va = by[picks[0].slug], vb = by[picks[1].slug];
    if (va === undefined || vb === undefined) return;
    out.of += 1;
    if (va > vb) out.a += 1; else if (vb > va) out.b += 1;
  });
  return out;
}

function bdLeadHTML(pos, axes, picks){
  if (!picks.length) return `<div class="bd-lead">${t("board.lead.none", {pos})}</div>`;
  if (picks.length === 1)
    return `<div class="bd-lead">${t("board.lead.one", {name: esc(nameInitial(picks[0].n)), pos})}</div>`;
  const k = bdTally(pos, axes, picks);
  if (!k.of) return `<div class="bd-lead">${t("board.lead.noShared")}</div>`;
  if (k.a === k.b) return `<div class="bd-lead">${t("board.lead.level", {n: k.a, of: k.of})}</div>`;
  const win = k.a > k.b ? picks[0] : picks[1];
  return `<div class="bd-lead">${t("board.lead.two",
    {name: `<b class="on">${esc(nameInitial(win.n))}</b>`, n: Math.max(k.a, k.b), of: k.of})}</div>`;
}

/* The chips are the legend the rail would otherwise need: the same two initials, beside the whole
   name, in the order the lanes read them. Each drops itself and there is no Clear beside them --
   with at most two chips a Clear removes one tap and, at 360px, wraps onto a row of its own. */
function bdChipsHTML(picks){
  if (!picks.length) return "";
  return `<div class="bd-picks">${picks.map(p =>
    `<span class="bd-pick"><span class="bd-key">${esc(initials(p.n))}</span
      ><b>${esc(nameInitial(p.n))}</b><button type="button" class="bd-x" data-bddrop="${esc(p.slug)}"
        aria-label="${t("board.action.remove", {name: esc(p.n)})}">✕</button></span>`).join("")}</div>`;
}

function bdControlsHTML(){
  return `<div class="filters">
    <span class="lbl">${t("board.filter.position")}</span>
    ${BD_POSITIONS.filter(p => bdAxes(p).length).map(p =>
      `<button class="chip" data-bdpos="${p}" aria-pressed="${BD_POS === p}">${p}</button>`).join("")}
    <span style="flex:1"></span>
    <button class="chip bd-add" data-bdadd>${t("board.action.add")}</button>
  </div>`;
}

function bdViewHTML(){
  const axes = bdAxes(BD_POS);
  if (!axes.length) return `<div class="wrap"><div class="state-empty" style="min-height:220px">
    <div><b>${t("board.empty.noSheetTitle")}</b><span>${t("board.empty.noSheetSub")}</span></div></div></div>`;
  const picks = bdPicked();
  return `<div class="wrap">
    ${bdControlsHTML()}
    ${BD_NOTE ? `<p class="bd-note">${BD_NOTE}</p>` : ""}
    ${bdChipsHTML(picks)}
    ${bdLeadHTML(BD_POS, axes, picks)}
    ${bdLabelsHTML(picks)}
    <div class="bd-lanes">${axes.map((a, i) => bdLaneHTML(BD_POS, a, picks, i)).join("")}</div>
    <div class="note bd-foot">${t("board.foot.source", {n: bdRows(BD_POS).length, pos: BD_POS})}</div>
  </div>`;
}

/* A pick of another position moves the board to his position and keeps only him. The axes are
   position-specific, so two positions cannot share a lane; refusing the pick instead would make
   the reader undo a search he meant, and the position chip visibly moving says what happened. */
function bdAdd(p){
  BD_NOTE = "";
  const row = ((USAGE.sheet || {}).rows || []).find(r => r.slug === p.slug);
  if (!row){
    BD_NOTE = t("board.note.noSheet", {name: esc(nameInitial(p.n))});
  } else {
    if (row.pos !== BD_POS){ BD_POS = row.pos; BD_PICKS = []; }
    BD_PICKS = [...BD_PICKS.filter(s => s !== row.slug), row.slug].slice(-2);
  }
  render();
}

function wireBd(v){
  const set = (sel, fn) => v.querySelectorAll(sel).forEach(b => b.addEventListener("click", () => { fn(b); render(); }));
  // Switching position drops the picks: they are rows of the position that just left the screen.
  set("[data-bdpos]", b => { BD_NOTE = ""; if (b.dataset.bdpos !== BD_POS){ BD_POS = b.dataset.bdpos; BD_PICKS = []; } });
  set("[data-bddrop]", b => { BD_NOTE = ""; BD_PICKS = BD_PICKS.filter(s => s !== b.dataset.bddrop); });
  // The picker is the app's own search sheet, handed a slot to fill instead of a profile to open.
  v.querySelectorAll("[data-bdadd]").forEach(b => b.addEventListener("click", () => searchOpen(bdAdd)));
}
